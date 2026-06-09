from pathlib import Path
from types import SimpleNamespace

from tests.test_helpers import _Column, _Query, _Result, load_isolated_module


def _load_provider_module(name):
    root = Path(__file__).resolve().parents[2]
    module_path = root / "bazarr" / "api" / "providers" / f"providers_{name}.py"

    class _Namespace:
        def __init__(self, *args, **kwargs):
            pass

        def route(self, *args, **kwargs):
            return lambda cls: cls

        def model(self, *args, **kwargs):
            return {}

        def response(self, *args, **kwargs):
            return lambda fn: fn

        def doc(self, *args, **kwargs):
            return lambda fn: fn

    class _Parser:
        def add_argument(self, *args, **kwargs):
            return None

        def parse_args(self):
            return {}

    table_movies = SimpleNamespace(
        title=_Column("title"),
        path=_Column("path"),
        sceneName=_Column("sceneName"),
        profileId=_Column("profileId"),
        missing_subtitles=_Column("missing_subtitles"),
        radarrId=_Column("radarrId"),
    )
    table_episodes = SimpleNamespace(
        path=_Column("path"),
        sceneName=_Column("sceneName"),
        missing_subtitles=_Column("missing_subtitles"),
        sonarrEpisodeId=_Column("sonarrEpisodeId"),
    )
    table_shows = SimpleNamespace(
        title=_Column("title"),
        profileId=_Column("profileId"),
    )

    return load_isolated_module(
        f"api.providers.providers_{name}",
        module_path,
        ["api", "api.providers", "app", "utilities", "subtitles", "subtitles.indexer"],
        {
            "flask_restx": SimpleNamespace(
                Resource=object,
                Namespace=_Namespace,
                reqparse=SimpleNamespace(RequestParser=_Parser),
                fields=SimpleNamespace(
                    List=lambda *args, **kwargs: None,
                    String=lambda *args, **kwargs: None,
                    Integer=lambda *args, **kwargs: None,
                ),
                marshal=lambda data, model, envelope=None: data,
            ),
            "api.utils": SimpleNamespace(
                authenticate=lambda fn: fn,
                normalize_flag_token=lambda value: "True"
                if isinstance(value, str) and value.strip().lower() == "true"
                else "False",
            ),
            "app.database": SimpleNamespace(
                TableMovies=table_movies,
                TableEpisodes=table_episodes,
                TableShows=table_shows,
                database=SimpleNamespace(execute=lambda stmt: _Result(first_value=None)),
                select=lambda *args, **kwargs: _Query(),
                get_subtitles=lambda **kwargs: [],
            ),
            "utilities.path_mappings": SimpleNamespace(
                path_mappings=SimpleNamespace(
                    path_replace=lambda path: path,
                    path_replace_movie=lambda path: path,
                )
            ),
            "app.get_providers": SimpleNamespace(get_providers=lambda: []),
            "subtitles.manual": SimpleNamespace(
                manual_search=lambda *args, **kwargs: [],
                episode_manually_download_specific_subtitle=lambda *args, **kwargs: None,
                movie_manually_download_specific_subtitle=lambda *args, **kwargs: None,
            ),
            "app.config": SimpleNamespace(settings=SimpleNamespace()),
            "app.jobs_queue": SimpleNamespace(jobs_queue=SimpleNamespace()),
            "subtitles.indexer.movies": SimpleNamespace(
                store_subtitles_movie=lambda *args, **kwargs: None,
                list_missing_subtitles_movies=lambda *args, **kwargs: None,
            ),
            "subtitles.indexer.series": SimpleNamespace(
                store_subtitles=lambda *args, **kwargs: None,
                list_missing_subtitles=lambda *args, **kwargs: None,
            ),
        },
    )


def test_provider_movies_get_reindexes_when_index_list_is_none():
    module = _load_provider_module("movies")
    movie_info = SimpleNamespace(
        title="Movie",
        path="/movies/movie.mkv",
        sceneName=None,
        profileId=1,
        missing_subtitles="['en']",
    )
    store_calls = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie_info)

    module.ProviderMovies.get_request_parser = SimpleNamespace(parse_args=lambda: {"radarrid": 7})
    module.database = _Database()
    module.get_subtitles = lambda **kwargs: None
    module.store_subtitles_movie = lambda movie_id: store_calls.append(movie_id)
    module.path_mappings.path_replace_movie = lambda path: path
    module.os.path.exists = lambda path: True
    module.get_providers = lambda: ["provider"]
    module.manual_search = lambda *args, **kwargs: []
    module.marshal = lambda data, model, envelope=None: data

    result = module.ProviderMovies().get()

    assert store_calls == [7]
    assert result == []


def test_provider_movies_get_handles_malformed_index_entries():
    module = _load_provider_module("movies")
    movie_info = SimpleNamespace(
        title="Movie",
        path="/movies/movie.mkv",
        sceneName=None,
        profileId=1,
        missing_subtitles="['en']",
    )
    store_calls = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie_info)

    module.ProviderMovies.get_request_parser = SimpleNamespace(parse_args=lambda: {"radarrid": 7})
    module.database = _Database()
    module.get_subtitles = lambda **kwargs: [{"path": None}]
    module.store_subtitles_movie = lambda movie_id: store_calls.append(movie_id)
    module.path_mappings.path_replace_movie = lambda path: path
    module.os.path.exists = lambda path: True
    module.get_providers = lambda: ["provider"]
    module.manual_search = lambda *args, **kwargs: []
    module.marshal = lambda data, model, envelope=None: data

    result = module.ProviderMovies().get()

    assert store_calls == [7]
    assert result == []


def test_provider_movies_get_reindexes_when_index_entry_is_missing_path_key():
    module = _load_provider_module("movies")
    movie_info = SimpleNamespace(
        title="Movie",
        path="/movies/movie.mkv",
        sceneName=None,
        profileId=1,
        missing_subtitles="['en']",
    )
    store_calls = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie_info)

    module.ProviderMovies.get_request_parser = SimpleNamespace(parse_args=lambda: {"radarrid": 7})
    module.database = _Database()
    module.get_subtitles = lambda **kwargs: [{}]
    module.store_subtitles_movie = lambda movie_id: store_calls.append(movie_id)
    module.path_mappings.path_replace_movie = lambda path: path
    module.os.path.exists = lambda path: True
    module.get_providers = lambda: ["provider"]
    module.manual_search = lambda *args, **kwargs: []
    module.marshal = lambda data, model, envelope=None: data

    result = module.ProviderMovies().get()

    assert store_calls == [7]
    assert result == []


def test_provider_episodes_get_reindexes_when_index_list_is_none():
    module = _load_provider_module("episodes")
    episode_info = SimpleNamespace(
        title="Series",
        path="/series/episode.mkv",
        sceneName=None,
        profileId=1,
        missing_subtitles="['en']",
    )
    store_calls = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode_info)

    module.ProviderEpisodes.get_request_parser = SimpleNamespace(parse_args=lambda: {"episodeid": 11})
    module.database = _Database()
    module.get_subtitles = lambda **kwargs: None
    module.store_subtitles = lambda episode_id: store_calls.append(episode_id)
    module.path_mappings.path_replace = lambda path: path
    module.os.path.exists = lambda path: True
    module.get_providers = lambda: ["provider"]
    module.manual_search = lambda *args, **kwargs: []
    module.marshal = lambda data, model, envelope=None: data

    result = module.ProviderEpisodes().get()

    assert store_calls == [11]
    assert result == []


def test_provider_episodes_get_handles_malformed_index_entries():
    module = _load_provider_module("episodes")
    episode_info = SimpleNamespace(
        title="Series",
        path="/series/episode.mkv",
        sceneName=None,
        profileId=1,
        missing_subtitles="['en']",
    )
    store_calls = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode_info)

    module.ProviderEpisodes.get_request_parser = SimpleNamespace(parse_args=lambda: {"episodeid": 11})
    module.database = _Database()
    module.get_subtitles = lambda **kwargs: [{"path": None}]
    module.store_subtitles = lambda episode_id: store_calls.append(episode_id)
    module.path_mappings.path_replace = lambda path: path
    module.os.path.exists = lambda path: True
    module.get_providers = lambda: ["provider"]
    module.manual_search = lambda *args, **kwargs: []
    module.marshal = lambda data, model, envelope=None: data

    result = module.ProviderEpisodes().get()

    assert store_calls == [11]
    assert result == []


def test_provider_episodes_get_reindexes_when_index_entry_is_missing_path_key():
    module = _load_provider_module("episodes")
    episode_info = SimpleNamespace(
        title="Series",
        path="/series/episode.mkv",
        sceneName=None,
        profileId=1,
        missing_subtitles="['en']",
    )
    store_calls = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode_info)

    module.ProviderEpisodes.get_request_parser = SimpleNamespace(parse_args=lambda: {"episodeid": 11})
    module.database = _Database()
    module.get_subtitles = lambda **kwargs: [{}]
    module.store_subtitles = lambda episode_id: store_calls.append(episode_id)
    module.path_mappings.path_replace = lambda path: path
    module.os.path.exists = lambda path: True
    module.get_providers = lambda: ["provider"]
    module.manual_search = lambda *args, **kwargs: []
    module.marshal = lambda data, model, envelope=None: data

    result = module.ProviderEpisodes().get()

    assert store_calls == [11]
    assert result == []


def test_provider_movies_get_returns_not_found_when_row_disappears_after_reindex():
    module = _load_provider_module("movies")
    movie_info = SimpleNamespace(
        title="Movie",
        path="/movies/movie.mkv",
        sceneName=None,
        profileId=1,
        missing_subtitles="['en']",
    )

    class _Database:
        def __init__(self):
            self.calls = 0

        def execute(self, statement):
            self.calls += 1
            return _Result(first_value=movie_info if self.calls == 1 else None)

    module.ProviderMovies.get_request_parser = SimpleNamespace(parse_args=lambda: {"radarrid": 7})
    module.database = _Database()
    module.get_subtitles = lambda **kwargs: None
    module.store_subtitles_movie = lambda movie_id: None

    result = module.ProviderMovies().get()

    assert result == ("Movie not found", 404)


def test_provider_episodes_get_returns_not_found_when_row_disappears_after_reindex():
    module = _load_provider_module("episodes")
    episode_info = SimpleNamespace(
        title="Series",
        path="/series/episode.mkv",
        sceneName=None,
        profileId=1,
        missing_subtitles="['en']",
    )

    class _Database:
        def __init__(self):
            self.calls = 0

        def execute(self, statement):
            self.calls += 1
            return _Result(first_value=episode_info if self.calls == 1 else None)

    module.ProviderEpisodes.get_request_parser = SimpleNamespace(parse_args=lambda: {"episodeid": 11})
    module.database = _Database()
    module.get_subtitles = lambda **kwargs: None
    module.store_subtitles = lambda episode_id: None

    result = module.ProviderEpisodes().get()

    assert result == ("Episode not found", 404)


def test_provider_movies_get_uses_none_string_for_missing_scene_name():
    module = _load_provider_module("movies")
    movie_info = SimpleNamespace(
        title="Movie",
        path="/movies/movie.mkv",
        sceneName=None,
        profileId=1,
        missing_subtitles="['en']",
    )
    captured_scene = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie_info)

    module.ProviderMovies.get_request_parser = SimpleNamespace(parse_args=lambda: {"radarrid": 7})
    module.database = _Database()
    module.get_subtitles = lambda **kwargs: [{"path": "/subs.srt"}]
    module.path_mappings.path_replace_movie = lambda path: path
    module.os.path.exists = lambda path: True
    module.get_providers = lambda: ["provider"]
    module.manual_search = lambda *args, **kwargs: captured_scene.append(args[3]) or []
    module.marshal = lambda data, model, envelope=None: data

    result = module.ProviderMovies().get()

    assert result == []
    assert captured_scene == ["None"]


def test_provider_episodes_get_uses_none_string_for_missing_scene_name():
    module = _load_provider_module("episodes")
    episode_info = SimpleNamespace(
        title="Series",
        path="/series/episode.mkv",
        sceneName=None,
        profileId=1,
        missing_subtitles="['en']",
    )
    captured_scene = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode_info)

    module.ProviderEpisodes.get_request_parser = SimpleNamespace(parse_args=lambda: {"episodeid": 11})
    module.database = _Database()
    module.get_subtitles = lambda **kwargs: [{"path": "/subs.srt"}]
    module.path_mappings.path_replace = lambda path: path
    module.os.path.exists = lambda path: True
    module.get_providers = lambda: ["provider"]
    module.manual_search = lambda *args, **kwargs: captured_scene.append(args[3]) or []
    module.marshal = lambda data, model, envelope=None: data

    result = module.ProviderEpisodes().get()

    assert result == []
    assert captured_scene == ["None"]


def test_provider_movies_get_returns_file_missing_when_path_is_none():
    module = _load_provider_module("movies")
    movie_info = SimpleNamespace(
        title="Movie",
        path=None,
        sceneName=None,
        profileId=1,
        missing_subtitles="['en']",
    )

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie_info)

    module.ProviderMovies.get_request_parser = SimpleNamespace(parse_args=lambda: {"radarrid": 7})
    module.database = _Database()
    module.get_subtitles = lambda **kwargs: [{"path": "/movies/sub.srt", "embedded_track_id": 1}]

    result = module.ProviderMovies().get()

    assert result == ("Movie file not found. Path mapping issue?", 500)


def test_provider_episodes_get_returns_file_missing_when_path_is_none():
    module = _load_provider_module("episodes")
    episode_info = SimpleNamespace(
        title="Series",
        path=None,
        sceneName=None,
        profileId=1,
        missing_subtitles="['en']",
    )

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode_info)

    module.ProviderEpisodes.get_request_parser = SimpleNamespace(parse_args=lambda: {"episodeid": 11})
    module.database = _Database()
    module.get_subtitles = lambda **kwargs: [{"path": "/series/sub.srt", "embedded_track_id": 1}]

    result = module.ProviderEpisodes().get()

    assert result == ("Episode file not found. Path mapping issue?", 500)


def test_provider_movies_post_normalizes_malformed_flags():
    module = _load_provider_module("movies")
    captured = {}

    module.ProviderMovies.post_request_parser = SimpleNamespace(
        parse_args=lambda: {
            "radarrid": 7,
            "hi": None,
            "forced": 1,
            "original_format": "not-a-bool",
            "provider": "provider",
            "subtitle": "sub-id",
        }
    )
    module.movie_manually_download_specific_subtitle = lambda **kwargs: captured.update(kwargs)

    result = module.ProviderMovies().post()

    assert result == ("", 204)
    assert captured["hi"] == "False"
    assert captured["forced"] == "False"
    assert captured["use_original_format"] == "False"


def test_provider_episodes_post_normalizes_malformed_flags():
    module = _load_provider_module("episodes")
    captured = {}

    module.ProviderEpisodes.post_request_parser = SimpleNamespace(
        parse_args=lambda: {
            "seriesid": 5,
            "episodeid": 11,
            "hi": None,
            "forced": {},
            "original_format": "truthy",
            "provider": "provider",
            "subtitle": "sub-id",
        }
    )
    module.episode_manually_download_specific_subtitle = lambda **kwargs: captured.update(kwargs)

    result = module.ProviderEpisodes().post()

    assert result == ("", 204)
    assert captured["hi"] == "False"
    assert captured["forced"] == "False"
    assert captured["use_original_format"] == "False"

from pathlib import Path
from types import SimpleNamespace

from tests.test_helpers import _Column, _Query, load_isolated_module


def _load_api_subtitles_module(module_name):
    root = Path(__file__).resolve().parents[2]
    module_path = root / "bazarr" / "api" / ("movies" if module_name == "movies_subtitles" else "episodes") / f"{module_name}.py"

    class _Namespace:
        def __init__(self, *args, **kwargs):
            pass

        def route(self, *args, **kwargs):
            return lambda cls: cls

        def doc(self, *args, **kwargs):
            return lambda fn: fn

        def response(self, *args, **kwargs):
            return lambda fn: fn

    class _Parser:
        def add_argument(self, *args, **kwargs):
            return None

        def parse_args(self):
            return {}

    table_movies = SimpleNamespace(path=_Column("path"), audio_language=_Column("audio_language"), radarrId=_Column("radarrId"))
    table_episodes = SimpleNamespace(path=_Column("path"), audio_language=_Column("audio_language"), sonarrEpisodeId=_Column("sonarrEpisodeId"))
    table_shows = SimpleNamespace(title=_Column("title"))

    module_import_name = f"api.movies.{module_name}" if module_name == "movies_subtitles" else f"api.episodes.{module_name}"

    return load_isolated_module(
        module_import_name,
        module_path,
        ["api", "api.movies", "api.episodes", "app", "utilities", "subtitles", "subtitles.mass_download", "subtitles.tools"],
        {
            "flask_restx": SimpleNamespace(
                Resource=object,
                Namespace=_Namespace,
                reqparse=SimpleNamespace(RequestParser=_Parser),
            ),
            "subliminal_patch.core": SimpleNamespace(SUBTITLE_EXTENSIONS={".srt", ".ass"}),
            "werkzeug.datastructures": SimpleNamespace(FileStorage=object),
            "app.database": SimpleNamespace(
                TableMovies=table_movies,
                TableEpisodes=table_episodes,
                TableShows=table_shows,
                get_profile_id=lambda **kwargs: 1,
                database=SimpleNamespace(execute=lambda stmt: None),
                select=lambda *args, **kwargs: _Query(),
            ),
            "utilities.path_mappings": SimpleNamespace(
                path_mappings=SimpleNamespace(
                    path_replace=lambda path: path,
                    path_replace_movie=lambda path: path,
                    path_replace_reverse=lambda path: path,
                    path_replace_reverse_movie=lambda path: path,
                )
            ),
            "subtitles.upload": SimpleNamespace(manual_upload_subtitle=lambda **kwargs: ("", 204)),
            "subtitles.mass_download.movies": SimpleNamespace(movie_download_specific_subtitles=lambda **kwargs: None),
            "subtitles.mass_download.series": SimpleNamespace(episode_download_specific_subtitles=lambda **kwargs: None),
            "subtitles.download": SimpleNamespace(generate_subtitles=lambda *args, **kwargs: []),
            "subtitles.tools.delete": SimpleNamespace(delete_subtitles=lambda **kwargs: True),
            "app.event_handler": SimpleNamespace(event_stream=lambda **kwargs: None),
            "app.config": SimpleNamespace(settings=SimpleNamespace()),
            "app.jobs_queue": SimpleNamespace(jobs_queue=SimpleNamespace()),
            "api.utils": SimpleNamespace(
                authenticate=lambda fn: fn,
                normalize_flag_token=lambda value: "True"
                if isinstance(value, str) and value.strip().lower() == "true"
                else "False",
            ),
        },
    )


def test_movies_subtitles_patch_normalizes_malformed_flags():
    module = _load_api_subtitles_module("movies_subtitles")
    captured = {}

    module.MoviesSubtitles.patch_request_parser = SimpleNamespace(
        parse_args=lambda: {"radarrid": 7, "language": "en", "hi": None, "forced": {}}
    )
    module.movie_download_specific_subtitles = lambda **kwargs: captured.update(kwargs)

    result = module.MoviesSubtitles().patch()

    assert result == ("", 204)
    assert captured["hi"] == "False"
    assert captured["forced"] == "False"


def test_episodes_subtitles_patch_normalizes_malformed_flags():
    module = _load_api_subtitles_module("episodes_subtitles")
    captured = {}

    module.EpisodesSubtitles.patch_request_parser = SimpleNamespace(
        parse_args=lambda: {"seriesid": 5, "episodeid": 11, "language": "fr", "hi": None, "forced": 123}
    )
    module.episode_download_specific_subtitles = lambda **kwargs: captured.update(kwargs)

    result = module.EpisodesSubtitles().patch()

    assert result == ("", 204)
    assert captured["hi"] == "False"
    assert captured["forced"] == "False"

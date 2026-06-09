import random
from types import SimpleNamespace

import pytest

from tests.test_helpers import _Result, load_mass_download_module


def test_movies_download_subtitles_builds_language_tuples_and_records_downloads(monkeypatch):
    module = load_mass_download_module("movies")

    movie = SimpleNamespace(
        path="/movies/movie.mkv",
        missing_subtitles="['en', 'fr:forced']",
        audio_language="['eng']",
        radarrId=7,
        sceneName="Scene",
        title="Movie",
        year=2024,
        tags=[],
        monitored=True,
        profileId=44,
    )
    generate_calls = []
    stored = []
    history = []
    notifications = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/movies/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "get_providers", lambda: ["provider"])
    monkeypatch.setattr(module, "store_subtitles_movie", lambda movie_id: stored.append(movie_id))
    monkeypatch.setattr(module, "history_log_movie", lambda *args: history.append(args))
    monkeypatch.setattr(module, "send_notifications_movie", lambda *args: notifications.append(args))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )
    def _generate(*args, **kwargs):
        generate_calls.append((args, kwargs))
        return iter([SimpleNamespace(message="downloaded")])

    monkeypatch.setattr(module, "generate_subtitles", _generate)

    module.movies_download_subtitles(7, job_id="job")

    assert generate_calls[0][0][1] == [("en", "False", "False"), ("fr", "False", "True")]
    assert stored == [7]
    assert len(history) == 1
    assert notifications == [(7, "downloaded")]


def test_movies_download_subtitles_falls_back_to_legacy_missing_text(monkeypatch):
    module = load_mass_download_module("movies")

    movie = SimpleNamespace(
        path="/movies/movie.mkv",
        missing_subtitles="['en']",
        audio_language="['eng']",
        radarrId=7,
        sceneName="Scene",
        title="Movie",
        year=2024,
        tags=[],
        monitored=True,
        profileId=44,
    )
    generated = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/movies/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "get_providers", lambda: ["provider"])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: generated.append(args[1]) or iter(()))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.movies_download_subtitles(7, job_id="job")

    assert generated == [[("en", "False", "False")]]


def test_movies_download_subtitles_handles_result_without_message(monkeypatch):
    module = load_mass_download_module("movies")

    movie = SimpleNamespace(
        path="/movies/movie.mkv",
        missing_subtitles="['en']",
        audio_language="['eng']",
        radarrId=7,
        sceneName="Scene",
        title="Movie",
        year=2024,
        tags=[],
        monitored=True,
        profileId=44,
    )
    history = []
    notifications = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/movies/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "get_providers", lambda: ["provider"])
    monkeypatch.setattr(module, "store_subtitles_movie", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "history_log_movie", lambda *args: history.append(args))
    monkeypatch.setattr(module, "send_notifications_movie", lambda *args: notifications.append(args))
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: iter([SimpleNamespace()]))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.movies_download_subtitles(7, job_id="job")

    assert len(history) == 1
    assert notifications == []


def test_movies_download_subtitles_enqueues_job_without_job_id(monkeypatch):
    module = load_mass_download_module("movies")

    job_calls = []
    module.database.scalar = lambda statement: "Movie"
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: job_calls.append((args, kwargs)),
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.movies_download_subtitles(7)

    assert job_calls and "Downloading missing subtitles for Movie" in job_calls[0][0][0]


def test_movies_download_subtitles_reports_throttled_when_no_providers(monkeypatch):
    module = load_mass_download_module("movies")

    movie = SimpleNamespace(
        path="/movies/movie.mkv",
        missing_subtitles="['en']",
        audio_language="['eng']",
        radarrId=7,
        sceneName="Scene",
        title="Movie",
        year=2024,
        tags=[],
        monitored=True,
        profileId=44,
    )
    progress = []
    names = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/movies/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "get_providers", lambda: [])
    monkeypatch.setattr(module, "store_subtitles_movie", lambda movie_id: store_calls.append(movie_id))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda **kwargs: progress.append(kwargs),
            update_job_name=lambda **kwargs: names.append(kwargs["new_job_name"]),
        ),
    )

    module.movies_download_subtitles(7, job_id="job")

    assert progress[-1]["progress_message"] == "All providers throttled"
    assert names == ["Downloaded missing subtitles for Movie (2024)"]


def test_movies_download_subtitles_reindexes_when_index_is_incomplete(monkeypatch):
    module = load_mass_download_module("movies")

    movie = SimpleNamespace(
        path="/movies/movie.mkv",
        missing_subtitles="['en']",
        audio_language="['eng']",
        radarrId=7,
        sceneName="Scene",
        title="Movie",
        year=2024,
        tags=[],
        monitored=True,
        profileId=44,
    )
    store_calls = []

    class _Database:
        def __init__(self):
            self.calls = 0

        def execute(self, statement):
            self.calls += 1
            return _Result(first_value=movie)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [])
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "get_providers", lambda: [])
    monkeypatch.setattr(module, "store_subtitles_movie", lambda movie_id: store_calls.append(movie_id))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.movies_download_subtitles(7, job_id="job")

    assert store_calls == [7]


def test_movies_download_subtitles_reindexes_when_index_list_is_none(monkeypatch):
    module = load_mass_download_module("movies")

    movie = SimpleNamespace(
        path="/movies/movie.mkv",
        missing_subtitles="['en']",
        audio_language="['eng']",
        radarrId=7,
        sceneName="Scene",
        title="Movie",
        year=2024,
        tags=[],
        monitored=True,
        profileId=44,
    )
    store_calls = []

    class _Database:
        def __init__(self):
            self.calls = 0

        def execute(self, statement):
            self.calls += 1
            return _Result(first_value=movie)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: None)
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "get_providers", lambda: [])
    monkeypatch.setattr(module, "store_subtitles_movie", lambda movie_id: store_calls.append(movie_id))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.movies_download_subtitles(7, job_id="job")

    assert store_calls == [7]


def test_movies_download_subtitles_rebuilds_missing_list_when_missing_subtitles_is_none(monkeypatch):
    module = load_mass_download_module("movies")

    initial_movie = SimpleNamespace(
        path="/movies/movie.mkv",
        missing_subtitles=None,
        audio_language="['eng']",
        radarrId=7,
        sceneName="Scene",
        title="Movie",
        year=2024,
        tags=[],
        monitored=True,
        profileId=44,
    )
    refreshed_movie = SimpleNamespace(**{**initial_movie.__dict__, "missing_subtitles": "['en']"})
    refresh_calls = []

    class _Database:
        def __init__(self):
            self.calls = 0

        def execute(self, statement):
            self.calls += 1
            return _Result(first_value=initial_movie if self.calls == 1 else refreshed_movie)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/movies/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "get_providers", lambda: [])
    monkeypatch.setattr(module, "list_missing_subtitles_movies", lambda **kwargs: refresh_calls.append(kwargs))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.movies_download_subtitles(7, job_id="job")

    assert refresh_calls == [{"no": 7}]


def test_movies_download_subtitles_raises_when_path_missing(monkeypatch):
    module = load_mass_download_module("movies")

    movie = SimpleNamespace(
        path="/movies/movie.mkv",
        missing_subtitles="['en']",
        audio_language="['eng']",
        radarrId=7,
        sceneName="Scene",
        title="Movie",
        year=2024,
        tags=[],
        monitored=True,
        profileId=44,
    )
    progress = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/movies/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: False)
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda **kwargs: progress.append(kwargs),
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    with pytest.raises(OSError):
        module.movies_download_subtitles(7, job_id="job")

    assert "Movie path doesn't exists" in progress[-1]["progress_message"]


def test_series_download_subtitles_dispatches_each_episode(monkeypatch):
    module = load_mass_download_module("series")

    series_row = SimpleNamespace(path="/series", title="Series")
    episodes = [
        SimpleNamespace(sonarrEpisodeId=11, title="Series", season=1, episode=1, episodeTitle="One"),
        SimpleNamespace(sonarrEpisodeId=22, title="Series", season=1, episode=2, episodeTitle="Two"),
    ]
    episode_calls = []
    progress = []

    class _Database:
        def __init__(self):
            self.calls = 0

        def execute(self, statement):
            self.calls += 1
            if self.calls == 1:
                return _Result(first_value=series_row)
            return _Result(all_value=episodes)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_providers", lambda: ["provider"])
    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(
            general=SimpleNamespace(
                use_whisper_fallback=True,
                use_whisper_fallback_series=True,
            )
        ),
    )
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda **kwargs: progress.append(kwargs),
            update_job_name=lambda *args, **kwargs: None,
        ),
    )
    monkeypatch.setattr(
        module,
        "episode_download_subtitles",
        lambda *args, **kwargs: episode_calls.append((args, kwargs)),
    )
    module.series_download_subtitles(5, job_id="job")

    assert [call[1]["no"] for call in episode_calls] == [11, 22]
    assert all(call[1]["fallback_allowed"] is True for call in episode_calls)
    assert progress[0]["progress_max"] == 2
    assert progress[-1]["progress_message"] == "Search completed"


def test_series_download_subtitles_handles_noninteger_episode_numbers(monkeypatch):
    module = load_mass_download_module("series")

    series_row = SimpleNamespace(path="/series", title="Series")
    episodes = [
        SimpleNamespace(sonarrEpisodeId=11, title="Series", season=None, episode="x", episodeTitle="One"),
    ]
    progress = []
    episode_calls = []

    class _Database:
        def __init__(self):
            self.calls = 0

        def execute(self, statement):
            self.calls += 1
            if self.calls == 1:
                return _Result(first_value=series_row)
            return _Result(all_value=episodes)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_providers", lambda: ["provider"])
    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(
            general=SimpleNamespace(
                use_whisper_fallback=True,
                use_whisper_fallback_series=True,
            )
        ),
    )
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda **kwargs: progress.append(kwargs),
            update_job_name=lambda *args, **kwargs: None,
        ),
    )
    monkeypatch.setattr(
        module,
        "episode_download_subtitles",
        lambda *args, **kwargs: episode_calls.append((args, kwargs)),
    )

    module.series_download_subtitles(5, job_id="job")

    assert episode_calls and episode_calls[0][1]["no"] == 11
    assert any("progress_message" in item for item in progress)


def test_series_download_subtitles_falls_back_when_batched_missing_languages_are_empty(monkeypatch):
    module = load_mass_download_module("series")

    series_row = SimpleNamespace(path="/series", title="Series")
    episodes = [SimpleNamespace(sonarrEpisodeId=11, title="Series", season=1, episode=1, episodeTitle="One")]
    episode_calls = []

    class _Database:
        def __init__(self):
            self.calls = 0

        def execute(self, statement):
            self.calls += 1
            if self.calls == 1:
                return _Result(first_value=series_row)
            return _Result(all_value=episodes)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_providers", lambda: ["provider"])
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )
    monkeypatch.setattr(
        module,
        "episode_download_subtitles",
        lambda *args, **kwargs: episode_calls.append(kwargs),
    )

    module.series_download_subtitles(5, job_id="job")

    # An empty get_missing_languages_map result falls back to the episode helper's own lookup path.
    assert "missing_languages" not in episode_calls[0]


def test_series_download_subtitles_enqueues_job_without_job_id(monkeypatch):
    module = load_mass_download_module("series")

    job_calls = []
    module.database.scalar = lambda statement: "Series"
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: job_calls.append((args, kwargs)),
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.series_download_subtitles(5)

    assert job_calls and "Downloading missing subtitles for Series" in job_calls[0][0][0]


def test_series_download_subtitles_raises_when_series_path_missing(monkeypatch):
    module = load_mass_download_module("series")

    class _Database:
        def execute(self, statement):
            return _Result(first_value=SimpleNamespace(path="/series", title="Series"))

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: False)

    with pytest.raises(OSError):
        module.series_download_subtitles(5, job_id="job")


def test_series_download_subtitles_handles_empty_episode_list(monkeypatch):
    module = load_mass_download_module("series")

    series_row = SimpleNamespace(path="/series", title="Series")
    progress = []

    class _Database:
        def __init__(self):
            self.calls = 0

        def execute(self, statement):
            self.calls += 1
            if self.calls == 1:
                return _Result(first_value=series_row)
            return _Result(all_value=[])

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda **kwargs: progress.append(kwargs),
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.series_download_subtitles(5, job_id="job")

    assert progress[-1]["progress_message"] == "Search completed"


def test_series_download_subtitles_reports_throttled_when_no_providers(monkeypatch):
    module = load_mass_download_module("series")

    series_row = SimpleNamespace(path="/series", title="Series")
    episodes = [SimpleNamespace(sonarrEpisodeId=11, title="Series", season=1, episode=1, episodeTitle="One")]
    progress = []

    class _Database:
        def __init__(self):
            self.calls = 0

        def execute(self, statement):
            self.calls += 1
            if self.calls == 1:
                return _Result(first_value=series_row)
            return _Result(all_value=episodes)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_providers", lambda: [])
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda **kwargs: progress.append(kwargs),
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.series_download_subtitles(5, job_id="job")

    assert progress[-1]["progress_message"] == "All providers throttled"


def test_episode_download_subtitles_uses_missing_languages_and_records_downloads(monkeypatch):
    module = load_mass_download_module("series")

    episode = SimpleNamespace(
        path="/series/episode.mkv",
        missing_subtitles="['en', 'fr:hi']",
        monitored=True,
        sonarrEpisodeId=11,
        sceneName="Scene",
        tags=[],
        title="Series",
        sonarrSeriesId=5,
        audio_language="['eng']",
        seriesType="standard",
        episodeTitle="Pilot",
        season=1,
        episode=1,
        profileId=44,
    )
    generated = []
    stored = []
    history = []
    notifications = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/series/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "store_subtitles", lambda episode_id: stored.append(episode_id))
    monkeypatch.setattr(module, "history_log", lambda *args: history.append(args))
    monkeypatch.setattr(module, "send_notifications", lambda *args: notifications.append(args))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )
    monkeypatch.setattr(
        module,
        "generate_subtitles",
        lambda *args, **kwargs: generated.append((args, kwargs)) or iter([SimpleNamespace(message="done")]),
    )

    module.episode_download_subtitles(
        11,
        job_id="job",
        job_sub_function=True,
        providers_list=["provider"],
        fallback_allowed=True,
    )

    assert generated[0][0][1] == [("en", "False", "False"), ("fr", "True", "False")]
    assert generated[0][1]["fallback_allowed"] is True
    assert stored == [11]
    assert len(history) == 1
    assert notifications == [(5, 11, "done")]


def test_movies_download_subtitles_handles_malformed_audio_profile_languages(monkeypatch):
    module = load_mass_download_module("movies")

    movie = SimpleNamespace(
        path="/movies/movie.mkv",
        missing_subtitles="['en']",
        audio_language="['eng']",
        radarrId=7,
        sceneName="Scene",
        title="Movie",
        year=2024,
        tags=[],
        monitored=True,
        profileId=44,
    )
    captured_audio = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/movies/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [None, {"bad": "shape"}])
    monkeypatch.setattr(module, "get_providers", lambda: ["provider"])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: captured_audio.append(args[2]) or iter(()))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.movies_download_subtitles(7, job_id="job")

    assert captured_audio == [None]


def test_episode_download_subtitles_handles_malformed_audio_profile_languages(monkeypatch):
    module = load_mass_download_module("series")

    episode = SimpleNamespace(
        path="/series/episode.mkv",
        missing_subtitles="['en']",
        monitored=True,
        sonarrEpisodeId=11,
        sceneName="Scene",
        tags=[],
        title="Series",
        sonarrSeriesId=5,
        audio_language="['eng']",
        seriesType="standard",
        episodeTitle="Pilot",
        season=1,
        episode=1,
        profileId=44,
    )
    captured_audio = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/series/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [None, {"bad": "shape"}])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: captured_audio.append(args[2]) or iter(()))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.episode_download_subtitles(11, job_id="job", job_sub_function=True, providers_list=["provider"])

    assert captured_audio == [None]


def test_episode_download_subtitles_handles_noninteger_episode_numbers(monkeypatch):
    module = load_mass_download_module("series")

    episode = SimpleNamespace(
        path="/series/episode.mkv",
        missing_subtitles="['en']",
        monitored=True,
        sonarrEpisodeId=11,
        sceneName="Scene",
        tags=[],
        title="Series",
        sonarrSeriesId=5,
        audio_language="['eng']",
        seriesType="standard",
        episodeTitle="Pilot",
        season="x",
        episode=None,
        profileId=44,
    )
    progress = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/series/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: iter(()))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda **kwargs: progress.append(kwargs),
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.episode_download_subtitles(11, job_id="job", job_sub_function=False, providers_list=["provider"])

    assert any("progress_message" in item for item in progress)


def test_episode_download_subtitles_falls_back_to_legacy_missing_text(monkeypatch):
    module = load_mass_download_module("series")

    episode = SimpleNamespace(
        path="/series/episode.mkv",
        missing_subtitles="['fr:hi']",
        monitored=True,
        sonarrEpisodeId=11,
        sceneName="Scene",
        tags=[],
        title="Series",
        sonarrSeriesId=5,
        audio_language="['eng']",
        seriesType="standard",
        episodeTitle="Pilot",
        season=1,
        episode=1,
        profileId=44,
    )
    generated = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/series/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: generated.append(args[1]) or iter(()))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.episode_download_subtitles(11, job_id="job", job_sub_function=True, providers_list=["provider"])

    assert generated == [[("fr", "True", "False")]]


def test_episode_download_subtitles_handles_result_without_message(monkeypatch):
    module = load_mass_download_module("series")

    episode = SimpleNamespace(
        path="/series/episode.mkv",
        missing_subtitles="['en']",
        monitored=True,
        sonarrEpisodeId=11,
        sceneName="Scene",
        tags=[],
        title="Series",
        sonarrSeriesId=5,
        audio_language="['eng']",
        seriesType="standard",
        episodeTitle="Pilot",
        season=1,
        episode=1,
        profileId=44,
    )
    history = []
    notifications = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/series/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "store_subtitles", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "history_log", lambda *args: history.append(args))
    monkeypatch.setattr(module, "send_notifications", lambda *args: notifications.append(args))
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: iter([SimpleNamespace()]))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.episode_download_subtitles(11, job_id="job", job_sub_function=True, providers_list=["provider"])

    assert len(history) == 1
    assert notifications == []


def test_episode_download_subtitles_raises_when_path_missing(monkeypatch):
    module = load_mass_download_module("series")

    episode = SimpleNamespace(
        path="/series/episode.mkv",
        missing_subtitles="['en']",
        monitored=True,
        sonarrEpisodeId=11,
        sceneName="Scene",
        tags=[],
        title="Series",
        sonarrSeriesId=5,
        audio_language="['eng']",
        seriesType="standard",
        episodeTitle="Pilot",
        season=1,
        episode=1,
        profileId=44,
    )
    progress = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/series/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: False)
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda **kwargs: progress.append(kwargs),
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    with pytest.raises(OSError):
        module.episode_download_subtitles(11, job_id="job", job_sub_function=True, providers_list=["provider"])

    assert "Episode path doesn't exists" in progress[-1]["progress_message"]


def test_episode_download_subtitles_enqueues_job_without_job_id(monkeypatch):
    module = load_mass_download_module("series")

    job_calls = []
    module.database.scalar = lambda statement: "Series"
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: job_calls.append((args, kwargs)),
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.episode_download_subtitles(11)

    assert job_calls and "Downloading missing subtitles for Series" in job_calls[0][0][0]


def test_episode_download_specific_subtitles_emits_event_when_nothing_found(monkeypatch):
    module = load_mass_download_module("series")

    episode_info = SimpleNamespace(
        path="/series/episode.mkv",
        sceneName="Scene",
        audio_language="['eng']",
        season=1,
        episode=2,
        episodeTitle="Second",
        title="Series",
    )
    events = []
    job_names = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode_info)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: iter([]))
    monkeypatch.setattr(module, "event_stream", lambda **kwargs: events.append(kwargs))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda **kwargs: job_names.append(kwargs["new_job_name"]),
        ),
    )

    result = module.episode_download_specific_subtitles(5, 11, "fr", "False", "True", job_id="job")

    assert result == ("", 204)
    assert events == [{"type": "episode", "payload": 11}]
    assert job_names == ["Searching FR:FORCED for Series - S01E02 - Second"]


def test_episode_download_specific_subtitles_returns_file_missing(monkeypatch):
    module = load_mass_download_module("series")

    episode_info = SimpleNamespace(
        path="/series/episode.mkv",
        sceneName="Scene",
        audio_language="['eng']",
        season=1,
        episode=2,
        episodeTitle="Second",
        title="Series",
    )

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode_info)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: False)

    result = module.episode_download_specific_subtitles(5, 11, "fr", "False", "False", job_id="job")

    assert result == ("Episode file not found. Path mapping issue?", 500)


def test_episode_download_specific_subtitles_records_success(monkeypatch):
    module = load_mass_download_module("series")

    episode_info = SimpleNamespace(
        path="/series/episode.mkv",
        sceneName="Scene",
        audio_language="['eng']",
        season=1,
        episode=2,
        episodeTitle="Second",
        title="Series",
    )
    stored = []
    history = []
    notifications = []
    job_names = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode_info)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "store_subtitles", lambda episode_id: stored.append(episode_id))
    monkeypatch.setattr(module, "history_log", lambda *args: history.append(args))
    monkeypatch.setattr(module, "send_notifications", lambda *args: notifications.append(args))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda **kwargs: job_names.append(kwargs["new_job_name"]),
        ),
    )
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: iter([SimpleNamespace(message="done")]))

    result = module.episode_download_specific_subtitles(5, 11, "fr", "True", "False", job_id="job")

    assert result == ("", 204)
    assert stored == [11]
    assert len(history) == 1
    assert notifications == [(5, 11, "done")]
    assert job_names == [
        "Searching FR:HI for Series - S01E02 - Second",
        "Searched FR:HI for Series - S01E02 - Second",
    ]


def test_episode_download_subtitles_reindexes_when_index_list_is_none(monkeypatch):
    module = load_mass_download_module("series")

    episode = SimpleNamespace(
        path="/series/episode.mkv",
        missing_subtitles="['en']",
        monitored=True,
        sonarrEpisodeId=11,
        sceneName="Scene",
        tags=[],
        title="Series",
        sonarrSeriesId=5,
        audio_language="['eng']",
        seriesType="standard",
        episodeTitle="Pilot",
        season=1,
        episode=1,
        profileId=44,
    )
    store_calls = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: None)
    monkeypatch.setattr(module, "store_subtitles", lambda episode_id: store_calls.append(episode_id))
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: iter(()))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.episode_download_subtitles(11, job_id="job", job_sub_function=True, providers_list=["provider"])

    assert store_calls == [11]


def test_movie_download_specific_subtitles_records_success(monkeypatch):
    module = load_mass_download_module("movies")

    movie_info = SimpleNamespace(
        title="Movie",
        path="/movies/movie.mkv",
        sceneName="Scene",
        audio_language="['eng']",
    )
    stored = []
    history = []
    notifications = []
    job_names = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie_info)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "store_subtitles_movie", lambda movie_id: stored.append(movie_id))
    monkeypatch.setattr(module, "history_log_movie", lambda *args: history.append(args))
    monkeypatch.setattr(module, "send_notifications_movie", lambda *args: notifications.append(args))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda **kwargs: job_names.append(kwargs["new_job_name"]),
        ),
    )
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: iter([SimpleNamespace(message="done")]))

    result = module.movie_download_specific_subtitles(7, "fr", "True", "False", job_id="job")

    assert result == ("", 204)
    assert stored == [7]
    assert len(history) == 1
    assert notifications == [(7, "done")]
    assert job_names == ["Searching FR:HI for Movie", "Searched FR:HI for Movie"]


def test_movie_download_specific_subtitles_uses_none_for_missing_scene_name(monkeypatch):
    module = load_mass_download_module("movies")

    movie_info = SimpleNamespace(
        title="Movie",
        path="/movies/movie.mkv",
        sceneName=None,
        audio_language="['eng']",
    )
    captured_scene = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie_info)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: captured_scene.append(args[3]) or iter([]))
    monkeypatch.setattr(module, "event_stream", lambda **kwargs: None)
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda **kwargs: None,
        ),
    )

    result = module.movie_download_specific_subtitles(7, "fr", "False", "False", job_id="job")

    assert result == ("", 204)
    assert captured_scene == [None]


def test_movie_download_specific_subtitles_emits_event_when_nothing_found(monkeypatch):
    module = load_mass_download_module("movies")

    movie_info = SimpleNamespace(
        title="Movie",
        path="/movies/movie.mkv",
        sceneName="Scene",
        audio_language="['eng']",
    )
    events = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie_info)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: iter([]))
    monkeypatch.setattr(module, "event_stream", lambda **kwargs: events.append(kwargs))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    result = module.movie_download_specific_subtitles(7, "fr", "False", "False", job_id="job")

    assert result == ("", 204)
    assert events == [{"type": "movie", "payload": 7}]


def test_movie_download_specific_subtitles_returns_file_missing(monkeypatch):
    module = load_mass_download_module("movies")

    movie_info = SimpleNamespace(
        title="Movie",
        path="/movies/movie.mkv",
        sceneName="Scene",
        audio_language="['eng']",
    )

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie_info)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: False)

    result = module.movie_download_specific_subtitles(7, "fr", "False", "False", job_id="job")

    assert result == ("Movie file not found. Path mapping issue?", 500)


def test_movie_download_specific_subtitles_returns_not_found(monkeypatch):
    module = load_mass_download_module("movies")

    class _Database:
        def execute(self, statement):
            return _Result(first_value=None)

    monkeypatch.setattr(module, "database", _Database())

    assert module.movie_download_specific_subtitles(7, "fr", "False", "False", job_id="job") == ("Movie not found", 404)


def test_movie_download_specific_subtitles_returns_conflict_on_oserror(monkeypatch):
    module = load_mass_download_module("movies")

    movie_info = SimpleNamespace(
        title="Movie",
        path="/movies/movie.mkv",
        sceneName="Scene",
        audio_language="['eng']",
    )

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie_info)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: (_ for _ in ()).throw(OSError()))

    assert module.movie_download_specific_subtitles(7, "fr", "False", "False", job_id="job") == (
        "Unable to save subtitles file. Permission or path mapping issue?",
        409,
    )


# ---------------------------------------------------------------------------
# Additional edge-case and boundary tests
# ---------------------------------------------------------------------------


def test_movies_download_subtitles_returns_early_when_movie_not_in_database(monkeypatch):
    """When the movie is not in the database the function should return early."""
    module = load_mass_download_module("movies")

    progress = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=None)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [])
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda **kwargs: progress.append(kwargs),
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    result = module.movies_download_subtitles(999, job_id="job")
    assert result is None
    assert any("not found" in (p.get("progress_message") or "").lower() for p in progress)


def test_movies_download_subtitles_skips_generation_when_missing_subtitles_empty(monkeypatch):
    """A movie whose missing_subtitles is '[]' should trigger no subtitle generation."""
    module = load_mass_download_module("movies")

    movie = SimpleNamespace(
        path="/movies/movie.mkv",
        missing_subtitles="[]",
        audio_language="['eng']",
        radarrId=7,
        sceneName="Scene",
        title="Movie",
        year=2024,
        tags=[],
        monitored=True,
        profileId=44,
    )
    generated = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/movies/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "get_providers", lambda: ["provider"])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: generated.append(args) or iter(()))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.movies_download_subtitles(7, job_id="job")

    assert generated == [], "generate_subtitles should not be called when missing_subtitles is '[]'"


def test_episode_download_subtitles_returns_early_when_episode_not_in_database(monkeypatch):
    """When the episode is not in the database the function should return early."""
    module = load_mass_download_module("series")

    progress = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=None)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [])
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda **kwargs: progress.append(kwargs),
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    result = module.episode_download_subtitles(999, job_id="job", job_sub_function=True, providers_list=["provider"])
    assert result is None
    assert any("not found" in (p.get("progress_message") or "").lower() for p in progress)


def test_movie_download_specific_subtitles_builds_plain_language_string(monkeypatch):
    """When hi='False' and forced='False' the language string should have no suffix."""
    module = load_mass_download_module("movies")

    movie_info = SimpleNamespace(
        title="Movie",
        path="/movies/movie.mkv",
        sceneName="Scene",
        audio_language="['eng']",
    )
    generate_args = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie_info)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(
        module,
        "generate_subtitles",
        lambda *args, **kwargs: generate_args.append(args) or iter([]),
    )
    monkeypatch.setattr(module, "event_stream", lambda **kwargs: None)
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.movie_download_specific_subtitles(7, "de", "False", "False", job_id="job")

    # The language tuple passed to generate_subtitles should be ("de", "False", "False")
    assert generate_args, "generate_subtitles was not called"
    language_tuples = generate_args[0][1]
    assert language_tuples == [("de", "False", "False")]


def test_episode_download_specific_subtitles_returns_not_found_when_episode_row_missing(monkeypatch):
    """When the database has no row for the given episode the function should return a 404-style tuple."""
    module = load_mass_download_module("series")

    class _Database:
        def execute(self, statement):
            return _Result(first_value=None)

    monkeypatch.setattr(module, "database", _Database())

    result = module.episode_download_specific_subtitles(5, 999, "fr", "False", "False", job_id="job")

    # Expect an error indicator — either a 404 tuple or similar non-success response.
    assert result is not None
    assert result != ("", 204)


def test_episode_download_specific_subtitles_uses_none_for_missing_scene_name(monkeypatch):
    module = load_mass_download_module("series")

    episode_info = SimpleNamespace(
        path="/series/episode.mkv",
        sceneName=None,
        audio_language="['eng']",
        season=1,
        episode=2,
        episodeTitle="Second",
        title="Series",
    )
    captured_scene = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode_info)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: captured_scene.append(args[3]) or iter([]))
    monkeypatch.setattr(module, "event_stream", lambda **kwargs: None)
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda **kwargs: None,
        ),
    )

    result = module.episode_download_specific_subtitles(5, 11, "fr", "False", "False", job_id="job")

    assert result == ("", 204)
    assert captured_scene == [None]


def test_series_download_subtitles_sets_fallback_allowed_per_settings(monkeypatch):
    """episode_download_subtitles calls should receive fallback_allowed from series-level settings."""
    module = load_mass_download_module("series")

    series_row = SimpleNamespace(path="/series", title="Series")
    episodes = [SimpleNamespace(sonarrEpisodeId=11, title="Series", season=1, episode=1, episodeTitle="One")]
    episode_calls = []

    class _Database:
        def __init__(self):
            self.calls = 0

        def execute(self, statement):
            self.calls += 1
            if self.calls == 1:
                return _Result(first_value=series_row)
            return _Result(all_value=episodes)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_providers", lambda: ["provider"])
    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(
            general=SimpleNamespace(
                use_whisper_fallback=False,
                use_whisper_fallback_series=False,
            )
        ),
    )
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )
    monkeypatch.setattr(
        module,
        "episode_download_subtitles",
        lambda *args, **kwargs: episode_calls.append(kwargs),
    )

    module.series_download_subtitles(5, job_id="job")

    assert episode_calls, "episode_download_subtitles was not called"
    assert all(call.get("fallback_allowed") is False for call in episode_calls)


def test_movies_download_subtitles_updates_job_name_on_completion(monkeypatch):
    """The job name should be updated to indicate download completion when job finishes."""
    module = load_mass_download_module("movies")

    movie = SimpleNamespace(
        path="/movies/movie.mkv",
        missing_subtitles="['en']",
        audio_language="['eng']",
        radarrId=7,
        sceneName="Scene",
        title="Movie",
        year=2024,
        tags=[],
        monitored=True,
        profileId=44,
    )
    names = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/movies/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "get_providers", lambda: [])
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda **kwargs: names.append(kwargs["new_job_name"]),
        ),
    )

    module.movies_download_subtitles(7, job_id="job")

    # Job name should mention the movie title when finished
    assert any("Movie" in n for n in names), f"Expected 'Movie' in job names but got: {names}"


def test_episode_download_subtitles_updates_job_name_on_completion(monkeypatch):
    """Episode download job should update its name to indicate completion."""
    module = load_mass_download_module("series")

    episode = SimpleNamespace(
        path="/series/episode.mkv",
        missing_subtitles="['en']",
        monitored=True,
        sonarrEpisodeId=11,
        sceneName="Scene",
        tags=[],
        title="Series",
        sonarrSeriesId=5,
        audio_language="['eng']",
        seriesType="standard",
        episodeTitle="Pilot",
        season=1,
        episode=1,
        profileId=44,
    )
    names = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/series/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: iter([]))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda **kwargs: names.append(kwargs["new_job_name"]),
        ),
    )

    module.episode_download_subtitles(11, job_id="job", job_sub_function=False, providers_list=["provider"])

    assert any("Series" in n or "Downloaded" in n for n in names), f"Expected series name in job names: {names}"


def test_movies_download_subtitles_handles_missing_row_after_reindex_refresh(monkeypatch):
    """If reindex refresh returns no movie row, wrapper should exit without crashing."""
    module = load_mass_download_module("movies")
    initial_movie = SimpleNamespace(
        path="/movies/movie.mkv",
        missing_subtitles="['en']",
        audio_language="['eng']",
        radarrId=7,
        sceneName="Scene",
        title="Movie",
        year=2024,
        tags=[],
        monitored=True,
        profileId=44,
    )

    class _Database:
        def __init__(self):
            self.calls = 0

        def execute(self, statement):
            self.calls += 1
            if self.calls == 1:
                return _Result(first_value=initial_movie)
            return _Result(first_value=None)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [])
    monkeypatch.setattr(module, "store_subtitles_movie", lambda *args, **kwargs: None)
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "get_providers", lambda: [])
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    result = module.movies_download_subtitles(7, job_id="job")
    assert result is None


def test_movies_download_subtitles_fuzz_malformed_missing_subtitles_fails_safe(monkeypatch):
    module = load_mass_download_module("movies")
    rng = random.Random(8844)
    malformed_values = [
        "",
        " ",
        "[",
        "not_a_list",
        "None",
        "{'en': 1}",
        "[1, 2, 3]",
        "[None, 1, {'x': 1}]",
    ]
    malformed_values.extend(
        "".join(rng.choice("[]{}()'\",abc123:-_ ") for _ in range(rng.randint(1, 20)))
        for _ in range(120)
    )

    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/movies/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module, "get_providers", lambda: ["provider"])
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    for malformed in malformed_values:
        movie = SimpleNamespace(
            path="/movies/movie.mkv",
            missing_subtitles=malformed,
            audio_language="['eng']",
            radarrId=7,
            sceneName="Scene",
            title="Movie",
            year=2024,
            tags=[],
            monitored=True,
            profileId=44,
        )
        generated = []
        monkeypatch.setattr(module, "database", SimpleNamespace(execute=lambda statement: _Result(first_value=movie)))
        monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: generated.append(args[1]) or iter(()))

        module.movies_download_subtitles(7, job_id="job")

        assert generated == []


def test_episode_download_subtitles_fuzz_malformed_missing_subtitles_fails_safe(monkeypatch):
    module = load_mass_download_module("series")
    rng = random.Random(4499)
    malformed_values = [
        "",
        " ",
        "[",
        "not_a_list",
        "None",
        "{'en': 1}",
        "[1, 2, 3]",
        "[None, 1, {'x': 1}]",
    ]
    malformed_values.extend(
        "".join(rng.choice("[]{}()'\",abc123:-_ ") for _ in range(rng.randint(1, 20)))
        for _ in range(120)
    )

    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/series/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    for malformed in malformed_values:
        episode = SimpleNamespace(
            path="/series/episode.mkv",
            missing_subtitles=malformed,
            monitored=True,
            sonarrEpisodeId=11,
            sceneName="Scene",
            tags=[],
            title="Series",
            sonarrSeriesId=5,
            audio_language="['eng']",
            seriesType="standard",
            episodeTitle="Pilot",
            season=1,
            episode=1,
            profileId=44,
        )
        generated = []
        monkeypatch.setattr(module, "database", SimpleNamespace(execute=lambda statement: _Result(first_value=episode)))
        monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: generated.append(args[1]) or iter(()))

        module.episode_download_subtitles(11, job_id="job", job_sub_function=True, providers_list=["provider"])

        assert generated == []


def test_movies_download_subtitles_normalizes_whitespace_language_tokens(monkeypatch):
    module = load_mass_download_module("movies")

    movie = SimpleNamespace(
        path="/movies/movie.mkv",
        missing_subtitles="[' en ', ' fr:forced ', ' de:hi  ']",
        audio_language="['eng']",
        radarrId=7,
        sceneName="Scene",
        title="Movie",
        year=2024,
        tags=[],
        monitored=True,
        profileId=44,
    )
    generated = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/movies/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "get_providers", lambda: ["provider"])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: generated.append(args[1]) or iter(()))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.movies_download_subtitles(7, job_id="job")

    assert generated == [[
        ("en", "False", "False"),
        ("fr", "False", "True"),
        ("de", "True", "False"),
    ]]


def test_episode_download_subtitles_normalizes_whitespace_language_tokens(monkeypatch):
    module = load_mass_download_module("series")

    episode = SimpleNamespace(
        path="/series/episode.mkv",
        missing_subtitles="[' en:hi ', ' fr ', ' de:forced  ']",
        monitored=True,
        sonarrEpisodeId=11,
        sceneName="Scene",
        tags=[],
        title="Series",
        sonarrSeriesId=5,
        audio_language="['eng']",
        seriesType="standard",
        episodeTitle="Pilot",
        season=1,
        episode=1,
        profileId=44,
    )
    generated = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/series/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: generated.append(args[1]) or iter(()))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.episode_download_subtitles(11, job_id="job", job_sub_function=True, providers_list=["provider"])

    assert generated == [[
        ("en", "True", "False"),
        ("fr", "False", "False"),
        ("de", "False", "True"),
    ]]


def test_movies_download_subtitles_normalizes_mixed_case_and_multi_colon_flags(monkeypatch):
    module = load_mass_download_module("movies")

    movie = SimpleNamespace(
        path="/movies/movie.mkv",
        missing_subtitles="['en:HI', 'fr:FORCED', 'de:Hi:Forced']",
        audio_language="['eng']",
        radarrId=7,
        sceneName="Scene",
        title="Movie",
        year=2024,
        tags=[],
        monitored=True,
        profileId=44,
    )
    generated = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=movie)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/movies/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(module, "get_providers", lambda: ["provider"])
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: generated.append(args[1]) or iter(()))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.movies_download_subtitles(7, job_id="job")

    assert generated == [[
        ("en", "True", "False"),
        ("fr", "False", "True"),
        ("de", "True", "True"),
    ]]


def test_episode_download_subtitles_uses_first_valid_audio_language_name(monkeypatch):
    module = load_mass_download_module("series")

    episode = SimpleNamespace(
        path="/series/episode.mkv",
        missing_subtitles="['en']",
        monitored=True,
        sonarrEpisodeId=11,
        sceneName="Scene",
        tags=[],
        title="Series",
        sonarrSeriesId=5,
        audio_language="['eng']",
        seriesType="standard",
        episodeTitle="Pilot",
        season=1,
        episode=1,
        profileId=44,
    )
    captured_audio = []

    class _Database:
        def execute(self, statement):
            return _Result(first_value=episode)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [{"path": "/series/sub.srt", "embedded_track_id": 1}])
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(
        module,
        "get_audio_profile_languages",
        lambda audio_language: [{"name": "   "}, {"bad": "shape"}, {"name": "English"}],
    )
    monkeypatch.setattr(module, "generate_subtitles", lambda *args, **kwargs: captured_audio.append(args[2]) or iter(()))
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    module.episode_download_subtitles(11, job_id="job", job_sub_function=True, providers_list=["provider"])

    assert captured_audio == ["English"]


def test_episode_download_subtitles_handles_missing_row_after_reindex_refresh(monkeypatch):
    """If reindex refresh returns no episode row, wrapper should exit without crashing."""
    module = load_mass_download_module("series")
    initial_episode = SimpleNamespace(
        path="/series/e01.mkv",
        missing_subtitles="['en']",
        monitored=True,
        sonarrEpisodeId=11,
        sceneName="Scene",
        tags=[],
        title="Series",
        sonarrSeriesId=5,
        audio_language="['eng']",
        seriesType="standard",
        episodeTitle="Pilot",
        season=1,
        episode=1,
        profileId=44,
    )

    class _Database:
        def __init__(self):
            self.calls = 0

        def execute(self, statement):
            self.calls += 1
            if self.calls == 1:
                return _Result(first_value=initial_episode)
            return _Result(first_value=None)

    monkeypatch.setattr(module, "database", _Database())
    monkeypatch.setattr(module, "get_subtitles", lambda **kwargs: [])
    monkeypatch.setattr(module, "store_subtitles", lambda *args, **kwargs: None)
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(
        module,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    result = module.episode_download_subtitles(
        11,
        job_id="job",
        job_sub_function=True,
        providers_list=["provider"],
    )
    assert result is None

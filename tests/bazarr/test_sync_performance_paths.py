# -*- coding: utf-8 -*-
import datetime

from types import SimpleNamespace

import pytest


class _Result:
    def __init__(self, first_value=None, all_value=None):
        self._first_value = first_value
        self._all_value = [] if all_value is None else all_value

    def first(self):
        return self._first_value

    def all(self):
        return self._all_value


class _Column:
    def __init__(self, name):
        self.name = name


def _model(**values):
    return SimpleNamespace(
        __table__=SimpleNamespace(columns=[_Column(name) for name in values]),
        **values,
    )


def test_update_one_series_fetches_and_inserts_for_standalone_call(monkeypatch):
    from sonarr.sync import series as series_sync

    execute_calls = []

    class _Database:
        def execute(self, statement):
            execute_calls.append(statement)
            if len(execute_calls) == 1:
                return _Result(first_value=None)
            return _Result()

    events = []
    monkeypatch.setattr(series_sync, "database", _Database())
    monkeypatch.setattr(
        series_sync,
        "settings",
        SimpleNamespace(
            general=SimpleNamespace(serie_default_enabled=False),
            sonarr=SimpleNamespace(apikey="sonarr-key"),
        ),
    )
    monkeypatch.setattr(series_sync, "get_profile_list", lambda: [])
    monkeypatch.setattr(series_sync, "get_tags", lambda: {})
    monkeypatch.setattr(series_sync, "get_language_profiles", lambda: [])
    monkeypatch.setattr(series_sync, "get_series_from_sonarr_api", lambda **kwargs: [{"id": 123}])
    monkeypatch.setattr(
        series_sync,
        "seriesParser",
        lambda *args, **kwargs: {"sonarrSeriesId": 123, "path": "/series/path"},
    )
    monkeypatch.setattr(series_sync, "event_stream", lambda **kwargs: events.append(kwargs))
    monkeypatch.setattr(series_sync.path_mappings, "path_replace", lambda path: path)

    series_sync.update_one_series(123, action="updated")

    assert len(execute_calls) == 2
    assert events == [{"type": "series", "action": "update", "payload": 123}]


def test_update_series_runs_one_explicit_episode_sync(monkeypatch):
    from sonarr.sync import series as series_sync

    update_calls = []
    episode_sync_calls = []

    class _Database:
        def execute(self, statement):
            return _Result(all_value=[])

    monkeypatch.setattr(series_sync, "database", _Database())
    monkeypatch.setattr(
        series_sync,
        "settings",
        SimpleNamespace(
            general=SimpleNamespace(debug=False),
            sonarr=SimpleNamespace(apikey="sonarr-key", sync_only_monitored_series=False),
        ),
    )
    monkeypatch.setattr(series_sync, "check_sonarr_rootfolder", lambda: None)
    monkeypatch.setattr(series_sync, "get_series_from_sonarr_api", lambda **kwargs: [{"id": 123, "title": "Series"}])
    monkeypatch.setattr(series_sync, "get_profile_list", lambda: [])
    monkeypatch.setattr(series_sync, "get_tags", lambda: {})
    monkeypatch.setattr(series_sync, "get_language_profiles", lambda: [])
    monkeypatch.setattr(
        series_sync,
        "update_one_series",
        lambda *args, **kwargs: update_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(series_sync, "sync_episodes", lambda series_id: episode_sync_calls.append(series_id))
    monkeypatch.setattr(
        series_sync,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )

    series_sync.update_series(job_id="job")

    assert episode_sync_calls == [123]
    assert len(update_calls) == 1
    assert update_calls[0][1]["sync_episodes_after_update"] is False


def test_unchanged_series_skips_update_but_manual_call_syncs_episodes(monkeypatch):
    from sonarr.sync import series as series_sync

    existing_series = _model(sonarrSeriesId=123, path="/series/path")
    execute_calls = []
    episode_sync_calls = []

    class _Database:
        def execute(self, statement):
            execute_calls.append(statement)
            return _Result(first_value=(existing_series,))

    monkeypatch.setattr(series_sync, "database", _Database())
    monkeypatch.setattr(
        series_sync,
        "settings",
        SimpleNamespace(
            general=SimpleNamespace(serie_default_enabled=False),
            sonarr=SimpleNamespace(apikey="sonarr-key"),
        ),
    )
    monkeypatch.setattr(series_sync, "get_profile_list", lambda: [])
    monkeypatch.setattr(series_sync, "get_tags", lambda: {})
    monkeypatch.setattr(series_sync, "get_language_profiles", lambda: [])
    monkeypatch.setattr(
        series_sync,
        "seriesParser",
        lambda *args, **kwargs: {"sonarrSeriesId": 123, "path": "/series/path"},
    )
    monkeypatch.setattr(series_sync, "sync_episodes", lambda series_id: episode_sync_calls.append(series_id))

    series_sync.update_one_series(
        123,
        action="updated",
        series_data=[{"id": 123}],
        sync_episodes_after_update=True,
    )

    assert len(execute_calls) == 1
    assert episode_sync_calls == [123]


def test_episode_parser_uses_reported_size_before_filesystem_stat(monkeypatch):
    from constants import MINIMUM_VIDEO_SIZE
    from sonarr.sync import parser

    monkeypatch.setattr(
        parser.os.path,
        "getsize",
        lambda path: pytest.fail("episodeParser should not stat files when Sonarr size is already valid"),
    )
    monkeypatch.setattr(parser, "audio_language_from_name", lambda name: name)

    parsed = parser.episodeParser(
        {
            "hasFile": True,
            "seriesId": 123,
            "id": 456,
            "title": "Episode",
            "seasonNumber": 1,
            "episodeNumber": 2,
            "monitored": True,
            "episodeFile": {
                "id": 789,
                "path": "/series/path/episode.mkv",
                "size": MINIMUM_VIDEO_SIZE + 1,
                "language": {"name": "English"},
                "mediaInfo": {},
                "quality": {"quality": {"name": "HDTV-1080p"}},
            },
        },
        parse_embedded_audio_track=False,
    )

    assert parsed["sonarrEpisodeId"] == 456
    assert parsed["file_size"] == MINIMUM_VIDEO_SIZE + 1


def test_update_movies_compares_against_matching_radarr_id(monkeypatch):
    from constants import MINIMUM_VIDEO_SIZE
    from radarr.sync import movies as movies_sync

    movie_rows = [
        (_model(radarrId=1, title="Movie 1", path="/movies/one.mkv"),),
        (_model(radarrId=2, title="Old Movie 2", path="/movies/two.mkv"),),
    ]
    updated_movies = []

    class _Database:
        def execute(self, statement):
            return _Result(all_value=movie_rows)

    def _movie_parser(movie, **kwargs):
        return {
            "radarrId": movie["id"],
            "title": movie["title"],
            "path": movie["movieFile"]["path"],
        }

    monkeypatch.setattr(movies_sync, "database", _Database())
    monkeypatch.setattr(
        movies_sync,
        "settings",
        SimpleNamespace(
            general=SimpleNamespace(movie_default_enabled=False, debug=False),
            radarr=SimpleNamespace(apikey="radarr-key", sync_only_monitored_movies=False),
        ),
    )
    monkeypatch.setattr(movies_sync, "check_radarr_rootfolder", lambda: None)
    monkeypatch.setattr(movies_sync, "get_profile_list", lambda: [])
    monkeypatch.setattr(movies_sync, "get_tags", lambda: {})
    monkeypatch.setattr(movies_sync, "get_language_profiles", lambda: [])
    monkeypatch.setattr(movies_sync, "movieParser", _movie_parser)
    monkeypatch.setattr(movies_sync, "update_movie", lambda movie: updated_movies.append(movie))
    monkeypatch.setattr(movies_sync, "event_stream", lambda **kwargs: None)
    monkeypatch.setattr(
        movies_sync,
        "jobs_queue",
        SimpleNamespace(
            add_job_from_function=lambda *args, **kwargs: None,
            update_job_progress=lambda *args, **kwargs: None,
            update_job_name=lambda *args, **kwargs: None,
        ),
    )
    monkeypatch.setattr(
        movies_sync,
        "get_movies_from_radarr_api",
        lambda apikey_radarr: [
            {
                "id": 1,
                "title": "Movie 1",
                "hasFile": True,
                "monitored": True,
                "movieFile": {"path": "/movies/one.mkv", "size": MINIMUM_VIDEO_SIZE + 1},
            },
            {
                "id": 2,
                "title": "New Movie 2",
                "hasFile": True,
                "monitored": True,
                "movieFile": {"path": "/movies/two.mkv", "size": MINIMUM_VIDEO_SIZE + 1},
            },
        ],
    )

    movies_sync.update_movies(job_id="job")

    assert updated_movies == [{"radarrId": 2, "title": "New Movie 2", "path": "/movies/two.mkv"}]


def test_get_providers_expired_throttle_cleanup_is_idempotent(monkeypatch):
    from app import get_providers as providers

    provider = "opensubtitlescom"
    providers.tp.clear()
    providers.tp[provider] = ("TooManyRequests", datetime.datetime.now(), "1 minute")

    removed_once = {"done": False}

    class _RacingThrottle(dict):
        def __delitem__(self, key):
            if not removed_once["done"]:
                removed_once["done"] = True
                super().__delitem__(key)
                raise KeyError(key)
            super().__delitem__(key)

    racing_tp = _RacingThrottle(providers.tp)
    monkeypatch.setattr(providers, "tp", racing_tp)
    monkeypatch.setattr(providers.provider_registry, "names", lambda: [provider])
    monkeypatch.setattr(providers, "settings", SimpleNamespace(general=SimpleNamespace(enabled_providers=[provider])))
    monkeypatch.setattr(providers, "set_throttled_providers", lambda data: None)

    assert providers.get_providers() == [provider]

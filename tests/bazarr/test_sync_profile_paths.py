from types import SimpleNamespace

import pytest

import radarr.sync.movies as radarr_movies
import radarr.sync.utils as radarr_utils
import app.database as app_database
import sonarr.sync.series as sonarr_series
import sonarr.sync.utils as sonarr_utils
import subtitles.sync as subtitle_sync


def _response(payload):
    return SimpleNamespace(json=lambda: payload)


@pytest.fixture
def configured_radarr(monkeypatch):
    monkeypatch.setattr(radarr_utils.settings.radarr, "apikey", "test")
    monkeypatch.setattr(radarr_utils.settings.radarr, "http_timeout", 30)
    monkeypatch.setattr(radarr_utils, "url_api_radarr", lambda: "http://localhost:7878/api/v3/")
    monkeypatch.setattr(radarr_utils.get_radarr_info, "is_legacy", lambda: True)
    return radarr_utils


@pytest.fixture
def configured_sonarr(monkeypatch):
    monkeypatch.setattr(sonarr_utils.settings.sonarr, "apikey", "test")
    monkeypatch.setattr(sonarr_utils.settings.sonarr, "http_timeout", 30)
    monkeypatch.setattr(sonarr_utils, "url_api_sonarr", lambda: "http://localhost:8989/api/v3/")
    monkeypatch.setattr(sonarr_utils.get_sonarr_info, "is_legacy", lambda: True)
    monkeypatch.setattr(sonarr_utils.get_sonarr_info, "version", lambda: "4.0.0")
    return sonarr_utils


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ([{"id": 1, "language": None}, {"id": 2, "language": "English"}], [[2, "English"]]),
        ([{"id": 1, "language": 123}, {"id": 2, "language": "French"}], [[2, "French"]]),
        ([None, "bad", {"id": 2, "language": "Spanish"}], [[2, "Spanish"]]),
    ],
)
def test_radarr_legacy_profile_parser_filters_malformed_languages(configured_radarr, monkeypatch, payload, expected):
    monkeypatch.setattr(configured_radarr.requests, "get", lambda *args, **kwargs: _response(payload))

    assert configured_radarr.get_profile_list() == expected


def test_radarr_v4_profile_parser_filters_malformed_nested_language_names(configured_radarr, monkeypatch):
    monkeypatch.setattr(configured_radarr.get_radarr_info, "is_legacy", lambda: False)
    monkeypatch.setattr(
        configured_radarr.requests,
        "get",
        lambda *args, **kwargs: _response(
            [{"id": 1, "language": {"name": None}}, {"id": 2, "language": {"name": "Spanish"}}]
        ),
    )

    assert configured_radarr.get_profile_list() == [[2, "Spanish"]]


def test_radarr_profile_parser_skips_missing_profile_id(configured_radarr, monkeypatch):
    monkeypatch.setattr(configured_radarr.requests, "get", lambda *args, **kwargs: _response([{"language": "English"}]))

    assert configured_radarr.get_profile_list() == []


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ([{"id": 1, "language": None}, {"id": 2, "language": "German"}], [[2, "German"]]),
        ([{"id": 1, "language": 123}, {"id": 2, "language": "Italian"}], [[2, "Italian"]]),
        ([None, "bad", {"id": 2, "language": "German"}], [[2, "German"]]),
        ([], []),
    ],
)
def test_sonarr_legacy_profile_parser_filters_malformed_languages(configured_sonarr, monkeypatch, payload, expected):
    monkeypatch.setattr(configured_sonarr.requests, "get", lambda *args, **kwargs: _response(payload))

    assert configured_sonarr.get_profile_list() == expected


def test_sonarr_v3_profile_parser_filters_malformed_names(configured_sonarr, monkeypatch):
    monkeypatch.setattr(configured_sonarr.get_sonarr_info, "is_legacy", lambda: False)
    monkeypatch.setattr(configured_sonarr.get_sonarr_info, "version", lambda: "3.0.0")
    monkeypatch.setattr(
        configured_sonarr.requests,
        "get",
        lambda *args, **kwargs: _response([{"id": 1, "name": None}, {"id": 2, "name": "Profile1"}]),
    )

    assert configured_sonarr.get_profile_list() == [[2, "Profile1"]]


def test_sonarr_v3_profile_parser_returns_empty_for_all_malformed(configured_sonarr, monkeypatch):
    monkeypatch.setattr(configured_sonarr.get_sonarr_info, "is_legacy", lambda: False)
    monkeypatch.setattr(configured_sonarr.get_sonarr_info, "version", lambda: "3.0.0")
    monkeypatch.setattr(
        configured_sonarr.requests,
        "get",
        lambda *args, **kwargs: _response([{"id": 1, "name": 123}, {"id": 2, "name": []}, {"id": 3}]),
    )

    assert configured_sonarr.get_profile_list() == []


def test_sonarr_profile_parser_skips_missing_profile_id(configured_sonarr, monkeypatch):
    monkeypatch.setattr(configured_sonarr.requests, "get", lambda *args, **kwargs: _response([{"language": "English"}]))

    assert configured_sonarr.get_profile_list() == []


def test_get_profile_cutoff_returns_none_for_malformed_profile_id(monkeypatch):
    monkeypatch.setattr(
        app_database,
        "update_profile_id_list",
        lambda: [{"profileId": 44, "cutoff": 1, "items": [{"id": 1, "language": "en"}]}],
    )

    assert app_database.get_profile_cutoff("not-a-profile-id") is None


def test_radarr_movie_sync_finalizes_job_for_non_list_payload(monkeypatch):
    names = []

    monkeypatch.setattr(radarr_movies, "check_radarr_rootfolder", lambda: None)
    monkeypatch.setattr(radarr_movies.settings.general, "movie_default_enabled", False)
    monkeypatch.setattr(radarr_movies.settings.radarr, "apikey", "test")
    monkeypatch.setattr(
        radarr_movies,
        "get_movies_from_radarr_api",
        lambda apikey_radarr: {"unexpected": "payload"},
    )
    monkeypatch.setattr(
        radarr_movies.database,
        "execute",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("database should not be queried")),
    )
    monkeypatch.setattr(
        radarr_movies.jobs_queue,
        "update_job_progress",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("progress should not be updated")),
    )
    monkeypatch.setattr(
        radarr_movies.jobs_queue,
        "update_job_name",
        lambda **kwargs: names.append(kwargs["new_job_name"]),
    )

    radarr_movies.update_movies(job_id="job")

    assert names == ["Synced movies with Radarr"]


def test_radarr_movie_sync_skips_file_payloads_without_movie_id(monkeypatch):
    progress = []
    names = []

    monkeypatch.setattr(radarr_movies, "check_radarr_rootfolder", lambda: None)
    monkeypatch.setattr(radarr_movies.settings.general, "movie_default_enabled", False)
    monkeypatch.setattr(radarr_movies.settings.general, "enable_strm_support", False)
    monkeypatch.setattr(radarr_movies.settings.radarr, "apikey", "test")
    monkeypatch.setattr(radarr_movies.settings.radarr, "sync_only_monitored_movies", False)
    monkeypatch.setattr(radarr_movies, "get_profile_list", lambda: [])
    monkeypatch.setattr(radarr_movies, "get_tags", lambda: [])
    monkeypatch.setattr(radarr_movies, "get_language_profiles", lambda: [])
    monkeypatch.setattr(radarr_movies, "get_movie_file_size_from_db", lambda path: 0)
    monkeypatch.setattr(
        radarr_movies,
        "get_movies_from_radarr_api",
        lambda apikey_radarr: [{"hasFile": True, "title": "Missing ID", "movieFile": {"size": 999999}}],
    )
    monkeypatch.setattr(radarr_movies.database, "execute", lambda *args, **kwargs: SimpleNamespace(all=lambda: []))
    monkeypatch.setattr(
        radarr_movies.jobs_queue,
        "update_job_progress",
        lambda **kwargs: progress.append(kwargs),
    )
    monkeypatch.setattr(
        radarr_movies.jobs_queue,
        "update_job_name",
        lambda **kwargs: names.append(kwargs["new_job_name"]),
    )

    radarr_movies.update_movies(job_id="job")

    assert progress[0]["progress_max"] == 1
    assert names == ["Synced movies with Radarr"]


def test_radarr_movie_sync_handles_malformed_movie_file_fields(monkeypatch):
    progress = []
    names = []
    traces = []

    monkeypatch.setattr(radarr_movies, "check_radarr_rootfolder", lambda: None)
    monkeypatch.setattr(radarr_movies.settings.general, "movie_default_enabled", False)
    monkeypatch.setattr(radarr_movies.settings.general, "enable_strm_support", True)
    monkeypatch.setattr(radarr_movies.settings.radarr, "apikey", "test")
    monkeypatch.setattr(radarr_movies.settings.radarr, "sync_only_monitored_movies", False)
    monkeypatch.setattr(radarr_movies, "get_profile_list", lambda: [])
    monkeypatch.setattr(radarr_movies, "get_tags", lambda: [])
    monkeypatch.setattr(radarr_movies, "get_language_profiles", lambda: [])
    monkeypatch.setattr(radarr_movies, "get_movie_file_size_from_db", lambda path: 0)
    monkeypatch.setattr(radarr_movies, "trace", traces.append)
    monkeypatch.setattr(
        radarr_movies,
        "get_movies_from_radarr_api",
        lambda apikey_radarr: [
            {"id": 1, "hasFile": True, "title": "Bad Size", "movieFile": {"size": "bad", "path": None}},
            {"id": 2, "hasFile": True, "title": "Missing Path", "movieFile": {"size": None}},
        ],
    )
    monkeypatch.setattr(radarr_movies.database, "execute", lambda *args, **kwargs: SimpleNamespace(all=lambda: []))
    monkeypatch.setattr(
        radarr_movies.jobs_queue,
        "update_job_progress",
        lambda **kwargs: progress.append(kwargs),
    )
    monkeypatch.setattr(
        radarr_movies.jobs_queue,
        "update_job_name",
        lambda **kwargs: names.append(kwargs["new_job_name"]),
    )

    radarr_movies.update_movies(job_id="job")

    assert progress[0]["progress_max"] == 2
    assert names == ["Synced movies with Radarr"]
    assert "Skipped 2 file missing movies out of 2" in traces


def test_radarr_movie_sync_skips_large_file_with_malformed_required_fields(monkeypatch):
    progress = []
    names = []
    traces = []

    monkeypatch.setattr(radarr_movies, "check_radarr_rootfolder", lambda: None)
    monkeypatch.setattr(radarr_movies.settings.general, "movie_default_enabled", False)
    monkeypatch.setattr(radarr_movies.settings.general, "enable_strm_support", False)
    monkeypatch.setattr(radarr_movies.settings.radarr, "apikey", "test")
    monkeypatch.setattr(radarr_movies.settings.radarr, "sync_only_monitored_movies", False)
    monkeypatch.setattr(radarr_movies, "get_profile_list", lambda: [])
    monkeypatch.setattr(radarr_movies, "get_tags", lambda: [])
    monkeypatch.setattr(radarr_movies, "get_language_profiles", lambda: [])
    monkeypatch.setattr(radarr_movies, "get_movie_file_size_from_db", lambda path: 0)
    monkeypatch.setattr(radarr_movies, "trace", traces.append)
    monkeypatch.setattr(
        radarr_movies,
        "get_movies_from_radarr_api",
        lambda apikey_radarr: [
            {
                "id": 1,
                "hasFile": True,
                "title": "Missing Path",
                "movieFile": {"id": 10, "size": 999999999, "path": None},
            },
            {
                "id": 2,
                "hasFile": True,
                "title": "Missing File ID",
                "movieFile": {"size": 999999999, "path": "/movies/movie.mkv"},
            },
        ],
    )
    monkeypatch.setattr(radarr_movies.database, "execute", lambda *args, **kwargs: SimpleNamespace(all=lambda: []))
    monkeypatch.setattr(
        radarr_movies,
        "movieParser",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("movieParser should not be called")),
    )
    monkeypatch.setattr(
        radarr_movies.jobs_queue,
        "update_job_progress",
        lambda **kwargs: progress.append(kwargs),
    )
    monkeypatch.setattr(
        radarr_movies.jobs_queue,
        "update_job_name",
        lambda **kwargs: names.append(kwargs["new_job_name"]),
    )

    radarr_movies.update_movies(job_id="job")

    assert progress[0]["progress_max"] == 2
    assert names == ["Synced movies with Radarr"]
    assert "Skipped 2 file missing movies out of 2" in traces


def test_sonarr_series_sync_returns_for_non_list_payload(monkeypatch):
    names = []

    monkeypatch.setattr(sonarr_series, "check_sonarr_rootfolder", lambda: None)
    monkeypatch.setattr(
        sonarr_series,
        "get_series_from_sonarr_api",
        lambda apikey_sonarr: {"unexpected": "payload"},
    )
    monkeypatch.setattr(
        sonarr_series.database,
        "execute",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("database should not be queried")),
    )
    monkeypatch.setattr(
        sonarr_series.jobs_queue,
        "update_job_progress",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("progress should not be updated")),
    )
    monkeypatch.setattr(
        sonarr_series.jobs_queue,
        "update_job_name",
        lambda **kwargs: names.append(kwargs["new_job_name"]),
    )
    monkeypatch.setattr(sonarr_series.gc, "collect", lambda: None)

    sonarr_series.update_series(job_id="job")

    assert names == ["Synced series with Sonarr"]


def test_sync_subtitles_handles_malformed_percent_score(monkeypatch):
    sync_calls = []
    job_names = []

    class SubSyncer:
        def sync(self, **kwargs):
            sync_calls.append(kwargs)

    monkeypatch.setattr(subtitle_sync.settings.subsync, "use_subsync", True)
    monkeypatch.setattr(subtitle_sync.settings.subsync, "use_subsync_movie_threshold", True)
    monkeypatch.setattr(subtitle_sync.settings.subsync, "subsync_movie_threshold", "80")
    monkeypatch.setattr(subtitle_sync, "_create_subsyncer", SubSyncer)
    monkeypatch.setattr(subtitle_sync.gc, "collect", lambda: None)
    monkeypatch.setattr(
        subtitle_sync.jobs_queue,
        "update_job_name",
        lambda **kwargs: job_names.append(kwargs["new_job_name"]),
    )

    result = subtitle_sync.sync_subtitles(
        video_path="/movies/movie.mkv",
        srt_path="/movies/movie.en.srt",
        srt_lang="en",
        forced=False,
        hi=False,
        percent_score=None,
        radarr_id=7,
        job_id="job",
    )

    assert result is True
    assert len(sync_calls) == 1
    assert job_names == ["Syncing /movies/movie.en.srt", "Synced /movies/movie.en.srt"]


def test_sync_subtitles_falls_back_for_invalid_threshold(monkeypatch):
    sync_calls = []
    job_names = []

    class SubSyncer:
        def sync(self, **kwargs):
            sync_calls.append(kwargs)

    monkeypatch.setattr(subtitle_sync.settings.subsync, "use_subsync", True)
    monkeypatch.setattr(subtitle_sync.settings.subsync, "use_subsync_movie_threshold", True)
    monkeypatch.setattr(subtitle_sync.settings.subsync, "subsync_movie_threshold", "abc")
    monkeypatch.setattr(subtitle_sync, "_create_subsyncer", SubSyncer)
    monkeypatch.setattr(subtitle_sync.gc, "collect", lambda: None)
    monkeypatch.setattr(
        subtitle_sync.jobs_queue,
        "update_job_name",
        lambda **kwargs: job_names.append(kwargs["new_job_name"]),
    )

    result = subtitle_sync.sync_subtitles(
        video_path="/movies/movie.mkv",
        srt_path="/movies/movie.en.srt",
        srt_lang="en",
        forced=False,
        hi=False,
        percent_score=50,
        radarr_id=7,
        job_id="job",
    )

    assert result is True
    assert len(sync_calls) == 1
    assert job_names == ["Syncing /movies/movie.en.srt", "Synced /movies/movie.en.srt"]


def test_sync_subtitles_reads_default_sync_options_at_call_time(monkeypatch):
    sync_calls = []

    class SubSyncer:
        def sync(self, **kwargs):
            sync_calls.append(kwargs)

    monkeypatch.setattr(subtitle_sync.settings.subsync, "use_subsync", True)
    monkeypatch.setattr(subtitle_sync.settings.subsync, "use_subsync_movie_threshold", False)
    monkeypatch.setattr(subtitle_sync.settings.subsync, "max_offset_seconds", 42)
    monkeypatch.setattr(subtitle_sync.settings.subsync, "gss", True)
    monkeypatch.setattr(subtitle_sync.settings.subsync, "no_fix_framerate", True)
    monkeypatch.setattr(subtitle_sync, "_create_subsyncer", SubSyncer)
    monkeypatch.setattr(subtitle_sync.gc, "collect", lambda: None)
    monkeypatch.setattr(subtitle_sync.jobs_queue, "update_job_name", lambda **kwargs: None)

    result = subtitle_sync.sync_subtitles(
        video_path="/movies/movie.mkv",
        srt_path="/movies/movie.en.srt",
        srt_lang="en",
        forced=False,
        hi=False,
        percent_score=100,
        radarr_id=7,
        job_id="job",
    )

    assert result is True
    assert sync_calls[0]["max_offset_seconds"] == "42"
    assert sync_calls[0]["gss"] is True
    assert sync_calls[0]["no_fix_framerate"] is True

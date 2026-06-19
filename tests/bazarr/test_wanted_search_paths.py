from datetime import datetime, timedelta, timezone
from functools import partial
from unittest.mock import Mock

import pytest
from sqlalchemy import select


def _no_exclusions(media_type):
    return []


def _single_provider_list():
    return ["provider"]


def _empty_provider_list():
    return []


def _english_audio_languages(audio_language):
    return [{"name": "English"}]


def _build_inactive_attempts(active_language, inactive_language):
    now = datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()
    old = now - timedelta(days=30).total_seconds()
    recent = now - timedelta(days=2).total_seconds()
    return [
        (active_language, old),
        (inactive_language, old),
        (inactive_language, recent),
    ]


def _capture_generate_subtitles(calls, *args, **kwargs):
    calls.append((args, kwargs))
    return iter(())


def _capture_wanted_download_subtitles(calls, item_id, **kwargs):
    calls.append(item_id)


def _captured_languages(generate_calls):
    return generate_calls[0][0][1]


def _captured_audio_language(generate_calls):
    return generate_calls[0][0][2]


def _captured_scene_name(generate_calls):
    return generate_calls[0][0][3]


def _run_wanted_worker(wanted_module, kind, row, providers=None, **kwargs):
    if providers is None:
        providers = ["provider"]
    if kind == "movies":
        wanted_module._wanted_movie(row, providers, **kwargs)
    else:
        wanted_module._wanted_episode(row, providers, **kwargs)


def _run_wanted_download_subtitles(wanted_download_subtitles, kind, row, providers=None, **kwargs):
    if providers is None:
        providers = ["provider"]
    if kind == "movies":
        return wanted_download_subtitles(
            row.radarrId,
            job_id="job",
            providers_list=providers,
            movie=row,
            **kwargs,
        )
    return wanted_download_subtitles(
        row.sonarrEpisodeId,
        job_id="job",
        providers_list=providers,
        episode_details=row,
        **kwargs,
    )


@pytest.mark.parametrize(
    "kind,active_language,inactive_language,expected",
    [
        ("movies", "fr:forced", "en", [("en", "False", "False"), ("fr", "False", "True")]),
        ("series", "fr:hi", "en", [("en", "False", "False"), ("fr", "True", "False")]),
    ],
)
def test_wanted_only_requests_due_languages(
    monkeypatch,
    wanted_module,
    row_factory,
    wanted_download_subtitles,
    kind,
    active_language,
    inactive_language,
    expected,
):
    row = row_factory(
        missing_languages=["en", active_language],
        failed_attempts=_build_inactive_attempts(active_language, inactive_language),
    )
    generate_calls = []

    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))
    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)

    _run_wanted_download_subtitles(wanted_download_subtitles, kind, row)

    assert _captured_languages(generate_calls) == expected


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_wanted_handles_malformed_audio_profile_languages(
    monkeypatch, wanted_module, row_factory, wanted_download_subtitles, kind
):
    row = row_factory(missing_languages=[], failed_attempts=[])
    generate_calls = []

    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))
    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", lambda audio_language: [None, {"bad": "shape"}])

    _run_wanted_download_subtitles(wanted_download_subtitles, kind, row, due_languages=["en"])

    assert _captured_audio_language(generate_calls) is None


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_wanted_uses_none_for_missing_scene_name(
    monkeypatch, wanted_module, row_factory, wanted_download_subtitles, kind
):
    row = row_factory(missing_languages=[], failed_attempts=[], sceneName=None)
    generate_calls = []

    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))
    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)

    _run_wanted_download_subtitles(wanted_download_subtitles, kind, row, due_languages=["en"])

    assert _captured_scene_name(generate_calls) is None


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_wanted_skips_generate_when_path_missing(
    monkeypatch, wanted_module, row_factory, wanted_download_subtitles, kind
):
    row = row_factory(missing_languages=[], failed_attempts=[])
    row.path = None
    generate_calls = []

    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))
    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)

    _run_wanted_download_subtitles(wanted_download_subtitles, kind, row, due_languages=["en"])

    assert generate_calls == []


def test_wanted_movie_does_not_stamp_failed_attempts_when_no_providers(
    monkeypatch,
    wanted_module,
    wanted_search_tables,
    row_factory,
):
    movie = row_factory(missing_languages=["en"], failed_attempts=[])
    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, []))
    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)

    wanted_module._wanted_movie(movie, [])

    attempts = wanted_module.database.execute(
        select(wanted_search_tables.failed_subtitle_attempts.c.language).where(
            wanted_search_tables.failed_subtitle_attempts.c.media_type == "movie",
            wanted_search_tables.failed_subtitle_attempts.c.media_id == movie.radarrId,
        )
    ).all()

    assert attempts == []


def test_wanted_episode_does_not_stamp_failed_attempts_when_no_providers(
    monkeypatch,
    wanted_module,
    wanted_search_tables,
    row_factory,
):
    episode = row_factory(missing_languages=["en"], failed_attempts=[])
    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, []))
    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)

    wanted_module._wanted_episode(episode, [])

    attempts = wanted_module.database.execute(
        select(wanted_search_tables.failed_subtitle_attempts.c.language).where(
            wanted_search_tables.failed_subtitle_attempts.c.media_type == "series",
            wanted_search_tables.failed_subtitle_attempts.c.media_id == episode.sonarrEpisodeId,
        )
    ).all()

    assert attempts == []


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_wanted_search_reports_throttled_when_all_providers_are_throttled(
    monkeypatch, wanted_module, row_factory, jobs_queue_factory, kind
):
    progress_updates = []

    row_factory()

    monkeypatch.setattr(wanted_module, "jobs_queue", jobs_queue_factory(progress_updates=progress_updates))
    monkeypatch.setattr(wanted_module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(wanted_module, "get_providers", _empty_provider_list)

    if kind == "movies":
        wanted_module.wanted_search_missing_subtitles_movies(job_id="job")
    else:
        wanted_module.wanted_search_missing_subtitles_series(job_id="job")

    assert progress_updates[-1]["progress_message"] == "All providers throttled"


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_wanted_search_marks_empty_run_complete(monkeypatch, wanted_module, jobs_queue_factory, kind):
    progress_updates = []

    monkeypatch.setattr(wanted_module, "jobs_queue", jobs_queue_factory(progress_updates=progress_updates))
    monkeypatch.setattr(wanted_module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(wanted_module, "get_providers", _single_provider_list)

    if kind == "movies":
        wanted_module.wanted_search_missing_subtitles_movies(job_id="job")
    else:
        wanted_module.wanted_search_missing_subtitles_series(job_id="job")

    assert any(update.get("progress_value") == "max" for update in progress_updates)
    assert progress_updates[-1]["progress_message"] == "Search completed"


@pytest.mark.parametrize("kind,id_attr", [("movies", "radarrId"), ("series", "sonarrEpisodeId")])
def test_wanted_search_refreshes_provider_availability(
    monkeypatch, wanted_module, row_factory, jobs_queue_factory, kind, id_attr
):
    row_one = row_factory()
    if kind == "movies":
        row_factory(radarrId=20, title="Second")
    else:
        row_factory(sonarrEpisodeId=20, title="Series", episodeTitle="Second", episode=2)

    provider_results = Mock(side_effect=[["provider"], []])
    searches = []
    monkeypatch.setattr(wanted_module, "jobs_queue", jobs_queue_factory())

    monkeypatch.setattr(wanted_module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(wanted_module, "get_providers", provider_results)
    if kind == "movies":
        monkeypatch.setattr(
            wanted_module,
            "wanted_download_subtitles_movie",
            partial(_capture_wanted_download_subtitles, searches),
        )
        wanted_module.wanted_search_missing_subtitles_movies(job_id="job")
    else:
        monkeypatch.setattr(
            wanted_module,
            "wanted_download_subtitles",
            partial(_capture_wanted_download_subtitles, searches),
        )
        wanted_module.wanted_search_missing_subtitles_series(job_id="job")

    assert searches == [getattr(row_one, id_attr)]


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_wanted_search_completes_with_empty_list(monkeypatch, wanted_module, jobs_queue_factory, kind):
    names = []

    monkeypatch.setattr(wanted_module, "jobs_queue", jobs_queue_factory(names=names))
    monkeypatch.setattr(wanted_module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(wanted_module, "get_providers", _single_provider_list)

    if kind == "movies":
        wanted_module.wanted_search_missing_subtitles_movies(job_id="job")
    else:
        wanted_module.wanted_search_missing_subtitles_series(job_id="job")

    assert names[-1] == (
        "Searched for missing movies subtitles"
        if kind == "movies"
        else "Searched for missing series subtitles"
    )


@pytest.mark.parametrize("bad_value", [None, "1", "x", 1.5])
def test_wanted_series_scheduled_search_handles_noninteger_episode_numbers(
    monkeypatch, bad_value, wanted_module, jobs_queue_factory, row_factory
):
    searched = []
    progress = []
    row = row_factory(
        sonarrEpisodeId=101,
        sonarrSeriesId=3,
        title="Series",
        season=bad_value,
        episode=bad_value,
        episodeTitle="Pilot",
        monitored=True,
    )

    monkeypatch.setattr(wanted_module, "jobs_queue", jobs_queue_factory(progress_updates=progress))
    monkeypatch.setattr(wanted_module, "wanted_download_subtitles", partial(_capture_wanted_download_subtitles, searched))
    monkeypatch.setattr(wanted_module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(wanted_module, "get_providers", _single_provider_list)

    wanted_module.wanted_search_missing_subtitles_series(job_id="job")

    assert searched == [101]
    assert any("progress_message" in update for update in progress)

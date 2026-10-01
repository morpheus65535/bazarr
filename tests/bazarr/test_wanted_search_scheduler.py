import sqlite3
from functools import partial
from unittest.mock import Mock

import pytest
from sqlalchemy import select

import subtitles.wanted_state as wanted_state


def _no_exclusions(media_type):
    return []


def _single_provider_list():
    return ["provider"]


def _empty_provider_list():
    return []


def _capture_wanted_download_subtitles(calls, item_id, **kwargs):
    calls.append(item_id)


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_scheduled_search_uses_normalized_due_rows(
    monkeypatch,
    wanted_module,
    row_factory,
    jobs_queue_factory,
    wanted_search_job,
    kind,
):
    searched = []
    row = row_factory(missing_languages=["en"], failed_attempts=[])
    wanted_download_subtitles = partial(_capture_wanted_download_subtitles, searched)

    if kind == "movies":
        monkeypatch.setattr(wanted_module, "wanted_download_subtitles_movie", wanted_download_subtitles)
    else:
        monkeypatch.setattr(wanted_module, "wanted_download_subtitles", wanted_download_subtitles)

    monkeypatch.setattr(wanted_module, "jobs_queue", jobs_queue_factory())
    monkeypatch.setattr(wanted_module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(wanted_module, "get_providers", _single_provider_list)

    wanted_search_job(job_id="job")

    key = row.radarrId if kind == "movies" else row.sonarrEpisodeId
    assert searched == [key]


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_wanted_download_rechecks_batched_due_languages(monkeypatch, wanted_module, row_factory, kind):
    item = row_factory(missing_languages=["en"], failed_attempts=[])
    provider_searches = []

    monkeypatch.setattr(
        wanted_module,
        "get_due_missing_languages_map",
        lambda media_type, media_ids, adaptive_search_policy=None: {media_ids[0]: []},
    )
    monkeypatch.setattr(
        wanted_module,
        "generate_subtitles",
        lambda *args, **kwargs: provider_searches.append(args) or iter(()),
    )

    if kind == "movies":
        wanted_module._wanted_movie(item, ["provider"], due_languages=["en"], adaptive_search_policy={})
    else:
        wanted_module._wanted_episode(item, ["provider"], due_languages=["en"], adaptive_search_policy={})

    assert provider_searches == []


@pytest.mark.skipif(not hasattr(sqlite3.Connection, "setlimit"), reason="requires SQLite connection limits")
@pytest.mark.parametrize("kind", ["movies", "series"])
def test_scheduled_search_bounds_detail_queries_for_legacy_sqlite(
    kind,
    monkeypatch,
    wanted_module,
    row_factory,
    jobs_queue_factory,
    transactional_connection,
):
    raw_connection = transactional_connection.connection.driver_connection
    previous_limit = raw_connection.getlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER)
    raw_connection.setlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER, 999)

    for media_id in range(1, 1001):
        overrides = {"radarrId": media_id} if kind == "movies" else {
            "sonarrEpisodeId": media_id,
            "episode": media_id,
        }
        row_factory(**overrides, missing_languages=["en"], failed_attempts=[])

    monkeypatch.setattr(wanted_module, "jobs_queue", jobs_queue_factory())
    monkeypatch.setattr(wanted_module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(wanted_module, "get_providers", _empty_provider_list)

    try:
        if kind == "movies":
            wanted_module._run_wanted_search_missing_subtitles_movies("job", {})
        else:
            wanted_module._run_wanted_search_missing_subtitles_series("job", {})
    finally:
        raw_connection.setlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER, previous_limit)


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

    expected_name = (
        "Searched for missing movies subtitles"
        if kind == "movies"
        else "Searched for missing series subtitles"
    )
    if kind == "movies":
        wanted_module.wanted_search_missing_subtitles_movies(job_id="job")
    else:
        wanted_module.wanted_search_missing_subtitles_series(job_id="job")
    assert names == [expected_name]


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


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_completed_failures_are_saved_when_later_search_raises(
    monkeypatch,
    wanted_module,
    wanted_search_job,
    row_factory,
    jobs_queue_factory,
    wanted_search_tables,
    transactional_session,
    kind,
):
    first = row_factory(missing_languages=["en"], failed_attempts=[])
    second = row_factory(
        **({"radarrId": 20} if kind == "movies" else {"sonarrEpisodeId": 20, "episode": 2}),
        missing_languages=["en"],
        failed_attempts=[],
    )
    id_attr = "radarrId" if kind == "movies" else "sonarrEpisodeId"
    media_type = "movie" if kind == "movies" else "series"
    media_table = wanted_module.TableMovies if kind == "movies" else wanted_module.TableEpisodes
    media_id_column = media_table.c[id_attr]
    monkeypatch.setattr(
        wanted_state,
        "TableMovies" if kind == "movies" else "TableEpisodes",
        media_table,
    )
    calls = []

    def search(item, *args, **kwargs):
        calls.append(getattr(item, id_attr))
        if getattr(item, id_attr) == getattr(second, id_attr):
            raise RuntimeError("later search failed")
        return ["en"]

    monkeypatch.setattr(wanted_module, "_movie_needs_wanted_lookup_refresh" if kind == "movies"
                        else "_episode_needs_wanted_lookup_refresh", lambda item: False)
    monkeypatch.setattr(wanted_module, "_wanted_movie" if kind == "movies" else "_wanted_episode", search)
    monkeypatch.setattr(wanted_module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(wanted_module, "get_providers", _single_provider_list)
    monkeypatch.setattr(wanted_module, "jobs_queue", jobs_queue_factory())

    with pytest.raises(RuntimeError, match="later search failed"):
        wanted_search_job(job_id="job")

    assert calls == [getattr(first, id_attr), getattr(second, id_attr)]
    media_id = getattr(first, id_attr)
    attempts = wanted_search_tables.failed_subtitle_attempts
    saved_languages = transactional_session.execute(
        select(attempts.c.language)
        .where(attempts.c.media_type == media_type)
        .where(attempts.c.media_id == media_id)
    ).scalars().all()
    assert saved_languages == ["en"]
    legacy = transactional_session.execute(
        select(media_table.c.failedAttempts).where(media_id_column == media_id)
    ).scalar_one()
    assert legacy == "[]"
    window = transactional_session.execute(
        select(attempts.c.initial_attempt_at, attempts.c.latest_attempt_at)
        .where(attempts.c.media_type == media_type)
        .where(attempts.c.media_id == media_id)
    ).one()
    assert window.initial_attempt_at == window.latest_attempt_at

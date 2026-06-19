from functools import partial
from unittest.mock import Mock

import pytest


def _no_exclusions(media_type):
    return []


def _single_provider_list():
    return ["provider"]


def _empty_provider_list():
    return []


def _capture_wanted_download_subtitles(calls, item_id, **kwargs):
    calls.append(item_id)


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_scheduled_search_falls_back_to_legacy_rows_when_due_map_is_empty(
    monkeypatch,
    wanted_module,
    row_factory,
    jobs_queue_factory,
    wanted_search_job,
    kind,
):
    searched = []
    row = row_factory(missing_subtitles="['en']", failedAttempts="[]")
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
        assert any("movie" in n.lower() or "search" in n.lower() or "subtitle" in n.lower() for n in names)
    else:
        wanted_module.wanted_search_missing_subtitles_series(job_id="job")
        assert any("subtitle" in n.lower() or "search" in n.lower() or "series" in n.lower() for n in names)


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

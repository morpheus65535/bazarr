# -*- coding: utf-8 -*-
"""
Tests for the task scheduler in app/scheduler.py.

The Scheduler builds a real APScheduler with real jobs, but BackgroundScheduler.start is
patched so no thread runs. The module-level scheduler instance is created at import time
regardless, so these tests build their own instances.
"""
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest import mock

import pytest
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_SUBMITTED
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app import scheduler as scheduler_module


class _Section(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e


@pytest.fixture
def sched_settings(monkeypatch):
    fake = SimpleNamespace(
        general=_Section(use_sonarr=True, use_radarr=True, auto_update=False,
                         wanted_search_frequency=6, wanted_search_frequency_movie=6, upgrade_frequency=12),
        sonarr=_Section(series_sync=15, full_update="Manually", full_update_hour=4, full_update_day=6,
                        series_sync_on_live=False, defer_search_signalr=False),
        radarr=_Section(movies_sync=15, full_update="Manually", full_update_hour=4, full_update_day=6,
                        movies_sync_on_live=False, defer_search_signalr=False),
        backup=_Section(frequency="Manually", hour=3, day=6),
    )
    monkeypatch.setattr(scheduler_module, "settings", fake)
    monkeypatch.setattr(scheduler_module, "args", SimpleNamespace(no_update=True, no_tasks=False))
    monkeypatch.setenv("BAZARR_VERSION", "1.0.0")
    return fake


@pytest.fixture
def build_scheduler(sched_settings, monkeypatch):
    """Build Scheduler instances started in paused mode: next run times are computed but no job runs."""
    created = []
    original_start = scheduler_module.BackgroundScheduler.start

    def paused_start(self, *args, **kwargs):
        original_start(self, paused=True)

    monkeypatch.setattr(scheduler_module.BackgroundScheduler, "start", paused_start)

    def build():
        sched = scheduler_module.Scheduler()
        created.append(sched)
        return sched

    yield build
    for sched in created:
        sched.aps_scheduler.shutdown(wait=False)


def _job_ids(sched):
    return {job.id for job in sched.aps_scheduler.get_jobs()}


def _job(sched, job_id):
    return next(job for job in sched.aps_scheduler.get_jobs() if job.id == job_id)


# Helpers

def test_in_a_century_is_far_in_the_future():
    assert scheduler_module.in_a_century() == datetime.now().year + 100


def test_a_long_time_from_now_treats_unscheduled_jobs_as_never():
    assert scheduler_module.a_long_time_from_now(SimpleNamespace(next_run_time=None)) is True


def test_a_long_time_from_now_distinguishes_near_and_far_runs():
    now = datetime.now().astimezone()

    assert scheduler_module.a_long_time_from_now(SimpleNamespace(next_run_time=now + timedelta(hours=1))) is False
    assert scheduler_module.a_long_time_from_now(SimpleNamespace(next_run_time=now + timedelta(days=400))) is True


# Job registration

def test_core_jobs_are_registered(build_scheduler):
    ids = _job_ids(build_scheduler())

    assert {
        "cache_cleanup", "check_health", "update_series", "update_movies", "backup",
        "series_full_scan_subtitles", "movies_full_scan_subtitles", "update_release",
        "update_announcements", "wanted_search_missing_subtitles_series",
        "wanted_search_missing_subtitles_movies", "upgrade_subtitles",
    } <= ids
    assert "update_bazarr" not in ids  # --no_update skips the self-updater


def test_sonarr_jobs_are_skipped_when_sonarr_is_disabled(sched_settings, build_scheduler):
    sched_settings.general["use_sonarr"] = False

    ids = _job_ids(build_scheduler())

    assert not {"update_series", "series_full_scan_subtitles", "wanted_search_missing_subtitles_series"} & ids
    assert "update_movies" in ids


def test_radarr_jobs_are_skipped_when_radarr_is_disabled(sched_settings, build_scheduler):
    sched_settings.general["use_radarr"] = False

    ids = _job_ids(build_scheduler())

    assert not {"update_movies", "movies_full_scan_subtitles", "wanted_search_missing_subtitles_movies"} & ids
    assert "update_series" in ids


def test_upgrade_job_is_skipped_when_no_provider_is_enabled(sched_settings, build_scheduler):
    sched_settings.general["use_sonarr"] = False
    sched_settings.general["use_radarr"] = False

    assert "upgrade_subtitles" not in _job_ids(build_scheduler())


@pytest.mark.parametrize("frequency", ["Daily", "Weekly"])
def test_full_scan_uses_cron_for_scheduled_frequencies(sched_settings, build_scheduler, frequency):
    sched_settings.sonarr["full_update"] = frequency

    job = _job(build_scheduler(), "series_full_scan_subtitles")

    assert isinstance(job.trigger, CronTrigger)
    assert str(job.trigger.fields[5]) == "4"  # hour


def test_auto_update_schedules_self_updater(sched_settings, build_scheduler, monkeypatch):
    # The updater is only imported when --no_update is off at import time, so stub it here
    monkeypatch.setattr(scheduler_module, "check_if_new_update", lambda: None, raising=False)
    monkeypatch.setattr(scheduler_module, "args", SimpleNamespace(no_update=False, no_tasks=False))
    sched_settings.general["auto_update"] = True

    job = _job(build_scheduler(), "update_bazarr")

    assert isinstance(job.trigger, IntervalTrigger)
    assert job.trigger.interval == timedelta(hours=6)


# Scheduling behavior

def test_no_tasks_unschedules_every_job(sched_settings, build_scheduler, monkeypatch):
    monkeypatch.setattr(scheduler_module, "args", SimpleNamespace(no_update=True, no_tasks=True))

    sched = build_scheduler()

    assert sched.aps_scheduler.get_jobs()
    assert all(job.next_run_time is None for job in sched.aps_scheduler.get_jobs())


def test_interval_jobs_start_inside_randomized_window(build_scheduler):
    sched = build_scheduler()
    job = _job(sched, "cache_cleanup")
    interval = job.trigger.interval.total_seconds()
    now = datetime.now(job.next_run_time.tzinfo)

    offset = (job.next_run_time - now).total_seconds()
    assert 0.75 * interval - 5 <= offset <= interval + 5


def test_execute_job_now_moves_next_run_to_now(build_scheduler):
    sched = build_scheduler()

    sched.execute_job_now("update_series")

    next_run = _job(sched, "update_series").next_run_time
    assert abs((next_run - datetime.now(next_run.tzinfo)).total_seconds()) < 5


def _listeners(sched):
    # APScheduler keeps (callback, event mask) pairs in a private list; the scheduler registers its
    # running-task listeners there.
    return sched.aps_scheduler._listeners


def test_running_tasks_track_submitted_jobs(build_scheduler):
    sched = build_scheduler()

    with mock.patch.object(scheduler_module, "event_stream") as stream:
        for callback, mask in _listeners(sched):
            if mask & EVENT_JOB_SUBMITTED:
                callback(SimpleNamespace(code=EVENT_JOB_SUBMITTED, job_id="update_series"))

    assert "update_series" in sched.get_running_tasks()
    stream.assert_called_with(type="task")


@pytest.mark.parametrize("finish_code", [EVENT_JOB_EXECUTED, EVENT_JOB_ERROR])
def test_running_tasks_drop_finished_jobs(build_scheduler, finish_code):
    sched = build_scheduler()

    with mock.patch.object(scheduler_module, "event_stream"):
        for callback, mask in _listeners(sched):
            if mask & EVENT_JOB_SUBMITTED:
                callback(SimpleNamespace(code=EVENT_JOB_SUBMITTED, job_id="update_series"))
            if mask & finish_code:
                callback(SimpleNamespace(code=finish_code, job_id="update_series"))

    assert "update_series" not in sched.get_running_tasks()


# Task list for the UI

def test_task_list_describes_interval_jobs(sched_settings, build_scheduler):
    sched_settings.sonarr["series_sync"] = 15
    sched_settings.general["upgrade_frequency"] = 6

    tasks = {task["job_id"]: task for task in build_scheduler().get_task_list()}

    assert tasks["update_series"]["name"] == "Sync with Sonarr"
    assert tasks["update_series"]["interval"] == "every 15 minutes"
    assert tasks["upgrade_subtitles"]["interval"] == "every 6 hours"
    assert tasks["update_series"]["job_running"] is False


@pytest.mark.xfail(
    strict=True,
    reason="get_time_from_interval compares with `>` and skips a unit that matches exactly, so a one-hour "
           "interval is shown as '60 minutes' instead of '1 hour'. Found while writing these tests.",
)
def test_task_list_shows_single_unit_intervals_naturally(sched_settings, build_scheduler):
    sched_settings.general["upgrade_frequency"] = 1

    tasks = {task["job_id"]: task for task in build_scheduler().get_task_list()}

    assert tasks["upgrade_subtitles"]["interval"] == "every 1 hour"


def test_task_list_describes_cron_jobs_by_weekday_and_hour(sched_settings, build_scheduler):
    sched_settings.sonarr["full_update"] = "Weekly"
    sched_settings.sonarr["full_update_day"] = 2
    sched_settings.sonarr["full_update_hour"] = 4

    tasks = {task["job_id"]: task for task in build_scheduler().get_task_list()}

    assert tasks["series_full_scan_subtitles"]["interval"] == "every Wednesday at 4:00"

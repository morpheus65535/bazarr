import pytest

from app import jobs_queue as jobs_queue_module
from app.jobs_queue import JobsQueue


@pytest.fixture
def queue(monkeypatch):
    monkeypatch.setattr(jobs_queue_module, "event_stream", lambda **kwargs: None)
    monkeypatch.setattr(jobs_queue_module.settings.general, "concurrent_jobs", 3)
    monkeypatch.setattr(jobs_queue_module.settings.subsync, "concurrent_syncs", 1)
    return JobsQueue()


def _add_sync(queue, srt_path):
    return queue.feed_jobs_pending_queue(job_name=f"Syncing {srt_path}", module="bazarr.subtitles.sync",
                                         func="sync_subtitles", kwargs={"srt_path": srt_path}, is_progress=True)


def _add_other(queue, name):
    return queue.feed_jobs_pending_queue(job_name=name, module="sonarr.sync.series", func="update_series",
                                         kwargs={"name": name})


def test_job_is_sync(queue):
    _add_sync(queue, "a.srt")
    _add_other(queue, "series")
    sync_job, other_job = queue.jobs_pending_queue
    assert sync_job.is_sync is True
    assert other_job.is_sync is False


def test_reserve_respects_concurrent_syncs(queue):
    first_sync = _add_sync(queue, "a.srt")
    second_sync = _add_sync(queue, "b.srt")
    other = _add_other(queue, "series")

    reserved = [queue._reserve_next_runnable_job() for _ in range(3)]

    # the second sync is skipped because of concurrent_syncs=1, the job behind it can still start
    assert [job.job_id if job else None for job in reserved] == [first_sync, other, None]
    assert [job.job_id for job in queue.jobs_pending_queue] == [second_sync]
    assert all(job.status == "running" for job in queue.jobs_running_queue)


def test_reserve_starts_next_sync_when_slot_frees(queue, monkeypatch):
    monkeypatch.setattr(jobs_queue_module.settings.subsync, "concurrent_syncs", 2)
    first_sync = _add_sync(queue, "a.srt")
    second_sync = _add_sync(queue, "b.srt")
    third_sync = _add_sync(queue, "c.srt")

    assert queue._reserve_next_runnable_job().job_id == first_sync
    assert queue._reserve_next_runnable_job().job_id == second_sync
    assert queue._reserve_next_runnable_job() is None

    queue.jobs_running_queue.popleft()
    assert queue._reserve_next_runnable_job().job_id == third_sync


def test_reserve_respects_concurrent_jobs(queue, monkeypatch):
    monkeypatch.setattr(jobs_queue_module.settings.general, "concurrent_jobs", 1)
    first = _add_other(queue, "one")
    _add_other(queue, "two")

    assert queue._reserve_next_runnable_job().job_id == first
    assert queue._reserve_next_runnable_job() is None
    assert len(queue.jobs_running_queue) == 1


def test_run_reserved_job_does_not_duplicate_running_entry(queue, monkeypatch):
    calls = []
    monkeypatch.setattr(jobs_queue_module.importlib, "import_module",
                        lambda name: type("M", (), {"update_series": staticmethod(
                            lambda **kwargs: calls.append(len(queue.jobs_running_queue)))}))
    job_id = _add_other(queue, "series")
    job = queue._reserve_next_runnable_job()

    assert queue._run_job(job_instance=job, reserved=True) is True
    # the job was in the running queue exactly once while running, then moved to completed
    assert calls == [1]
    assert len(queue.jobs_running_queue) == 0
    assert queue.jobs_completed_queue[-1].job_id == job_id

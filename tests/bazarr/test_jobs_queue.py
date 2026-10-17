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


def _cancel(queue, job_id, new_name=None):
    job = next(job for job in queue.jobs_pending_queue if job.job_id == job_id)
    queue.jobs_pending_queue.remove(job)
    job.kwargs["job_id"] = job.job_id
    job.status = "canceled"
    if new_name:
        job.job_name = new_name
    queue.jobs_canceled_queue.append(job)
    return job


def test_rerun_canceled_job_queues_a_fresh_copy(queue):
    job_id = _add_sync(queue, "a.srt")
    canceled = _cancel(queue, job_id, new_name="Sync canceled a.srt")

    new_job_id = queue.rerun_canceled_job(job_id)

    assert new_job_id and new_job_id != job_id
    assert list(queue.jobs_canceled_queue) == []
    (new_job,) = queue.jobs_pending_queue
    assert new_job.job_name == "Syncing a.srt"
    assert new_job.kwargs == {"srt_path": "a.srt"}
    assert new_job.status == "pending"
    assert (new_job.module, new_job.func, new_job.is_progress) == (canceled.module, canceled.func, True)


def test_rerun_ignores_jobs_that_are_not_canceled(queue):
    job_id = _add_sync(queue, "a.srt")

    assert queue.rerun_canceled_job(job_id) is False
    assert queue.rerun_canceled_job(12345) is False
    assert len(queue.jobs_pending_queue) == 1


def test_rerun_keeps_canceled_job_when_identical_job_already_queued(queue):
    job_id = _add_sync(queue, "a.srt")
    _cancel(queue, job_id)
    _add_sync(queue, "a.srt")

    assert queue.rerun_canceled_job(job_id) is False
    assert len(queue.jobs_canceled_queue) == 1
    assert len(queue.jobs_pending_queue) == 1


def _run_threads_inline(monkeypatch):
    class InlineThread:
        def __init__(self, target, daemon=None):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(jobs_queue_module, "Thread", InlineThread)


def _add_sync_with_callback(queue, srt_path, calls):
    return queue.feed_jobs_pending_queue(job_name=f"Syncing {srt_path}", module="bazarr.subtitles.sync",
                                         func="sync_subtitles",
                                         kwargs={"srt_path": srt_path, "callback": lambda: calls.append(srt_path)},
                                         is_progress=True)


def test_removing_pending_job_runs_its_callback(queue, monkeypatch):
    _run_threads_inline(monkeypatch)
    calls = []
    job_id = _add_sync_with_callback(queue, "a.srt", calls)
    _add_sync_with_callback(queue, "b.srt", calls)

    assert queue.remove_job_from_pending_queue(job_id) is True
    assert calls == ["a.srt"]
    assert len(queue.jobs_pending_queue) == 1


def test_emptying_pending_queue_runs_callbacks(queue, monkeypatch):
    _run_threads_inline(monkeypatch)
    calls = []
    _add_sync_with_callback(queue, "a.srt", calls)
    _add_other(queue, "series")

    def failing_callback():
        raise RuntimeError("boom")

    queue.feed_jobs_pending_queue(job_name="failing", module="bazarr.subtitles.sync", func="sync_subtitles",
                                  kwargs={"srt_path": "c.srt", "callback": failing_callback})
    _add_sync_with_callback(queue, "b.srt", calls)

    assert queue.empty_jobs_queue("pending") is True
    # a failing callback doesn't prevent the next ones from running
    assert calls == ["a.srt", "b.srt"]
    assert list(queue.jobs_pending_queue) == []


def test_emptying_other_queues_does_not_run_callbacks(queue, monkeypatch):
    _run_threads_inline(monkeypatch)
    calls = []
    job_id = _add_sync_with_callback(queue, "a.srt", calls)
    _cancel(queue, job_id)

    assert queue.empty_jobs_queue("canceled") is True
    assert calls == []

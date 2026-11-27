"""
The jobs queue imports a job by its file path, so the full league sync runs as bazarr.sportarr.sync.leagues, a
second module object next to sportarr.sync.leagues. The debt that the event stream keeps must still settle when
that copy completes a full sync.
"""
import importlib

from app.jobs_queue import jobs_queue
import pytest

from sportarr import sse_client
from sportarr.sync import leagues as sync_leagues
from sportarr.sync import state as sync_state


@pytest.fixture
def isolated_sync_state(monkeypatch):
    """The job writes the shared sync state and leaves a job in the global queue. Both are undone."""
    for name in ('last_complete_sync_started_at', 'last_sync_started_at', 'last_incomplete_sync_reason'):
        monkeypatch.setattr(sync_state, name, getattr(sync_state, name))
    queues = (jobs_queue.jobs_pending_queue, jobs_queue.jobs_running_queue, jobs_queue.jobs_completed_queue,
              jobs_queue.jobs_failed_queue)
    before = [list(queue) for queue in queues]
    yield
    for queue, jobs in zip(queues, before):
        queue.clear()
        queue.extend(jobs)


def test_full_sync_run_by_the_jobs_queue_settles_the_stream_debt(tmp_path, monkeypatch, isolated_sync_state):
    monkeypatch.setattr(sse_client, 'cursor_file_path', lambda: str(tmp_path / 'sportarr_stream.json'))
    monkeypatch.setattr(sse_client, 'url_sportarr', lambda: 'http://sportarr:1867')
    monkeypatch.setattr(sse_client, 'queue_full_sync', lambda: None)
    monkeypatch.setattr(sse_client, 'full_sync_queued_or_running', lambda: False)
    client = sse_client.SportarrSSEClient()
    run = sse_client._Run()
    client.load_cursor(run)
    client._run = run
    client.owe_full_sync(run)
    assert run.owed_at is not None

    # Queue the sync the way the scheduler does, and find the module the jobs queue will import.
    job_id = sync_leagues.update_leagues()
    job = next(job for job in jobs_queue.jobs_pending_queue if job.job_id == job_id)
    job_module = importlib.import_module(job.module)
    assert job.module == 'bazarr.sportarr.sync.leagues'
    assert job_module is not sync_leagues
    # Sportarr answers with an empty, complete league list, so nothing else runs.
    monkeypatch.setattr(job_module, 'check_sportarr_rootfolder', lambda: None)
    monkeypatch.setattr(job_module, 'get_leagues_from_sportarr_api', lambda **kwargs: [])
    monkeypatch.setattr(job_module, 'get_tags', lambda: [])
    monkeypatch.setattr(job_module, 'get_language_profiles', lambda: [])
    monkeypatch.setattr(job_module, 'update_one_league', lambda *args, **kwargs: None)

    assert jobs_queue._run_job(job)
    client.settle_full_sync(run)

    assert run.owed_at is None

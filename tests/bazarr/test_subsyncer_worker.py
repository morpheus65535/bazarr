import textwrap

import pytest

from subtitles.tools import subsyncer as subsyncer_module
from subtitles.tools.subsyncer import SubSyncer


def _fake_worker(tmp_path, body):
    worker = tmp_path / "fake_worker.py"
    worker.write_text(textwrap.dedent("""
        import json, sys
        payload = json.loads(sys.stdin.read())
        def emit(message):
            print(json.dumps(message), flush=True)
    """) + textwrap.dedent(body))
    return str(worker)


@pytest.fixture
def progress_calls(monkeypatch):
    calls = []
    monkeypatch.setattr(subsyncer_module.jobs_queue, "update_job_progress", lambda **kwargs: calls.append(kwargs))
    return calls


def test_run_in_subprocess_forwards_progress_and_returns_result(tmp_path, monkeypatch, progress_calls):
    monkeypatch.setattr(subsyncer_module, "WORKER_PATH", _fake_worker(tmp_path, """
        sys.stderr.write(json.dumps({"name": "ffsubsync.ffsubsync", "levelno": 20, "msg": "hello"}) + "\\n")
        sys.stderr.write("not json\\n")
        emit({"type": "progress", "processed": 5.0, "total": 10.0})
        emit({"type": "progress", "processed": 1.0, "total": None})
        emit({"type": "result", "result": {"retval": 0, "offset_seconds": 1.5,
                                          "framerate_scale_factor": 1.0, "args": payload["args"]}})
    """))
    syncer = SubSyncer()
    syncer.job_id = 7

    result = syncer._run_in_subprocess(["video.mkv", "-i", "sub.srt"])

    assert result["offset_seconds"] == 1.5
    assert result["args"] == ["video.mkv", "-i", "sub.srt"]
    # progress with an unknown total is ignored
    assert progress_calls == [{"job_id": 7, "progress_value": 5.0, "progress_max": 10.0}]


def test_run_in_subprocess_raises_on_worker_error(tmp_path, monkeypatch, progress_calls):
    monkeypatch.setattr(subsyncer_module, "WORKER_PATH", _fake_worker(tmp_path, """
        emit({"type": "error", "message": "it broke"})
        sys.exit(1)
    """))

    with pytest.raises(RuntimeError, match="it broke"):
        SubSyncer()._run_in_subprocess([])


def test_run_in_subprocess_raises_when_worker_dies_without_result(tmp_path, monkeypatch, progress_calls):
    monkeypatch.setattr(subsyncer_module, "WORKER_PATH", _fake_worker(tmp_path, """
        sys.exit(3)
    """))

    with pytest.raises(RuntimeError, match="code 3"):
        SubSyncer()._run_in_subprocess([])


def test_real_worker_loads_ffsubsync_and_reports_bad_arguments(progress_calls):
    # runs the actual worker: it must be able to import ffsubsync from libs on its own
    with pytest.raises(RuntimeError, match="arguments parsing failed"):
        SubSyncer()._run_in_subprocess(["--this-option-does-not-exist"])

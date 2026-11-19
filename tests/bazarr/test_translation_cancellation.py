import threading

import pytest

from app.jobs_queue import Job, JobCanceled, jobs_queue
from bazarr.subtitles.tools.translate.services import lingarr_translator
from bazarr.subtitles.tools.translate.services import openai_compatible_translator


@pytest.fixture
def running_job():
    """Place a cancellable job in the running queue for the duration of a test."""
    job = Job(job_id=901, job_name="Translating test", module="m", func="f", is_cancellable=True)
    jobs_queue.jobs_running_queue.append(job)
    try:
        yield job
    finally:
        jobs_queue.jobs_running_queue.remove(job)


def test_cancel_running_job_sets_event_only_for_cancellable_jobs(running_job):
    """Cancellable jobs get their cancel event set; other running jobs are left alone."""
    assert jobs_queue.cancel_running_job(job_id=running_job.job_id) is True
    assert running_job.cancel_event.is_set()

    running_job.is_cancellable = False
    running_job.cancel_event.clear()
    assert jobs_queue.cancel_running_job(job_id=running_job.job_id) is False
    assert not running_job.cancel_event.is_set()


def test_raise_if_cancel_requested_only_raises_after_cancel(running_job):
    """The safe-point check is a no-op until cancellation is requested."""
    jobs_queue.raise_if_cancel_requested(running_job.job_id)
    jobs_queue.raise_if_cancel_requested(None)

    running_job.cancel_event.set()
    with pytest.raises(JobCanceled):
        jobs_queue.raise_if_cancel_requested(running_job.job_id)


def _srt_file(tmp_path):
    path = tmp_path / "input.srt"
    path.write_text("1\n00:00:01,000 --> 00:00:02,000\nHello\n\n", encoding="utf-8")
    return str(path)


def test_openai_translation_stops_before_first_batch_when_cancelled(mocker, tmp_path, running_job):
    """A cancelled job makes no translation request and raises JobCanceled."""
    running_job.cancel_event.set()
    request = mocker.patch.object(openai_compatible_translator, "_request_translation")
    service = openai_compatible_translator.OpenAICompatibleTranslatorService(
        source_srt_file=_srt_file(tmp_path),
        dest_srt_file=str(tmp_path / "output.srt"),
        to_lang="fra",
        media_type="movie",
        sonarr_series_id=None,
        sonarr_episode_id=None,
        radarr_id=1,
        forced=False,
        hi=False,
        video_path="/tmp/video.mkv",
        from_lang="en",
        orig_to_lang="fr",
    )

    with pytest.raises(JobCanceled):
        service.translate(job_id=running_job.job_id)

    request.assert_not_called()
    assert not (tmp_path / "output.srt").exists()


def _lingarr_response(status_code, json_body=None):
    response = type("R", (), {})()
    response.status_code = status_code
    response.text = ""
    response.json = lambda: json_body
    response.raise_for_status = lambda: None
    return response


def _lingarr_service(tmp_path):
    return lingarr_translator.LingarrTranslatorService(
        source_srt_file=str(tmp_path / "input.srt"),
        dest_srt_file=str(tmp_path / "output.srt"),
        lang_obj=type("L", (), {"alpha2": "fr"})(),
        to_lang="fra",
        from_lang="en",
        media_type="movie",
        video_path="/tmp/video.mkv",
        orig_to_lang="fr",
        forced=False,
        hi=False,
        sonarr_series_id=1,
        sonarr_episode_id=1,
        radarr_id=1,
    )


def test_lingarr_cancel_while_request_in_flight_cancels_remote_request(mocker, tmp_path, running_job):
    """Cancelling mid-request looks up the Lingarr request, cancels it once, and does not resubmit."""
    release = threading.Event()
    title = "Synthetic title · input.srt"
    remote_request = {"id": 7, "title": title, "completedAt": None, "status": 1}
    cancel_calls = []

    def fake_post(url, **kwargs):
        if url.endswith("/api/translate/content"):
            release.wait(10)
            return _lingarr_response(200, [])
        cancel_calls.append((url, kwargs))
        return _lingarr_response(200, remote_request)

    def fake_get(url, **kwargs):
        return _lingarr_response(200, {"items": [remote_request], "totalCount": 1})

    mocker.patch.object(lingarr_translator, "get_title", return_value="Synthetic title")
    mocker.patch.object(lingarr_translator.settings.translator, "lingarr_url", "http://lingarr:9876", create=True)
    mocker.patch.object(lingarr_translator.settings.translator, "lingarr_token", "", create=True)
    mocker.patch.object(lingarr_translator.settings.translator, "lingarr_timeout", 1920, create=True)
    post = mocker.patch.object(lingarr_translator.requests, "post", side_effect=fake_post)
    mocker.patch.object(lingarr_translator.requests, "get", side_effect=fake_get)

    service = _lingarr_service(tmp_path)
    timer = threading.Timer(0.2, running_job.cancel_event.set)
    timer.start()
    try:
        with pytest.raises(JobCanceled):
            service._translate_content(["Hello"], job_id=running_job.job_id)
    finally:
        release.set()
        timer.cancel()

    content_posts = [c for c in post.call_args_list if c.args[0].endswith("/api/translate/content")]
    assert len(content_posts) == 1
    assert len(cancel_calls) == 1
    assert cancel_calls[0][0] == "http://lingarr:9876/api/TranslationRequest/cancel"
    assert cancel_calls[0][1]["json"] == remote_request


def test_cancel_lookup_survives_concurrent_queue_changes(running_job):
    """Cancel checks from worker threads must not fail while the job runner changes the running queue."""
    import sys
    import time

    switch_interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    errors = []
    stop = threading.Event()

    def churn():
        """Repeatedly add and remove running jobs, as the job runner does."""
        i = 0
        while not stop.is_set():
            job = Job(job_id=50_000 + i, job_name="churn", module="m", func="f")
            jobs_queue.jobs_running_queue.append(job)
            for k in range(20):
                jobs_queue.jobs_running_queue.append(Job(job_id=60_000 + k, job_name="other", module="m", func="f"))
            for _ in range(20):
                jobs_queue.jobs_running_queue.pop()
            jobs_queue.jobs_running_queue.remove(job)
            i += 1

    def check():
        """Repeatedly run the safe-point check, as translator worker threads do."""
        while not stop.is_set():
            try:
                jobs_queue.raise_if_cancel_requested(99_999)  # not queued, so every lookup scans the whole queue
            except JobCanceled:
                pass
            except Exception as e:
                errors.append(e)

    threads = [threading.Thread(target=churn)] + [threading.Thread(target=check) for _ in range(8)]
    try:
        for thread in threads:
            thread.start()
        time.sleep(3)
    finally:
        stop.set()
        for thread in threads:
            thread.join()
        sys.setswitchinterval(switch_interval)

    assert errors == []

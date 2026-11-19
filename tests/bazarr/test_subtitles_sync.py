import pytest

from subtitles import sync as sync_module


class FakeSubSyncer:
    calls = []

    def sync(self, **kwargs):
        self.calls.append(kwargs)


def test_sync_subtitles_reads_default_settings_at_runtime(monkeypatch):
    monkeypatch.setattr(sync_module, "_create_subsyncer", FakeSubSyncer)
    monkeypatch.setattr(sync_module.jobs_queue, "update_job_name", lambda **kwargs: None)
    monkeypatch.setattr(sync_module.settings.subsync, "use_subsync", True)
    monkeypatch.setattr(sync_module.settings.subsync, "use_subsync_threshold", False)
    monkeypatch.setattr(sync_module.settings.subsync, "max_offset_seconds", 300)
    monkeypatch.setattr(sync_module.settings.subsync, "no_fix_framerate", False)
    monkeypatch.setattr(sync_module.settings.subsync, "gss", False)
    FakeSubSyncer.calls = []

    result = sync_module.sync_subtitles(
        video_path="/media/show/episode.mkv",
        srt_path="/media/show/episode.en.srt",
        srt_lang="en",
        forced=False,
        hi=False,
        percent_score=100,
        sonarr_series_id=1,
        sonarr_episode_id=2,
        job_id=3,
    )

    assert result is True
    assert FakeSubSyncer.calls[0]["max_offset_seconds"] == "300"
    assert FakeSubSyncer.calls[0]["no_fix_framerate"] is False
    assert FakeSubSyncer.calls[0]["gss"] is False


def test_sync_subtitles_preserves_explicit_sync_options(monkeypatch):
    monkeypatch.setattr(sync_module, "_create_subsyncer", FakeSubSyncer)
    monkeypatch.setattr(sync_module.jobs_queue, "update_job_name", lambda **kwargs: None)
    monkeypatch.setattr(sync_module.settings.subsync, "use_subsync", True)
    monkeypatch.setattr(sync_module.settings.subsync, "use_subsync_threshold", False)
    monkeypatch.setattr(sync_module.settings.subsync, "max_offset_seconds", 600)
    monkeypatch.setattr(sync_module.settings.subsync, "no_fix_framerate", True)
    monkeypatch.setattr(sync_module.settings.subsync, "gss", True)
    FakeSubSyncer.calls = []

    result = sync_module.sync_subtitles(
        video_path="/media/show/episode.mkv",
        srt_path="/media/show/episode.en.srt",
        srt_lang="en",
        forced=False,
        hi=False,
        percent_score=100,
        sonarr_series_id=1,
        sonarr_episode_id=2,
        job_id=3,
        max_offset_seconds="120",
        no_fix_framerate=False,
        gss=False,
        reference="a:0",
        force_sync=True,
    )

    assert result is True
    assert FakeSubSyncer.calls[0]["max_offset_seconds"] == "120"
    assert FakeSubSyncer.calls[0]["no_fix_framerate"] is False
    assert FakeSubSyncer.calls[0]["gss"] is False
    assert FakeSubSyncer.calls[0]["reference"] == "a:0"
    assert FakeSubSyncer.calls[0]["force_sync"] is True


def _patch_subsyncer(monkeypatch, sync_result):
    from subtitles.tools import subsyncer as subsyncer_module

    from ffsubsync.ffsubsync import make_parser

    captured = {}

    def fake_run_in_subprocess(self, unparsed_args):
        # parse the arguments the same way the worker process does
        args = make_parser().parse_args(args=unparsed_args)
        captured["args"] = args
        with open(args.srtout, "w") as f:
            f.write("synced")
        return sync_result

    monkeypatch.setattr(subsyncer_module, "get_binary", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(subsyncer_module.SubSyncer, "_run_in_subprocess", fake_run_in_subprocess)
    monkeypatch.setattr(subsyncer_module, "history_log", lambda **kwargs: captured.setdefault("history", kwargs))
    monkeypatch.setattr(subsyncer_module.settings.subsync, "debug", False)
    monkeypatch.setattr(subsyncer_module.settings.subsync, "force_audio", False)
    monkeypatch.setattr(subsyncer_module.settings.subsync, "use_original_language", False)
    monkeypatch.setattr(subsyncer_module.settings.subsync, "auto_use_original_language", False)
    return subsyncer_module.SubSyncer(), captured


def _sync(subsyncer, srt_path, no_fix_framerate=True):
    return subsyncer.sync(video_path="/media/show/episode.mkv", srt_path=str(srt_path), srt_lang="en", hi=False,
                          forced=False, max_offset_seconds="60", no_fix_framerate=no_fix_framerate, gss=False,
                          sonarr_series_id=1, sonarr_episode_id=2, quality_min_score=0.0,
                          quality_max_offset_seconds=30, quality_max_framerate_deviation=0.1)


def test_subsyncer_enables_quality_checks_without_framerate_fixing(monkeypatch, tmp_path):
    srt = tmp_path / "episode.en.srt"
    srt.write_text("original")
    subsyncer, captured = _patch_subsyncer(monkeypatch, {"sync_was_successful": True, "offset_seconds": 1.0,
                                                         "framerate_scale_factor": 1.0})

    _sync(subsyncer, srt, no_fix_framerate=True)

    assert captured["args"].no_fix_framerate is True
    assert captured["args"].skip_sync_on_low_quality is True
    assert captured["args"].min_score == 0.0
    assert captured["args"].quality_max_offset_seconds == 30.0


def test_subsyncer_enables_quality_checks_with_framerate_fixing(monkeypatch, tmp_path):
    srt = tmp_path / "episode.en.srt"
    srt.write_text("original")
    subsyncer, captured = _patch_subsyncer(monkeypatch, {"sync_was_successful": True, "offset_seconds": 1.0,
                                                         "framerate_scale_factor": 1.0})

    _sync(subsyncer, srt, no_fix_framerate=False)

    assert captured["args"].no_fix_framerate is False
    assert captured["args"].skip_sync_on_low_quality is True
    assert captured["args"].max_framerate_deviation == 0.1


def test_subsyncer_keeps_original_when_sync_rejected(monkeypatch, tmp_path):
    srt = tmp_path / "episode.en.srt"
    srt.write_text("original")
    subsyncer, captured = _patch_subsyncer(monkeypatch, {"sync_was_successful": False, "offset_seconds": None,
                                                         "framerate_scale_factor": None})

    _sync(subsyncer, srt)

    assert srt.read_text() == "original"
    assert not (tmp_path / "episode.en.synced.srt").exists()
    assert "history" not in captured


def test_subsyncer_replaces_original_when_sync_succeeds(monkeypatch, tmp_path):
    srt = tmp_path / "episode.en.srt"
    srt.write_text("original")
    subsyncer, captured = _patch_subsyncer(monkeypatch, {"sync_was_successful": True, "offset_seconds": 1.0,
                                                         "framerate_scale_factor": 1.0})

    _sync(subsyncer, srt)

    assert srt.read_text() == "synced"
    assert not (tmp_path / "episode.en.synced.srt").exists()
    assert "history" in captured


class FailingSubSyncer:
    def sync(self, **kwargs):
        raise RuntimeError("boom")


def _patch_common(monkeypatch, subsyncer=FakeSubSyncer):
    monkeypatch.setattr(sync_module, "_create_subsyncer", subsyncer)
    monkeypatch.setattr(sync_module.jobs_queue, "update_job_name", lambda **kwargs: None)
    monkeypatch.setattr(sync_module.jobs_queue, "update_job_progress", lambda **kwargs: None)
    monkeypatch.setattr(sync_module.settings.subsync, "use_subsync", True)
    FakeSubSyncer.calls = []


def _sync_with_callback(callback, percent_score=100):
    return sync_module.sync_subtitles(
        video_path="/media/movie.mkv",
        srt_path="/media/movie.en.srt",
        srt_lang="en",
        forced=False,
        hi=False,
        percent_score=percent_score,
        radarr_id=1,
        job_id=3,
        callback=callback,
    )


def test_sync_subtitles_runs_callback_after_sync(monkeypatch):
    _patch_common(monkeypatch)
    monkeypatch.setattr(sync_module.settings.subsync, "use_subsync_movie_threshold", False)
    calls = []

    assert _sync_with_callback(lambda: calls.append(len(FakeSubSyncer.calls))) is True
    # callback runs once, after the sync itself
    assert calls == [1]


def test_sync_subtitles_runs_callback_when_threshold_skips_sync(monkeypatch):
    _patch_common(monkeypatch)
    monkeypatch.setattr(sync_module.settings.subsync, "use_subsync_movie_threshold", True)
    monkeypatch.setattr(sync_module.settings.subsync, "subsync_movie_threshold", 70)
    calls = []

    assert _sync_with_callback(lambda: calls.append(True), percent_score=100) is False
    assert FakeSubSyncer.calls == []
    assert calls == [True]


def test_sync_subtitles_runs_callback_when_sync_fails(monkeypatch):
    _patch_common(monkeypatch, subsyncer=FailingSubSyncer)
    monkeypatch.setattr(sync_module.settings.subsync, "use_subsync_movie_threshold", False)
    calls = []

    assert _sync_with_callback(lambda: calls.append(True)) is False
    assert calls == [True]


def test_sync_subtitles_without_job_id_queues_a_job_and_defers_callback(monkeypatch):
    _patch_common(monkeypatch)
    queued = []
    monkeypatch.setattr(sync_module.jobs_queue, "add_job_from_function",
                        lambda job_name, is_progress, is_cancellable: queued.append((job_name, is_cancellable)))
    calls = []

    result = sync_module.sync_subtitles(
        video_path="/media/movie.mkv",
        srt_path="/media/movie.en.srt",
        srt_lang="en",
        forced=False,
        hi=False,
        percent_score=100,
        radarr_id=1,
        callback=lambda: calls.append(True),
    )

    assert result is False
    assert queued == [("Syncing /media/movie.en.srt", True)]
    assert FakeSubSyncer.calls == []
    assert calls == []


def test_sync_subtitles_runs_callback_when_sync_disabled(monkeypatch):
    _patch_common(monkeypatch)
    monkeypatch.setattr(sync_module.settings.subsync, "use_subsync", False)
    queued = []
    monkeypatch.setattr(sync_module.jobs_queue, "add_job_from_function", lambda **kwargs: queued.append(kwargs))
    calls = []

    result = sync_module.sync_subtitles(
        video_path="/media/movie.mkv",
        srt_path="/media/movie.en.srt",
        srt_lang="en",
        forced=False,
        hi=False,
        percent_score=100,
        radarr_id=1,
        callback=lambda: calls.append(True),
    )

    assert result is False
    assert queued == []
    assert calls == [True]


class CanceledSubSyncer:
    def sync(self, **kwargs):
        raise sync_module.JobCanceled


def test_sync_subtitles_propagates_cancel_and_runs_callback(monkeypatch):
    _patch_common(monkeypatch, subsyncer=CanceledSubSyncer)
    monkeypatch.setattr(sync_module.settings.subsync, "use_subsync_movie_threshold", False)
    calls = []

    with pytest.raises(sync_module.JobCanceled):
        _sync_with_callback(lambda: calls.append(True))
    # the downloaded subtitles are still there (unsynced), so post-processing and notifications still happen
    assert calls == [True]


def test_subsyncer_removes_partial_output_when_canceled(monkeypatch, tmp_path):
    srt = tmp_path / "episode.en.srt"
    srt.write_text("original")
    subsyncer, captured = _patch_subsyncer(monkeypatch, None)
    from subtitles.tools import subsyncer as subsyncer_module

    def canceled_run_in_subprocess(self, unparsed_args):
        (tmp_path / "episode.en.synced.srt").write_text("partial")
        raise subsyncer_module.JobCanceled

    monkeypatch.setattr(subsyncer_module.SubSyncer, "_run_in_subprocess", canceled_run_in_subprocess)

    with pytest.raises(subsyncer_module.JobCanceled):
        _sync(subsyncer, srt)

    assert srt.read_text() == "original"
    assert not (tmp_path / "episode.en.synced.srt").exists()
    assert "history" not in captured

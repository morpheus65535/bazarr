from subtitles import sync as sync_module


class FakeSubSyncer:
    calls = []

    def sync(self, **kwargs):
        self.calls.append(kwargs)


def test_sync_subtitles_reads_default_settings_at_runtime(monkeypatch):
    monkeypatch.setattr(sync_module, "SubSyncer", FakeSubSyncer)
    monkeypatch.setattr(sync_module.jobs_queue, "update_job_name", lambda **kwargs: None)
    monkeypatch.setattr(sync_module.gc, "collect", lambda: None)
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
    monkeypatch.setattr(sync_module, "SubSyncer", FakeSubSyncer)
    monkeypatch.setattr(sync_module.jobs_queue, "update_job_name", lambda **kwargs: None)
    monkeypatch.setattr(sync_module.gc, "collect", lambda: None)
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

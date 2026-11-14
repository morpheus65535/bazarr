from io import BytesIO
from types import SimpleNamespace

from subtitles import sync as sync_module


class FakeSubSyncer:
    calls = []

    def sync(self, **kwargs):
        self.calls.append(kwargs)


def _patch_sync(monkeypatch):
    monkeypatch.setattr(sync_module, "_create_subsyncer", FakeSubSyncer)
    monkeypatch.setattr(sync_module.jobs_queue, "update_job_name", lambda **kwargs: None)
    monkeypatch.setattr(sync_module.jobs_queue, "update_job_progress", lambda **kwargs: None)
    monkeypatch.setattr(sync_module.gc, "collect", lambda: None)
    monkeypatch.setattr(sync_module.settings.subsync, "use_subsync", True)
    monkeypatch.setattr(sync_module.settings.subsync, "use_subsync_threshold", True)
    monkeypatch.setattr(sync_module.settings.subsync, "subsync_threshold", 90)
    monkeypatch.setattr(sync_module.settings.subsync, "use_subsync_movie_threshold", True)
    monkeypatch.setattr(sync_module.settings.subsync, "subsync_movie_threshold", 50)
    FakeSubSyncer.calls = []


def _sync_sports(percent_score):
    return sync_module.sync_subtitles(
        video_path="/sports/league/event.mkv",
        srt_path="/sports/league/event.en.srt",
        srt_lang="en",
        forced=False,
        hi=False,
        percent_score=percent_score,
        sportarr_league_id=5,
        sports_event_id=11,
        job_id=3,
    )


def test_sports_sync_uses_the_series_threshold(monkeypatch):
    _patch_sync(monkeypatch)

    # The score is above the movie threshold and below the series threshold.
    assert _sync_sports(percent_score=80) is True
    assert FakeSubSyncer.calls[0]["sportarr_league_id"] == 5
    assert FakeSubSyncer.calls[0]["sports_event_id"] == 11
    assert FakeSubSyncer.calls[0]["radarr_id"] is None

    FakeSubSyncer.calls = []
    assert _sync_sports(percent_score=95) is False
    assert FakeSubSyncer.calls == []


def test_sports_subsyncer_logs_sports_history(monkeypatch, tmp_path):
    from subtitles.tools import subsyncer as subsyncer_module

    captured = {}

    def fake_run(args, progress_handler=None):
        with open(args.srtout, "w") as f:
            f.write("synced")
        return {"sync_was_successful": True, "offset_seconds": 1.0, "framerate_scale_factor": 1.0}

    monkeypatch.setattr(subsyncer_module, "get_binary", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(subsyncer_module, "run", fake_run)
    monkeypatch.setattr(subsyncer_module, "history_log", lambda **kwargs: captured.setdefault("series", kwargs))
    monkeypatch.setattr(subsyncer_module, "history_log_movie", lambda **kwargs: captured.setdefault("movie", kwargs))
    monkeypatch.setattr(subsyncer_module, "history_log_sports",
                        lambda **kwargs: captured.setdefault("sports", kwargs))
    monkeypatch.setattr(subsyncer_module.path_mappings, "path_replace_reverse_sports",
                        lambda path: f"sports:{path}")
    monkeypatch.setattr(subsyncer_module.path_mappings, "path_replace_reverse_movie",
                        lambda path: f"movie:{path}")
    monkeypatch.setattr(subsyncer_module.settings.subsync, "debug", False)
    monkeypatch.setattr(subsyncer_module.settings.subsync, "force_audio", False)
    monkeypatch.setattr(subsyncer_module.settings.subsync, "use_original_language", False)
    monkeypatch.setattr(subsyncer_module.settings.subsync, "auto_use_original_language", False)

    srt = tmp_path / "event.en.srt"
    srt.write_text("original")
    subsyncer_module.SubSyncer().sync(
        video_path="/sports/league/event.mkv", srt_path=str(srt), srt_lang="en", hi=False, forced=False,
        max_offset_seconds="60", no_fix_framerate=True, gss=False, sportarr_league_id=5, sports_event_id=11,
        quality_min_score=0.0, quality_max_offset_seconds=30, quality_max_framerate_deviation=0.1)

    assert srt.read_text() == "synced"
    assert "movie" not in captured
    assert "series" not in captured
    assert captured["sports"]["action"] == 5
    assert captured["sports"]["sportarr_league_id"] == 5
    assert captured["sports"]["sports_event_id"] == 11
    assert captured["sports"]["result"].path == "sports:/sports/league/event.mkv"
    assert captured["sports"]["result"].subs_path == f"sports:{srt}"


def test_sports_upload_syncs_with_the_event_ids(monkeypatch):
    import subtitles.upload as upload

    sync_calls = []
    metadata = SimpleNamespace(id=11, sportarrLeagueId=5, profileId=None)
    monkeypatch.setattr(upload.database, 'execute', lambda statement: SimpleNamespace(first=lambda: metadata))
    monkeypatch.setattr(upload, 'get_profiles_list', lambda profile_id: [])
    monkeypatch.setattr(upload, 'get_audio_profile_languages', lambda audio_language: [])
    monkeypatch.setattr(upload, 'get_target_folder', lambda path: '/subs')
    monkeypatch.setattr(upload, 'save_subtitles', lambda *args, **kwargs: [
        SimpleNamespace(storage_path='/subs/event.en.srt')])
    monkeypatch.setattr(upload, 'sync_subtitles', lambda **kwargs: sync_calls.append(kwargs))
    monkeypatch.setattr(upload, 'notify_sportarr', lambda *args, **kwargs: None)
    monkeypatch.setattr(upload, 'event_stream', lambda **kwargs: None)
    monkeypatch.setattr(upload, 'store_subtitles_sports', lambda *args, **kwargs: None)
    monkeypatch.setattr(upload, 'history_log_sports', lambda *args, **kwargs: None)
    monkeypatch.setattr(upload.path_mappings, 'path_replace_reverse_sports', lambda path: path)
    monkeypatch.setattr(upload.settings.general, 'single_language', False)
    monkeypatch.setattr(upload.settings.general, 'use_postprocessing', False)
    monkeypatch.setattr(upload.settings.general, 'chmod_enabled', False)
    monkeypatch.setattr(upload.settings.general, 'utf8_encode', False)
    monkeypatch.setattr(upload.settings.general, 'subzero_mods', [])

    upload.manual_upload_subtitle(
        path='/sports/event.mkv', language='en', forced=False, hi=False,
        media_type='sports', subtitle=BytesIO(b'1\n00:00:00,000 --> 00:00:01,000\nHi\n'),
        filename='event.en.srt', audio_language='[]', job_id='job',
        sportarrLeagueId=5, sportsEventId=11)

    assert sync_calls[0]['sportarr_league_id'] == 5
    assert sync_calls[0]['sports_event_id'] == 11
    assert sync_calls[0].get('radarr_id') is None

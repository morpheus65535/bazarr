from unittest import mock


def test_sports_delete_sends_delete_action_to_external_webhook(monkeypatch, tmp_path):
    from subtitles.tools import delete
    from utilities.autopulse_webhook import call_external_webhook

    subtitle = tmp_path / "UFC 318 Main Card.en.srt"
    subtitle.write_text("1\n00:00:01,000 --> 00:00:02,000\nHi\n", encoding="utf-8")
    webhook = mock.create_autospec(call_external_webhook)

    monkeypatch.setattr(delete.path_mappings, "path_replace_sports", lambda path: path)
    monkeypatch.setattr(delete.path_mappings, "path_replace_reverse_sports", lambda path: path)
    monkeypatch.setattr(delete, "store_subtitles_sports", lambda event_id: None)
    monkeypatch.setattr(delete, "history_log_sports", lambda *args, **kwargs: None)
    monkeypatch.setattr(delete, "notify_sportarr", lambda league_id: None)
    monkeypatch.setattr(delete, "event_stream", lambda **kwargs: None)
    monkeypatch.setattr(delete, "call_external_webhook", webhook)

    assert delete.delete_subtitles(media_type="sports", language="en", forced=False, hi=False,
                                   media_path=str(tmp_path / "UFC 318 Main Card.mkv"),
                                   subtitles_path=str(subtitle), sportarr_league_id=1, sports_event_id=2)

    assert not subtitle.exists()
    assert webhook.call_count == 1
    assert webhook.call_args.kwargs["action_type"] == "delete"

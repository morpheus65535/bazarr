from io import BytesIO
from types import SimpleNamespace

import pytest

from languages import get_languages
import subtitles.upload as upload


@pytest.fixture
def upload_module(bind_wanted_database, monkeypatch):
    module = upload
    bind_wanted_database(module, "movies")
    bind_wanted_database(module, "series")

    monkeypatch.setattr(
        get_languages,
        "languages_dict",
        [{"code2": "en", "code3": "eng", "code3b": None, "name": "English"}],
        raising=False,
    )
    monkeypatch.setattr(module, "set_chmod", lambda **kwargs: None)
    monkeypatch.setattr(module, "sync_subtitles", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "postprocessing", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "notify_sonarr", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "notify_radarr", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "history_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "history_log_movie", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "store_subtitles", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "store_subtitles_movie", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "event_stream", lambda **kwargs: None)
    monkeypatch.setattr(module, "send_notifications", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "send_notifications_movie", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        module,
        "save_subtitles",
        lambda *args, **kwargs: [SimpleNamespace(storage_path="/subs/sub.srt")],
    )
    monkeypatch.setattr(module.settings.general, "single_language", False)
    monkeypatch.setattr(module.settings.general, "use_postprocessing", False)
    monkeypatch.setattr(module.settings.general, "postprocessing_cmd", "")
    monkeypatch.setattr(module.settings.general, "chmod_enabled", False)
    monkeypatch.setattr(module.settings.general, "utf8_encode", False)
    monkeypatch.setattr(module.settings.general, "subzero_mods", [])
    monkeypatch.setattr(module.settings.general, "dont_notify_manual_actions", True)
    monkeypatch.setattr(module.settings.general, "use_plex", False)
    monkeypatch.setattr(module.settings.general, "use_jellyfin", False)
    return module


def _subtitle_file():
    return BytesIO(b"1\n00:00:00,000 --> 00:00:01,000\nHi\n")


def test_manual_upload_subtitle_series_handles_missing_profile_key_and_none_audio_language(
    upload_module, episode_row_factory, monkeypatch
):
    episode_row_factory(sonarrSeriesId=5, sonarrEpisodeId=11, profileId=44)

    monkeypatch.setattr(upload_module, "get_profiles_list", lambda profile_id: {})
    monkeypatch.setattr(upload_module, "get_audio_profile_languages", lambda audio_language: None)

    result = upload_module.manual_upload_subtitle(
        path="/series/episode.mkv",
        language="en",
        forced=False,
        hi=False,
        media_type="series",
        subtitle=_subtitle_file(),
        filename="subtitle.srt",
        audio_language="['eng']",
        job_id="job",
        sonarrSeriesId=5,
        sonarrEpisodeId=11,
    )

    assert result == ("", 204)


def test_manual_upload_subtitle_movie_handles_missing_profile_key_and_none_audio_language(
    upload_module, movie_row_factory, monkeypatch
):
    movie_row_factory(radarrId=7, profileId=44)

    monkeypatch.setattr(upload_module, "get_profiles_list", lambda profile_id: {})
    monkeypatch.setattr(upload_module, "get_audio_profile_languages", lambda audio_language: None)

    result = upload_module.manual_upload_subtitle(
        path="/movies/movie.mkv",
        language="en",
        forced=False,
        hi=False,
        media_type="movie",
        subtitle=_subtitle_file(),
        filename="subtitle.srt",
        audio_language="['eng']",
        job_id="job",
        radarrId=7,
    )

    assert result == ("", 204)


def test_manual_upload_subtitle_postprocessing_handles_partial_audio_language_dict(
    upload_module, movie_row_factory, monkeypatch
):
    movie_row_factory(radarrId=7, profileId=44)
    commands = []

    monkeypatch.setattr(upload_module.settings.general, "use_postprocessing", True)
    monkeypatch.setattr(upload_module, "get_profiles_list", lambda profile_id: {})
    monkeypatch.setattr(upload_module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(upload_module, "pp_replace", lambda *args, **kwargs: commands.append(args) or "cmd")

    result = upload_module.manual_upload_subtitle(
        path="/movies/movie.mkv",
        language="en",
        forced=False,
        hi=False,
        media_type="movie",
        subtitle=_subtitle_file(),
        filename="subtitle.srt",
        audio_language="['eng']",
        job_id="job",
        radarrId=7,
    )

    assert result == ("", 204)
    assert len(commands) == 1

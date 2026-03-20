import time

import pytest

from bazarr.subtitles.tools.translate.services import gemini_translator


def _build_service():
    return gemini_translator.GeminiTranslatorService(
        source_srt_file="input.srt",
        dest_srt_file="output.srt",
        to_lang="eng",
        media_type="series",
        sonarr_series_id=1,
        sonarr_episode_id=1,
        radarr_id=1,
        forced=False,
        hi=False,
        video_path="/tmp/video.mkv",
        from_lang="en",
        orig_to_lang="eng",
    )


def test_get_batch_size_uses_configured_value(mocker):
    service = _build_service()
    mocker.patch.object(
        gemini_translator.settings.translator,
        "gemini_batch_size",
        450,
        create=True,
    )
    assert service._get_batch_size() == 450


def test_get_batch_size_falls_back_to_default_for_invalid_value(mocker):
    service = _build_service()
    mocker.patch.object(
        gemini_translator.settings.translator,
        "gemini_batch_size",
        "invalid",
        create=True,
    )
    assert service._get_batch_size() == gemini_translator.DEFAULT_GEMINI_BATCH_SIZE


def test_get_batch_size_is_clamped_to_minimum_of_one(mocker):
    service = _build_service()
    mocker.patch.object(
        gemini_translator.settings.translator,
        "gemini_batch_size",
        0,
        create=True,
    )
    assert service._get_batch_size() == 1


@pytest.fixture(autouse=True)
def _clear_gemini_key_cooldowns():
    cooldowns = getattr(gemini_translator, "_GEMINI_KEY_COOLDOWNS", None)
    if cooldowns is not None:
        cooldowns.clear()
    yield
    cooldowns = getattr(gemini_translator, "_GEMINI_KEY_COOLDOWNS", None)
    if cooldowns is not None:
        cooldowns.clear()


def test_get_configured_api_keys_trims_and_deduplicates(mocker):
    service = _build_service()
    mocker.patch.object(
        gemini_translator.settings.translator,
        "gemini_keys",
        [" key-1 ", "", "key-2", "key-1"],
        create=True,
    )

    assert service._get_configured_api_keys() == ["key-1", "key-2"]


def test_get_configured_api_keys_returns_empty_when_no_keys(mocker):
    service = _build_service()
    mocker.patch.object(
        gemini_translator.settings.translator,
        "gemini_keys",
        [],
        create=True,
    )

    assert service._get_configured_api_keys() == []


def test_select_next_api_key_skips_keys_on_cooldown():
    service = _build_service()
    service.api_keys = ["key-1", "key-2"]
    service.current_api_index = -1
    gemini_translator._GEMINI_KEY_COOLDOWNS["key-1"] = time.time() + 60

    selected_key = service._select_next_api_key()

    assert selected_key == "key-2"


def test_handle_rate_limited_key_applies_cooldown_and_rotates_key():
    class _RateLimitedResponse:
        status_code = 429
        headers = {"Retry-After": "7"}

    service = _build_service()
    service.api_keys = ["key-1", "key-2"]
    service.current_api_index = 0
    service.current_api_key = "key-1"

    service._handle_rate_limited_key(_RateLimitedResponse())

    assert gemini_translator._GEMINI_KEY_COOLDOWNS["key-1"] > time.time() + 6
    assert service.current_api_key == "key-2"


def test_handle_rate_limited_key_raises_when_all_keys_unavailable():
    class _RateLimitedResponse:
        status_code = 429
        headers = {"Retry-After": "3"}

    service = _build_service()
    service.api_keys = ["key-1"]
    service.current_api_index = 0
    service.current_api_key = "key-1"

    with pytest.raises(RuntimeError, match="All Gemini API keys are currently rate limited"):
        service._handle_rate_limited_key(_RateLimitedResponse())

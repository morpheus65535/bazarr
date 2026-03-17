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

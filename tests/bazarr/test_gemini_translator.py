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


def test_translate_with_gemini_does_not_leave_output_file_on_failure(tmp_path, mocker):
    input_file = tmp_path / "input.srt"
    output_file = tmp_path / "output.srt"
    input_file.write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nHello world\n\n",
        encoding="utf-8",
    )

    service = _build_service()
    service.input_file = str(input_file)
    service.output_file = str(output_file)
    service.api_keys = ["key-1"]
    service.current_api_key = "key-1"
    service.target_language = "English"
    service.batch_size = 1
    service.job_id = "job-1"

    def _fail_after_output_file_created(*args, **kwargs):
        # Translation output file should be opened before batch processing starts.
        assert output_file.exists()
        raise RuntimeError("boom")

    mocker.patch.object(service, "_process_batch", side_effect=_fail_after_output_file_created)
    mocker.patch.object(gemini_translator.jobs_queue, "update_job_progress")

    with pytest.raises(RuntimeError, match="boom"):
        service._translate_with_gemini()

    assert not output_file.exists()


def _write_ass_file(path):
    import pysubs2

    subs = pysubs2.SSAFile()
    subs.events.append(pysubs2.SSAEvent(start=0, end=2000, text="Hello {\\i1}there{\\i0}"))
    subs.events.append(pysubs2.SSAEvent(start=3000, end=5000, text="Second\\Nline"))
    subs.save(str(path), encoding="utf-8")


def test_prepare_input_srt_converts_ass_source_to_parseable_srt(tmp_path, mocker):
    import pysubs2
    import srt

    ass_file = tmp_path / "episode.ass"
    _write_ass_file(ass_file)

    service = _build_service()
    service.source_srt_file = str(ass_file)
    subs = pysubs2.load(str(ass_file), encoding="utf-8")
    subs.remove_miscellaneous_events()

    converted = service._prepare_input_srt(subs)

    assert converted == str(tmp_path / "episode.gemini-source.srt")
    parsed = list(srt.parse(open(converted, encoding="utf-8").read()))
    assert [sub.index for sub in parsed] == [1, 2]
    assert "Hello" in parsed[0].content
    assert "Second" in parsed[1].content

    service._remove_converted_input()
    assert not (tmp_path / "episode.gemini-source.srt").exists()


def test_prepare_input_srt_returns_srt_source_unchanged(tmp_path):
    import pysubs2

    srt_file = tmp_path / "episode.srt"
    srt_file.write_text("1\n00:00:00,000 --> 00:00:02,000\nHello\n\n", encoding="utf-8")

    service = _build_service()
    service.source_srt_file = str(srt_file)
    subs = pysubs2.load(str(srt_file), encoding="utf-8")

    assert service._prepare_input_srt(subs) == str(srt_file)
    assert service._converted_input_file is None
    assert not (tmp_path / "episode.gemini-source.srt").exists()


def test_translate_with_gemini_raises_parse_error_not_unbound_local(tmp_path, mocker):
    import srt

    input_file = tmp_path / "input.srt"
    output_file = tmp_path / "output.srt"
    input_file.write_text("[Script Info]\nTitle: not srt\n\nDialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,Hi\n",
                          encoding="utf-8")

    service = _build_service()
    service.input_file = str(input_file)
    service.output_file = str(output_file)
    service.api_keys = ["key-1"]
    service.current_api_key = "key-1"
    service.target_language = "English"
    service.job_id = "job-1"

    progress_mock = mocker.patch.object(gemini_translator.jobs_queue, "update_job_progress")

    with pytest.raises(srt.SRTParseError):
        service._translate_with_gemini()

    progress_values = [call.kwargs.get("progress_value") for call in progress_mock.call_args_list]
    assert 0 in progress_values
    assert not output_file.exists()


def test_remove_converted_input_ignores_missing_file(tmp_path):
    service = _build_service()
    service._converted_input_file = str(tmp_path / "missing.gemini-source.srt")

    service._remove_converted_input()

    assert service._converted_input_file is None

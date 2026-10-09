import pytest

from bazarr.subtitles.tools.translate.services import google_translator
from deep_translator.exceptions import RequestError


def _build_service(tmp_path):
    return google_translator.GoogleTranslatorService(
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


def test_looks_like_error_response_detects_html_and_error_text():
    assert google_translator.GoogleTranslatorService._looks_like_error_response(
        "<html><body>Error 500</body></html>")
    assert google_translator.GoogleTranslatorService._looks_like_error_response(
        "Too Many Requests")
    assert google_translator.GoogleTranslatorService._looks_like_error_response(
        "Error 500: Internal Server Error")
    assert google_translator.GoogleTranslatorService._looks_like_error_response(
        "<div class='captcha'>unusual traffic</div>")


def test_looks_like_error_response_leaves_real_translations_alone():
    assert not google_translator.GoogleTranslatorService._looks_like_error_response("Bonjour le monde")
    assert not google_translator.GoogleTranslatorService._looks_like_error_response("¿Qué hora es?")
    # An unrelated "500" inside normal text must not be flagged as an error.
    assert not google_translator.GoogleTranslatorService._looks_like_error_response(
        "The reward is 500 dollars.")


def test_translate_text_raises_on_error_response_baked_into_result(mocker, tmp_path):
    """
    Regression: the free Google endpoint can answer 200 OK with an error/captcha page, and
    deep_translator returns that error text as the translation. The translator must reject it
    (raising RequestError so @retry can retry) instead of baking "Error 500" into the subtitle.
    """
    service = _build_service(tmp_path)
    mocker.patch.object(google_translator, "GoogleTranslator")

    # Force the inner retry to give up quickly so the test stays fast.
    mocker.patch.object(
        google_translator,
        "retry",
        lambda *a, **kw: (lambda f: f),
    )

    google_translator.GoogleTranslator.return_value.translate.return_value = "Error 500: Server Error"
    mocker.patch.object(google_translator.jobs_queue, "update_job_progress")

    with pytest.raises(RequestError):
        service._translate_text("Hello world", job_id="job-1")


def test_translate_aborts_when_lines_fail_instead_of_writing_partial_file(mocker, tmp_path):
    """
    Regression: per-line failures used to be swallowed by the futures loop, the subtitle was
    saved with untranslated lines, and the job reported success. We now collect failures and
    raise so no partially-translated subtitle is written.
    """
    input_file = tmp_path / "input.srt"
    output_file = tmp_path / "output.srt"
    input_file.write_text("1\n00:00:00,000 --> 00:00:02,000\nHello world\n\n", encoding="utf-8")

    service = _build_service(tmp_path)

    # Make every line fail to translate.
    mocker.patch.object(service, "_translate_text", side_effect=RequestError("boom"))
    mocker.patch.object(google_translator.jobs_queue, "update_job_progress")
    # Guard: saving must never happen when translation failed.
    save_mock = mocker.patch("pysubs2.SSAFile.save", autospec=True)

    with pytest.raises(RequestError, match="1/1 line"):
        service.translate(job_id="job-1")

    save_mock.assert_not_called()


def test_translate_succeeds_when_all_lines_translate(mocker, tmp_path):
    """Happy path: when translation succeeds the output file is written and the path returned."""
    input_file = tmp_path / "input.srt"
    output_file = tmp_path / "output.srt"
    input_file.write_text("1\n00:00:00,000 --> 00:00:02,000\nHello world\n\n", encoding="utf-8")

    service = _build_service(tmp_path)
    mocker.patch.object(service, "_translate_text", return_value="Bonjour le monde")
    mocker.patch.object(google_translator.jobs_queue, "update_job_progress")
    mocker.patch.object(google_translator, "history_log")
    mocker.patch.object(google_translator, "history_log_movie")

    result = service.translate(job_id="job-1")

    assert result == str(output_file)
    assert output_file.exists()

import pytest

from bazarr.subtitles.tools.translate.services import lingarr_translator


def _build_service(tmp_path, media_type="movie", sonarr_series_id=1, sonarr_episode_id=1):
    return lingarr_translator.LingarrTranslatorService(
        source_srt_file=str(tmp_path / "input.srt"),
        dest_srt_file=str(tmp_path / "output.srt"),
        lang_obj=type("L", (), {"alpha2": "fr"})(),
        to_lang="fra",
        from_lang="en",
        media_type=media_type,
        video_path="/tmp/video.mkv",
        orig_to_lang="fr",
        forced=False,
        hi=False,
        sonarr_series_id=sonarr_series_id,
        sonarr_episode_id=sonarr_episode_id,
        radarr_id=1,
    )


def _patch_lingarr(mocker, response_json):
    mocker.patch.object(lingarr_translator, "get_title", return_value="Synthetic title")
    mocker.patch.object(
        lingarr_translator.settings.translator,
        "lingarr_url",
        "http://lingarr:9876",
        create=True,
    )
    mocker.patch.object(
        lingarr_translator.settings.translator,
        "lingarr_token",
        "",
        create=True,
    )

    response = mocker.Mock()
    response.status_code = 200
    response.json.return_value = response_json

    return mocker.patch.object(
        lingarr_translator.requests,
        "post",
        return_value=response,
    )


def test_lingarr_request_skips_blank_lines_and_preserves_positions(mocker, tmp_path):
    """Blank lines are skipped while original positions are preserved."""
    service = _build_service(tmp_path)
    translated = [
        {"position": 0, "line": "Bonjour"},
        {"position": 3, "line": "Au revoir"},
    ]
    post = _patch_lingarr(mocker, translated)

    result = service._translate_content(
        ["Hello", "", "   ", "Goodbye"],
        job_id="job-1",
    )

    assert result == translated
    assert post.call_args.kwargs["json"]["lines"] == [
        {"position": 0, "line": "Hello"},
        {"position": 3, "line": "Goodbye"},
    ]


def test_lingarr_request_sends_sonarr_episode_id_for_episodes(mocker, tmp_path):
    """Lingarr resolves arrMediaId as a Sonarr episode id, so episodes must send the episode id."""
    service = _build_service(tmp_path, media_type="episode", sonarr_series_id=7, sonarr_episode_id=42)
    post = _patch_lingarr(mocker, [{"position": 0, "line": "Bonjour"}])

    service._translate_content(["Hello"], job_id="job-1")

    payload = post.call_args.kwargs["json"]
    assert payload["mediaType"] == "Episode"
    assert payload["arrMediaId"] == 42


def _patch_lingarr_responses(mocker, responses):
    """Patch the Lingarr POST to return or raise each item in order and disable retry sleeps."""
    mocker.patch.object(lingarr_translator, "get_title", return_value="Synthetic title")
    mocker.patch.object(lingarr_translator.settings.translator, "lingarr_url", "http://lingarr:9876", create=True)
    mocker.patch.object(lingarr_translator.settings.translator, "lingarr_token", "", create=True)
    mocker.patch("time.sleep")
    return mocker.patch.object(lingarr_translator.requests, "post", side_effect=responses)


def _response(status_code, json_body=None):
    response = type("R", (), {})()
    response.status_code = status_code
    response.text = ""
    response.json = lambda: json_body
    return response


def test_lingarr_server_error_is_not_resubmitted(mocker, tmp_path):
    """A 5xx after a long run must fail once instead of re-sending the whole file."""
    from deep_translator.exceptions import RequestError

    service = _build_service(tmp_path)
    post = _patch_lingarr_responses(mocker, [_response(500)] * 3)

    with pytest.raises(RequestError):
        service._translate_content(["Hello", "Goodbye"], job_id="job-1")

    assert post.call_count == 1


def test_lingarr_timeout_is_not_resubmitted(mocker, tmp_path):
    """A read timeout must fail once instead of re-sending the whole file."""
    from deep_translator.exceptions import RequestError

    service = _build_service(tmp_path)
    post = _patch_lingarr_responses(mocker, [lingarr_translator.requests.exceptions.ReadTimeout()] * 3)

    with pytest.raises(RequestError):
        service._translate_content(["Hello"], job_id="job-1")

    assert post.call_count == 1


def test_lingarr_connection_error_is_retried(mocker, tmp_path):
    """A connection error means the request never reached Lingarr, so it is retried."""
    service = _build_service(tmp_path)
    translated = [{"position": 0, "line": "Bonjour"}]
    post = _patch_lingarr_responses(
        mocker,
        [lingarr_translator.requests.exceptions.ConnectionError(), _response(200, translated)],
    )

    assert service._translate_content(["Hello"], job_id="job-1") == translated
    assert post.call_count == 2


def test_lingarr_rate_limit_is_retried(mocker, tmp_path):
    """A 429 means Lingarr rejected the request without processing it, so it is retried."""
    service = _build_service(tmp_path)
    translated = [{"position": 0, "line": "Bonjour"}]
    post = _patch_lingarr_responses(mocker, [_response(429), _response(200, translated)])

    assert service._translate_content(["Hello"], job_id="job-1") == translated
    assert post.call_count == 2


def test_lingarr_request_uses_configured_timeout(mocker, tmp_path):
    """The content POST must use the timeout from settings instead of a hard-coded value."""
    service = _build_service(tmp_path)
    post = _patch_lingarr_responses(mocker, [_response(200, [{"position": 0, "line": "Bonjour"}])])
    mocker.patch.object(lingarr_translator.settings.translator, "lingarr_timeout", 600, create=True)

    service._translate_content(["Hello"], job_id="job-1")

    assert post.call_args.kwargs["timeout"] == 600

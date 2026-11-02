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

from bazarr.subtitles.tools.translate.services import lingarr_translator


def _build_service(tmp_path):
    return lingarr_translator.LingarrTranslatorService(
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


def test_lingarr_request_skips_blank_lines_and_preserves_positions(mocker, tmp_path):
    """Blank lines are skipped while original positions are preserved."""
    service = _build_service(tmp_path)

    mocker.patch.object(lingarr_translator, "get_title", return_value="Synthetic movie")
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
    response.json.return_value = [
        {"position": 0, "line": "Bonjour"},
        {"position": 3, "line": "Au revoir"},
    ]

    post = mocker.patch.object(
        lingarr_translator.requests,
        "post",
        return_value=response,
    )

    result = service._translate_content(
        ["Hello", "", "   ", "Goodbye"],
        job_id="job-1",
    )

    assert result == response.json.return_value
    assert post.call_args.kwargs["json"]["lines"] == [
        {"position": 0, "line": "Hello"},
        {"position": 3, "line": "Goodbye"},
    ]

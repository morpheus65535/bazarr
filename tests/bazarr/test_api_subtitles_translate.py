import pytest


def _resolve(subtitles, subtitles_path, subtitles_id, validator=None):
    # The language validator is injected to keep these tests off the database.
    from bazarr.subtitles.tools.translate.core.translator_utils import resolve_translation_source

    if validator is None:
        # Treat any non-empty code as valid, except the explicit invalid sentinel "zzz".
        validator = lambda code: None if code == "zzz" else (code or None)

    return resolve_translation_source(
        subtitles, subtitles_path, subtitles_id, language_validator=validator
    )


def _external(path="/movies/Foo (2020)/Foo.en.srt", code2="eng", sub_id=1):
    return {"path": path, "code2": code2, "id": sub_id, "embedded_track_id": None}


def _embedded(code2="eng", sub_id=2, track_id=4):
    return {"path": None, "code2": code2, "id": sub_id, "embedded_track_id": track_id}


def test_resolve_external_by_path():
    subs = [_external(), _embedded()]
    from_language, embedded_id = _resolve(subs, "/movies/Foo (2020)/Foo.en.srt", None)
    assert from_language == "eng"
    assert embedded_id is None


def test_resolve_embedded_by_id_returns_track_id_for_extraction():
    subs = [_external(), _embedded(code2="eng", sub_id=2, track_id=4)]
    from_language, embedded_id = _resolve(subs, None, 2)
    assert from_language == "eng"
    # The embedded track id is returned so the caller can extract it before translating.
    assert embedded_id == 2


def test_resolve_rejects_external_id_passed_as_embedded():
    # id 1 points to an external file (no embedded_track_id), not an embedded track.
    subs = [_external(sub_id=1), _embedded(sub_id=2)]
    with pytest.raises(ValueError, match="not an embedded track"):
        _resolve(subs, None, 1)


def test_resolve_unknown_path_raises():
    subs = [_external()]
    with pytest.raises(ValueError, match="Invalid source language code"):
        _resolve(subs, "/nope.srt", None)


def test_resolve_unknown_id_raises():
    subs = [_embedded(sub_id=2)]
    with pytest.raises(ValueError, match="Invalid source language code"):
        _resolve(subs, None, 999)


def test_resolve_invalid_language_raises():
    subs = [{"path": "/x.srt", "code2": "zzz", "id": 1, "embedded_track_id": None}]
    with pytest.raises(ValueError, match="Invalid source language code"):
        _resolve(subs, "/x.srt", None)


def test_resolve_neither_path_nor_id_raises():
    with pytest.raises(ValueError, match="Invalid source language code"):
        _resolve([_external()], None, None)


def _run_combined(mocker, job_id=None, extracted_path="/tmp/extracted.en.srt"):
    from bazarr.subtitles.tools.translate.main import extract_and_translate_embedded

    # extract_embedded_subtitle is imported inside the job body from its top-level module path,
    # so patch it there rather than under the bazarr.* package path used by these tests.
    extract = mocker.patch("subtitles.embedded.extract_embedded_subtitle",
                           return_value=extracted_path)
    translate = mocker.patch("bazarr.subtitles.tools.translate.main.translate_subtitles_file")

    extract_and_translate_embedded(
        subtitles_id=4, media_type="movie", video_path="/movies/Foo (2020)/Foo.mkv",
        from_lang="eng", to_lang="fra", forced=False, hi=True,
        sonarr_series_id=None, sonarr_episode_id=None, radarr_id=12,
        metadata={"imdbId": "tt0000001"}, original_format=True, job_id=job_id)

    return extract, translate


def test_combined_job_self_enqueues_without_job_id(mocker):
    enqueue = mocker.patch("bazarr.subtitles.tools.translate.main.jobs_queue.add_job_from_function",
                           return_value=1)

    extract, translate = _run_combined(mocker, job_id=None)

    # A single job is enqueued and neither step runs synchronously.
    enqueue.assert_called_once()
    assert "ENG" in enqueue.call_args[0][0] and "FRA" in enqueue.call_args[0][0]
    extract.assert_not_called()
    translate.assert_not_called()


def test_combined_job_extracts_then_translates_with_same_job_id(mocker):
    extract, translate = _run_combined(mocker, job_id=99)

    extract.assert_called_once_with(subtitles_id=4, media_type="movie", job_id=99)
    translate.assert_called_once_with(
        video_path="/movies/Foo (2020)/Foo.mkv", source_srt_file="/tmp/extracted.en.srt",
        from_lang="eng", to_lang="fra", forced=False, hi=True, media_type="movie",
        sonarr_series_id=None, sonarr_episode_id=None, radarr_id=12,
        metadata={"imdbId": "tt0000001"}, original_format=True, job_id=99)


def test_combined_job_skips_translation_when_extraction_fails(mocker):
    extract, translate = _run_combined(mocker, job_id=99, extracted_path=None)

    extract.assert_called_once()
    translate.assert_not_called()

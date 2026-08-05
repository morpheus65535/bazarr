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

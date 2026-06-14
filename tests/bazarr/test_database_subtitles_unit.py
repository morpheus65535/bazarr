from types import SimpleNamespace

from app import database
from languages import get_languages


def test_subtitle_payload_maps_language_and_path():
    original_languages = getattr(get_languages, "languages_dict", None)
    get_languages.languages_dict = [{"code2": "en", "code3": "eng", "code3b": None, "name": "English"}]
    subtitle = SimpleNamespace(
        path="/media/movie.en.srt",
        language="en",
        forced=False,
        hi=True,
        size=123,
        embedded_track_id=None,
    )

    try:
        result = database._subtitle_payload(subtitle, lambda path: path.replace("/media", "/mapped"))
    finally:
        if original_languages is None:
            del get_languages.languages_dict
        else:
            get_languages.languages_dict = original_languages

    assert result == {
        "path": "/mapped/movie.en.srt",
        "name": "English",
        "code2": "en",
        "code3": "eng",
        "forced": False,
        "hi": True,
        "file_size": 123,
        "embedded_track_id": None,
    }


def test_sort_subtitles_matches_legacy_get_subtitles_order():
    subtitles = [
        {"name": "French", "forced": True},
        {"name": "English", "forced": True},
        {"name": "English", "forced": False},
    ]

    assert database._sort_subtitles(subtitles) == [
        {"name": "English", "forced": False},
        {"name": "English", "forced": True},
        {"name": "French", "forced": True},
    ]

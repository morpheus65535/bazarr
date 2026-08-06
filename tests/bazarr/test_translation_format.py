from bazarr.subtitles.tools.translate.core.translator_utils import get_translation_extension


def test_defaults_to_srt_when_not_preserving():
    assert get_translation_extension("/m/Foo.en.ass", False, "google_translate") == ".srt"


def test_preserves_supported_source_format_for_pysubs2_translators():
    assert get_translation_extension("/m/Foo.en.ass", True, "google_translate") == ".ass"
    assert get_translation_extension("/m/Foo.en.vtt", True, "lingarr") == ".vtt"
    assert get_translation_extension("/m/Foo.en.ssa", True, "google_translate") == ".ssa"


def test_srt_source_stays_srt():
    assert get_translation_extension("/m/Foo.en.srt", True, "google_translate") == ".srt"


def test_gemini_cannot_preserve_non_srt():
    # Gemini only reads/writes SRT, so a .ass source falls back to .srt even when preserving.
    assert get_translation_extension("/m/Foo.en.ass", True, "gemini") == ".srt"
    assert get_translation_extension("/m/Foo.en.vtt", True, "gemini") == ".srt"


def test_gemini_srt_is_preserved():
    assert get_translation_extension("/m/Foo.en.srt", True, "gemini") == ".srt"


def test_unsupported_extension_falls_back_to_srt():
    assert get_translation_extension("/m/Foo.en.sub", True, "google_translate") == ".srt"
    assert get_translation_extension("/m/Foo.en", True, "google_translate") == ".srt"


def test_extension_lookup_is_case_insensitive():
    assert get_translation_extension("/m/Foo.EN.ASS", True, "google_translate") == ".ass"

import pytest

from subtitles.tools.translate.core.translator_utils import validate_translation_params


def test_validate_translation_params_accepts_distinct_languages(tmp_path):
    source = tmp_path / "Movie.en.srt"
    source.write_text("1\n", encoding="utf-8")

    assert validate_translation_params("/media/Movie.mkv", str(source), "en", "fr") is True


@pytest.mark.parametrize("from_lang,to_lang", [("en", "en"), ("EN", "en"), (" en ", "en")])
def test_validate_translation_params_rejects_same_language(tmp_path, from_lang, to_lang):
    source = tmp_path / "Movie.en.srt"
    source.write_text("1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must differ"):
        validate_translation_params("/media/Movie.mkv", str(source), from_lang, to_lang)

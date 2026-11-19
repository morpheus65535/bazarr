# -*- coding: utf-8 -*-
import pytest

from subliminal_patch import core
from subzero.language import Language


def _touch(directory, name: str) -> None:
    (directory / name).write_text("1\n00:00:01,000 --> 00:00:02,000\nhi\n", encoding="utf-8")


@pytest.mark.parametrize("ietf, alpha3, country", [
    ("es-419", "spa", "MX"),
    ("ES-419", "spa", "MX"),
    ("en-001", "eng", None),
    ("es-150", "spa", None),
    ("es-MX", "spa", "MX"),
    ("pt-BR", "por", "BR"),
])
def test_fromietf_handles_m49_numeric_regions(ietf: str, alpha3: str, country: str | None) -> None:
    language = Language.fromietf(ietf)

    assert language.alpha3 == alpha3
    assert (str(language.country) if language.country else None) == country


def test_scanner_parses_m49_external_subtitles(tmp_path) -> None:
    video = tmp_path / "movie.mkv"
    video.write_text("", encoding="utf-8")
    names = ("movie.es-419.srt", "movie.es-419.forced.srt", "movie.es-419.hi.srt", "movie.en-001.srt")
    for name in names:
        _touch(tmp_path, name)

    found = core._search_external_subtitles(str(video))

    assert set(found) == set(names)
    for name in names[:3]:
        assert found[name] is not None
        assert found[name].alpha3 == "spa"
        assert str(found[name].country) == "MX"
    assert found["movie.es-419.forced.srt"].forced is True
    assert found["movie.es-419.hi.srt"].hi is True
    assert found["movie.en-001.srt"] is not None
    assert found["movie.en-001.srt"].alpha3 == "eng"
    assert found["movie.en-001.srt"].country is None


def test_scanner_still_parses_plain_codes(tmp_path) -> None:
    video = tmp_path / "movie.mkv"
    video.write_text("", encoding="utf-8")
    _touch(tmp_path, "movie.es.srt")

    found = core._search_external_subtitles(str(video))

    assert found["movie.es.srt"] is not None
    assert found["movie.es.srt"].alpha3 == "spa"
    assert found["movie.es.srt"].country is None

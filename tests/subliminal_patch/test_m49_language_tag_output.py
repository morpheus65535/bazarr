# -*- coding: utf-8 -*-
import os

import pytest

from subliminal_patch.core import get_subtitle_path
from subliminal_patch.core import save_subtitles
from subzero.language import Language
from subzero.language import m49_basename


@pytest.mark.parametrize("ietf, expected", [
    ("es-MX", "es-419"),
    ("es-419", "es-419"),
    ("en", "en"),
    ("pt-BR", "pt-BR"),
])
def test_m49_basename_uses_mapped_region_only(ietf: str, expected: str) -> None:
    assert m49_basename(Language.fromietf(ietf)) == expected


def test_m49_basename_keeps_forced_out_of_tag() -> None:
    language = Language.rebuild(Language.fromietf("es-419"), forced=True)

    assert m49_basename(language) == "es-419"


def test_get_subtitle_path_default_keeps_country_tag() -> None:
    path = get_subtitle_path("/media/movie.mkv", Language.fromietf("es-419"), extension=".srt")

    assert path == "/media/movie.es-MX.srt"


def test_get_subtitle_path_m49_flag_writes_region_tag() -> None:
    path = get_subtitle_path("/media/movie.mkv", Language.fromietf("es-419"), extension=".srt",
                             m49_language_tag=True)

    assert path == "/media/movie.es-419.srt"


def test_get_subtitle_path_m49_flag_keeps_forced_and_hi_tags() -> None:
    path = get_subtitle_path("/media/movie.mkv", Language.fromietf("es-419"), extension=".srt",
                             forced_tag=True, m49_language_tag=True)

    assert path == "/media/movie.es-419.forced.srt"


class _Savable:
    def __init__(self, language: Language) -> None:
        self.id = "sub"
        self.provider_name = "test"
        self.content = b"1\n00:00:01,000 --> 00:00:02,000\nhi\n\n"
        self.text = "1\n00:00:01,000 --> 00:00:02,000\nhi\n\n"
        self.language = language
        self.format = "srt"
        self.mods = None
        self.storage_path = None

    def get_modified_content(self, format: str = "srt", debug: bool = False) -> bytes:
        return self.content


@pytest.mark.parametrize("flag, expected_name", [
    (False, "video.es-MX.srt"),
    (True, "video.es-419.srt"),
])
def test_save_subtitles_respects_m49_flag(tmp_path, flag: bool, expected_name: str) -> None:
    video = str(tmp_path / "video.mkv")

    saved = save_subtitles(video, [_Savable(Language.fromietf("es-419"))], directory=str(tmp_path),
                           m49_language_tag=flag)

    assert len(saved) == 1
    assert os.path.basename(saved[0].storage_path) == expected_name
    assert os.path.exists(tmp_path / expected_name)

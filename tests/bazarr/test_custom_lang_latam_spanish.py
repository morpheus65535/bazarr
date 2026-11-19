# -*- coding: utf-8 -*-
import pytest

from languages.custom_lang import CustomLanguage


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("movie.es-419.srt", "ea"),
        ("movie.es-419.forced.srt", "ea:forced"),
        ("movie.es-419.hi.srt", "ea:HI"),
        ("movie.es-MX.srt", "ea"),
    ],
)
def test_found_external_labels_es_419_as_latino(filename: str, expected: str) -> None:
    assert CustomLanguage.found_external(filename, filename) == expected

import pytest
import os

from subliminal_patch.providers import utils
from zipfile import ZipFile
from rarfile import RarFile


@pytest.mark.parametrize(
    "sub_names,forced,episode,expected",
    [
        (("breaking bad s01e01.srt",), False, 1, "breaking bad s01e01.srt"),
        (("taxi.driver.1976.srt",), False, None, "taxi.driver.1976.srt"),
        (("taxi.driver.1976.s01e01.srt",), False, None, "taxi.driver.1976.s01e01.srt"),
        (("breaking.bad.s01e02.srt", "breaking.bad.s01e03.srt"), False, 1, None),
        (
            ("breaking.bad.s01e02.srt", "breaking.bad.s01e01.srt"),
            False,
            1,
            "breaking.bad.s01e01.srt",
        ),
        (("dummy.forced.srt",), True, 1, "dummy.forced.srt"),
        (("dummy.forced.srt",), False, 1, None),
    ],
)
def test_get_matching_sub(sub_names, episode, forced, expected):
    assert utils._get_matching_sub(sub_names, forced, episode) == expected


def test_get_subtitle_from_archive_movie(data):
    with ZipFile(os.path.join(data, "archive_1.zip")) as zf:
        assert utils.get_subtitle_from_archive(zf) is not None


def test_get_subtitle_from_archive_season_pack(data):
    with RarFile(os.path.join(data, "archive_2.rar")) as zf:
        assert utils.get_subtitle_from_archive(zf, episode=4) is not None


@pytest.mark.parametrize("filename", ["archive_1.zip", "archive_2.rar"])
def test_get_archive_from_bytes_zip(data, filename):
    with open(os.path.join(data, filename), "rb") as zf:
        assert utils.get_archive_from_bytes(zf.read()) is not None


def test_get_archive_from_bytes_none():
    assert utils.get_archive_from_bytes(bytes()) is None

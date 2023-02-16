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
        (("dummy.forced.srt",), True, None, "dummy.forced.srt"),
        (("dummy.forced.srt",), False, 1, None),
    ],
)
def test_get_matching_sub(sub_names, episode, forced, expected):
    assert utils._get_matching_sub(sub_names, forced, episode) == expected


def test_get_matching_sub_complex_season_pack():
    files = [
        "30. Hard Drive Courage. The Ride Of The Valkyries.srt",
        "S03E15.srt",
        "S03E16.srt",
        "S03E17.srt",
        "28. Campsite Of Terror. The Record Deal.srt",
        "33. Feast Of The Bullfrogs. Tulip's Worm.srt",
        "37. Dome Of Doom. Snowman's Revenge.srt",
        "35. Mondo Magic. Watch The Birdies.srt",
        "29. Stormy Weather. The Sandman Sleeps.srt",
        "38. The Quilt Club. Swindlin' Wind.srt",
    ]
    # Courage the Cowardly Dog S03E17 "Mondo Magic"
    matched = utils._get_matching_sub(files, False, 17, episode_title="Mondo Magic")
    assert matched == "35. Mondo Magic. Watch The Birdies.srt"


def _gen_subs():
    files = {
        15: "11b - Little Bigfoot.srt",
        14: "11a - Kiss Kiss, Bang Bang.srt",
        17: "10b - The Invaders.srt",
        18: "09a - The Tell Tale Tail.srt",
        1: "01 - The Thing That Wouldn't Stop It.srt",
        5: "03b - They Came from Down There.srt",
        4: "03a - Bad Day on the Moon.srt",
        8: "04a - The Friend for Life.srt",
        21: "08b - The Glazed McGuffin Affair.srt",
        13: "07b - It's Dangly Deever Time.srt",
        9: "04b - Dysfunction of the Gods.srt",
    }
    for episode, title in files.items():
        yield episode, title.split("-")[1].strip().rstrip(".srt"), title


@pytest.mark.parametrize("episode,title,file", _gen_subs())
def test_get_matching_sub_complete_series_pack_mixed(episode, title, file):
    files = [
        "11b - Little Bigfoot.srt",
        "11a - Kiss Kiss, Bang Bang.srt",
        "10b - The Invaders.srt",
        "09a - The Tell Tale Tail.srt",
        "01 - The Thing That Wouldn't Stop It.srt",
        "03b - They Came from Down There.srt",
        "03a - Bad Day on the Moon.srt",
        "04a - The Friend for Life.srt",
        "08b - The Glazed McGuffin Affair.srt",
        "07b - It's Dangly Deever Time.srt",
        "04b - Dysfunction of the Gods.srt",
        "05b - A Glitch in Time.srt",
        "12b - Sam & Max vs. the Uglions.srt",
        "08a - Aaiiieee Robot.srt",
        "02b - Max's Big Day.srt",
        "05a - Big Trouble at the Earth's Core.srt",
        "13 - The Final Episode.srt",
        "02a - The Second Show Ever.srt",
        "10a - Tonight We Love.srt",
        "12a - Fools Die on Friday.srt",
        "09b - The Trouble with Gary.srt",
        "06b - We Drop at Dawn.srt",
        "07a - Christmas Bloody Christmas.srt",
        "06a - That Darn Gator.srt",
    ]
    assert utils._get_matching_sub(files, False, episode, title) == file


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


def test_update_matches(movies):
    matches = set()
    utils.update_matches(
        matches, movies["dune"], "Subs for dune 2021 bluray x264\nDune webrip x264"
    )
    assert "source" in matches


def test_update_matches_iterable(movies):
    matches = set()
    utils.update_matches(
        matches, movies["dune"], ["Subs for dune 2021 bluray x264", "Dune webrip x264"]
    )
    assert "source" in matches


@pytest.mark.parametrize(
    "content,expected", [("the.wire.s01e01", True), ("taxi driver 1976", False)]
)
def test_is_episode(content, expected):
    assert utils.is_episode(content) is expected

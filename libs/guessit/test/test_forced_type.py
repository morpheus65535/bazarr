#!/usr/bin/env python
"""Consistency of the forced ``type`` modes (#939).

Forcing the type guessit already infers must be a no-op: ``guessit(name, {"type": t})`` has to
return exactly ``guessit(name)`` whenever the latter yields ``type: t``. The whole yaml corpus is
swept, so any new divergence shows up here even though the corpus itself barely exercises the
forced modes.
"""

from __future__ import annotations

import os

import pytest
import yaml

from .. import guessit
from ..options import load_config
from ..rules.properties.episodes import _split_words
from ..yamlutils import OrderedDictYAMLLoader
from . import test_yml

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def corpus_names() -> list[str]:
    """Every input string of the yaml corpus, minus the entries pinned to their own options."""
    names: list[str] = []
    for filename, _ in zip(*test_yml.files_and_ids(), strict=False):
        with open(os.path.join(__location__, filename), encoding="utf-8") as infile:
            data = yaml.load(infile, OrderedDictYAMLLoader)
        for string, expected in data.items():
            if string == "__default__" or (isinstance(expected, dict) and "options" in expected):
                continue
            match = test_yml.TestYml.options_re.match(str(string))
            name = match.group(2) if match else str(string)
            if name:
                names.append(test_yml.TestYml.fix_encoding(name))
    return sorted(set(names))


def test_forcing_the_inferred_type_is_a_no_op() -> None:
    divergences = {}
    for name in corpus_names():
        inferred = guessit(name)
        guessed_type = inferred.get("type")
        if guessed_type not in ("movie", "episode"):
            continue
        forced = guessit(name, {"type": guessed_type})
        if dict(forced) != dict(inferred):
            divergences[name] = (dict(inferred), dict(forced))

    assert not divergences, "forcing the inferred type changed the result:\n" + "\n".join(
        f"  {name}\n    inferred={inferred}\n    forced  ={forced}" for name, (inferred, forced) in divergences.items()
    )


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        # A year in the part keeps the leading number of the title out of the episode reading,
        # whatever the requested type (#939).
        ("12.Angry.Men.1957.mkv", {"title": "12 Angry Men", "year": 1957}),
        ("Movies/21 (2008)/21.(2008).DVDRip.x264.AC3-FtS.mkv", {"title": "21", "year": 2008, "release_group": "FtS"}),
        # An explicit episode marker is still numbered, year or not.
        (
            "Mastercook Italia - Stagione 6 (2016) 720p Episodio 13 spyro.mkv",
            {"season": 6, "episode": 13, "year": 2016},
        ),
    ],
)
def test_forced_episode_keeps_year_anchored_properties(name: str, expected: dict[str, object]) -> None:
    result = guessit(name, {"type": "episode"})
    for prop, value in expected.items():
        assert result.get(prop) == value, f"{prop}: {result.get(prop)!r} != {value!r} in {dict(result)}"


def marker_names(word_key: str) -> list[str]:
    """One "Show Name <marker> 5" per configured season/episode word, reversed for number-first ones."""
    config = load_config({"no_user_config": True})["advanced_config"]["episodes"]
    words, numfirst = _split_words(config[word_key])
    return [f"Show Name 5 {word}" if word in set(numfirst) else f"Show Name {word} 5" for word in words]


@pytest.mark.parametrize("options", [{}, {"type": "episode"}], ids=["inferred", "forced"])
@pytest.mark.parametrize("name", marker_names("episode_words"))
def test_every_episode_word_is_claimed_by_its_number(name: str, options: dict[str, str]) -> None:
    """A marker is claimed whole: a shorter one leaving its tail in the title is the #948 bug."""
    result = guessit(name, options)
    assert result.get("episode") == 5, f"episode: {dict(result)}"
    assert result.get("title") == "Show Name", f"title: {dict(result)}"


@pytest.mark.parametrize("options", [{}, {"type": "episode"}], ids=["inferred", "forced"])
@pytest.mark.parametrize("name", marker_names("season_words"))
def test_every_season_word_is_claimed_by_its_number(name: str, options: dict[str, str]) -> None:
    """Same guard on the season side, where the numeral pattern is shared by both modes."""
    result = guessit(name, options)
    assert result.get("season") == 5, f"season: {dict(result)}"
    assert result.get("title") == "Show Name", f"title: {dict(result)}"


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        # The "Complete" marker is anchored on the numbered season word, so it survives the season
        # chain being off (#944).
        ("Series/Mad Men Season 1 Complete/Mad.Men.S01E01.avi", {"title": "Mad Men", "other": "Complete"}),
        ("Something Seasons 1 & 2 - Complete", {"title": "Something", "other": "Complete"}),
        ("Something Seasons 4 Complete", {"title": "Something", "other": "Complete"}),
        # An absolute episode run nothing claims must not swallow the trailing release group.
        ("Bleach.s16e03-04.313-314-GROUP", {"title": "Bleach", "release_group": "GROUP"}),
        ("Show.Name.16x03-05.313-315-GROUP", {"title": "Show Name", "release_group": "GROUP"}),
    ],
)
def test_forced_movie_keeps_properties_unrelated_to_episodes(name: str, expected: dict[str, object]) -> None:
    result = guessit(name, {"type": "movie"})
    for prop, value in expected.items():
        assert result.get(prop) == value, f"{prop}: {result.get(prop)!r} != {value!r} in {dict(result)}"


@pytest.mark.parametrize(
    "name",
    [
        "Show.Name.2019.313-314-GROUP",
        "Show Name 313-314-GROUP",
        "12-Monkeys",
    ],
)
def test_a_numeric_run_alone_does_not_yield_a_release_group(name: str) -> None:
    """Only a run anchored on a season/episode marker vouches for the word behind it (#944)."""
    assert "release_group" not in guessit(name, {"type": "movie"})


def test_forced_episode_ignores_an_episode_word_from_another_filepart() -> None:
    """A parent directory named "Episode" must not vouch for a number in the file below it."""
    result = guessit("Series/Episode/12.Angry.Men.1957.mkv", {"type": "episode"})
    assert result.get("title") == "12 Angry Men"
    assert result.get("year") == 1957


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        # A lone digit only the forced-episode patterns see must not evict what owns its span:
        # the tail of a title, a word of the episode title, a duplicate suffix, a release group,
        # or a parent directory (#943).
        ("Thumping.Spike.2.E01.DF.WEBRip.720p-DRAMATV.mp4", {"title": "Thumping Spike 2", "episode": 1}),
        (
            "GTTV.E3.All.Access.Live.Day.1.Xbox.Showcase.Preshow.HDTV.x264-SYS",
            {"episode": 3, "episode_title": "All Access Live Day 1 Xbox Showcase Preshow"},
        ),
        ("[t.3.3.d]_Mikakunin_de_Shinkoukei_-_12_[720p][5DDC1352].mkv", {"episode": 12, "release_group": "t.3.3.d"}),
        ("[7.1.7.8.5] Foo Bar - 11 (H.264) [5235532D].mkv", {"episode": 11, "release_group": "7.8.5"}),
        (
            "/Volumes/data-1/Series/Futurama/Season 3/Futurama_-_S03_DVD_Bonus_-_Deleted_Scenes_Part_3.ogm",
            {"title": "Futurama", "season": 3},
        ),
        # A number that does carry the episode numbering stays, marked or not.
        ("Some Series E01 02 03", {"episode": [1, 2, 3]}),
        ("Show.Name.Season.4.Episodes.1-12", {"season": 4, "episode": list(range(1, 13))}),
        ("FooBar.7.PDTV-FlexGet", {"episode": 7}),
        ("Show Name - 313-315 - s16e03-05", {"absolute_episode": [313, 314, 315], "episode": [3, 4, 5]}),
        # The fractional digit of a half episode is not a second episode (#948).
        ("[GroupName].Show.Name.-.02.5.(Special).[BD.1080p]", {"episode": 2, "episode_title": "5"}),
        ("Show.Name.-.12.5.(Special)", {"episode": 12, "episode_title": "5"}),
    ],
)
def test_forced_episode_keeps_a_lone_digit_out_of_other_properties(name: str, expected: dict[str, object]) -> None:
    result = guessit(name, {"type": "episode"})
    for prop, value in expected.items():
        assert result.get(prop) == value, f"{prop}: {result.get(prop)!r} != {value!r} in {dict(result)}"

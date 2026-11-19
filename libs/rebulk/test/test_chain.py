#!/usr/bin/env python
from __future__ import annotations

import re
from functools import partial
from typing import TYPE_CHECKING, Any

from rebulk.pattern import FunctionalPattern, RePattern, StringPattern

from ..chain import Chain
from ..match import Match
from ..rebulk import Rebulk
from ..validators import chars_surround

if TYPE_CHECKING:
    from ..match import Matches


def test_chain_close() -> None:
    rebulk = Rebulk()
    ret = rebulk.chain().close()

    assert ret == rebulk
    assert len(rebulk.effective_patterns()) == 1


def test_build_chain() -> None:
    rebulk = Rebulk()

    def digit(input_string: str) -> tuple[int, int] | None:
        i = input_string.find("1849")
        if i > -1:
            return i, i + len("1849")
        return None

    builder: Any = rebulk.chain()
    ret = (
        builder.functional(digit)
        .string("test")
        .repeater(2)
        .string("x")
        .repeater("{1,3}")
        .string("optional")
        .repeater("?")
        .regex("f?x")
        .repeater("+")
        .close()
    )

    assert ret == rebulk
    assert len(rebulk.effective_patterns()) == 1

    chain = rebulk.effective_patterns()[0]
    assert isinstance(chain, Chain)

    assert len(chain.parts) == 5

    assert isinstance(chain.parts[0].pattern, FunctionalPattern)
    assert chain.parts[0].repeater_start == 1
    assert chain.parts[0].repeater_end == 1

    assert isinstance(chain.parts[1].pattern, StringPattern)
    assert chain.parts[1].repeater_start == 2
    assert chain.parts[1].repeater_end == 2

    assert isinstance(chain.parts[2].pattern, StringPattern)
    assert chain.parts[2].repeater_start == 1
    assert chain.parts[2].repeater_end == 3

    assert isinstance(chain.parts[3].pattern, StringPattern)
    assert chain.parts[3].repeater_start == 0
    assert chain.parts[3].repeater_end == 1

    assert isinstance(chain.parts[4].pattern, RePattern)
    assert chain.parts[4].repeater_start == 1
    assert chain.parts[4].repeater_end is None


def test_chain_defaults() -> None:
    rebulk = Rebulk()
    rebulk.defaults(validator=lambda x: x.value.startswith("t"), ignore_names=["testIgnore"], children=True)

    chain: Any = rebulk.chain()
    chain.regex("(?P<test>test)").regex(" ").repeater("*").regex("(?P<best>best)").regex(" ").repeater("*").regex(
        "(?P<testIgnore>testIgnore)"
    )
    matches = rebulk.matches("test best testIgnore")

    assert len(matches) == 1
    assert matches[0].name == "test"


def test_chain_with_validators() -> None:
    def chain_validator(match: Match) -> bool:
        return bool(match.value.startswith("t") and match.value.endswith("t"))

    def default_validator(match: Match) -> bool:
        return bool(match.value.startswith("t") and match.value.endswith("g"))

    def custom_validator(match: Match) -> bool:
        return bool(match.value.startswith("b") and match.value.endswith("t"))

    rebulk = Rebulk()
    rebulk.defaults(children=True, validator=default_validator)

    chain: Any = rebulk.chain(validate_all=True, validator={"__parent__": chain_validator})
    chain.regex("(?P<test>testing)", validator=default_validator).repeater("+").regex(" ").repeater("+").regex(
        "(?P<best>best)", validator=custom_validator
    ).repeater("+")
    matches = rebulk.matches("some testing best end")

    assert len(matches) == 2
    assert matches[0].name == "test"
    assert matches[1].name == "best"


def test_matches_docs() -> None:
    rebulk = (
        Rebulk()
        .regex_defaults(flags=re.IGNORECASE)
        .defaults(children=True, formatter={"episode": int, "version": int})
        .chain()
        .regex(r"e(?P<episode>\d{1,4})")
        .repeater(1)
        .regex(r"v(?P<version>\d+)")
        .repeater("?")
        .regex(r"[ex-](?P<episode>\d{1,4})")
        .repeater("*")
        .close()
    )  # .repeater(1) could be omitted as it's the default behavior

    result = rebulk.matches("This is E14v2-15-16-17").to_dict()  # converts matches to dict

    assert "episode" in result
    assert result["episode"] == [14, 15, 16, 17]
    assert "version" in result
    assert result["version"] == 2


def test_matches() -> None:
    rebulk = Rebulk()

    def digit(input_string: str) -> tuple[int, int] | None:
        i = input_string.find("1849")
        if i > -1:
            return i, i + len("1849")
        return None

    input_string = "1849testtestxxfixfux_foxabc1849testtestxoptionalfoxabc"

    chain = (
        rebulk.chain()
        .functional(digit)
        .string("test")
        .hidden()
        .repeater(2)
        .string("x")
        .hidden()
        .repeater("{1,3}")
        .string("optional")
        .hidden()
        .repeater("?")
        .regex("f.?x", name="result")
        .repeater("+")
        .close()
    )

    matches = chain.matches(input_string)

    assert len(matches) == 2
    children = matches[0].children

    assert children[0].value == "1849"
    assert children[1].value == "fix"
    assert children[2].value == "fux"

    children = matches[1].children
    assert children[0].value == "1849"
    assert children[1].value == "fox"

    input_string = "_1850testtestxoptionalfoxabc"
    matches = chain.matches(input_string)

    assert len(matches) == 0

    input_string = "_1849testtesttesttestxoptionalfoxabc"
    matches = chain.matches(input_string)

    assert len(matches) == 0

    input_string = "_1849testtestxxxxoptionalfoxabc"
    matches = chain.matches(input_string)

    assert len(matches) == 0

    input_string = "_1849testtestoptionalfoxabc"
    matches = chain.matches(input_string)

    assert len(matches) == 0

    input_string = "_1849testtestxoptionalabc"
    matches = chain.matches(input_string)

    assert len(matches) == 0

    input_string = "_1849testtestxoptionalfaxabc"
    matches = chain.matches(input_string)

    assert len(matches) == 1
    children = matches[0].children

    assert children[0].value == "1849"
    assert children[1].value == "fax"


def test_matches_2() -> None:
    rebulk = (
        Rebulk()
        .regex_defaults(flags=re.IGNORECASE)
        .defaults(children=True, formatter={"episode": int, "version": int})
        .chain()
        .regex(r"e(?P<episode>\d{1,4})")
        .regex(r"v(?P<version>\d+)")
        .repeater("?")
        .regex(r"[ex-](?P<episode>\d{1,4})")
        .repeater("*")
        .close()
    )

    matches = rebulk.matches("This is E14v2-15E16x17")
    assert len(matches) == 5

    assert matches[0].name == "episode"
    assert matches[0].value == 14

    assert matches[1].name == "version"
    assert matches[1].value == 2

    assert matches[2].name == "episode"
    assert matches[2].value == 15

    assert matches[3].name == "episode"
    assert matches[3].value == 16

    assert matches[4].name == "episode"
    assert matches[4].value == 17


def test_matches_3() -> None:
    alt_dash = (r"@", r"[\W_]")  # abbreviation

    match_names = ["season", "episode"]
    other_names = ["screen_size", "video_codec", "audio_codec", "audio_channels", "container", "date"]

    rebulk = Rebulk()
    rebulk.defaults(
        formatter={"season": int, "episode": int},
        tags=["SxxExx"],
        abbreviations=[alt_dash],
        private_names=["episodeSeparator", "seasonSeparator"],
        children=True,
        private_parent=True,
        conflict_solver=lambda match, other: (
            match if match.name in match_names and other.name in other_names else "__default__"
        ),
    )

    chain: Any = rebulk.chain()
    chain.defaults(children=True, private_parent=True).regex(r"(?P<season>\d+)@?x@?(?P<episode>\d+)").regex(
        r"(?P<episodeSeparator>x|-|\+|&)(?P<episode>\d+)"
    ).repeater("*").close().chain().defaults(children=True, private_parent=True).regex(
        r"S(?P<season>\d+)@?(?:xE|Ex|E|x)@?(?P<episode>\d+)"
    ).regex(r"(?:(?P<episodeSeparator>xE|Ex|E|x|-|\+|&)(?P<episode>\d+))").repeater("*").close().chain().defaults(
        children=True, private_parent=True
    ).regex(r"S(?P<season>\d+)").regex(r"(?P<seasonSeparator>S|-|\+|&)(?P<season>\d+)").repeater("*")

    matches = rebulk.matches("test-01x02-03")
    assert len(matches) == 3

    assert matches[0].name == "season"
    assert matches[0].value == 1

    assert matches[1].name == "episode"
    assert matches[1].value == 2

    assert matches[2].name == "episode"
    assert matches[2].value == 3

    matches = rebulk.matches("test-S01E02-03")

    assert len(matches) == 3
    assert matches[0].name == "season"
    assert matches[0].value == 1

    assert matches[1].name == "episode"
    assert matches[1].value == 2

    assert matches[2].name == "episode"
    assert matches[2].value == 3

    matches = rebulk.matches("test-S01-02-03-04")

    assert len(matches) == 4
    assert matches[0].name == "season"
    assert matches[0].value == 1

    assert matches[1].name == "season"
    assert matches[1].value == 2

    assert matches[2].name == "season"
    assert matches[2].value == 3

    assert matches[3].name == "season"
    assert matches[3].value == 4


def test_matches_4() -> None:
    seps_surround = partial(chars_surround, " ")

    rebulk = Rebulk()
    rebulk.regex_defaults(flags=re.IGNORECASE)
    rebulk.defaults(validate_all=True, children=True)
    rebulk.defaults(private_names=["episodeSeparator", "seasonSeparator"], private_parent=True)

    chain: Any = rebulk.chain(validator={"__parent__": seps_surround}, formatter={"episode": int, "version": int})
    chain.defaults(formatter={"episode": int, "version": int}).regex(r"e(?P<episode>\d{1,4})").regex(
        r"v(?P<version>\d+)"
    ).repeater("?").regex(r"(?P<episodeSeparator>e|x|-)(?P<episode>\d{1,4})").repeater("*")

    matches = rebulk.matches("Some Series E01E02E03")
    assert len(matches) == 3

    assert matches[0].value == 1
    assert matches[1].value == 2
    assert matches[2].value == 3


def test_matches_5() -> None:
    seps_surround = partial(chars_surround, " ")

    rebulk = Rebulk()
    rebulk.regex_defaults(flags=re.IGNORECASE)

    chain: Any = rebulk.chain(
        private_names=["episodeSeparator", "seasonSeparator"],
        validate_all=True,
        validator={"__parent__": seps_surround},
        children=True,
        private_parent=True,
        formatter={"episode": int, "version": int},
    )
    chain.defaults(children=True, private_parent=True).regex(r"e(?P<episode>\d{1,4})").regex(
        r"v(?P<version>\d+)"
    ).repeater("?").regex(r"(?P<episodeSeparator>e|x|-)(?P<episode>\d{1,4})").repeater("{2,3}")

    matches = rebulk.matches("Some Series E01E02E03")
    assert len(matches) == 3

    matches = rebulk.matches("Some Series E01E02")
    assert len(matches) == 0

    matches = rebulk.matches("Some Series E01E02E03E04E05E06")  # Parent can't be validated, so no results at all
    assert len(matches) == 0


def test_matches_6() -> None:
    rebulk = Rebulk()
    rebulk.regex_defaults(flags=re.IGNORECASE)
    rebulk.defaults(
        private_names=["episodeSeparator", "seasonSeparator"],
        validate_all=True,
        validator=None,
        children=True,
        private_parent=True,
    )

    chain: Any = rebulk.chain(formatter={"episode": int, "version": int})
    chain.defaults(children=True, private_parent=True).regex(r"e(?P<episode>\d{1,4})").regex(
        r"v(?P<version>\d+)"
    ).repeater("?").regex(r"(?P<episodeSeparator>e|x|-)(?P<episode>\d{1,4})").repeater("{2,3}")

    matches = rebulk.matches("Some Series E01E02E03")
    assert len(matches) == 3

    matches = rebulk.matches("Some Series E01E02")
    assert len(matches) == 0

    matches = rebulk.matches("Some Series E01E02E03E04E05E06")  # No validator on parent, so it should give 4 episodes.
    assert len(matches) == 4


def test_matches_7() -> None:
    seps_surround = partial(chars_surround, " .-/")
    rebulk = Rebulk()
    rebulk.regex_defaults(flags=re.IGNORECASE)
    rebulk.defaults(children=True, private_parent=True)

    chain: Any = rebulk.chain()
    chain.regex(r"S(?P<season>\d+)", validate_all=True, validator={"__parent__": seps_surround}).regex(
        r"[ -](?P<season>\d+)", validator=seps_surround
    ).repeater("*")

    matches = rebulk.matches("Some S01")
    assert len(matches) == 1
    matches[0].value = 1

    matches = rebulk.matches("Some S01-02")
    assert len(matches) == 2
    matches[0].value = 1
    matches[1].value = 2

    matches = rebulk.matches("programs4/Some S01-02")
    assert len(matches) == 2
    matches[0].value = 1
    matches[1].value = 2

    matches = rebulk.matches("programs4/SomeS01middle.S02-03.andS04here")
    assert len(matches) == 2
    matches[0].value = 2
    matches[1].value = 3

    matches = rebulk.matches("Some 02.and.S04-05.here")
    assert len(matches) == 2
    matches[0].value = 4
    matches[1].value = 5


def test_chain_breaker() -> None:
    def chain_breaker(matches: Matches) -> bool:
        seasons = matches.named("season")
        return bool(len(seasons) > 1 and seasons[-1].value - seasons[-2].value > 10)

    seps_surround = partial(chars_surround, " .-/")
    rebulk = Rebulk()
    rebulk.regex_defaults(flags=re.IGNORECASE)
    rebulk.defaults(children=True, private_parent=True, formatter={"season": int})

    chain: Any = rebulk.chain(chain_breaker=chain_breaker)
    chain.regex(r"S(?P<season>\d+)", validate_all=True, validator={"__parent__": seps_surround}).regex(
        r"[ -](?P<season>\d+)", validator=seps_surround
    ).repeater("*")

    matches = rebulk.matches("Some S01-02-03-50-51")
    assert len(matches) == 3
    matches[0].value = 1
    matches[1].value = 2
    matches[2].value = 3


def test_chain_breaker_defaults() -> None:
    def chain_breaker(matches: Matches) -> bool:
        seasons = matches.named("season")
        return bool(len(seasons) > 1 and seasons[-1].value - seasons[-2].value > 10)

    seps_surround = partial(chars_surround, " .-/")
    rebulk = Rebulk()
    rebulk.regex_defaults(flags=re.IGNORECASE)
    rebulk.defaults(chain_breaker=chain_breaker, children=True, private_parent=True, formatter={"season": int})

    chain: Any = rebulk.chain()
    chain.regex(r"S(?P<season>\d+)", validate_all=True, validator={"__parent__": seps_surround}).regex(
        r"[ -](?P<season>\d+)", validator=seps_surround
    ).repeater("*")

    matches = rebulk.matches("Some S01-02-03-50-51")
    assert len(matches) == 3
    matches[0].value = 1
    matches[1].value = 2
    matches[2].value = 3


def test_chain_breaker_defaults2() -> None:
    def chain_breaker(matches: Matches) -> bool:
        seasons = matches.named("season")
        return bool(len(seasons) > 1 and seasons[-1].value - seasons[-2].value > 10)

    seps_surround = partial(chars_surround, " .-/")
    rebulk = Rebulk()
    rebulk.regex_defaults(flags=re.IGNORECASE)
    rebulk.chain_defaults(chain_breaker=chain_breaker)
    rebulk.defaults(children=True, private_parent=True, formatter={"season": int})

    chain: Any = rebulk.chain()
    chain.regex(r"S(?P<season>\d+)", validate_all=True, validator={"__parent__": seps_surround}).regex(
        r"[ -](?P<season>\d+)", validator=seps_surround
    ).repeater("*")

    matches = rebulk.matches("Some S01-02-03-50-51")
    assert len(matches) == 3
    matches[0].value = 1
    matches[1].value = 2
    matches[2].value = 3


def test_group_by_match_index_sorts_unordered_input() -> None:
    # groupby only groups consecutive equal keys, so _group_by_match_index must
    # sort by match_index first; otherwise unordered matches split (and overwrite)
    # groups sharing an index.
    matches: list[Match] = []
    for start, match_index in ((0, 2), (5, 0), (10, 1), (15, 2)):
        match = Match(start, start + 1, name="test")
        match.match_index = match_index
        matches.append(match)

    grouped = Chain._group_by_match_index(matches)

    assert sorted(grouped) == [0, 1, 2]
    assert [m.start for m in grouped[0]] == [5]
    assert [m.start for m in grouped[1]] == [10]
    # both match_index=2 matches are kept, in their original relative order
    assert [m.start for m in grouped[2]] == [0, 15]


def test_nested_chain() -> None:
    # A chain whose single part is itself a chain (a then b), matched end to end.
    rebulk = Rebulk()
    nested = rebulk.chain(children=True).chain()
    nested.regex(r"(?P<a>a)").regex(r"(?P<b>b)")

    assert nested.close() is rebulk

    matches = rebulk.matches("ab")

    assert [m.value for m in matches.named("a")] == ["a"]
    assert [m.value for m in matches.named("b")] == ["b"]

#!/usr/bin/env python

from __future__ import annotations

import re
from typing import Any, cast

import pytest

from ..match import Match
from ..pattern import FunctionalPattern, Pattern, RePattern, StringPattern
from ..remodule import REGEX_ENABLED


class TestStringPattern:
    """
    Tests for StringPattern matching
    """

    input_string = (
        "An Abyssinian fly playing a Celtic violin was annoyed by trashy flags on which were the Hebrew letter qoph."
    )

    def test_single(self) -> None:
        pattern = StringPattern("Celtic")

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1
        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (28, 34)
        assert matches[0].value == "Celtic"

    def test_repr(self) -> None:
        pattern = StringPattern("Celtic")

        assert repr(pattern) == "<StringPattern:('Celtic',)>"

    def test_ignore_case(self) -> None:
        pattern = StringPattern("celtic", ignore_case=False)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 0

        pattern = StringPattern("celtic", ignore_case=True)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1
        assert matches[0].value == "Celtic"

    def test_private_names(self) -> None:
        pattern = StringPattern("celtic", name="test", private_names=["test"], ignore_case=True)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1
        assert matches[0].private

    def test_ignore_names(self) -> None:
        pattern = StringPattern("celtic", name="test", ignore_names=["test"], ignore_case=True)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 0

    def test_no_match(self) -> None:
        pattern = StringPattern("Python")

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert not matches

    def test_multiple_patterns(self) -> None:
        pattern = StringPattern("playing", "annoyed", "Hebrew")

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 3

        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (18, 25)
        assert matches[0].value == "playing"

        assert isinstance(matches[1], Match)
        assert matches[1].pattern == pattern
        assert matches[1].span == (46, 53)
        assert matches[1].value == "annoyed"

        assert isinstance(matches[2], Match)
        assert matches[2].pattern == pattern
        assert matches[2].span == (88, 94)
        assert matches[2].value == "Hebrew"

    def test_start_end_kwargs(self) -> None:
        pattern = StringPattern("Abyssinian", start=20, end=40)
        matches = cast("list[Match]", list(pattern.matches(self.input_string)))

        assert len(matches) == 0

    def test_matches_kwargs(self) -> None:
        pattern = StringPattern("Abyssinian", name="test", value="AB")
        matches = cast("list[Match]", list(pattern.matches(self.input_string)))

        assert len(matches) == 1
        assert matches[0].name == "test"
        assert matches[0].value == "AB"

    def test_post_processor(self) -> None:
        def post_processor(matches: list[Match], pattern: Pattern) -> list[Match]:
            assert len(matches) == 1
            assert isinstance(pattern, StringPattern)

            return []

        pattern = StringPattern("Abyssinian", name="test", value="AB", post_processor=post_processor)
        matches = cast("list[Match]", list(pattern.matches(self.input_string)))

        assert len(matches) == 0


class TestRePattern:
    """
    Tests for RePattern matching
    """

    input_string = (
        "An Abyssinian fly playing a Celtic violin was annoyed by trashy flags on which were the Hebrew letter qoph."
    )

    def test_single_compiled(self) -> None:
        pattern = RePattern(re.compile("Celt.?c"))

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1
        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (28, 34)
        assert matches[0].value == "Celtic"

    def test_single_string(self) -> None:
        pattern = RePattern("Celt.?c")

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1
        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (28, 34)
        assert matches[0].value == "Celtic"

    def test_single_kwargs(self) -> None:
        pattern = RePattern({"pattern": "celt.?c", "flags": re.IGNORECASE})

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1
        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (28, 34)
        assert matches[0].value == "Celtic"

    def test_single_vargs(self) -> None:
        pattern = RePattern(("celt.?c", re.IGNORECASE))

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1
        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (28, 34)
        assert matches[0].value == "Celtic"

    def test_no_match(self) -> None:
        pattern = RePattern("abc.?def")

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 0

    def test_shortcuts(self) -> None:
        pattern = RePattern("Celtic-violin", abbreviations=[("-", r"[\W_]+")])

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1

        pattern = RePattern({"pattern": "celtic-violin", "flags": re.IGNORECASE}, abbreviations=[("-", r"[\W_]+")])

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1

    def test_multiple_patterns(self) -> None:
        pattern = RePattern("pla.?ing", "ann.?yed", "Heb.?ew")

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 3

        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (18, 25)
        assert matches[0].value == "playing"

        assert isinstance(matches[1], Match)
        assert matches[1].pattern == pattern
        assert matches[1].span == (46, 53)
        assert matches[1].value == "annoyed"

        assert isinstance(matches[2], Match)
        assert matches[2].pattern == pattern
        assert matches[2].span == (88, 94)
        assert matches[2].value == "Hebrew"

    def test_unnamed_groups(self) -> None:
        pattern = RePattern(r"(Celt.?c)\s+(\w+)")

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1

        parent = matches[0]

        assert isinstance(parent, Match)
        assert parent.pattern == pattern
        assert parent.span == (28, 41)
        assert parent.name is None
        assert parent.value == "Celtic violin"

        assert len(parent.children) == 2

        group1, group2 = parent.children

        assert isinstance(group1, Match)
        assert group1.pattern == pattern
        assert group1.span == (28, 34)
        assert group1.name is None
        assert group1.value == "Celtic"
        assert group1.parent == parent

        assert isinstance(group2, Match)
        assert group2.pattern == pattern
        assert group2.span == (35, 41)
        assert group2.name is None
        assert group2.value == "violin"
        assert group2.parent == parent

    def test_named_groups(self) -> None:
        pattern = RePattern(r"(?P<param1>Celt.?c)\s+(?P<param2>\w+)")

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1

        parent = matches[0]

        assert isinstance(parent, Match)
        assert parent.pattern == pattern
        assert parent.span == (28, 41)
        assert parent.name is None
        assert parent.value == "Celtic violin"

        assert len(parent.children) == 2
        group1, group2 = parent.children

        assert isinstance(group1, Match)
        assert group1.pattern == pattern
        assert group1.span == (28, 34)
        assert group1.name == "param1"
        assert group1.value == "Celtic"
        assert group1.parent == parent

        assert isinstance(group2, Match)
        assert group2.pattern == pattern
        assert group2.span == (35, 41)
        assert group2.name == "param2"
        assert group2.value == "violin"
        assert group2.parent == parent

    def test_children(self) -> None:
        pattern = RePattern(r"(?P<param1>Celt.?c)\s+(?P<param2>\w+)", children=True)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 2
        group1, group2 = matches

        assert isinstance(group1, Match)
        assert group1.pattern == pattern
        assert group1.span == (28, 34)
        assert group1.name == "param1"
        assert group1.value == "Celtic"

        assert isinstance(group2, Match)
        assert group2.pattern == pattern
        assert group2.span == (35, 41)
        assert group2.name == "param2"
        assert group2.value == "violin"

    def test_children_parent_private(self) -> None:
        pattern = RePattern(r"(?P<param1>Celt.?c)\s+(?P<param2>\w+)", children=True, private_parent=True)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 3
        parent, group1, group2 = matches

        assert isinstance(group1, Match)
        assert parent.private
        assert parent.pattern == pattern
        assert parent.span == (28, 41)
        assert parent.name is None
        assert parent.value == "Celtic violin"

        assert isinstance(group1, Match)
        assert not group1.private
        assert group1.pattern == pattern
        assert group1.span == (28, 34)
        assert group1.name == "param1"
        assert group1.value == "Celtic"

        assert isinstance(group2, Match)
        assert not group2.private
        assert group2.pattern == pattern
        assert group2.span == (35, 41)
        assert group2.name == "param2"
        assert group2.value == "violin"

    def test_parent_children_private(self) -> None:
        pattern = RePattern(r"(?P<param1>Celt.?c)\s+(?P<param2>\w+)", private_children=True)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 3
        parent, group1, group2 = matches

        assert isinstance(group1, Match)
        assert not parent.private
        assert parent.pattern == pattern
        assert parent.span == (28, 41)
        assert parent.name is None
        assert parent.value == "Celtic violin"

        assert isinstance(group1, Match)
        assert group1.private
        assert group1.pattern == pattern
        assert group1.span == (28, 34)
        assert group1.name == "param1"
        assert group1.value == "Celtic"

        assert isinstance(group2, Match)
        assert group2.private
        assert group2.pattern == pattern
        assert group2.span == (35, 41)
        assert group2.name == "param2"
        assert group2.value == "violin"

    def test_every(self) -> None:
        pattern = RePattern(r"(?P<param1>Celt.?c)\s+(?P<param2>\w+)", every=True)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 3
        parent, group1, group2 = matches

        assert isinstance(group1, Match)
        assert not parent.private
        assert parent.pattern == pattern
        assert parent.span == (28, 41)
        assert parent.name is None
        assert parent.value == "Celtic violin"

        assert isinstance(group1, Match)
        assert not group1.private
        assert group1.pattern == pattern
        assert group1.span == (28, 34)
        assert group1.name == "param1"
        assert group1.value == "Celtic"

        assert isinstance(group2, Match)
        assert not group2.private
        assert group2.pattern == pattern
        assert group2.span == (35, 41)
        assert group2.name == "param2"
        assert group2.value == "violin"

    def test_private_names(self) -> None:
        pattern = RePattern(r"(?P<param1>Celt.?c)\s+(?P<param2>\w+)", private_names=["param2"], children=True)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 2
        assert matches[0].name == "param1"
        assert not matches[0].private
        assert matches[1].name == "param2"
        assert matches[1].private

    def test_ignore_names(self) -> None:
        pattern = RePattern(r"(?P<param1>Celt.?c)\s+(?P<param2>\w+)", ignore_names=["param2"], children=True)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1
        assert matches[0].name == "param1"

    def test_matches_kwargs(self) -> None:
        pattern = RePattern("He.rew", name="test", value="HE")
        matches = cast("list[Match]", list(pattern.matches(self.input_string)))

        assert len(matches) == 1
        assert matches[0].name == "test"
        assert matches[0].value == "HE"

        pattern = RePattern("H(e.)(rew)", name="test", value="HE")
        matches = cast("list[Match]", list(pattern.matches(self.input_string)))

        assert len(matches) == 1
        assert matches[0].name == "test"
        assert matches[0].value == "HE"

        children = matches[0].children
        assert len(children) == 2
        assert children[0].name == "test"
        assert children[0].value == "HE"

        assert children[1].name == "test"
        assert children[1].value == "HE"

        pattern = RePattern("H(?P<first>e.)(?P<second>rew)", name="test", value="HE")
        matches = cast("list[Match]", list(pattern.matches(self.input_string)))

        assert len(matches) == 1
        assert matches[0].name == "test"
        assert matches[0].value == "HE"

        children = matches[0].children
        assert len(children) == 2
        assert children[0].name == "first"
        assert children[0].value == "HE"

        assert children[1].name == "second"
        assert children[1].value == "HE"


class TestFunctionalPattern:
    """
    Tests for FunctionalPattern matching
    """

    input_string = (
        "An Abyssinian fly playing a Celtic violin was annoyed by trashy flags on which were the Hebrew letter qoph."
    )

    def test_single_vargs(self) -> None:
        def func(input_string: str) -> Any:
            i = input_string.find("fly")
            if i > -1:
                return i, i + len("fly"), "fly", "functional"
            return None

        pattern = FunctionalPattern(func)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1
        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (14, 17)
        assert matches[0].name == "functional"
        assert matches[0].value == "fly"

    def test_single_kwargs(self) -> None:
        def func(input_string: str) -> Any:
            i = input_string.find("fly")
            if i > -1:
                return {"start": i, "end": i + len("fly"), "name": "functional"}
            return None

        pattern = FunctionalPattern(func)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1
        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (14, 17)
        assert matches[0].name == "functional"
        assert matches[0].value == "fly"

    def test_multiple_objects(self) -> None:
        def func(input_string: str) -> Any:
            i = input_string.find("fly")
            matches: list[Any] = []
            if i > -1:
                matches.append((i, i + len("fly"), {"name": "functional"}))
                i = input_string.find("annoyed")
            if i > -1:
                matches.append((i, i + len("annoyed")))
            i = input_string.find("Hebrew")
            if i > -1:
                matches.append({"start": i, "end": i + len("Hebrew")})
            return matches

        pattern = FunctionalPattern(func)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 3
        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (14, 17)
        assert matches[0].name == "functional"
        assert matches[0].value == "fly"

        assert isinstance(matches[1], Match)
        assert matches[1].pattern == pattern
        assert matches[1].span == (46, 53)
        assert matches[1].value == "annoyed"

        assert isinstance(matches[2], Match)
        assert matches[2].pattern == pattern
        assert matches[2].span == (88, 94)
        assert matches[2].value == "Hebrew"

    def test_multiple_generator(self) -> None:
        def func(input_string: str) -> Any:
            i = input_string.find("fly")
            if i > -1:
                yield (i, i + len("fly"), {"name": "functional"})
            i = input_string.find("annoyed")
            if i > -1:
                yield (i, i + len("annoyed"))
            i = input_string.find("Hebrew")
            if i > -1:
                yield (i, {"end": i + len("Hebrew")})

        pattern = FunctionalPattern(func)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 3
        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (14, 17)
        assert matches[0].name == "functional"
        assert matches[0].value == "fly"

        assert isinstance(matches[1], Match)
        assert matches[1].pattern == pattern
        assert matches[1].span == (46, 53)
        assert matches[1].value == "annoyed"

        assert isinstance(matches[2], Match)
        assert matches[2].pattern == pattern
        assert matches[2].span == (88, 94)
        assert matches[2].value == "Hebrew"

    def test_no_match(self) -> None:
        pattern = FunctionalPattern(lambda x: None)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 0

    def test_multiple_patterns(self) -> None:
        def playing(input_string: str) -> Any:
            i = input_string.find("playing")
            if i > -1:
                return i, i + len("playing")
            return None

        def annoyed(input_string: str) -> Any:
            i = input_string.find("annoyed")
            if i > -1:
                return i, i + len("annoyed")
            return None

        def hebrew(input_string: str) -> Any:
            i = input_string.find("Hebrew")
            if i > -1:
                return i, i + len("Hebrew")
            return None

        pattern = FunctionalPattern(playing, annoyed, hebrew)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 3

        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (18, 25)
        assert matches[0].value == "playing"

        assert isinstance(matches[1], Match)
        assert matches[1].pattern == pattern
        assert matches[1].span == (46, 53)
        assert matches[1].value == "annoyed"

        assert isinstance(matches[2], Match)
        assert matches[2].pattern == pattern
        assert matches[2].span == (88, 94)
        assert matches[2].value == "Hebrew"

    def test_matches_kwargs(self) -> None:
        def playing(input_string: str) -> Any:
            i = input_string.find("playing")
            if i > -1:
                return i, i + len("playing")
            return None

        pattern = FunctionalPattern(playing, name="test", value="PLAY")
        matches = cast("list[Match]", list(pattern.matches(self.input_string)))

        assert len(matches) == 1
        assert matches[0].name == "test"
        assert matches[0].value == "PLAY"


class TestValue:
    """
    Tests for value option
    """

    input_string = "This string contains 1849 a number"

    def test_str_value(self) -> None:
        pattern = StringPattern("1849", name="dummy", value="test")

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1
        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (21, 25)
        assert matches[0].value == "test"

    def test_dict_child_value(self) -> None:
        pattern = RePattern(
            r"(?P<strParam>cont.?ins)\s+(?P<intParam>\d+)",
            formatter={"intParam": lambda x: int(x) * 2, "strParam": lambda x: "really " + x},
            format_all=True,
            value={"intParam": "INT_PARAM_VALUE"},
        )

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1

        parent = matches[0]
        assert len(parent.children) == 2

        group1, group2 = parent.children

        assert isinstance(group1, Match)
        assert group1.pattern == pattern
        assert group1.span == (12, 20)
        assert group1.value == "really contains"

        assert isinstance(group2, Match)
        assert group2.pattern == pattern
        assert group2.span == (21, 25)
        assert group2.value == "INT_PARAM_VALUE"

    def test_dict_default_value(self) -> None:
        pattern = RePattern(
            r"(?P<strParam>cont.?ins)\s+(?P<intParam>\d+)",
            formatter={"intParam": lambda x: int(x) * 2, "strParam": lambda x: "really " + x},
            format_all=True,
            value={"__children__": "CHILD", "strParam": "STR_VALUE", "__parent__": "PARENT"},
        )

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1

        parent = matches[0]
        assert parent.value == "PARENT"
        assert len(parent.children) == 2

        group1, group2 = parent.children

        assert isinstance(group1, Match)
        assert group1.pattern == pattern
        assert group1.span == (12, 20)
        assert group1.value == "STR_VALUE"

        assert isinstance(group2, Match)
        assert group2.pattern == pattern
        assert group2.span == (21, 25)
        assert group2.value == "CHILD"


class TestFormatter:
    """
    Tests for formatter option
    """

    input_string = "This string contains 1849 a number"

    def test_single_string(self) -> None:
        pattern = StringPattern("1849", name="dummy", formatter=lambda x: int(x) / 2)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1
        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (21, 25)
        assert matches[0].value == 1849 / 2

    def test_single_re_no_group(self) -> None:
        pattern = RePattern(r"\d+", formatter=lambda x: int(x) * 2)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1
        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (21, 25)
        assert matches[0].value == 1849 * 2

    def test_single_re_named_groups(self) -> None:
        pattern = RePattern(
            r"(?P<strParam>cont.?ins)\s+(?P<intParam>\d+)",
            formatter={"intParam": lambda x: int(x) * 2, "strParam": lambda x: "really " + x},
            format_all=True,
        )

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1

        parent = matches[0]
        assert len(parent.children) == 2

        group1, group2 = parent.children

        assert isinstance(group1, Match)
        assert group1.pattern == pattern
        assert group1.span == (12, 20)
        assert group1.value == "really contains"

        assert isinstance(group2, Match)
        assert group2.pattern == pattern
        assert group2.span == (21, 25)
        assert group2.value == 1849 * 2

    def test_repeated_captures_option(self) -> None:
        pattern = RePattern(r"\[(\d+)\](?:-(\d+))*")

        matches = cast("list[Match]", list(pattern.matches("[02]-03-04-05-06")))
        assert len(matches) == 1

        match = matches[0]
        if REGEX_ENABLED:
            assert len(match.children) == 5
            assert [child.value for child in match.children] == ["02", "03", "04", "05", "06"]
        else:
            assert len(match.children) == 2
            assert [child.value for child in match.children] == ["02", "06"]

            with pytest.raises(NotImplementedError):
                RePattern(r"\[(\d+)\](?:-(\d+))*", repeated_captures=True)

        pattern = RePattern(r"\[(\d+)\](?:-(\d+))*", repeated_captures=False)

        matches = cast("list[Match]", list(pattern.matches("[02]-03-04-05-06")))
        assert len(matches) == 1

        match = matches[0]
        assert len(match.children) == 2
        assert [child.value for child in match.children] == ["02", "06"]

    def test_single_functional(self) -> None:
        def digit(input_string: str) -> Any:
            i = input_string.find("1849")
            if i > -1:
                return i, i + len("1849")
            return None

        pattern = FunctionalPattern(digit, formatter=lambda x: int(x) * 3)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1
        assert isinstance(matches[0], Match)
        assert matches[0].pattern == pattern
        assert matches[0].span == (21, 25)
        assert matches[0].value == 1849 * 3


class TestValidator:
    """
    Tests for validator option
    """

    input_string = "This string contains 1849 a number"

    @staticmethod
    def true_validator(match: Match) -> bool:
        return int(match.value) < 1850

    @staticmethod
    def false_validator(match: Match) -> bool:
        return int(match.value) >= 1850

    def test_single_string(self) -> None:
        pattern = StringPattern("1849", name="dummy", validator=self.false_validator)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 0

        pattern = StringPattern("1849", validator=self.true_validator)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1

    def test_single_re_no_group(self) -> None:
        pattern = RePattern(r"\d+", validator=self.false_validator)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 0

        pattern = RePattern(r"\d+", validator=self.true_validator)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1

    def test_single_re_named_groups(self) -> None:
        pattern = RePattern(
            r"(?P<strParam>cont.?ins)\s+(?P<intParam>\d+)",
            validator={"intParam": self.false_validator},
            validate_all=True,
        )

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 0

        pattern = RePattern(
            r"(?P<strParam>cont.?ins)\s+(?P<intParam>\d+)",
            validator={"intParam": self.true_validator},
            validate_all=True,
        )

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1

    def test_validate_all(self) -> None:
        pattern = RePattern(
            r"contains (?P<intParam>\d+)", formatter=int, validator=lambda match: match.value < 100, children=True
        )

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 0

        pattern = RePattern(
            r"contains (?P<intParam>\d+)", formatter=int, validator=lambda match: match.value > 100, children=True
        )

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1

        def invalid_func(match: Match) -> bool:
            if match.name == "intParam":
                return True
            return bool(match.value.startswith("abc"))

        pattern = RePattern(
            r"contains (?P<intParam>\d+)", formatter=int, validator=invalid_func, validate_all=True, children=True
        )

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 0

        def func(match: Match) -> bool:
            if match.name == "intParam":
                return True
            return bool(match.value.startswith("contains"))

        pattern = RePattern(
            r"contains (?P<intParam>\d+)", formatter=int, validator=func, validate_all=True, children=True
        )

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1

    def test_format_all(self) -> None:
        pattern = RePattern(r"contains (?P<intParam>\d+)", formatter=int, children=True)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1
        for match in matches:
            assert match.value is not None

        with pytest.raises(ValueError):  # noqa: PT011, PT012
            pattern = RePattern(r"contains (?P<intParam>\d+)", formatter=int, format_all=True)
            matches = cast("list[Match]", list(pattern.matches(self.input_string)))
            for match in matches:
                assert match.value is not None

    def test_single_functional(self) -> None:
        def digit(input_string: str) -> Any:
            i = input_string.find("1849")
            if i > -1:
                return i, i + len("1849")
            return None

        pattern = FunctionalPattern(digit, validator=self.false_validator)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 0

        pattern = FunctionalPattern(digit, validator=self.true_validator)

        matches = cast("list[Match]", list(pattern.matches(self.input_string)))
        assert len(matches) == 1

#!/usr/bin/env python
import pytest

from rebulk.test.default_rules_module import (
    RuleAppend0,
    RuleAppend1,
    RuleAppend2,
    RuleAppend3,
    RuleAppendTags0,
    RuleAppendTags1,
    RuleRemove0,
    RuleRemove1,
    RuleRemoveTags0,
    RuleRemoveTags1,
    RuleRename0,
    RuleRename1,
    RuleRename2,
    RuleRename3,
)

from ..match import Match, Matches
from ..rules import Rules
from . import rules_module as rm
from .rules_module import Rule0, Rule1, Rule1Disabled, Rule2, Rule3


def test_rule_priority() -> None:
    matches = Matches([Match(1, 2)])

    rules = Rules(Rule1, Rule2())

    rules.execute_all_rules(matches, {})
    assert len(matches) == 0
    matches = Matches([Match(1, 2)])

    rules = Rules(Rule1(), Rule0)

    rules.execute_all_rules(matches, {})
    assert len(matches) == 1
    assert matches[0] == Match(3, 4)


def test_rules_duplicates() -> None:
    matches = Matches([Match(1, 2)])

    rules = Rules(Rule1, Rule1)

    with pytest.raises(ValueError):  # noqa: PT011
        rules.execute_all_rules(matches, {})


def test_rule_disabled() -> None:
    matches = Matches([Match(1, 2)])

    rules = Rules(Rule1Disabled(), Rule2())

    rules.execute_all_rules(matches, {})
    assert len(matches) == 2
    assert matches[0] == Match(1, 2)
    assert matches[1] == Match(3, 4)


def test_rule_when() -> None:
    matches = Matches([Match(1, 2)])

    rules = Rules(Rule3())

    rules.execute_all_rules(matches, {"when": False})
    assert len(matches) == 1
    assert matches[0] == Match(1, 2)

    matches = Matches([Match(1, 2)])

    rules.execute_all_rules(matches, {"when": True})
    assert len(matches) == 2
    assert matches[0] == Match(1, 2)
    assert matches[1] == Match(3, 4)


class TestDefaultRules:
    def test_remove(self) -> None:
        rules = Rules(RuleRemove0)

        matches = Matches([Match(1, 2)])
        rules.execute_all_rules(matches, {})

        assert len(matches) == 0

        rules = Rules(RuleRemove1)

        matches = Matches([Match(1, 2)])
        rules.execute_all_rules(matches, {})

        assert len(matches) == 0

    def test_append(self) -> None:
        rules = Rules(RuleAppend0)

        matches = Matches([Match(1, 2)])
        rules.execute_all_rules(matches, {})

        assert len(matches) == 2

        rules = Rules(RuleAppend1)

        matches = Matches([Match(1, 2)])
        rules.execute_all_rules(matches, {})

        assert len(matches) == 2

        rules = Rules(RuleAppend2)

        matches = Matches([Match(1, 2)])
        rules.execute_all_rules(matches, {})

        assert len(matches) == 2
        assert len(matches.named("renamed")) == 1

        rules = Rules(RuleAppend3)

        matches = Matches([Match(1, 2)])
        rules.execute_all_rules(matches, {})

        assert len(matches) == 2
        assert len(matches.named("renamed")) == 1

    def test_rename(self) -> None:
        rules = Rules(RuleRename0)

        matches = Matches([Match(1, 2, name="original")])
        rules.execute_all_rules(matches, {})

        assert len(matches.named("original")) == 1
        assert len(matches.named("renamed")) == 0

        rules = Rules(RuleRename1)

        matches = Matches([Match(5, 10, name="original")])
        rules.execute_all_rules(matches, {})

        assert len(matches.named("original")) == 0
        assert len(matches.named("renamed")) == 1

        rules = Rules(RuleRename2)

        matches = Matches([Match(5, 10, name="original")])
        rules.execute_all_rules(matches, {})

        assert len(matches.named("original")) == 0
        assert len(matches.named("renamed")) == 1

        rules = Rules(RuleRename3)

        matches = Matches([Match(5, 10, name="original")])
        rules.execute_all_rules(matches, {})

        assert len(matches.named("original")) == 0
        assert len(matches.named("renamed")) == 1

    def test_append_tags(self) -> None:
        rules = Rules(RuleAppendTags0)

        matches = Matches([Match(1, 2, name="tags", tags=["other"])])
        rules.execute_all_rules(matches, {})

        assert len(matches.named("tags")) == 1
        assert matches.named("tags")[0].tags == ["other", "new-tag"]

        rules = Rules(RuleAppendTags1)

        matches = Matches([Match(1, 2, name="tags", tags=["other"])])
        rules.execute_all_rules(matches, {})

        assert len(matches.named("tags")) == 1
        assert matches.named("tags")[0].tags == ["other", "new-tag"]

    def test_remove_tags(self) -> None:
        rules = Rules(RuleRemoveTags0)

        matches = Matches([Match(1, 2, name="tags", tags=["other", "new-tag"])])
        rules.execute_all_rules(matches, {})

        assert len(matches.named("tags")) == 1
        assert matches.named("tags")[0].tags == ["other"]

        rules = Rules(RuleRemoveTags1)

        matches = Matches([Match(1, 2, name="tags", tags=["other", "new-tag"])])
        rules.execute_all_rules(matches, {})

        assert len(matches.named("tags")) == 1
        assert matches.named("tags")[0].tags == ["other"]


def test_rule_module() -> None:
    rules = Rules(rm)

    matches = Matches([Match(1, 2)])
    rules.execute_all_rules(matches, {})

    assert len(matches) == 1


def test_rule_repr() -> None:
    assert str(Rule0()) == "<Rule0>"
    assert str(Rule1()) == "<Rule1>"
    assert str(Rule2()) == "<Rule2>"
    assert str(Rule1Disabled()) == "<Disabled Rule1>"

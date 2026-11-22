#!/usr/bin/env python
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..match import Match
from ..rules import AppendMatch, AppendTags, RemoveMatch, RemoveTags, RenameMatch, Rule

if TYPE_CHECKING:
    from ..match import Matches


class RuleRemove0(Rule):
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return matches[0]


class RuleAppend0(Rule):
    consequence = AppendMatch()

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return Match(5, 10)


class RuleRename0(Rule):
    consequence = [RenameMatch("renamed")]

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return [Match(5, 10, name="original")]


class RuleRemove1(Rule):
    consequence = [RemoveMatch()]

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return [matches[0]]


class RuleAppend1(Rule):
    consequence = [AppendMatch]

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return [Match(5, 10)]


class RuleRename1(Rule):
    consequence = RenameMatch("renamed")

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return [Match(5, 10, name="original")]


class RuleAppend2(Rule):
    consequence = [AppendMatch("renamed")]
    properties = {"renamed": [None]}

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return [Match(5, 10)]


class RuleRename2(Rule):
    consequence = RenameMatch("renamed")

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return Match(5, 10, name="original")


class RuleAppend3(Rule):
    consequence = AppendMatch("renamed")
    properties = {"renamed": [None]}

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return [Match(5, 10)]


class RuleRename3(Rule):
    consequence = [RenameMatch("renamed")]

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return Match(5, 10, name="original")


class RuleAppendTags0(Rule):
    consequence = AppendTags(["new-tag"])

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return matches.named("tags", 0)


class RuleRemoveTags0(Rule):
    consequence = RemoveTags(["new-tag"])

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return matches.named("tags", 0)


class RuleAppendTags1(Rule):
    consequence = AppendTags(["new-tag"])

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return matches.named("tags")


class RuleRemoveTags1(Rule):
    consequence = RemoveTags(["new-tag"])

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return matches.named("tags")

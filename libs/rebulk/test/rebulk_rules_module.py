#!/usr/bin/env python
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rebulk.rules import CustomRule, RemoveMatch, Rule

if TYPE_CHECKING:
    from rebulk.match import Matches


class RemoveAllButLastYear(Rule):
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        entries = matches.named("year")
        return entries[:-1]


class PrefixedSuffixedYear(CustomRule):
    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        toRemove = []
        years = matches.named("year")
        for year in years:
            if not matches.previous(year, lambda p: p.name == "yearPrefix") and not matches.next(
                year, lambda n: n.name == "yearSuffix"
            ):
                toRemove.append(year)
        return toRemove

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> Any:
        for to_remove in when_response:
            matches.remove(to_remove)


class PrefixedSuffixedYearNoLambda(Rule):
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        toRemove = []
        years = matches.named("year")
        for year in years:
            if not [m for m in matches.previous(year) if m.name == "yearPrefix"] and not [
                m for m in matches.next(year) if m.name == "yearSuffix"
            ]:
                toRemove.append(year)
        return toRemove

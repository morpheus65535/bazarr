#!/usr/bin/env python
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..match import Match
from ..rules import Rule

if TYPE_CHECKING:
    from ..match import Matches


class Rule3(Rule):
    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return context.get("when")  # type: ignore[union-attr]

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> Any:
        assert when_response in [True, False]
        matches.append(Match(3, 4))


class Rule2(Rule):
    dependency = Rule3

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return True

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> Any:
        assert when_response
        matches.append(Match(3, 4))


class Rule1(Rule):
    dependency = Rule2

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return True

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> Any:
        assert when_response
        matches.clear()


class Rule0(Rule):
    dependency = Rule1

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return True

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> Any:
        assert when_response
        matches.append(Match(3, 4))


class Rule1Disabled(Rule1):
    name = "Disabled Rule1"

    def enabled(self, context: dict[str, Any] | None) -> bool:
        return False

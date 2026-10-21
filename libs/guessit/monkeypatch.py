#!/usr/bin/env python
"""
Monkeypatch initialisation functions
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from rebulk.match import Match


def monkeypatch_rebulk() -> None:
    """Monkeypatch rebulk classes"""

    @property  # type: ignore[misc]
    def match_advanced(self: Match) -> OrderedDict[str, Any]:
        """
        Build advanced dict from match
        :param self:
        :return:
        """

        ret: OrderedDict[str, Any] = OrderedDict()
        ret["value"] = self.value
        if self.raw:
            ret["raw"] = self.raw
        ret["start"] = self.start
        ret["end"] = self.end
        return ret

    Match.advanced = match_advanced  # type: ignore[attr-defined]

    # Defend against shared-list mutation: a config pattern declaring a list value
    # (e.g. edition "ultimate-collector'?s?-edition" -> ["Ultimate", "Collector"])
    # hands the *same* list object to every match. Matches.to_dict aliases that
    # list into its result and appends sibling values to it in place, which mutates
    # the shared config list and leaks into later guesses. Returning a fresh copy
    # of list values keeps the config immutable. See guessit-io/guessit#822.
    _rebulk_value = Match.value  # the original property (preserves formatter logic)

    def value_getter(self: Match) -> Any:
        value = _rebulk_value.fget(self)  # type: ignore[attr-defined]
        return list(value) if isinstance(value, list) else value

    Match.value = property(  # type: ignore[method-assign,assignment]
        value_getter,
        _rebulk_value.fset,  # type: ignore[attr-defined]
        _rebulk_value.fdel,  # type: ignore[attr-defined]
    )

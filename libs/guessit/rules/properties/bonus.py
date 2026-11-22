#!/usr/bin/env python
"""
bonus property
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rebulk import AppendMatch, Rebulk, Rule
from rebulk.remodule import re

from ...config import load_config_patterns
from ..common.formatters import cleanup
from ..common.keys import BONUS
from ..common.pattern import is_disabled
from .title import TitleFromPosition

if TYPE_CHECKING:
    from rebulk.match import Matches


def bonus(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, "bonus"))
    rebulk = rebulk.regex_defaults(name="bonus", flags=re.IGNORECASE)
    rebulk.declare_keys(BONUS)

    load_config_patterns(rebulk, config.get("bonus"))

    rebulk.rules(BonusTitleRule)

    return rebulk


class BonusTitleRule(Rule):
    """
    Find bonus title after bonus.
    """

    dependency = TitleFromPosition
    consequence = AppendMatch

    properties = {"bonus_title": [None]}

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        bonus_number = matches.named("bonus", lambda match: not match.private, index=0)
        if bonus_number:
            filepath = matches.markers.at_match(bonus_number, lambda marker: marker.name == "path", 0)
            if filepath:
                hole = matches.holes(bonus_number.end, filepath.end + 1, formatter=cleanup, index=0)
                if hole and hole.value:
                    hole.name = "bonus_title"
                    return hole
        return None

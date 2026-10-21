#!/usr/bin/env python
"""
part property
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rebulk import Rebulk
from rebulk.remodule import re

from ...reutils import build_or_pattern
from ..common import dash
from ..common.numeral import numeral, parse_numeral
from ..common.pattern import is_disabled
from ..common.validators import and_, int_coercable, seps_surround

if TYPE_CHECKING:
    from rebulk.match import Match


def part(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, "part"))
    rebulk.regex_defaults(flags=re.IGNORECASE, abbreviations=[dash], validator={"__parent__": seps_surround})

    prefixes = config["prefixes"]

    def validate_roman(match: Match) -> bool:
        """
        Validate a roman match if surrounded by separators
        :param match:
        :type match:
        :return:
        :rtype:
        """
        if match.raw is not None and int_coercable(match.raw):
            return True
        return bool(seps_surround(match))

    rebulk.regex(
        build_or_pattern(prefixes) + r"-?(?P<part>" + numeral + r")",
        prefixes=prefixes,
        validate_all=True,
        private_parent=True,
        children=True,
        formatter=parse_numeral,
        validator={"part": and_(validate_roman, lambda m: 0 < m.value < 100)},
    )

    return rebulk

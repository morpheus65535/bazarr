#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
part property
"""
from rebulk.remodule import re

from rebulk import Rebulk
from ..common import dash
from ..common.validators import seps_surround, int_coercable, compose
from ..common.numeral import numeral, parse_numeral
from ...reutils import build_or_pattern


def part():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash], validator={'__parent__': seps_surround})

    prefixes = ['pt', 'part']

    def validate_roman(match):
        """
        Validate a roman match if surrounded by separators
        :param match:
        :type match:
        :return:
        :rtype:
        """
        if int_coercable(match.raw):
            return True
        return seps_surround(match)

    rebulk.regex(build_or_pattern(prefixes) + r'-?(?P<part>' + numeral + r')',
                 prefixes=prefixes, validate_all=True, private_parent=True, children=True, formatter=parse_numeral,
                 validator={'part': compose(validate_roman, lambda m: 0 < m.value < 100)})

    return rebulk

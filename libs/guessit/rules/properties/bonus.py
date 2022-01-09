#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
bonus property
"""
from rebulk import Rebulk, AppendMatch, Rule
from rebulk.remodule import re

from .title import TitleFromPosition
from ..common.formatters import cleanup
from ..common.pattern import is_disabled
from ...config import load_config_patterns


def bonus(config):  # pylint:disable=unused-argument
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, 'bonus'))
    rebulk = rebulk.regex_defaults(name='bonus', flags=re.IGNORECASE)

    load_config_patterns(rebulk, config.get('bonus'))

    rebulk.rules(BonusTitleRule)

    return rebulk


class BonusTitleRule(Rule):
    """
    Find bonus title after bonus.
    """
    dependency = TitleFromPosition
    consequence = AppendMatch

    properties = {'bonus_title': [None]}

    def when(self, matches, context):  # pylint:disable=inconsistent-return-statements
        bonus_number = matches.named('bonus', lambda match: not match.private, index=0)
        if bonus_number:
            filepath = matches.markers.at_match(bonus_number, lambda marker: marker.name == 'path', 0)
            hole = matches.holes(bonus_number.end, filepath.end + 1, formatter=cleanup, index=0)
            if hole and hole.value:
                hole.name = 'bonus_title'
                return hole

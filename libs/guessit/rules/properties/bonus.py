#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
bonus property
"""
from rebulk.remodule import re

from rebulk import Rebulk, AppendMatch, Rule

from .title import TitleFromPosition
from ..common.formatters import cleanup
from ..common.pattern import is_disabled
from ..common.validators import seps_surround


def bonus(config):  # pylint:disable=unused-argument
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, 'bonus'))
    rebulk = rebulk.regex_defaults(flags=re.IGNORECASE)

    rebulk.regex(r'x(\d+)', name='bonus', private_parent=True, children=True, formatter=int,
                 validator={'__parent__': lambda match: seps_surround},
                 conflict_solver=lambda match, conflicting: match
                 if conflicting.name in ('video_codec', 'episode') and 'weak-episode' not in conflicting.tags
                 else '__default__')

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

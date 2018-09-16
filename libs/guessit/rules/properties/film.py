#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
film property
"""
from rebulk import Rebulk, AppendMatch, Rule
from rebulk.remodule import re

from ..common.formatters import cleanup
from ..common.pattern import is_disabled
from ..common.validators import seps_surround


def film(config):  # pylint:disable=unused-argument
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, validate_all=True, validator={'__parent__': seps_surround})

    rebulk.regex(r'f(\d{1,2})', name='film', private_parent=True, children=True, formatter=int,
                 disabled=lambda context: is_disabled(context, 'film'))

    rebulk.rules(FilmTitleRule)

    return rebulk


class FilmTitleRule(Rule):
    """
    Rule to find out film_title (hole after film property
    """
    consequence = AppendMatch

    properties = {'film_title': [None]}

    def enabled(self, context):
        return not is_disabled(context, 'film_title')

    def when(self, matches, context):  # pylint:disable=inconsistent-return-statements
        bonus_number = matches.named('film', lambda match: not match.private, index=0)
        if bonus_number:
            filepath = matches.markers.at_match(bonus_number, lambda marker: marker.name == 'path', 0)
            hole = matches.holes(filepath.start, bonus_number.start + 1, formatter=cleanup, index=0)
            if hole and hole.value:
                hole.name = 'film_title'
                return hole

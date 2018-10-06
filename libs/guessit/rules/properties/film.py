#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
film property
"""
from rebulk import Rebulk, AppendMatch, Rule
from rebulk.remodule import re

from ..common.formatters import cleanup
from ..common.validators import seps_surround


def film():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, validate_all=True, validator={'__parent__': seps_surround})

    rebulk.regex(r'f(\d{1,2})', name='film', private_parent=True, children=True, formatter=int)

    rebulk.rules(FilmTitleRule)

    return rebulk


class FilmTitleRule(Rule):
    """
    Rule to find out film_title (hole after film property
    """
    consequence = AppendMatch

    properties = {'film_title': [None]}

    def when(self, matches, context):
        bonus_number = matches.named('film', lambda match: not match.private, index=0)
        if bonus_number:
            filepath = matches.markers.at_match(bonus_number, lambda marker: marker.name == 'path', 0)
            hole = matches.holes(filepath.start, bonus_number.start + 1, formatter=cleanup, index=0)
            if hole and hole.value:
                hole.name = 'film_title'
                return hole

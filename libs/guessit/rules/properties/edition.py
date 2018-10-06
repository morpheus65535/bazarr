#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
edition property
"""
from rebulk.remodule import re

from rebulk import Rebulk
from ..common import dash
from ..common.validators import seps_surround


def edition():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash]).string_defaults(ignore_case=True)
    rebulk.defaults(name='edition', validator=seps_surround)

    rebulk.regex('collector', 'collector-edition', 'edition-collector', value='Collector Edition')
    rebulk.regex('special-edition', 'edition-special', value='Special Edition',
                 conflict_solver=lambda match, other: other
                 if other.name == 'episode_details' and other.value == 'Special'
                 else '__default__')
    rebulk.string('se', value='Special Edition', tags='has-neighbor')
    rebulk.regex('criterion-edition', 'edition-criterion', value='Criterion Edition')
    rebulk.regex('deluxe', 'deluxe-edition', 'edition-deluxe', value='Deluxe Edition')
    rebulk.regex('limited', 'limited-edition', value='Limited Edition', tags=['has-neighbor', 'release-group-prefix'])
    rebulk.regex(r'theatrical-cut', r'theatrical-edition', r'theatrical', value='Theatrical Edition')
    rebulk.regex(r"director'?s?-cut", r"director'?s?-cut-edition", r"edition-director'?s?-cut", 'DC',
                 value="Director's Cut")
    rebulk.regex('extended', 'extended-?cut', 'extended-?version',
                 value='Extended', tags=['has-neighbor', 'release-group-prefix'])
    rebulk.regex('alternat(e|ive)(?:-?Cut)?', value='Alternative Cut', tags=['has-neighbor', 'release-group-prefix'])
    for value in ('Remastered', 'Uncensored', 'Uncut', 'Unrated'):
        rebulk.string(value, value=value, tags=['has-neighbor', 'release-group-prefix'])
    rebulk.string('Festival', value='Festival', tags=['has-neighbor-before', 'has-neighbor-after'])

    return rebulk

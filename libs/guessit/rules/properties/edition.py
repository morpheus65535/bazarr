#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
edition property
"""
from rebulk.remodule import re

from rebulk import Rebulk
from ..common import dash
from ..common.pattern import is_disabled
from ..common.validators import seps_surround


def edition(config):  # pylint:disable=unused-argument
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, 'edition'))
    rebulk = rebulk.regex_defaults(flags=re.IGNORECASE, abbreviations=[dash]).string_defaults(ignore_case=True)
    rebulk.defaults(name='edition', validator=seps_surround)

    rebulk.regex('collector', "collector'?s?-edition", 'edition-collector', value='Collector')
    rebulk.regex('special-edition', 'edition-special', value='Special',
                 conflict_solver=lambda match, other: other
                 if other.name == 'episode_details' and other.value == 'Special'
                 else '__default__')
    rebulk.string('se', value='Special', tags='has-neighbor')
    rebulk.string('ddc', value="Director's Definitive Cut")
    rebulk.regex('criterion-edition', 'edition-criterion', 'CC', value='Criterion')
    rebulk.regex('deluxe', 'deluxe-edition', 'edition-deluxe', value='Deluxe')
    rebulk.regex('limited', 'limited-edition', value='Limited', tags=['has-neighbor', 'release-group-prefix'])
    rebulk.regex(r'theatrical-cut', r'theatrical-edition', r'theatrical', value='Theatrical')
    rebulk.regex(r"director'?s?-cut", r"director'?s?-cut-edition", r"edition-director'?s?-cut", 'DC',
                 value="Director's Cut")
    rebulk.regex('extended', 'extended-?cut', 'extended-?version',
                 value='Extended', tags=['has-neighbor', 'release-group-prefix'])
    rebulk.regex('alternat(e|ive)(?:-?Cut)?', value='Alternative Cut', tags=['has-neighbor', 'release-group-prefix'])
    for value in ('Remastered', 'Uncensored', 'Uncut', 'Unrated'):
        rebulk.string(value, value=value, tags=['has-neighbor', 'release-group-prefix'])
    rebulk.string('Festival', value='Festival', tags=['has-neighbor-before', 'has-neighbor-after'])
    rebulk.regex('imax', 'imax-edition', value='IMAX')
    rebulk.regex('fan-edit(?:ion)?', 'fan-collection', value='Fan')
    rebulk.regex('ultimate-edition', value='Ultimate')
    rebulk.regex("ultimate-collector'?s?-edition", value=['Ultimate', 'Collector'])
    rebulk.regex('ultimate-fan-edit(?:ion)?', 'ultimate-fan-collection', value=['Ultimate', 'Fan'])

    return rebulk

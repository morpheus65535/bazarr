#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
cd and cd_count properties
"""
from rebulk.remodule import re

from rebulk import Rebulk
from ..common import dash


def cds():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash])

    rebulk.regex(r'cd-?(?P<cd>\d+)(?:-?of-?(?P<cd_count>\d+))?',
                 validator={'cd': lambda match: 0 < match.value < 100,
                            'cd_count': lambda match: 0 < match.value < 100},
                 formatter={'cd': int, 'cd_count': int},
                 children=True,
                 private_parent=True,
                 properties={'cd': [None], 'cd_count': [None]})
    rebulk.regex(r'(?P<cd_count>\d+)-?cds?',
                 validator={'cd': lambda match: 0 < match.value < 100,
                            'cd_count': lambda match: 0 < match.value < 100},
                 formatter={'cd_count': int},
                 children=True,
                 private_parent=True,
                 properties={'cd': [None], 'cd_count': [None]})

    return rebulk

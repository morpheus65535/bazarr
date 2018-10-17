#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
size property
"""
import re

from rebulk import Rebulk

from ..common.validators import seps_surround
from ..common import dash


def size():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """

    def format_size(value):
        """Format size using uppercase and no space."""
        return re.sub(r'(?<=\d)[.](?=[^\d])', '', value.upper())

    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash])
    rebulk.defaults(name='size', validator=seps_surround)
    rebulk.regex(r'\d+\.?[mgt]b', r'\d+\.\d+[mgt]b', formatter=format_size, tags=['release-group-prefix'])

    return rebulk

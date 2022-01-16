#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
edition property
"""
from rebulk import Rebulk
from rebulk.remodule import re

from ..common import dash
from ..common.pattern import is_disabled
from ..common.validators import seps_surround
from ...config import load_config_patterns


def edition(config):  # pylint:disable=unused-argument
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, 'edition'))
    rebulk.regex_defaults(flags=re.IGNORECASE, abbreviations=[dash]).string_defaults(ignore_case=True)
    rebulk.defaults(name='edition', validator=seps_surround)

    load_config_patterns(rebulk, config.get('edition'))

    return rebulk

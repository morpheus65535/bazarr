#!/usr/bin/env python
"""
edition property
"""

from __future__ import annotations

from typing import Any

from rebulk import Rebulk
from rebulk.remodule import re

from ...config import load_config_patterns
from ..common import dash
from ..common.pattern import is_disabled
from ..common.validators import seps_surround


def edition(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, "edition"))
    rebulk.regex_defaults(flags=re.IGNORECASE, abbreviations=[dash]).string_defaults(ignore_case=True)
    rebulk.defaults(name="edition", validator=seps_surround)

    load_config_patterns(rebulk, config.get("edition"))

    return rebulk

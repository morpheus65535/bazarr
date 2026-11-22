#!/usr/bin/env python
"""
volume property
"""

from __future__ import annotations

import re
from typing import Any

from rebulk import Rebulk

from ..common.keys import VOLUME
from ..common.pattern import is_disabled
from ..common.validators import seps_surround


def volume(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, "volume"))
    rebulk = rebulk.regex_defaults(flags=re.IGNORECASE)

    # Match the whole "vol…N" token (so it is excluded from the title) and extract
    # the number: either the short marker glued to digits ("vol127") or any marker
    # followed by a separator ("vol.3", "vol 3", "volume 12"). "volume1" (full word
    # glued, as in the NAS path "/volume1/") is intentionally NOT matched.
    rebulk.regex(
        r"vol(?:\d{1,3}|(?:ume)?[-. ]\d{1,3})",
        key=VOLUME,
        validator=seps_surround,
    )

    return rebulk

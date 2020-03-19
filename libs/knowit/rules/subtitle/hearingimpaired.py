# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from ...rule import Rule


class HearingImpairedRule(Rule):
    """Hearing Impaired rule."""

    hi_re = re.compile(r'(\bsdh\b)', re.IGNORECASE)

    def execute(self, props, pv_props, context):
        """Hearing Impaired."""
        name = props.get('name')
        if name and self.hi_re.search(name):
            return True

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from ...rule import Rule


class ClosedCaptionRule(Rule):
    """Closed caption rule."""

    cc_re = re.compile(r'(\bcc\d\b)', re.IGNORECASE)

    def execute(self, props, pv_props, context):
        """Execute closed caption rule."""
        for name in (pv_props.get('_closed_caption'), props.get('name')):
            if name and self.cc_re.search(name):
                return True

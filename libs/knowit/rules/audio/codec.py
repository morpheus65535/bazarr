# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ...rule import Rule


class AudioCodecRule(Rule):
    """Audio Codec rule."""

    def execute(self, props, pv_props, context):
        """Execute the rule against properties."""
        if '_codec' in pv_props:
            return pv_props.get('_codec')

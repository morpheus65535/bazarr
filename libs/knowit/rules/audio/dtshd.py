# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ...rule import Rule


class DtsHdRule(Rule):
    """DTS-HD rule."""

    @classmethod
    def _redefine(cls, props, name, index):
        actual = props.get(name)
        if isinstance(actual, list):
            value = actual[index]
            if value is None:
                del props[name]
            else:
                props[name] = value

    def execute(self, props, pv_props, context):
        """Execute the rule against properties."""
        if props.get('codec') == 'DTS-HD':
            index = None
            for i, profile in enumerate(props.get('profile', [])):
                if profile and profile.upper() != 'CORE':
                    index = i
                    break

            if index is not None:
                for name in ('profile', 'channels_count', 'bit_rate',
                             'bit_rate_mode', 'sampling_rate', 'compression'):
                    self._redefine(props, name, index)

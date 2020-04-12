# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ...rule import Rule


class AtmosRule(Rule):
    """Atmos rule."""

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
        codecs = props.get('codec') or []
        # TODO: handle this properly
        if 'atmos' in {codec.lower() for codec in codecs if codec}:
            index = None
            for i, codec in enumerate(codecs):
                if codec and 'atmos' in codec.lower():
                    index = i
                    break

            if index is not None:
                for name in ('channels_count', 'sampling_rate'):
                    self._redefine(props, name, index)

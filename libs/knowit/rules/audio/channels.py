# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from logging import NullHandler, getLogger
from six import text_type

from ...rule import Rule

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class AudioChannelsRule(Rule):
    """Audio Channel rule."""

    mapping = {
        1: '1.0',
        2: '2.0',
        6: '5.1',
        8: '7.1',
    }

    def execute(self, props, pv_props, context):
        """Execute the rule against properties."""
        count = props.get('channels_count')
        if count is None:
            return

        channels = self.mapping.get(count) if isinstance(count, int) else None
        positions = pv_props.get('channel_positions') or []
        positions = positions if isinstance(positions, list) else [positions]
        candidate = 0
        for position in positions:
            if not position:
                continue

            c = 0
            for i in position.split('/'):
                try:
                    c += float(i)
                except ValueError:
                    logger.debug('Invalid %s: %s', self.description, i)
                    pass

            c_count = int(c) + int(round((c - int(c)) * 10))
            if c_count == count:
                return text_type(c)

            candidate = max(candidate, c)

        if channels:
            return channels

        if candidate:
            return text_type(candidate)

        self.report(positions, context)

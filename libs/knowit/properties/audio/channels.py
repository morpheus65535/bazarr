# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six import text_type

from ...property import Property


class AudioChannels(Property):
    """Audio Channels property."""

    ignored = {
        'object based',  # Dolby Atmos
    }

    def handle(self, value, context):
        """Handle audio channels."""
        if isinstance(value, int):
            return value

        v = text_type(value).lower()
        if v not in self.ignored:
            try:
                return int(v)
            except ValueError:
                self.report(value, context)

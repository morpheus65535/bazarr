# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from datetime import timedelta

from six import text_type

from ..property import Property


class Duration(Property):
    """Duration property."""

    duration_re = re.compile(r'(?P<hours>\d{1,2}):'
                             r'(?P<minutes>\d{1,2}):'
                             r'(?P<seconds>\d{1,2})(?:\.'
                             r'(?P<millis>\d{3})'
                             r'(?P<micro>\d{3})?\d*)?')

    def handle(self, value, context):
        """Return duration as timedelta."""
        if isinstance(value, timedelta):
            return value
        elif isinstance(value, int):
            return timedelta(milliseconds=value)
        try:
            return timedelta(milliseconds=int(float(value)))
        except ValueError:
            pass

        try:
            h, m, s, ms, mc = self.duration_re.match(text_type(value)).groups('0')
            return timedelta(hours=int(h), minutes=int(m), seconds=int(s), milliseconds=int(ms), microseconds=int(mc))
        except ValueError:
            pass

        self.report(value, context)

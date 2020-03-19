# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from six import text_type

from ...property import Property


class Ratio(Property):
    """Ratio property."""

    def __init__(self, name, unit=None, **kwargs):
        """Constructor."""
        super(Ratio, self).__init__(name, **kwargs)
        self.unit = unit

    ratio_re = re.compile(r'(?P<width>\d+)[:/](?P<height>\d+)')

    def handle(self, value, context):
        """Handle ratio."""
        match = self.ratio_re.match(text_type(value))
        if match:
            width, height = match.groups()
            if (width, height) == ('0', '1'):  # identity
                return 1.

            result = round(float(width) / float(height), 3)
            if self.unit:
                result *= self.unit

            return result

        self.report(value, context)

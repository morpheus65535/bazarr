# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from logging import NullHandler, getLogger

from six import text_type

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class Reportable(object):
    """Reportable abstract class."""

    def __init__(self, name, description=None, reportable=True):
        """Constructor."""
        self.name = name
        self._description = description
        self.reportable = reportable

    @property
    def description(self):
        """Rule description."""
        return self._description or self.name

    def report(self, value, context):
        """Report unknown value."""
        if not value or not self.reportable:
            return

        value = text_type(value)
        if 'report' in context:
            report_map = context['report'].setdefault(self.description, {})
            if value not in report_map:
                report_map[value] = context['path']
        logger.info('Invalid %s: %r', self.description, value)

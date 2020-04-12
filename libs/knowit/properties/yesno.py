# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six import text_type

from ..property import Property


class YesNo(Property):
    """Yes or No handler."""

    mapping = ('yes', 'true', '1')

    def __init__(self, name, yes=True, no=False, hide_value=None, **kwargs):
        """Init method."""
        super(YesNo, self).__init__(name, **kwargs)
        self.yes = yes
        self.no = no
        self.hide_value = hide_value

    def handle(self, value, context):
        """Handle boolean values."""
        v = text_type(value).lower()
        result = self.yes if v in self.mapping else self.no
        return result if result != self.hide_value else None

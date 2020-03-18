# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import babelfish

from ..property import Property


class Language(Property):
    """Language property."""

    def handle(self, value, context):
        """Handle languages."""
        try:
            if len(value) == 3:
                return babelfish.Language.fromalpha3b(value)

            return babelfish.Language.fromietf(value)
        except (babelfish.Error, ValueError):
            pass

        try:
            return babelfish.Language.fromname(value)
        except babelfish.Error:
            pass

        self.report(value, context)
        return babelfish.Language('und')

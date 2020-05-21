#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JSON Utils
"""
import json

from six import text_type
from rebulk.match import Match

class GuessitEncoder(json.JSONEncoder):
    """
    JSON Encoder for guessit response
    """

    def default(self, o):  # pylint:disable=method-hidden
        if isinstance(o, Match):
            return o.advanced
        if hasattr(o, 'name'):  # Babelfish languages/countries long name
            return text_type(o.name)
        # pragma: no cover
        return text_type(o)

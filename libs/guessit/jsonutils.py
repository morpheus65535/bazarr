#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JSON Utils
"""
import json
try:
    from collections import OrderedDict
except ImportError:  # pragma: no-cover
    from ordereddict import OrderedDict  # pylint:disable=import-error

from rebulk.match import Match


class GuessitEncoder(json.JSONEncoder):
    """
    JSON Encoder for guessit response
    """

    def default(self, o):  # pylint:disable=method-hidden
        if isinstance(o, Match):
            ret = OrderedDict()
            ret['value'] = o.value
            if o.raw:
                ret['raw'] = o.raw
            ret['start'] = o.start
            ret['end'] = o.end
            return ret
        elif hasattr(o, 'name'):  # Babelfish languages/countries long name
            return str(o.name)
        else:  # pragma: no cover
            return str(o)

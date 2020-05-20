#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Monkeypatch initialisation functions
"""

try:
    from collections import OrderedDict
except ImportError:  # pragma: no-cover
    from ordereddict import OrderedDict  # pylint:disable=import-error

from rebulk.match import Match


def monkeypatch_rebulk():
    """Monkeypatch rebulk classes"""

    @property
    def match_advanced(self):
        """
        Build advanced dict from match
        :param self:
        :return:
        """

        ret = OrderedDict()
        ret['value'] = self.value
        if self.raw:
            ret['raw'] = self.raw
        ret['start'] = self.start
        ret['end'] = self.end
        return ret

    Match.advanced = match_advanced

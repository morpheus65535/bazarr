# -*- coding: utf-8 -*-
from babelfish import LanguageReverseConverter

from ..exceptions import ConfigurationError


class TheSubDBConverter(LanguageReverseConverter):
    def __init__(self):
        self.from_thesubdb = {'en': ('eng',), 'es': ('spa',), 'fr': ('fra',), 'it': ('ita',), 'nl': ('nld',),
                              'pl': ('pol',), 'pt': ('por', 'BR'), 'ro': ('ron',), 'sv': ('swe',), 'tr': ('tur',)}
        self.to_thesubdb = {v: k for k, v in self.from_thesubdb.items()}
        self.codes = set(self.from_thesubdb.keys())

    def convert(self, alpha3, country=None, script=None):
        if (alpha3, country) in self.to_thesubdb:
            return self.to_thesubdb[(alpha3, country)]
        if (alpha3,) in self.to_thesubdb:
            return self.to_thesubdb[(alpha3,)]

        raise ConfigurationError('Unsupported language for thesubdb: %s, %s, %s' % (alpha3, country, script))

    def reverse(self, thesubdb):
        if thesubdb in self.from_thesubdb:
            return self.from_thesubdb[thesubdb]

        raise ConfigurationError('Unsupported language code for thesubdb: %s' % thesubdb)

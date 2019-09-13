# -*- coding: utf-8 -*-
from babelfish import LanguageReverseConverter

from ..exceptions import ConfigurationError


class LegendasTVConverter(LanguageReverseConverter):
    def __init__(self):
        self.from_legendastv = {1: ('por', 'BR'), 2: ('eng',), 3: ('spa',), 4: ('fra',), 5: ('deu',), 6: ('jpn',),
                                7: ('dan',), 8: ('nor',), 9: ('swe',), 10: ('por',), 11: ('ara',), 12: ('ces',),
                                13: ('zho',), 14: ('kor',), 15: ('bul',), 16: ('ita',), 17: ('pol',)}
        self.to_legendastv = {v: k for k, v in self.from_legendastv.items()}
        self.codes = set(self.from_legendastv.keys())

    def convert(self, alpha3, country=None, script=None):
        if (alpha3, country) in self.to_legendastv:
            return self.to_legendastv[(alpha3, country)]
        if (alpha3,) in self.to_legendastv:
            return self.to_legendastv[(alpha3,)]

        raise ConfigurationError('Unsupported language code for legendastv: %s, %s, %s' % (alpha3, country, script))

    def reverse(self, legendastv):
        if legendastv in self.from_legendastv:
            return self.from_legendastv[legendastv]

        raise ConfigurationError('Unsupported language number for legendastv: %s' % legendastv)

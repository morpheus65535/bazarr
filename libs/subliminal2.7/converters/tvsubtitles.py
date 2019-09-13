# -*- coding: utf-8 -*-
from babelfish import LanguageReverseConverter, language_converters


class TVsubtitlesConverter(LanguageReverseConverter):
    def __init__(self):
        self.alpha2_converter = language_converters['alpha2']
        self.from_tvsubtitles = {'br': ('por', 'BR'), 'ua': ('ukr',), 'gr': ('ell',), 'cn': ('zho',), 'jp': ('jpn',),
                                 'cz': ('ces',)}
        self.to_tvsubtitles = {v: k for k, v in self.from_tvsubtitles.items()}
        self.codes = self.alpha2_converter.codes | set(self.from_tvsubtitles.keys())

    def convert(self, alpha3, country=None, script=None):
        if (alpha3, country) in self.to_tvsubtitles:
            return self.to_tvsubtitles[(alpha3, country)]
        if (alpha3,) in self.to_tvsubtitles:
            return self.to_tvsubtitles[(alpha3,)]

        return self.alpha2_converter.convert(alpha3, country, script)

    def reverse(self, tvsubtitles):
        if tvsubtitles in self.from_tvsubtitles:
            return self.from_tvsubtitles[tvsubtitles]

        return self.alpha2_converter.reverse(tvsubtitles)

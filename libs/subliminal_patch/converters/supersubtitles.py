# -*- coding: utf-8 -*-
from babelfish import LanguageReverseConverter, language_converters


class SuperSubtitlesConverter(LanguageReverseConverter):
    def __init__(self):
        self.alpha2_converter = language_converters['alpha2']
        self.from_supersubtitles = {'hu': ('hun', ), 'en': ('eng',)}
        self.to_supersubtitles = {v: k for k, v in self.from_supersubtitles.items()}
        self.codes = self.alpha2_converter.codes | set(self.from_supersubtitles.keys())

    def convert(self, alpha3, country=None, script=None):
        if (alpha3, country) in self.to_supersubtitles:
            return self.to_supersubtitles[(alpha3, country)]
        if (alpha3,) in self.to_supersubtitles:
            return self.to_supersubtitles[(alpha3,)]

        return self.alpha2_converter.convert(alpha3, country, script)

    def reverse(self, supersubtitles):
        if supersubtitles in self.from_supersubtitles:
            return self.from_supersubtitles[supersubtitles]

        return self.alpha2_converter.reverse(supersubtitles)

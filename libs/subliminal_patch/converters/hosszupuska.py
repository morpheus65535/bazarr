# -*- coding: utf-8 -*-
from babelfish import LanguageReverseConverter, language_converters


class HosszupuskaConverter(LanguageReverseConverter):
    def __init__(self):
        self.alpha2_converter = language_converters['alpha2']
        self.from_hosszupuska = {'hu': ('hun', ), 'en': ('eng',)}
        self.to_hosszupuska = {v: k for k, v in self.from_hosszupuska.items()}
        self.codes = self.alpha2_converter.codes | set(self.from_hosszupuska.keys())

    def convert(self, alpha3, country=None, script=None):
        if (alpha3, country) in self.to_hosszupuska:
            return self.to_hosszupuska[(alpha3, country)]
        if (alpha3,) in self.to_hosszupuska:
            return self.to_hosszupuska[(alpha3,)]

        return self.alpha2_converter.convert(alpha3, country, script)

    def reverse(self, hosszupuska):
        if hosszupuska in self.from_hosszupuska:
            return self.from_hosszupuska[hosszupuska]

        return self.alpha2_converter.reverse(hosszupuska)

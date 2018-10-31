# coding=utf-8
import logging

from babelfish import LanguageReverseConverter
from subliminal.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class TitloviConverter(LanguageReverseConverter):
    def __init__(self):
        self.from_titlovi = {'Bosanski': ('bos',),
                             'English': ('eng',),
                             'Hrvatski': ('hrv',),
                             'Makedonski': ('mkd',),
                             'Srpski': ('srp',),
                             'Cirilica': ('srp', None, 'Cyrl'),
                             'Slovenski': ('slv',),
                             }
        self.to_titlovi = {('bos',): 'Bosanski',
                           ('eng',): 'English',
                           ('hrv',): 'Hrvatski',
                           ('mkd',): 'Makedonski',
                           ('srp',): 'Srpski',
                           ('srp', None, 'Cyrl'): 'Cirilica',
                           ('slv',): 'Slovenski'
                           }
        self.codes = set(self.from_titlovi.keys())

        # temporary fix, should be removed as soon as API is used
        self.lang_from_countrycode = {'ba': ('bos',),
                                 'en': ('eng',),
                                 'hr': ('hrv',),
                                 'mk': ('mkd',),
                                 'rs': ('srp',),
                                 'rsc': ('srp', None, 'Cyrl'),
                                 'si': ('slv',)
                                 }

    def convert(self, alpha3, country=None, script=None):
        if (alpha3, country, script) in self.to_titlovi:
            return self.to_titlovi[(alpha3, country, script)]
        if (alpha3,) in self.to_titlovi:
            return self.to_titlovi[(alpha3,)]

        raise ConfigurationError('Unsupported language code for titlovi: %s, %s, %s' % (alpha3, country, script))

    def reverse(self, titlovi):
        if titlovi in self.from_titlovi:
            return self.from_titlovi[titlovi]

        # temporary fix, should be removed as soon as API is used
        if titlovi in self.lang_from_countrycode:
            return self.lang_from_countrycode[titlovi]

        raise ConfigurationError('Unsupported language number for titlovi: %s' % titlovi)


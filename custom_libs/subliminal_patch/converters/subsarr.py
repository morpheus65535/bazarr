# coding=utf-8
from __future__ import absolute_import
import logging

from babelfish import LanguageReverseConverter
from subliminal.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class SubsarrConverter(LanguageReverseConverter):
    """Language converter for subsarr's lowercase/slugified language names."""

    def __init__(self):
        self.from_subsarr = {
            'english': ('eng',),
            'arabic': ('ara',),
            'farsi_persian': ('fas',),
            'indonesian': ('ind',),
            'french': ('fra',),
            'vietnamese': ('vie',),
            'danish': ('dan',),
            'italian': ('ita',),
            'spanish': ('spa',),
            'brazillian-portuguese': ('por', 'BR'),
            'swedish': ('swe',),
            'norwegian': ('nor',),
            'korean': ('kor',),
            'turkish': ('tur',),
            'dutch': ('nld',),
            'finnish': ('fin',),
            'malay': ('msa',),
            'hebrew': ('heb',),
            'thai': ('tha',),
            'chinese-bg-code': ('zho',),
            'portuguese': ('por',),
            'greek': ('ell',),
            'romanian': ('ron',),
            'german': ('deu',),
            'czech': ('ces',),
            'polish': ('pol',),
            'japanese': ('jpn',),
            'bengali': ('ben',),
            'russian': ('rus',),
            'bulgarian': ('bul',),
            'croatian': ('hrv',),
            'hungarian': ('hun',),
            'serbian': ('srp',),
            'sinhala': ('sin',),
            'slovak': ('slk',),
            'ukranian': ('ukr',),
            'burmese': ('mya',),
            'slovenian': ('slv',),
            'hindi': ('hin',),
            'icelandic': ('isl',),
            'estonian': ('est',),
            'malayalam': ('mal',),
            'urdu': ('urd',),
            'tamil': ('tam',),
            'telugu': ('tel',),
            'lithuanian': ('lit',),
            'tagalog': ('tgl',),
            'albanian': ('sqi',),
            'cambodian-khmer': ('khm',),
            'latvian': ('lav',),
            'kurdish': ('kur',),
            'macedonian': ('mkd',),
            'bosnian': ('bos',),
            'catalan': ('cat',),
            'nepali': ('nep',),
            'basque': ('eus',),
            'swahili': ('swa',),
            'pashto': ('pus',),
            'kannada': ('kan',),
            'mongolian': ('mon',),
            'azerbaijani': ('aze',),
            'armenian': ('hye',),
            'esperanto': ('epo',),
            'belarusian': ('bel',),
            'georgian': ('kat',),
            'somali': ('som',),
            'punjabi': ('pan',),
            'kinyarwanda': ('kin',),
            'yoruba': ('yor',),
            'sundanese': ('sun',),
            'afrikaans': ('afr',),
        }
        self.to_subsarr = {v: k for k, v in self.from_subsarr.items()}
        self.codes = set(self.from_subsarr.keys())

    def convert(self, alpha3, country=None, script=None):
        if (alpha3, country, script) in self.to_subsarr:
            return self.to_subsarr[(alpha3, country, script)]
        if country and (alpha3, country) in self.to_subsarr:
            return self.to_subsarr[(alpha3, country)]
        if (alpha3,) in self.to_subsarr:
            return self.to_subsarr[(alpha3,)]

        raise ConfigurationError('Unsupported language code for subsarr: %s, %s, %s' % (alpha3, country, script))

    def reverse(self, subsarr):
        if subsarr in self.from_subsarr:
            return self.from_subsarr[subsarr]

        raise ConfigurationError('Unsupported language name for subsarr: %s' % subsarr)

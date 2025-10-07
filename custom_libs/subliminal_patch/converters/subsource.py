# coding=utf-8
from __future__ import absolute_import
import logging

from babelfish import LanguageReverseConverter
from subliminal.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class SubsourceConverter(LanguageReverseConverter):
    def __init__(self):
        self.from_subsource = {'English': ('eng',),
                               'Farsi/Persian': ('fas',),
                               'Abkhazian': ('abk',),
                               'Afrikaans': ('afr',),
                               'Albanian': ('sqi',),
                               'Amharic': ('amh',),
                               'Arabic': ('ara',),
                               'Aragonese': ('arg',),
                               'Armenian': ('hye',),
                               'Assamese': ('asm',),
                               # 'Asturian': ('',),  # no alpha_2 so unsupported by Bazarr
                               'Azerbaijani': ('aze',),
                               'Basque': ('eus',),
                               'Belarusian': ('bel',),
                               'Bengali': ('ben',),
                               # 'Big 5 code': (''),
                               'Bosnian': ('bos',),
                               'Brazillian Portuguese': ('por', 'BR'),
                               'Breton': ('bre',),
                               'Bulgarian': ('bul',),
                               'Burmese': ('mya',),
                               'Catalan': ('cat',),
                               # 'Chinese': ('',),
                               # 'Chinese (Cantonese)': ('',),
                               # 'Chinese (Simplified)': ('zho', 'CN'),  # we'll have to parse subtitles commentary to get this
                               # 'Chinese (Traditional)': ('zho', 'TW'),  # we'll have to parse subtitles commentary to get this
                               'Chinese BG code': ('zho',),  # all Chinese subtitles seem to be uploaded using this language name
                               # 'Chinese Bilingual': ('',),
                               'Croatian': ('hrv',),
                               'Czech': ('ces',),
                               'Danish': ('dan',),
                               # 'Dari': ('',),  # no alpha_2 so unsupported by Bazarr
                               'Dutch': ('nld',),
                               'Espranto': ('epo',),
                               'Estonian': ('est',),
                               # 'Extremaduran': ('',),  # no alpha_2 so unsupported by Bazarr
                               'Finnish': ('fin',),
                               'French': ('fra',),
                               # 'French (Canada)': ('',),  # all French variations are considered the same
                               # 'French (France)': ('',),  # all French variations are considered the same
                               'Gaelic': ('gla',),
                               # 'Gaelician': ('',),  # unknown language in pycountry.languages
                               'Georgian': ('kat',),
                               'German': ('deu',),
                               'Greek': ('ell',),
                               # 'Greenlandic': ('',),  # unknown language in pycountry.languages
                               'Hebrew': ('heb',),
                               'Hindi': ('hin',),
                               'Hungarian': ('hun',),
                               'Icelandic': ('isl',),
                               'Igbo': ('ibo',),
                               'Indonesian': ('ind',),
                               'Interlingua': ('ina',),
                               'Irish': ('gle',),
                               'Italian': ('ita',),
                               'Japanese': ('jpn',),
                               'Kannada': ('kan',),
                               'Kazakh': ('kaz',),
                               'Khmer': ('khm',),
                               'Korean': ('kor',),
                               'Kurdish': ('kur',),
                               # 'Kyrgyz': ('',),  # unknown language in pycountry.languages
                               'Latvian': ('lav',),
                               'Lithuanian': ('lit',),
                               'Luxembourgish': ('ltz',),
                               'Macedonian': ('mkd',),
                               'Malay': ('msa',),
                               'Malayalam': ('mal',),
                               # 'Manipuri': ('',),  # no alpha_2 so unsupported by Bazarr
                               'Marathi': ('mar',),
                               'Mongolian': ('mon',),
                               # 'Montenegrin': ('',),  # no alpha_2 so unsupported by Bazarr
                               'Navajo': ('nav',),
                               'Nepali': ('nep',),
                               'Northen Sami': ('sme',),
                               'Norwegian': ('nor',),
                               'Occitan': ('oci',),
                               # 'Odia': ('',),  # no alpha_2 so unsupported by Bazarr
                               # 'Pashto': ('',),  # unknown language in pycountry.languages
                               'Polish': ('pol',),
                               'Portuguese': ('por',),
                               'Pushto': ('pus',),
                               'Romanian': ('ron',),
                               'Russian': ('rus',),
                               # 'Santli': ('',),  # unknown language in pycountry.languages
                               'Serbian': ('srp',),
                               'Sindhi': ('snd',),
                               'Sinhala': ('sin',),
                               # 'Sinhalese': ('',),  # unknown language in pycountry.languages
                               'Slovak': ('slk',),
                               'Slovenian': ('slv',),
                               'Somali': ('som',),
                               # 'Sorbian': ('',),  # unknown language in pycountry.languages
                               'Spanish': ('spa',),
                               # 'Spanish (Latin America)': ('spa', 'MX'),  # we'll have to parse subtitles commentary to get this
                               # 'Spanish (Spain)': ('spa',),  # we'll have to parse subtitles commentary to get this
                               'Swahili': ('swa',),
                               'Swedish': ('swe',),
                               # 'Syriac': ('',),  # no alpha_2 so unsupported by Bazarr
                               'Tagalog': ('tgl',),
                               'Tamil': ('tam',),
                               'Tatar': ('tat',),
                               'Telugu': ('tel',),
                               # 'Tetum': ('',),  # no alpha_2 so unsupported by Bazarr
                               'Thai': ('tha',),
                               # 'Toki Pona': ('',),  # no alpha_2 so unsupported by Bazarr
                               'Turkish': ('tur',),
                               'Turkmen': ('tuk',),
                               'Ukrainian': ('ukr',),
                               'Urdu': ('urd',),
                               'Uzbek': ('uzb',),
                               'Vietnamese': ('vie',),
                               'Welsh': ('cym',),
                               }
        self.to_subsource = {v: k for k, v in self.from_subsource.items()}
        self.codes = set(self.from_subsource.keys())

    def convert(self, alpha3, country=None, script=None):
        if (alpha3, country, script) in self.to_subsource:
            return self.to_subsource[(alpha3, country, script)]
        if (alpha3,) in self.to_subsource:
            return self.to_subsource[(alpha3,)]

        raise ConfigurationError('Unsupported language code for subsource: %s, %s, %s' % (alpha3, country, script))

    def reverse(self, subsource):
        if subsource in self.from_subsource:
            return self.from_subsource[subsource]

        raise ConfigurationError('Unsupported language number for subsource: %s' % subsource)


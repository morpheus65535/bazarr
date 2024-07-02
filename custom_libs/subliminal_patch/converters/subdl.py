# -*- coding: utf-8 -*-
from __future__ import absolute_import
from babelfish import LanguageReverseConverter
from subliminal.exceptions import ConfigurationError


class SubdlConverter(LanguageReverseConverter):
    def __init__(self):
        self.from_subdl = {
            "AR": ("ara", None, None),  # Arabic
            "DA": ("dan", None, None),  # Danish
            "NL": ("nld", None, None),  # Dutch
            "EN": ("eng", None, None),  # English
            "FA": ("fas", None, None),  # Farsi_Persian
            "FI": ("fin", None, None),  # Finnish
            "FR": ("fra", None, None),  # French
            "ID": ("ind", None, None),  # Indonesian
            "IT": ("ita", None, None),  # Italian
            "NO": ("nor", None, None),  # Norwegian
            "RO": ("ron", None, None),  # Romanian
            "ES": ("spa", None, None),  # Spanish
            "SV": ("swe", None, None),  # Swedish
            "VI": ("vie", None, None),  # Vietnamese
            "SQ": ("sqi", None, None),  # Albanian
            "AZ": ("aze", None, None),  # Azerbaijani
            "BE": ("bel", None, None),  # Belarusian
            "BN": ("ben", None, None),  # Bengali
            "BS": ("bos", None, None),  # Bosnian
            "BG": ("bul", None, None),  # Bulgarian
            "MY": ("mya", None, None),  # Burmese
            "CA": ("cat", None, None),  # Catalan
            "ZH": ("zho", None, None),  # Chinese BG code
            "HR": ("hrv", None, None),  # Croatian
            "CS": ("ces", None, None),  # Czech
            "EO": ("epo", None, None),  # Esperanto
            "ET": ("est", None, None),  # Estonian
            "KA": ("kat", None, None),  # Georgian
            "DE": ("deu", None, None),  # German
            "EL": ("ell", None, None),  # Greek
            "KL": ("kal", None, None),  # Greenlandic
            "HE": ("heb", None, None),  # Hebrew
            "HI": ("hin", None, None),  # Hindi
            "HU": ("hun", None, None),  # Hungarian
            "IS": ("isl", None, None),  # Icelandic
            "JA": ("jpn", None, None),  # Japanese
            "KO": ("kor", None, None),  # Korean
            "KU": ("kur", None, None),  # Kurdish
            "LV": ("lav", None, None),  # Latvian
            "LT": ("lit", None, None),  # Lithuanian
            "MK": ("mkd", None, None),  # Macedonian
            "MS": ("msa", None, None),  # Malay
            "ML": ("mal", None, None),  # Malayalam
            "PL": ("pol", None, None),  # Polish
            "PT": ("por", None, None),  # Portuguese
            "RU": ("rus", None, None),  # Russian
            "SR": ("srp", None, None),  # Serbian
            "SI": ("sin", None, None),  # Sinhala
            "SK": ("slk", None, None),  # Slovak
            "SL": ("slv", None, None),  # Slovenian
            "TL": ("tgl", None, None),  # Tagalog
            "TA": ("tam", None, None),  # Tamil
            "TE": ("tel", None, None),  # Telugu
            "TH": ("tha", None, None),  # Thai
            "TR": ("tur", None, None),  # Turkish
            "UK": ("ukr", None, None),  # Ukrainian
            "UR": ("urd", None, None),  # Urdu
            # custom languages
            "BR_PT": ("por", "BR", None),  # Brazilian Portuguese
            "ZH_BG": ("zho", None, "Hant"),  # Big 5 code
            # unsupported language in Bazarr
            # "BG_EN": "Bulgarian_English",
            # "NL_EN": "Dutch_English",
            # "EN_DE": "English_German",
            # "HU_EN": "Hungarian_English",
            # "MNI": "Manipuri",
        }
        self.to_subdl = {v: k for k, v in self.from_subdl.items()}
        self.codes = set(self.from_subdl.keys())

    def convert(self, alpha3, country=None, script=None):
        if (alpha3, country, script) in self.to_subdl:
            return self.to_subdl[(alpha3, country, script)]

        raise ConfigurationError('Unsupported language for subdl: %s, %s, %s' % (alpha3, country, script))

    def reverse(self, subdl):
        if subdl in self.from_subdl:
            return self.from_subdl[subdl]

        raise ConfigurationError('Unsupported language code for subdl: %s' % subdl)

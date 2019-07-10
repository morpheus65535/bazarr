# coding=utf-8

from babelfish import LanguageReverseConverter
from subliminal.exceptions import ConfigurationError
from subzero.language import Language


# alpha3 codes extracted from `https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes`
# Subscene language list extracted from it's upload form
from_subscene = {
        'Farsi/Persian': 'fas', 'Greek': 'ell', 'Greenlandic': 'kal',
        'Malay': 'msa', 'Pashto': 'pus', 'Punjabi': 'pan', 'Swahili': 'swa'
}

from_subscene_with_country = {
    'Brazillian Portuguese': ('por', 'BR')
}

to_subscene_with_country = {val: key for key, val in from_subscene_with_country.items()}


to_subscene = {v: k for k, v in from_subscene.items()}

exact_languages_alpha3 = [
        'ara', 'aze', 'bel', 'ben', 'bos', 'bul', 'cat', 'ces', 'dan', 'deu',
        'eng', 'epo', 'est', 'eus', 'fin', 'fra', 'heb', 'hin', 'hrv', 'hun',
        'hye', 'ind', 'isl', 'ita', 'jpn', 'kat', 'kor', 'kur', 'lav', 'lit',
        'mal', 'mkd', 'mni', 'mon', 'mya', 'nld', 'nor', 'pol', 'por', 'ron',
        'rus', 'sin', 'slk', 'slv', 'som', 'spa', 'sqi', 'srp', 'sun', 'swe',
        'tam', 'tel', 'tgl', 'tha', 'tur', 'ukr', 'urd', 'vie', 'yor'
]

language_ids = {
        'ara':  2, 'dan': 10, 'nld': 11, 'eng': 13, 'fas': 46, 'fin': 17,
        'fra': 18, 'heb': 22, 'ind': 44, 'ita': 26, 'msa': 50, 'nor': 30,
        'ron': 33, 'spa': 38, 'swe': 39, 'vie': 45, 'sqi':  1, 'hye': 73,
        'aze': 55, 'eus': 74, 'bel': 68, 'ben': 54, 'bos': 60, 'bul':  5,
        'mya': 61, 'cat': 49, 'hrv':  8, 'ces':  9, 'epo': 47, 'est': 16,
        'kat': 62, 'deu': 19, 'ell': 21, 'kal': 57, 'hin': 51, 'hun': 23,
        'isl': 25, 'jpn': 27, 'kor': 28, 'kur': 52, 'lav': 29, 'lit': 43,
        'mkd': 48, 'mal': 64, 'mni': 65, 'mon': 72, 'pus': 67, 'pol': 31,
        'por': 32, 'pan': 66, 'rus': 34, 'srp': 35, 'sin': 58, 'slk': 36,
        'slv': 37, 'som': 70, 'tgl': 53, 'tam': 59, 'tel': 63, 'tha': 40,
        'tur': 41, 'ukr': 56, 'urd': 42, 'yor': 71, 'pt-BR': 4
}

# TODO: specify codes for unspecified_languages
unspecified_languages = [
        'Big 5 code', 'Bulgarian/ English',
        'Chinese BG code', 'Dutch/ English', 'English/ German',
        'Hungarian/ English', 'Rohingya'
]

supported_languages = {Language(l) for l in exact_languages_alpha3}

alpha3_of_code = {l.name: l.alpha3 for l in supported_languages}

supported_languages.update({Language(l) for l in to_subscene})

supported_languages.update({Language(lang, cr) for lang, cr in to_subscene_with_country})


class SubsceneConverter(LanguageReverseConverter):
    codes = {l.name for l in supported_languages}

    def convert(self, alpha3, country=None, script=None):
        if alpha3 in exact_languages_alpha3:
            return Language(alpha3).name

        if alpha3 in to_subscene:
            return to_subscene[alpha3]

        if (alpha3, country) in to_subscene_with_country:
            return to_subscene_with_country[(alpha3, country)]

        raise ConfigurationError('Unsupported language for subscene: %s, %s, %s' % (alpha3, country, script))

    def reverse(self, code):
        if code in from_subscene_with_country:
            return from_subscene_with_country[code]

        if code in from_subscene:
            return (from_subscene[code],)

        if code in alpha3_of_code:
            return (alpha3_of_code[code],)

        if code in unspecified_languages:
            raise NotImplementedError("currently this language is unspecified: %s" % code)

        raise ConfigurationError('Unsupported language code for subscene: %s' % code)
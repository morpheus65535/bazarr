import requests

BASE_URLS = {
    "GOOGLE_TRANSLATE": "https://translate.google.com/m",
    "PONS": "https://en.pons.com/translate/",
    "YANDEX": "https://translate.yandex.net/api/{version}/tr.json/{endpoint}",
    "LINGUEE": "https://www.linguee.com/",
    "MYMEMORY": "http://api.mymemory.translated.net/get",
    "QCRI": "https://mt.qcri.org/api/v1/{endpoint}?",
    "DEEPL": "https://api.deepl.com/{version}/",
    "DEEPL_FREE": "https://api-free.deepl.com/v2/",
    "MICROSOFT_TRANSLATE": "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0",
    "PAPAGO": "https://papago.naver.com/",
    "PAPAGO_API": "https://openapi.naver.com/v1/papago/n2mt",
    "LIBRE": "https://libretranslate.com/",
    "LIBRE_FREE": "https://libretranslate.de/",
}

GOOGLE_CODES_TO_LANGUAGES = {
    'af': 'afrikaans',
    'sq': 'albanian',
    'am': 'amharic',
    'ar': 'arabic',
    'hy': 'armenian',
    'az': 'azerbaijani',
    'eu': 'basque',
    'be': 'belarusian',
    'bn': 'bengali',
    'bs': 'bosnian',
    'bg': 'bulgarian',
    'ca': 'catalan',
    'ceb': 'cebuano',
    'ny': 'chichewa',
    'zh-CN': 'chinese (simplified)',
    'zh-TW': 'chinese (traditional)',
    'co': 'corsican',
    'hr': 'croatian',
    'cs': 'czech',
    'da': 'danish',
    'nl': 'dutch',
    'en': 'english',
    'eo': 'esperanto',
    'et': 'estonian',
    'tl': 'filipino',
    'fi': 'finnish',
    'fr': 'french',
    'fy': 'frisian',
    'gl': 'galician',
    'ka': 'georgian',
    'de': 'german',
    'el': 'greek',
    'gu': 'gujarati',
    'ht': 'haitian creole',
    'ha': 'hausa',
    'haw': 'hawaiian',
    'iw': 'hebrew',
    'hi': 'hindi',
    'hmn': 'hmong',
    'hu': 'hungarian',
    'is': 'icelandic',
    'ig': 'igbo',
    'id': 'indonesian',
    'ga': 'irish',
    'it': 'italian',
    'ja': 'japanese',
    'jw': 'javanese',
    'kn': 'kannada',
    'kk': 'kazakh',
    'km': 'khmer',
    'rw': 'kinyarwanda',
    'ko': 'korean',
    'ku': 'kurdish',
    'ky': 'kyrgyz',
    'lo': 'lao',
    'la': 'latin',
    'lv': 'latvian',
    'lt': 'lithuanian',
    'lb': 'luxembourgish',
    'mk': 'macedonian',
    'mg': 'malagasy',
    'ms': 'malay',
    'ml': 'malayalam',
    'mt': 'maltese',
    'mi': 'maori',
    'mr': 'marathi',
    'mn': 'mongolian',
    'my': 'myanmar',
    'ne': 'nepali',
    'no': 'norwegian',
    'or': 'odia',
    'ps': 'pashto',
    'fa': 'persian',
    'pl': 'polish',
    'pt': 'portuguese',
    'pa': 'punjabi',
    'ro': 'romanian',
    'ru': 'russian',
    'sm': 'samoan',
    'gd': 'scots gaelic',
    'sr': 'serbian',
    'st': 'sesotho',
    'sn': 'shona',
    'sd': 'sindhi',
    'si': 'sinhala',
    'sk': 'slovak',
    'sl': 'slovenian',
    'so': 'somali',
    'es': 'spanish',
    'su': 'sundanese',
    'sw': 'swahili',
    'sv': 'swedish',
    'tg': 'tajik',
    'ta': 'tamil',
    'tt': 'tatar',
    'te': 'telugu',
    'th': 'thai',
    'tr': 'turkish',
    'tk': 'turkmen',
    'uk': 'ukrainian',
    'ur': 'urdu',
    'ug': 'uyghur',
    'uz': 'uzbek',
    'vi': 'vietnamese',
    'cy': 'welsh',
    'xh': 'xhosa',
    'yi': 'yiddish',
    'yo': 'yoruba',
    'zu': 'zulu',
}

GOOGLE_LANGUAGES_TO_CODES = {v: k for k, v in GOOGLE_CODES_TO_LANGUAGES.items()}

# This dictionary maps the primary name of language to its secondary names in list manner (if any)
GOOGLE_LANGUAGES_SECONDARY_NAMES = {
    'myanmar': ['burmese'],
    'odia': ['oriya'],
    'kurdish':  ['kurmanji']
}


PONS_CODES_TO_LANGUAGES = {
    'ar': 'arabic',
    'bg': 'bulgarian',
    'zh-cn': 'chinese',
    'cs': 'czech',
    'da': 'danish',
    'nl': 'dutch',
    'en': 'english',
    'fr': 'french',
    'de': 'german',
    'el': 'greek',
    'hu': 'hungarian',
    'it': 'italian',
    'la': 'latin',
    'no': 'norwegian',
    'pl': 'polish',
    'pt': 'portuguese',
    'ru': 'russian',
    'sl': 'slovenian',
    'es': 'spanish',
    'sv': 'swedish',
    'tr': 'turkish',
    'elv': 'elvish'
}

PONS_LANGUAGES_TO_CODES = {v: k for k, v in PONS_CODES_TO_LANGUAGES.items()}

LINGUEE_LANGUAGES_TO_CODES = {
    "maltese": "mt",
    "english": "en",
    "german": "de",
    "bulgarian": "bg",
    "polish": "pl",
    "portuguese": "pt",
    "hungarian": "hu",
    "romanian": "ro",
    "russian": "ru",
    # "serbian": "sr",
    "dutch": "nl",
    "slovakian": "sk",
    "greek": "el",
    "slovenian": "sl",
    "danish": "da",
    "italian": "it",
    "spanish": "es",
    "finnish": "fi",
    "chinese": "zh",
    "french": "fr",
    # "croatian": "hr",
    "czech": "cs",
    "laotian": "lo",
    "swedish": "sv",
    "latvian": "lv",
    "estonian": "et",
    "japanese": "ja"
}

LINGUEE_CODE_TO_LANGUAGE = {v: k for k, v in LINGUEE_LANGUAGES_TO_CODES.items()}

# "72e9e2cc7c992db4dcbdd6fb9f91a0d1"

# obtaining the current list of supported Microsoft languages for translation

microsoft_languages_api_url = "https://api.cognitive.microsofttranslator.com/languages?api-version=3.0&scope=translation"
microsoft_languages_response = requests.get(microsoft_languages_api_url)
translation_dict = microsoft_languages_response.json()['translation']

MICROSOFT_CODES_TO_LANGUAGES = {translation_dict[k]['name'].lower(): k for k in translation_dict.keys()}

DEEPL_LANGUAGE_TO_CODE = {
    "bulgarian": "bg",
    "czech": "cs",
    "danish": "da",
    "german": "de",
    "greek": "el",
    "english": "en",
    "spanish": "es",
    "estonian": "et",
    "finnish": "fi",
    "french": "fr",
    "hungarian": "hu",
    "italian": "it",
    "japanese": "ja",
    "lithuanian": "lt",
    "latvian": "lv",
    "dutch": "nl",
    "polish": "pl",
    "portuguese": "pt",
    "romanian": "ro",
    "russian": "ru",
    "slovak": "sk",
    "slovenian": "sl",
    "swedish": "sv",
    "chinese": "zh"
}

DEEPL_CODE_TO_LANGUAGE = {v: k for k, v in DEEPL_LANGUAGE_TO_CODE.items()}

PAPAGO_CODE_TO_LANGUAGE = {
    'ko': 'Korean',
    'en': 'English',
    'ja': 'Japanese',
    'zh-CN': 'Chinese',
    'zh-TW': 'Chinese traditional',
    'es': 'Spanish',
    'fr': 'French',
    'vi': 'Vietnamese',
    'th': 'Thai',
    'id': 'Indonesia'
}

PAPAGO_LANGUAGE_TO_CODE = {v: k for v, k in PAPAGO_CODE_TO_LANGUAGE.items()}

QCRI_CODE_TO_LANGUAGE = {
    'ar': 'Arabic',
    'en': 'English',
    'es': 'Spanish'
}

QCRI_LANGUAGE_TO_CODE = {
    v: k for k, v in QCRI_CODE_TO_LANGUAGE.items()
}

LIBRE_CODES_TO_LANGUAGES = {
    'en': 'English',
    'ar': 'Arabic',
    'zh': 'Chinese',
    'fr': 'French',
    'de': 'German',
    'hi': 'Hindi',
    'id': 'Indonesian',
    'ga': 'Irish',
    'it': 'Italian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'es': 'Spanish',
    'tr': 'Turkish',
    'vi': 'Vietnamese'
}

LIBRE_LANGUAGES_TO_CODES = {
    v: k for k, v in LIBRE_CODES_TO_LANGUAGES.items()
}

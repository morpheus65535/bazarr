"""Guess the natural language of a text
"""
#   © 2012 spirit <hiddenspirit@gmail.com>
#   https://bitbucket.org/spirit/guess_language
#
#   Original Python package:
#   Copyright (c) 2008, Kent S Johnson
#   http://code.google.com/p/guess-language/
#
#   Original C++ version for KDE:
#   Copyright (c) 2006 Jacob R Rideout <kde@jacobrideout.net>
#   http://websvn.kde.org/branches/work/sonnet-refactoring/common/nlp/guesslanguage.cpp?view=markup
#
#   Original Language::Guess Perl module:
#   Copyright (c) 2004-2006 Maciej Ceglowski
#   http://web.archive.org/web/20090228163219/http://languid.cantbedone.org/
#
#   Note: Language::Guess is GPL-licensed. KDE developers received permission
#   from the author to distribute their port under LGPL:
#   http://lists.kde.org/?l=kde-sonnet&m=116910092228811&w=2
#
#   This program is free software: you can redistribute it and/or modify it
#   under the terms of the GNU Lesser General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#   See the GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with this program. If not, see <http://www.gnu.org/licenses/>.

import functools
import re
import warnings

from collections import defaultdict, OrderedDict

from .data import BLOCKS, BLOCK_RSHIFT


__all__ = [
    "guess_language", "use_enchant",
]

MAX_LENGTH = 4096
MIN_LENGTH = 20
MAX_GRAMS = 300
WORD_RE = re.compile(r"(?:[^\W\d_]|['’])+", re.U)
MODEL_ROOT = __name__ + ".data.models."
FALLBACK_LANGUAGE = "en_US"

BASIC_LATIN = {
    "ceb", "en", "eu", "ha", "haw", "id", "la", "nr", "nso", "so", "ss", "st",
    "sw", "tlh", "tn", "ts", "xh", "zu"
}
EXTENDED_LATIN = {
    "af", "az", "ca", "cs", "cy", "da", "de", "eo", "es", "et", "fi", "fr",
    "hr", "hu", "is", "it", "lt", "lv", "nb", "nl", "pl", "pt", "ro", "sk",
    "sl", "sq", "sv", "tl", "tr", "ve", "vi"
}
ALL_LATIN = BASIC_LATIN.union(EXTENDED_LATIN)
CYRILLIC = {"bg", "kk", "ky", "mk", "mn", "ru", "sr", "uk", "uz"}
ARABIC = {"ar", "fa", "ps", "ur"}
DEVANAGARI = {"hi", "ne"}
PT = {"pt_BR", "pt_PT"}

# NOTE mn appears twice, once for mongolian script and once for CYRILLIC
SINGLETONS = [
    ("Armenian", "hy"),
    ("Hebrew", "he"),
    ("Bengali", "bn"),
    ("Gurmukhi", "pa"),
    ("Greek", "el"),
    ("Gujarati", "gu"),
    ("Oriya", "or"),
    ("Tamil", "ta"),
    ("Telugu", "te"),
    ("Kannada", "kn"),
    ("Malayalam", "ml"),
    ("Sinhala", "si"),
    ("Thai", "th"),
    ("Lao", "lo"),
    ("Tibetan", "bo"),
    ("Burmese", "my"),
    ("Georgian", "ka"),
    ("Mongolian", "mn-Mong"),
    ("Khmer", "km"),
]

NAME_MAP = {
    "ab": "Abkhazian",
    "af": "Afrikaans",
    "ar": "Arabic",
    "az": "Azeri",
    "be": "Byelorussian",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "bo": "Tibetan",
    "br": "Breton",
    "ca": "Catalan",
    "ceb": "Cebuano",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "eo": "Esperanto",
    "es": "Spanish",
    "et": "Estonian",
    "eu": "Basque",
    "fa": "Farsi",
    "fi": "Finnish",
    "fo": "Faroese",
    "fr": "French",
    "fy": "Frisian",
    "gd": "Scots Gaelic",
    "gl": "Galician",
    "gu": "Gujarati",
    "ha": "Hausa",
    "haw": "Hawaiian",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "hu": "Hungarian",
    "hy": "Armenian",
    "id": "Indonesian",
    "is": "Icelandic",
    "it": "Italian",
    "ja": "Japanese",
    "ka": "Georgian",
    "kk": "Kazakh",
    "km": "Cambodian",
    "ko": "Korean",
    "ku": "Kurdish",
    "ky": "Kyrgyz",
    "la": "Latin",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mg": "Malagasy",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mn": "Mongolian",
    "mr": "Marathi",
    "ms": "Malay",
    "nd": "Ndebele",
    "ne": "Nepali",
    "nl": "Dutch",
    "nn": "Nynorsk",
    "no": "Norwegian",
    "nso": "Sepedi",
    "pa": "Punjabi",
    "pl": "Polish",
    "ps": "Pashto",
    "pt": "Portuguese",
    "pt_PT": "Portuguese (Portugal)",
    "pt_BR": "Portuguese (Brazil)",
    "ro": "Romanian",
    "ru": "Russian",
    "sa": "Sanskrit",
    "sh": "Serbo-Croatian",
    "sk": "Slovak",
    "sl": "Slovene",
    "so": "Somali",
    "sq": "Albanian",
    "sr": "Serbian",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tl": "Tagalog",
    "tlh": "Klingon",
    "tn": "Setswana",
    "tr": "Turkish",
    "ts": "Tsonga",
    "tw": "Twi",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "ve": "Venda",
    "vi": "Vietnamese",
    "xh": "Xhosa",
    "zh": "Chinese",
    "zh_TW": "Traditional Chinese (Taiwan)",
    "zu": "Zulu",
}

IANA_MAP = {
    "ab": 12026,
    "af": 40,
    "ar": 26020,
    "az": 26030,
    "be": 11890,
    "bg": 26050,
    "bn": 26040,
    "bo": 26601,
    "br": 1361,
    "ca": 3,
    "ceb": 26060,
    "cs": 26080,
    "cy": 26560,
    "da": 26090,
    "de": 26160,
    "el": 26165,
    "en": 26110,
    "eo": 11933,
    "es": 26460,
    "et": 26120,
    "eu": 1232,
    "fa": 26130,
    "fi": 26140,
    "fo": 11817,
    "fr": 26150,
    "fy": 1353,
    "gd": 65555,
    "gl": 1252,
    "gu": 26599,
    "ha": 26170,
    "haw": 26180,
    "he": 26592,
    "hi": 26190,
    "hr": 26070,
    "hu": 26200,
    "hy": 26597,
    "id": 26220,
    "is": 26210,
    "it": 26230,
    "ja": 26235,
    "ka": 26600,
    "kk": 26240,
    "km": 1222,
    "ko": 26255,
    "ku": 11815,
    "ky": 26260,
    "la": 26280,
    "lt": 26300,
    "lv": 26290,
    "mg": 1362,
    "mk": 26310,
    "ml": 26598,
    "mn": 26320,
    "mr": 1201,
    "ms": 1147,
    "ne": 26330,
    "nl": 26100,
    "nn": 172,
    "no": 26340,
    "pa": 65550,
    "pl": 26380,
    "ps": 26350,
    "pt": 26390,
    "ro": 26400,
    "ru": 26410,
    "sa": 1500,
    "sh": 1399,
    "sk": 26430,
    "sl": 26440,
    "so": 26450,
    "sq": 26010,
    "sr": 26420,
    "sv": 26480,
    "sw": 26470,
    "ta": 26595,
    "te": 26596,
    "th": 26594,
    "tl": 26490,
    "tlh": 26250,
    "tn": 65578,
    "tr": 26500,
    "tw": 1499,
    "uk": 26520,
    "ur": 26530,
    "uz": 26540,
    "vi": 26550,
    "zh": 26065,
    "zh_TW": 22,
}

models = {}

try:
    from importlib import import_module
except ImportError:
    import sys

    def import_module(name):
        """Import a module.
        """
        __import__(name)
        return sys.modules[name]

try:
    from collections import namedtuple

    LanguageInfo = namedtuple("LanguageInfo", ["tag", "id", "name"])
except ImportError:
    class LanguageInfo(tuple):
        def __new__(cls, tag, id, name): #@ReservedAssignment
            return tuple.__new__(cls, (tag, id, name))

        def __init__(self, tag, id, name): #@ReservedAssignment
            self.tag = tag
            self.id = id
            self.name = name


class UNKNOWN(str):
    """Unknown language
    """
    def __bool__(self):
        return False


UNKNOWN = UNKNOWN("UNKNOWN")


def guess_language(text: str, hints=None):
    """Return the ISO 639-1 language code.
    """
    words = WORD_RE.findall(text[:MAX_LENGTH].replace("’", "'"))
    return identify(words, find_runs(words), hints)


def guess_language_info(text: str, hints=None):
    """Return LanguageInfo(tag, id, name).
    """
    tag = guess_language(text, hints)

    if tag is UNKNOWN:
        return LanguageInfo(UNKNOWN, UNKNOWN, UNKNOWN)

    return LanguageInfo(tag, _get_id(tag), _get_name(tag))


# An alias for guess_language
guess_language_tag = guess_language


def guess_language_id(text: str, hints=None):
    """Return the language ID.
    """
    return _get_id(guess_language(text, hints))


def guess_language_name(text: str, hints=None):
    """Return the language name (in English).
    """
    return _get_name(guess_language(text, hints))


def _get_id(tag):
    return IANA_MAP.get(tag, UNKNOWN)


def _get_name(tag):
    return NAME_MAP.get(tag, UNKNOWN)


def find_runs(words):
    """Count the number of characters in each character block.
    """
    run_types = defaultdict(int)

    total_count = 0

    for word in words:
        for char in word:
            block = BLOCKS[ord(char) >> BLOCK_RSHIFT]
            run_types[block] += 1
            total_count += 1

    #pprint(run_types)

    # return run types that used for 40% or more of the string
    # return Basic Latin if found more than 15%
    ## and extended additional latin if over 10% (for Vietnamese)
    relevant_runs = []
    for key, value in run_types.items():
        pct = value * 100 // total_count
        if pct >= 40 or pct >= 15 and key == "Basic Latin":
            relevant_runs.append(key)
        #elif pct >= 10 and key == "Latin Extended Additional":
            #relevant_runs.append(key)

    return relevant_runs


def identify(words, scripts, hints=None):
    """Identify the language.
    """
    if ("Hangul Syllables" in scripts or "Hangul Jamo" in scripts or
            "Hangul Compatibility Jamo" in scripts or "Hangul" in scripts):
        return "ko"

    if "Greek and Coptic" in scripts:
        return "el"

    if "Kana" in scripts:
        return "ja"

    if ("CJK Unified Ideographs" in scripts or "Bopomofo" in scripts or
            "Bopomofo Extended" in scripts or "KangXi Radicals" in scripts):
# This is in both Ceglowski and Rideout
# I can't imagine why...
#            or "Arabic Presentation Forms-A" in scripts
        return "zh"

    if "Cyrillic" in scripts:
        return check(words, filter_languages(CYRILLIC, hints))

    if ("Arabic" in scripts or "Arabic Presentation Forms-A" in scripts or
            "Arabic Presentation Forms-B" in scripts):
        return check(words, filter_languages(ARABIC, hints))

    if "Devanagari" in scripts:
        return check(words, filter_languages(DEVANAGARI, hints))

    # Try languages with unique scripts
    for block_name, lang_name in SINGLETONS:
        if block_name in scripts:
            return lang_name

    #if "Latin Extended Additional" in scripts:
        #return "vi"

    if "Extended Latin" in scripts:
        latin_lang = check(words, filter_languages(EXTENDED_LATIN, hints))
        if latin_lang == "pt":
            return check(words, filter_languages(PT))
        else:
            return latin_lang

    if "Basic Latin" in scripts:
        return check(words, filter_languages(ALL_LATIN, hints))

    return UNKNOWN


def filter_languages(languages, hints=None):
    """Filter languages.
    """
    return languages.intersection(hints) if hints else languages


def check_with_all(words, languages):
    """Check what the best match is.
    """
    return (check_with_enchant(words, languages) or
            check_with_models(words, languages))


check = check_with_all


def use_enchant(use_enchant=True):
    """Enable or disable checking with PyEnchant.
    """
    global check
    check = check_with_all if use_enchant else check_with_models


def check_with_models(words, languages):
    """Check against known models.
    """
    sample = " ".join(words)

    if len(sample) < MIN_LENGTH:
        return UNKNOWN

    scores = []
    model = create_ordered_model(sample)  # QMap<int,QString>

    for key in languages:
        lkey = key.lower()

        try:
            known_model = models[lkey]
        except KeyError:
            try:
                known_model = import_module(MODEL_ROOT + lkey).model
            except ImportError:
                known_model = None
            models[lkey] = known_model

        if known_model:
            scores.append((distance(model, known_model), key))

    if not scores:
        return UNKNOWN

    # we want the lowest score, less distance = greater chance of match
    #pprint(sorted(scores))
    return min(scores)[1]


def create_ordered_model(content):
    """Create a list of trigrams in content sorted by frequency.
    """
    trigrams = defaultdict(int)  # QHash<QString,int>
    content = content.lower()

    for i in range(len(content) - 2):
        trigrams[content[i:i+3]] += 1

    return sorted(trigrams.keys(), key=lambda k: (-trigrams[k], k))


def distance(model, known_model):
    """Calculate the distance to the known model.
    """
    dist = 0

    for i, value in enumerate(model[:MAX_GRAMS]):
        if value in known_model:
            dist += abs(i - known_model[value])
        else:
            dist += MAX_GRAMS

    return dist


try:
    import enchant
except ImportError:
    warnings.warn("PyEnchant is unavailable", ImportWarning)
    enchant = None

    def check_with_enchant(*args, **kwargs):
        return UNKNOWN
else:
    import locale

    enchant_base_languages_dict = None

    def check_with_enchant(words, languages,
                           threshold=0.7, min_words=1, dictionaries={}):
        """Check against installed spelling dictionaries.
        """
        if len(words) < min_words:
            return UNKNOWN

        best_score = 0
        best_tag = UNKNOWN

        for tag, enchant_tag in get_enchant_base_languages_dict().items():
            if tag not in languages:
                continue
            try:
                d = dictionaries[tag]
            except KeyError:
                d = dictionaries[tag] = enchant.Dict(enchant_tag)
            score = sum([1 for word in words if d.check(word)])
            if score > best_score:
                best_score = score
                best_tag = tag

        if best_score / len(words) < threshold:
            return UNKNOWN

        return best_tag

    def get_enchant_base_languages_dict():
        """Get ordered dictionary of enchant base languages.

        locale_language, then "en", then the rest.
        """
        global enchant_base_languages_dict
        if enchant_base_languages_dict is None:
            def get_language_sub_tag(tag):
                return tag.split("_")[0]
            enchant_base_languages_dict = OrderedDict()
            enchant_languages = sorted(enchant.list_languages())
            for full_tag in [get_locale_language(), FALLBACK_LANGUAGE]:
                sub_tag = get_language_sub_tag(full_tag)
                if sub_tag not in enchant_base_languages_dict:
                    for tag in [full_tag, sub_tag]:
                        try:
                            index = enchant_languages.index(tag)
                        except ValueError:
                            pass
                        else:
                            enchant_base_languages_dict[sub_tag] = tag
                            del enchant_languages[index]
                            break
            for tag in enchant_languages:
                sub_tag = get_language_sub_tag(tag)
                if sub_tag not in enchant_base_languages_dict:
                    enchant_base_languages_dict[sub_tag] = tag
        return enchant_base_languages_dict

    def get_locale_language():
        """Get the language code for the current locale setting.
        """
        return (locale.getlocale()[0] or locale.getdefaultlocale()[0] or
                FALLBACK_LANGUAGE)


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.
    """
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.warn(
            "call to deprecated function %s()" % func.__name__,
            category=DeprecationWarning,
            stacklevel=2
        )
        return func(*args, **kwargs)
    return new_func


@deprecated
def guessLanguage(text):
    """Deprecated function - use guess_language() instead.
    """
    return guess_language(decode_text(text))


@deprecated
def guessLanguageTag(text):
    """Deprecated function - use guess_language_tag() instead.
    """
    return guess_language_tag(decode_text(text))


@deprecated
def guessLanguageId(text):
    """Deprecated function - use guess_language_id() instead.
    """
    return guess_language_id(decode_text(text))


@deprecated
def guessLanguageName(text):
    """Deprecated function - use guess_language_name() instead.
    """
    return guess_language_name(decode_text(text))


@deprecated
def guessLanguageInfo(text):
    """Deprecated function - use guess_language_info() instead.
    """
    return guess_language_info(decode_text(text))


def decode_text(text, encoding="utf-8"):
    """Decode text if needed (for deprecated functions).
    """
    if not isinstance(text, str):
        warnings.warn("passing an encoded string is deprecated",
                      DeprecationWarning, 4)
        text = text.decode(encoding)
    return text

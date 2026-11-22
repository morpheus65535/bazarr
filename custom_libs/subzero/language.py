# coding=utf-8
from __future__ import absolute_import
import types
import re

from babelfish.exceptions import LanguageError
from babelfish import Language as Language_, basestr, LANGUAGE_MATRIX
from six.moves import zip

repl_map = {
    "dk": "da",
    "nld": "nl",
    "english": "en",
    "alb": "sq",
    "arm": "hy",
    "baq": "eu",
    "bur": "my",
    "chi": "zh",
    "cze": "cs",
    "dut": "nl",
    "fre": "fr",
    "geo": "ka",
    "ger": "de",
    "gre": "el",
    "ice": "is",
    "mac": "mk",
    "mao": "mi",
    "may": "ms",
    "per": "fa",
    "rum": "ro",
    "slo": "sk",
    "tib": "bo",
}

CUSTOM_LIST = ["chs", "sc", "zhs", "hans", "gb", u"简", u"双语",
               "cht", "tc", "zht", "hant", "big5", u"繁", u"雙語",
               "spl", "ea", "pob", "pb"]

ALPHA2_LIST = list(set(filter(lambda x: x, map(lambda x: x.alpha2, LANGUAGE_MATRIX)))) + list(repl_map.values())
ALPHA3b_LIST = list(set(filter(lambda x: x, map(lambda x: x.alpha3, LANGUAGE_MATRIX)))) + \
               list(set(filter(lambda x: len(x) == 3, list(repl_map.keys()))))
FULL_LANGUAGE_LIST = ALPHA2_LIST + ALPHA3b_LIST
FULL_LANGUAGE_LIST.extend(CUSTOM_LIST)


def language_from_stream(l):
    if not l:
        raise LanguageError()
    for method in ("fromietf", "fromalpha3t", "fromalpha3b"):
        try:
            return getattr(Language, method)(l)
        except (LanguageError, ValueError):
            pass
    raise LanguageError()


def wrap_forced(f):
    def inner(*args, **kwargs):
        """
        classmethod wrapper
        :param args: args[0] = cls
        :param kwargs:
        :return:
        """
        args = list(args)
        cls = args[0]
        args = args[1:]
        s = args.pop(0)
        forced = None
        hi = None
        if isinstance(s, (str,)):
            base, forced = s.split(":") if ":" in s else (s, False)
        else:
            base = s

        instance = f(cls, base, *args, **kwargs)
        if isinstance(instance, Language):
            instance.forced = forced == "forced"
            instance.hi = hi == "hi"
        return instance

    return inner


# UN M.49 numeric region codes (e.g. "419" for Latin America in "es-419") are valid BCP-47 subtags,
# but babelfish reads a 3-digit subtag as a script and rejects it. Codes listed here are rewritten to the
# ISO 3166-1 alpha-2 country Bazarr uses for that region. Codes not listed fall back to the base language.
M49_REGION_TO_COUNTRY = {
    "419": "MX",  # Latin America -> Spanish (Latino), which Bazarr maps to Mexico
}

M49_REGION_FOR_COUNTRY = {country: region for region, country in M49_REGION_TO_COUNTRY.items()}

_M49_TAG_RE = re.compile(r"^([a-z]{2,3})-(\d{3})$")


def _normalize_m49_region(ietf: str) -> str:
    """Rewrite a BCP-47 tag that carries a UN M.49 numeric region into a form babelfish can parse.

    :param str ietf: BCP-47 language tag, e.g. ``es-419`` or ``en-001``.
    :return: the tag with a mapped ISO alpha-2 region, or the base language when the region is unmapped.
    :rtype: str
    """
    match = _M49_TAG_RE.match(ietf.lower())
    if match is None:
        return ietf

    language, region = match.groups()
    country = M49_REGION_TO_COUNTRY.get(region)
    return f"{language}-{country}" if country else language


def m49_basename(language: "Language") -> str:
    """Return the language tag for a filename, using a UN M.49 region when one is mapped for the country.

    :param language: language whose tag is written to a subtitle filename.
    :type language: :class:`Language`
    :return: ``basename`` with the country replaced by its M.49 region (e.g. ``es-419`` for Spanish, Mexico),
        or the unchanged ``basename`` when the country has no mapped region.
    :rtype: str
    """
    basename = str(language.basename)
    country = language.country
    if country is None:
        return basename

    region = M49_REGION_FOR_COUNTRY.get(str(country))
    if region is None:
        return basename

    return f"{basename.split('-')[0]}-{region}"


class Language(Language_):
    forced = False
    hi = False

    def __init__(self, language, country=None, script=None, unknown=None, forced=False, hi=False):
        self.forced = forced
        self.hi = hi
        super(Language, self).__init__(language, country=country, script=script, unknown=unknown)

    def __getstate__(self):
        return self.alpha3, self.country, self.script, self.hi, self.forced

    def __setstate__(self, forced):
        self.alpha3, self.country, self.script, self.hi, self.forced = forced

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if isinstance(other, basestr):
            return str(self) == other
        if not isinstance(other, Language):
            return False
        return (self.alpha3 == other.alpha3 and
                self.country == other.country and
                self.script == other.script and
                bool(self.forced) == bool(other.forced) and
                bool(self.hi) == bool(other.hi))

    def __str__(self):
        return super(Language, self).__str__() + (":forced" if self.forced else "")

    def __repr__(self):
        info = ";".join(f"{k}={v}" for k, v in vars(self).items() if v)
        return f"<{self.__class__.__name__}: {info}>"

    @property
    def basename(self):
        return super(Language, self).__str__()

    def __getattr__(self, name):
        ret = super(Language, self).__getattr__(name)
        if isinstance(ret, Language):
            ret.forced = self.forced
            ret.hi = self.hi
        return ret

    @classmethod
    def rebuild(cls, instance, **replkw):
        state = instance.__getstate__()
        attrs = ("country", "script", "hi", "forced")
        language = state[0]
        kwa = dict(list(zip(attrs, state[1:])))
        kwa.update(replkw)
        return cls(language, **kwa)

    @classmethod
    @wrap_forced
    def fromcode(cls, code, converter):
        return Language(*Language_.fromcode(code, converter).__getstate__())

    @classmethod
    @wrap_forced
    def fromietf(cls, ietf):
        ietf_lower = ietf.lower()
        if ietf_lower in repl_map:
            ietf = repl_map[ietf_lower]

        ietf = _normalize_m49_region(ietf)

        return Language(*Language_.fromietf(ietf).__getstate__())

    @classmethod
    @wrap_forced
    def fromalpha3b(cls, s):
        if s in repl_map:
            s = repl_map[s]
            return Language(*Language_.fromietf(s).__getstate__())

        return Language(*Language_.fromalpha3b(s).__getstate__())


ENDSWITH_LANGUAGECODE_RE = re.compile(r"\.([^-.]{2,3})(?:-[A-Za-z0-9]{2,})?$")

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

ALPHA2_LIST = list(set(filter(lambda x: x, map(lambda x: x.alpha2, LANGUAGE_MATRIX)))) + list(repl_map.values())
ALPHA3b_LIST = list(set(filter(lambda x: x, map(lambda x: x.alpha3, LANGUAGE_MATRIX)))) + \
               list(set(filter(lambda x: len(x) == 3, list(repl_map.keys()))))
FULL_LANGUAGE_LIST = ALPHA2_LIST + ALPHA3b_LIST


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

        return Language(*Language_.fromietf(ietf).__getstate__())

    @classmethod
    @wrap_forced
    def fromalpha3b(cls, s):
        if s in repl_map:
            s = repl_map[s]
            return Language(*Language_.fromietf(s).__getstate__())

        return Language(*Language_.fromalpha3b(s).__getstate__())


IETF_MATCH = ".+\.([^-.]+)(?:-[A-Za-z]+)?$"
ENDSWITH_LANGUAGECODE_RE = re.compile("\.([^-.]{2,3})(?:-[A-Za-z]{2,})?$")


def match_ietf_language(s, ietf=False):
    language_match = re.match(".+\.([^\.]+)$" if not ietf
                              else IETF_MATCH, s)
    if language_match and len(language_match.groups()) == 1:
        language = language_match.groups()[0]
        return language
    return s

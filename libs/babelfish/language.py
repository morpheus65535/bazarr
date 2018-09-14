# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 the BabelFish authors. All rights reserved.
# Use of this source code is governed by the 3-clause BSD license
# that can be found in the LICENSE file.
#
from __future__ import unicode_literals
from collections import namedtuple
from functools import partial
from pkg_resources import resource_stream  # @UnresolvedImport
from .converters import ConverterManager
from .country import Country
from .exceptions import LanguageConvertError
from .script import Script
from . import basestr


LANGUAGES = set()
LANGUAGE_MATRIX = []

#: The namedtuple used in the :data:`LANGUAGE_MATRIX`
IsoLanguage = namedtuple('IsoLanguage', ['alpha3', 'alpha3b', 'alpha3t', 'alpha2', 'scope', 'type', 'name', 'comment'])

f = resource_stream('babelfish', 'data/iso-639-3.tab')
f.readline()
for l in f:
    iso_language = IsoLanguage(*l.decode('utf-8').split('\t'))
    LANGUAGES.add(iso_language.alpha3)
    LANGUAGE_MATRIX.append(iso_language)
f.close()


class LanguageConverterManager(ConverterManager):
    """:class:`~babelfish.converters.ConverterManager` for language converters"""
    entry_point = 'babelfish.language_converters'
    internal_converters = ['alpha2 = babelfish.converters.alpha2:Alpha2Converter',
                           'alpha3b = babelfish.converters.alpha3b:Alpha3BConverter',
                           'alpha3t = babelfish.converters.alpha3t:Alpha3TConverter',
                           'name = babelfish.converters.name:NameConverter',
                           'scope = babelfish.converters.scope:ScopeConverter',
                           'type = babelfish.converters.type:LanguageTypeConverter',
                           'opensubtitles = babelfish.converters.opensubtitles:OpenSubtitlesConverter']

language_converters = LanguageConverterManager()


class LanguageMeta(type):
    """The :class:`Language` metaclass

    Dynamically redirect :meth:`Language.frommycode` to :meth:`Language.fromcode` with the ``mycode`` `converter`

    """
    def __getattr__(cls, name):
        if name.startswith('from'):
            return partial(cls.fromcode, converter=name[4:])
        return type.__getattribute__(cls, name)


class Language(LanguageMeta(str('LanguageBase'), (object,), {})):
    """A human language

    A human language is composed of a language part following the ISO-639
    standard and can be country-specific when a :class:`~babelfish.country.Country`
    is specified.

    The :class:`Language` is extensible with custom converters (see :ref:`custom_converters`)

    :param string language: the language as a 3-letter ISO-639-3 code
    :param country: the country (if any) as a 2-letter ISO-3166 code or :class:`~babelfish.country.Country` instance
    :type country: string or :class:`~babelfish.country.Country` or None
    :param script: the script (if any) as a 4-letter ISO-15924 code or :class:`~babelfish.script.Script` instance
    :type script: string or :class:`~babelfish.script.Script` or None
    :param unknown: the unknown language as a three-letters ISO-639-3 code to use as fallback
    :type unknown: string or None
    :raise: ValueError if the language could not be recognized and `unknown` is ``None``

    """
    def __init__(self, language, country=None, script=None, unknown=None):
        if unknown is not None and language not in LANGUAGES:
            language = unknown
        if language not in LANGUAGES:
            raise ValueError('%r is not a valid language' % language)
        self.alpha3 = language
        self.country = None
        if isinstance(country, Country):
            self.country = country
        elif country is None:
            self.country = None
        else:
            self.country = Country(country)
        self.script = None
        if isinstance(script, Script):
            self.script = script
        elif script is None:
            self.script = None
        else:
            self.script = Script(script)

    @classmethod
    def fromcode(cls, code, converter):
        """Create a :class:`Language` by its `code` using `converter` to
        :meth:`~babelfish.converters.LanguageReverseConverter.reverse` it

        :param string code: the code to reverse
        :param string converter: name of the :class:`~babelfish.converters.LanguageReverseConverter` to use
        :return: the corresponding :class:`Language` instance
        :rtype: :class:`Language`

        """
        return cls(*language_converters[converter].reverse(code))

    @classmethod
    def fromietf(cls, ietf):
        """Create a :class:`Language` by from an IETF language code

        :param string ietf: the ietf code
        :return: the corresponding :class:`Language` instance
        :rtype: :class:`Language`

        """
        subtags = ietf.split('-')
        language_subtag = subtags.pop(0).lower()
        if len(language_subtag) == 2:
            language = cls.fromalpha2(language_subtag)
        else:
            language = cls(language_subtag)
        while subtags:
            subtag = subtags.pop(0)
            if len(subtag) == 2:
                language.country = Country(subtag.upper())
            else:
                language.script = Script(subtag.capitalize())
            if language.script is not None:
                if subtags:
                    raise ValueError('Wrong IETF format. Unmatched subtags: %r' % subtags)
                break
        return language

    def __getstate__(self):
        return self.alpha3, self.country, self.script

    def __setstate__(self, state):
        self.alpha3, self.country, self.script = state

    def __getattr__(self, name):
        alpha3 = self.alpha3
        country = self.country.alpha2 if self.country is not None else None
        script = self.script.code if self.script is not None else None
        try:
            return language_converters[name].convert(alpha3, country, script)
        except KeyError:
            raise AttributeError(name)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if isinstance(other, basestr):
            return str(self) == other
        if not isinstance(other, Language):
            return False
        return (self.alpha3 == other.alpha3 and
                self.country == other.country and
                self.script == other.script)

    def __ne__(self, other):
        return not self == other

    def __bool__(self):
        return self.alpha3 != 'und'
    __nonzero__ = __bool__

    def __repr__(self):
        return '<Language [%s]>' % self

    def __str__(self):
        try:
            s = self.alpha2
        except LanguageConvertError:
            s = self.alpha3
        if self.country is not None:
            s += '-' + str(self.country)
        if self.script is not None:
            s += '-' + str(self.script)
        return s

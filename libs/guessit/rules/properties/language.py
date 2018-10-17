#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
language and subtitle_language properties
"""
# pylint: disable=no-member
import copy
from collections import defaultdict, namedtuple

import babelfish
from rebulk import Rebulk, Rule, RemoveMatch, RenameMatch
from rebulk.remodule import re

from ..common.words import iter_words, COMMON_WORDS
from ..common.validators import seps_surround


def language():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk()

    rebulk.string(*subtitle_prefixes, name="subtitle_language.prefix", ignore_case=True, private=True,
                  validator=seps_surround, tags=['release-group-prefix'])
    rebulk.string(*subtitle_suffixes, name="subtitle_language.suffix", ignore_case=True, private=True,
                  validator=seps_surround)
    rebulk.string(*lang_suffixes, name="language.suffix", ignore_case=True, private=True,
                  validator=seps_surround, tags=['format-suffix'])
    rebulk.functional(find_languages, properties={'language': [None]})
    rebulk.rules(SubtitlePrefixLanguageRule, SubtitleSuffixLanguageRule, SubtitleExtensionRule)

    return rebulk


COMMON_WORDS_STRICT = frozenset(['brazil'])

UNDETERMINED = babelfish.Language('und')

SYN = {('ell', None): ['gr', 'greek'],
       ('spa', None): ['esp', 'español', 'espanol'],
       ('fra', None): ['français', 'vf', 'vff', 'vfi', 'vfq'],
       ('swe', None): ['se'],
       ('por', 'BR'): ['po', 'pb', 'pob', 'ptbr', 'br', 'brazilian'],
       ('cat', None): ['català', 'castellano', 'espanol castellano', 'español castellano'],
       ('ces', None): ['cz'],
       ('ukr', None): ['ua'],
       ('zho', None): ['cn'],
       ('jpn', None): ['jp'],
       ('hrv', None): ['scr'],
       ('mul', None): ['multi', 'dl']}  # http://scenelingo.wordpress.com/2009/03/24/what-does-dl-mean/


class GuessitConverter(babelfish.LanguageReverseConverter):  # pylint: disable=missing-docstring
    _with_country_regexp = re.compile(r'(.*)\((.*)\)')
    _with_country_regexp2 = re.compile(r'(.*)-(.*)')

    def __init__(self):
        self.guessit_exceptions = {}
        for (alpha3, country), synlist in SYN.items():
            for syn in synlist:
                self.guessit_exceptions[syn.lower()] = (alpha3, country, None)

    @property
    def codes(self):  # pylint: disable=missing-docstring
        return (babelfish.language_converters['alpha3b'].codes |
                babelfish.language_converters['alpha2'].codes |
                babelfish.language_converters['name'].codes |
                babelfish.language_converters['opensubtitles'].codes |
                babelfish.country_converters['name'].codes |
                frozenset(self.guessit_exceptions.keys()))

    def convert(self, alpha3, country=None, script=None):
        return str(babelfish.Language(alpha3, country, script))

    def reverse(self, name):  # pylint:disable=arguments-differ
        with_country = (GuessitConverter._with_country_regexp.match(name) or
                        GuessitConverter._with_country_regexp2.match(name))

        name = name.lower()
        if with_country:
            lang = babelfish.Language.fromguessit(with_country.group(1).strip())
            lang.country = babelfish.Country.fromguessit(with_country.group(2).strip())
            return lang.alpha3, lang.country.alpha2 if lang.country else None, lang.script or None

        # exceptions come first, as they need to override a potential match
        # with any of the other guessers
        try:
            return self.guessit_exceptions[name]
        except KeyError:
            pass

        for conv in [babelfish.Language,
                     babelfish.Language.fromalpha3b,
                     babelfish.Language.fromalpha2,
                     babelfish.Language.fromname,
                     babelfish.Language.fromopensubtitles]:
            try:
                reverse = conv(name)
                return reverse.alpha3, reverse.country, reverse.script
            except (ValueError, babelfish.LanguageReverseError):
                pass

        raise babelfish.LanguageReverseError(name)


def length_comparator(value):
    """
    Return value length.
    """
    return len(value)


babelfish.language_converters['guessit'] = GuessitConverter()


subtitle_both = ['sub', 'subs', 'subbed', 'custom subbed', 'custom subs',
                 'custom sub', 'customsubbed', 'customsubs', 'customsub',
                 'soft subtitles', 'soft subs']
subtitle_prefixes = sorted(subtitle_both +
                           ['st', 'vost', 'subforced', 'fansub', 'hardsub',
                            'legenda', 'legendas', 'legendado', 'subtitulado',
                            'soft', 'subtitles'], key=length_comparator)
subtitle_suffixes = sorted(subtitle_both +
                           ['subforced', 'fansub', 'hardsub'], key=length_comparator)
lang_both = ['dublado', 'dubbed', 'dub']
lang_suffixes = sorted(lang_both + ['audio'], key=length_comparator)
lang_prefixes = sorted(lang_both + ['true'], key=length_comparator)

weak_prefixes = ('audio', 'true')

_LanguageMatch = namedtuple('_LanguageMatch', ['property_name', 'word', 'lang'])


class LanguageWord(object):
    """
    Extension to the Word namedtuple in order to create compound words.

    E.g.: pt-BR, soft subtitles, custom subs
    """

    def __init__(self, start, end, value, input_string, next_word=None):
        self.start = start
        self.end = end
        self.value = value
        self.input_string = input_string
        self.next_word = next_word

    @property
    def extended_word(self):
        """
        Return the extended word for this instance, if any.
        """
        if self.next_word:
            separator = self.input_string[self.end:self.next_word.start]
            next_separator = self.input_string[self.next_word.end:self.next_word.end + 1]

            if (separator == '-' and separator != next_separator) or separator in (' ', '.'):
                value = self.input_string[self.start:self.next_word.end].replace('.', ' ')

                return LanguageWord(self.start, self.next_word.end, value, self.input_string, self.next_word.next_word)

    def __repr__(self):
        return '<({start},{end}): {value}'.format(start=self.start, end=self.end, value=self.value)


def to_rebulk_match(language_match):
    """
    Convert language match to rebulk Match: start, end, dict
    """
    word = language_match.word
    start = word.start
    end = word.end
    name = language_match.property_name
    if language_match.lang == UNDETERMINED:
        return start, end, dict(name=name, value=word.value.lower(),
                                formatter=babelfish.Language, tags=['weak-language'])

    return start, end, dict(name=name, value=language_match.lang)


class LanguageFinder(object):
    """
    Helper class to search and return language matches: 'language' and 'subtitle_language' properties
    """

    def __init__(self, allowed_languages):
        self.parsed = dict()
        self.allowed_languages = allowed_languages
        self.common_words = COMMON_WORDS_STRICT if allowed_languages else COMMON_WORDS

    def find(self, string):
        """
        Return all matches for language and subtitle_language.

        Undetermined language matches are removed if a regular language is found.
        Multi language matches are removed if there are only undetermined language matches
        """
        regular_lang_map = defaultdict(set)
        undetermined_map = defaultdict(set)
        multi_map = defaultdict(set)

        for match in self.iter_language_matches(string):
            key = match.property_name
            if match.lang == UNDETERMINED:
                undetermined_map[key].add(match)
            elif match.lang == 'mul':
                multi_map[key].add(match)
            else:
                regular_lang_map[key].add(match)

        for key, values in multi_map.items():
            if key in regular_lang_map or key not in undetermined_map:
                for value in values:
                    yield to_rebulk_match(value)

        for key, values in undetermined_map.items():
            if key not in regular_lang_map:
                for value in values:
                    yield to_rebulk_match(value)

        for values in regular_lang_map.values():
            for value in values:
                yield to_rebulk_match(value)

    def iter_language_matches(self, string):
        """
        Return language matches for the given string.
        """
        candidates = []
        previous = None
        for word in iter_words(string):
            language_word = LanguageWord(start=word.span[0], end=word.span[1], value=word.value, input_string=string)
            if previous:
                previous.next_word = language_word
                candidates.append(previous)
            previous = language_word
        if previous:
            candidates.append(previous)

        for candidate in candidates:
            for match in self.iter_matches_for_candidate(candidate):
                yield match

    def iter_matches_for_candidate(self, language_word):
        """
        Return language matches for the given candidate word.
        """
        tuples = [
            (language_word, language_word.next_word,
             dict(subtitle_language=subtitle_prefixes, language=lang_prefixes),
             lambda string, prefix: string.startswith(prefix),
             lambda string, prefix: string[len(prefix):]),
            (language_word.next_word, language_word,
             dict(subtitle_language=subtitle_suffixes, language=lang_suffixes),
             lambda string, suffix: string.endswith(suffix),
             lambda string, suffix: string[:len(string) - len(suffix)])
        ]

        for word, fallback_word, affixes, is_affix, strip_affix in tuples:
            if not word:
                continue

            match = self.find_match_for_word(word, fallback_word, affixes, is_affix, strip_affix)
            if match:
                yield match

        match = self.find_language_match_for_word(language_word)
        if match:
            yield match

    def find_match_for_word(self, word, fallback_word, affixes, is_affix, strip_affix):
        """
        Return the language match for the given word and affixes.
        """
        for current_word in (word.extended_word, word):
            if not current_word:
                continue

            word_lang = current_word.value.lower()
            if word_lang in self.common_words:
                continue

            for key, parts in affixes.items():
                for part in parts:
                    if not is_affix(word_lang, part):
                        continue

                    match = None
                    value = strip_affix(word_lang, part)
                    if not value:
                        if fallback_word:
                            match = self.find_language_match_for_word(fallback_word, key=key, force=True)

                        if not match and part not in weak_prefixes:
                            match = self.create_language_match(key, LanguageWord(current_word.start, current_word.end,
                                                                                 'und', current_word.input_string))
                    elif value not in self.common_words:
                        match = self.create_language_match(key, LanguageWord(current_word.start, current_word.end,
                                                                             value, current_word.input_string))

                    if match:
                        return match

    def find_language_match_for_word(self, word, key='language', force=False):
        """
        Return the language match for the given word.
        """
        for current_word in (word.extended_word, word):
            if current_word and (force or current_word.value.lower() not in self.common_words):
                match = self.create_language_match(key, current_word)
                if match:
                    return match

    def create_language_match(self, key, word):
        """
        Create a LanguageMatch for a given word
        """
        lang = self.parse_language(word.value.lower())

        if lang is not None:
            return _LanguageMatch(property_name=key, word=word, lang=lang)

    def parse_language(self, lang_word):
        """
        Parse the lang_word into a valid Language.

        Multi and Undetermined languages are also valid languages.
        """
        if lang_word in self.parsed:
            return self.parsed[lang_word]

        try:
            lang = babelfish.Language.fromguessit(lang_word)
            if self.allowed_languages:
                if (hasattr(lang, 'name') and lang.name.lower() in self.allowed_languages) \
                        or (hasattr(lang, 'alpha2') and lang.alpha2.lower() in self.allowed_languages) \
                        or lang.alpha3.lower() in self.allowed_languages:
                    self.parsed[lang_word] = lang
                    return lang
            # Keep language with alpha2 equivalent. Others are probably
            # uncommon languages.
            elif lang in ('mul', UNDETERMINED) or hasattr(lang, 'alpha2'):
                self.parsed[lang_word] = lang
                return lang

            self.parsed[lang_word] = None
        except babelfish.Error:
            self.parsed[lang_word] = None


def find_languages(string, context=None):
    """Find languages in the string

    :return: list of tuple (property, Language, lang_word, word)
    """
    return LanguageFinder(context.get('allowed_languages')).find(string)


class SubtitlePrefixLanguageRule(Rule):
    """
    Convert language guess as subtitle_language if previous match is a subtitle language prefix
    """
    consequence = RemoveMatch

    properties = {'subtitle_language': [None]}

    def when(self, matches, context):
        to_rename = []
        to_remove = matches.named('subtitle_language.prefix')
        for lang in matches.named('language'):
            prefix = matches.previous(lang, lambda match: match.name == 'subtitle_language.prefix', 0)
            if not prefix:
                group_marker = matches.markers.at_match(lang, lambda marker: marker.name == 'group', 0)
                if group_marker:
                    # Find prefix if placed just before the group
                    prefix = matches.previous(group_marker, lambda match: match.name == 'subtitle_language.prefix',
                                              0)
                    if not prefix:
                        # Find prefix if placed before in the group
                        prefix = matches.range(group_marker.start, lang.start,
                                               lambda match: match.name == 'subtitle_language.prefix', 0)
            if prefix:
                to_rename.append((prefix, lang))
                to_remove.extend(matches.conflicting(lang))
                if prefix in to_remove:
                    to_remove.remove(prefix)
        return to_rename, to_remove

    def then(self, matches, when_response, context):
        to_rename, to_remove = when_response
        super(SubtitlePrefixLanguageRule, self).then(matches, to_remove, context)
        for prefix, match in to_rename:
            # Remove suffix equivalent of  prefix.
            suffix = copy.copy(prefix)
            suffix.name = 'subtitle_language.suffix'
            if suffix in matches:
                matches.remove(suffix)
            matches.remove(match)
            match.name = 'subtitle_language'
            matches.append(match)


class SubtitleSuffixLanguageRule(Rule):
    """
    Convert language guess as subtitle_language if next match is a subtitle language suffix
    """
    dependency = SubtitlePrefixLanguageRule
    consequence = RemoveMatch

    properties = {'subtitle_language': [None]}

    def when(self, matches, context):
        to_append = []
        to_remove = matches.named('subtitle_language.suffix')
        for lang in matches.named('language'):
            suffix = matches.next(lang, lambda match: match.name == 'subtitle_language.suffix', 0)
            if suffix:
                to_append.append(lang)
                if suffix in to_remove:
                    to_remove.remove(suffix)
        return to_append, to_remove

    def then(self, matches, when_response, context):
        to_rename, to_remove = when_response
        super(SubtitleSuffixLanguageRule, self).then(matches, to_remove, context)
        for match in to_rename:
            matches.remove(match)
            match.name = 'subtitle_language'
            matches.append(match)


class SubtitleExtensionRule(Rule):
    """
    Convert language guess as subtitle_language if next match is a subtitle extension.

    Since it's a strong match, it also removes any conflicting format with it.
    """
    consequence = [RemoveMatch, RenameMatch('subtitle_language')]

    properties = {'subtitle_language': [None]}

    def when(self, matches, context):
        subtitle_extension = matches.named('container',
                                           lambda match: 'extension' in match.tags and 'subtitle' in match.tags,
                                           0)
        if subtitle_extension:
            subtitle_lang = matches.previous(subtitle_extension, lambda match: match.name == 'language', 0)
            if subtitle_lang:
                return matches.conflicting(subtitle_lang, lambda m: m.name == 'format'), subtitle_lang

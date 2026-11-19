#!/usr/bin/env python
"""
language and subtitle_language properties
"""

from __future__ import annotations

import copy
from collections import defaultdict, namedtuple
from typing import TYPE_CHECKING, Any

import babelfish
from rebulk import Rebulk, RemoveMatch, RenameMatch, Rule
from rebulk.remodule import re

from ..common import seps
from ..common.pattern import is_disabled
from ..common.validators import seps_surround
from ..common.words import iter_words

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from rebulk.match import Match, Matches


def language(config: dict[str, Any], common_words: frozenset[str]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :param common_words: common words
    :type common_words: set
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    subtitle_both = config["subtitle_affixes"]
    subtitle_prefixes = sorted(subtitle_both + config["subtitle_prefixes"], key=length_comparator)
    subtitle_suffixes = sorted(subtitle_both + config["subtitle_suffixes"], key=length_comparator)
    lang_both = config["language_affixes"]
    lang_prefixes = sorted(lang_both + config["language_prefixes"], key=length_comparator)
    lang_suffixes = sorted(lang_both + config["language_suffixes"], key=length_comparator)
    weak_affixes = frozenset(config["weak_affixes"])

    rebulk = Rebulk(
        disabled=lambda context: is_disabled(context, "language") and is_disabled(context, "subtitle_language")
    )

    rebulk.string(
        *subtitle_prefixes,
        name="subtitle_language.prefix",
        ignore_case=True,
        private=True,
        validator=seps_surround,
        tags=["release-group-prefix"],
        disabled=lambda context: is_disabled(context, "subtitle_language"),
    )
    rebulk.string(
        *subtitle_suffixes,
        name="subtitle_language.suffix",
        ignore_case=True,
        private=True,
        validator=seps_surround,
        disabled=lambda context: is_disabled(context, "subtitle_language"),
    )
    rebulk.string(
        *lang_suffixes,
        name="language.suffix",
        ignore_case=True,
        private=True,
        validator=seps_surround,
        tags=["source-suffix"],
        disabled=lambda context: is_disabled(context, "language"),
    )

    def find_languages(string: str, context: dict[str, Any] | None = None) -> Iterator[tuple[int, int, dict[str, Any]]]:
        """Find languages in the string

        :return: list of tuple (property, Language, lang_word, word)
        """
        return LanguageFinder(
            context, subtitle_prefixes, subtitle_suffixes, lang_prefixes, lang_suffixes, weak_affixes
        ).find(string)

    rebulk.functional(
        find_languages, properties={"language": [None]}, disabled=lambda context: not context.get("allowed_languages")
    )
    rebulk.rules(
        SubtitleExtensionRule,
        SubtitlePrefixLanguageRule,
        SubtitleSuffixLanguageRule,
        RemoveLanguage,
        RemoveInvalidLanguages(common_words),
        RemoveUndeterminedLanguages,
    )

    babelfish.language_converters["guessit"] = GuessitConverter(config["synonyms"])

    return rebulk


UNDETERMINED = babelfish.Language("und")
MULTIPLE = babelfish.Language("mul")
NON_SPECIFIC_LANGUAGES = frozenset([UNDETERMINED, MULTIPLE])


class GuessitConverter(babelfish.LanguageReverseConverter):  # type: ignore[misc]
    _with_country_regexp = re.compile(r"(.*)\((.*)\)")
    _with_country_regexp2 = re.compile(r"(.*)-(.*)")

    def __init__(self, synonyms: dict[str, Any]) -> None:
        self.guessit_exceptions: dict[str, Any] = {}
        for code, synlist in synonyms.items():
            if "_" in code:
                (alpha3, country) = code.split("_")
            else:
                (alpha3, country) = (code, None)
            for syn in synlist:
                self.guessit_exceptions[syn.lower()] = (alpha3, country, None)

    @property
    def codes(self) -> Any:
        return (
            babelfish.language_converters["alpha3b"].codes
            | babelfish.language_converters["alpha2"].codes
            | babelfish.language_converters["name"].codes
            | babelfish.language_converters["opensubtitles"].codes
            | babelfish.country_converters["name"].codes
            | frozenset(self.guessit_exceptions.keys())
        )

    def convert(self, alpha3: str, country: str | None = None, script: str | None = None) -> str:
        return str(babelfish.Language(alpha3, country, script))

    def reverse(self, name: str) -> Any:
        name = name.lower()
        # exceptions come first, as they need to override a potential match
        # with any of the other guessers
        try:
            return self.guessit_exceptions[name]
        except KeyError:
            pass

        for conv in [
            babelfish.Language,
            babelfish.Language.fromalpha3b,
            babelfish.Language.fromalpha2,
            babelfish.Language.fromname,
            babelfish.Language.fromopensubtitles,
            babelfish.Language.fromietf,
        ]:
            try:
                reverse = conv(name)
                return reverse.alpha3, reverse.country, reverse.script
            except (ValueError, babelfish.LanguageReverseError):
                pass

        raise babelfish.LanguageReverseError(name)


def length_comparator(value: str) -> int:
    """
    Return value length.
    """
    return len(value)


_LanguageMatch = namedtuple("_LanguageMatch", ["property_name", "word", "lang"])


class LanguageWord:
    """
    Extension to the Word namedtuple in order to create compound words.

    E.g.: pt-BR, soft subtitles, custom subs
    """

    def __init__(
        self, start: int, end: int, value: str, input_string: str, next_word: LanguageWord | None = None
    ) -> None:
        self.start = start
        self.end = end
        self.value = value
        self.input_string = input_string
        self.next_word = next_word

    @property
    def extended_word(self) -> LanguageWord | None:
        """
        Return the extended word for this instance, if any.
        """
        if self.next_word:
            separator = self.input_string[self.end : self.next_word.start]
            next_separator = self.input_string[self.next_word.end : self.next_word.end + 1]

            if (separator == "-" and separator != next_separator) or separator in (" ", "."):
                value = self.input_string[self.start : self.next_word.end].replace(".", " ")

                return LanguageWord(self.start, self.next_word.end, value, self.input_string, self.next_word.next_word)
        return None

    def __repr__(self) -> str:
        return f"<({self.start},{self.end}): {self.value}"


def to_rebulk_match(language_match: _LanguageMatch) -> tuple[int, int, dict[str, Any]]:
    """
    Convert language match to rebulk Match: start, end, dict
    """
    word = language_match.word
    start = word.start
    end = word.end
    name = language_match.property_name
    if language_match.lang == UNDETERMINED:
        return (
            start,
            end,
            {"name": name, "value": word.value.lower(), "formatter": babelfish.Language, "tags": ["weak-language"]},
        )

    return start, end, {"name": name, "value": language_match.lang}


class LanguageFinder:
    """
    Helper class to search and return language matches: 'language' and 'subtitle_language' properties
    """

    def __init__(
        self,
        context: dict[str, Any] | None,
        subtitle_prefixes: list[str],
        subtitle_suffixes: list[str],
        lang_prefixes: list[str],
        lang_suffixes: list[str],
        weak_affixes: frozenset[str],
    ) -> None:
        allowed_languages = context.get("allowed_languages") if context else None
        self.allowed_languages = {lang.lower() for lang in allowed_languages or []}
        self.weak_affixes = weak_affixes
        self.prefixes_map: dict[str, list[str]] = {}
        self.suffixes_map: dict[str, list[str]] = {}

        if not is_disabled(context, "subtitle_language"):
            self.prefixes_map["subtitle_language"] = subtitle_prefixes
            self.suffixes_map["subtitle_language"] = subtitle_suffixes

        self.prefixes_map["language"] = lang_prefixes
        self.suffixes_map["language"] = lang_suffixes

    def find(self, string: str) -> Iterator[tuple[int, int, dict[str, Any]]]:
        """
        Return all matches for language and subtitle_language.

        Undetermined language matches are removed if a regular language is found.
        Multi language matches are removed if there are only undetermined language matches
        """
        regular_lang_map: defaultdict[Any, set[Any]] = defaultdict(set)
        undetermined_map: defaultdict[Any, set[Any]] = defaultdict(set)
        multi_map: defaultdict[Any, set[Any]] = defaultdict(set)

        for match in self.iter_language_matches(string):
            key = match.property_name
            if match.lang == UNDETERMINED:
                undetermined_map[key].add(match)
            elif match.lang == MULTIPLE:
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

    def iter_language_matches(self, string: str) -> Iterator[_LanguageMatch]:
        """
        Return language matches for the given string.
        """
        candidates: list[LanguageWord] = []
        previous: LanguageWord | None = None
        for word in iter_words(string):
            language_word = LanguageWord(start=word.span[0], end=word.span[1], value=word.value, input_string=string)
            if previous:
                previous.next_word = language_word
                candidates.append(previous)
            previous = language_word
        if previous:
            candidates.append(previous)

        for candidate in candidates:
            yield from self.iter_matches_for_candidate(candidate)

    def iter_matches_for_candidate(self, language_word: LanguageWord) -> Iterator[_LanguageMatch]:
        """
        Return language matches for the given candidate word.
        """
        tuples = [
            (
                language_word,
                language_word.next_word,
                self.prefixes_map,
                lambda string, prefix: string.startswith(prefix),
                lambda string, prefix: string[len(prefix) :],
            ),
            (
                language_word.next_word,
                language_word,
                self.suffixes_map,
                lambda string, suffix: string.endswith(suffix),
                lambda string, suffix: string[: len(string) - len(suffix)],
            ),
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

    def find_match_for_word(
        self,
        word: LanguageWord,
        fallback_word: LanguageWord | None,
        affixes: dict[str, list[str]],
        is_affix: Callable[[str, str], bool],
        strip_affix: Callable[[str, str], str],
    ) -> _LanguageMatch | None:
        """
        Return the language match for the given word and affixes.
        """
        for current_word in (word.extended_word, word):
            if not current_word:
                continue

            word_lang = current_word.value.lower()

            for key, parts in affixes.items():
                for part in parts:
                    if not is_affix(word_lang, part):
                        continue

                    match = None
                    value = strip_affix(word_lang, part)
                    if not value:
                        if fallback_word and (
                            abs(fallback_word.start - word.end) <= 1 or abs(word.start - fallback_word.end) <= 1
                        ):
                            match = self.find_language_match_for_word(fallback_word, key=key)

                        if not match and part not in self.weak_affixes:
                            match = self.create_language_match(
                                key,
                                LanguageWord(current_word.start, current_word.end, "und", current_word.input_string),
                            )
                    else:
                        match = self.create_language_match(
                            key, LanguageWord(current_word.start, current_word.end, value, current_word.input_string)
                        )

                    if match:
                        return match
        return None

    def find_language_match_for_word(self, word: LanguageWord, key: str = "language") -> _LanguageMatch | None:
        """
        Return the language match for the given word.
        """
        for current_word in (word.extended_word, word):
            if current_word:
                match = self.create_language_match(key, current_word)
                if match:
                    return match
        return None

    def create_language_match(self, key: str, word: LanguageWord) -> _LanguageMatch | None:
        """
        Create a LanguageMatch for a given word
        """
        lang = self.parse_language(word.value.lower())

        if lang is not None:
            return _LanguageMatch(property_name=key, word=word, lang=lang)
        return None

    def parse_language(self, lang_word: str) -> Any:
        """
        Parse the lang_word into a valid Language.

        Multi and Undetermined languages are also valid languages.
        """
        try:
            lang = babelfish.Language.fromguessit(lang_word)
            if (
                (hasattr(lang, "name") and lang.name.lower() in self.allowed_languages)
                or (hasattr(lang, "alpha2") and lang.alpha2.lower() in self.allowed_languages)
                or lang.alpha3.lower() in self.allowed_languages
            ):
                return lang

        except babelfish.Error:
            pass


class SubtitlePrefixLanguageRule(Rule):
    """
    Convert language guess as subtitle_language if previous match is a subtitle language prefix
    """

    consequence = RemoveMatch

    properties = {"subtitle_language": [None]}

    def enabled(self, context: dict[str, Any] | None) -> bool:
        return not is_disabled(context, "subtitle_language")

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_rename: list[tuple[Match, Match]] = []
        to_remove = matches.named("subtitle_language.prefix")
        for lang in matches.named("language"):
            prefix = matches.previous(lang, lambda match: match.name == "subtitle_language.prefix", 0)
            if not prefix:
                group_marker = matches.markers.at_match(lang, lambda marker: marker.name == "group", 0)
                if group_marker:
                    # Find prefix if placed just before the group
                    prefix = matches.previous(group_marker, lambda match: match.name == "subtitle_language.prefix", 0)
                    if not prefix:
                        # Find prefix if placed before in the group
                        prefix = matches.range(
                            group_marker.start, lang.start, lambda match: match.name == "subtitle_language.prefix", 0
                        )
            if prefix:
                to_rename.append((prefix, lang))
                to_remove.extend(matches.conflicting(lang))
                if prefix in to_remove:
                    to_remove.remove(prefix)
        if to_rename or to_remove:
            return to_rename, to_remove
        return False

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> None:
        to_rename, to_remove = when_response
        super().then(matches, to_remove, context)
        for prefix, match in to_rename:
            # Remove suffix equivalent of  prefix.
            suffix = copy.copy(prefix)
            suffix.name = "subtitle_language.suffix"
            if suffix in matches:
                matches.remove(suffix)
            matches.remove(match)
            match.name = "subtitle_language"
            matches.append(match)


class SubtitleSuffixLanguageRule(Rule):
    """
    Convert language guess as subtitle_language if next match is a subtitle language suffix
    """

    dependency = SubtitlePrefixLanguageRule
    consequence = RemoveMatch

    properties = {"subtitle_language": [None]}

    def enabled(self, context: dict[str, Any] | None) -> bool:
        return not is_disabled(context, "subtitle_language")

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_append: list[Match] = []
        to_remove = matches.named("subtitle_language.suffix")
        for lang in matches.named("language"):
            suffix = matches.next(lang, lambda match: match.name == "subtitle_language.suffix", 0)
            if suffix:
                to_append.append(lang)
                if suffix in to_remove:
                    to_remove.remove(suffix)
        if to_append or to_remove:
            return to_append, to_remove
        return False

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> None:
        to_rename, to_remove = when_response
        super().then(matches, to_remove, context)
        for match in to_rename:
            matches.remove(match)
            match.name = "subtitle_language"
            matches.append(match)


class SubtitleExtensionRule(Rule):
    """
    Convert language guess as subtitle_language if next match is a subtitle extension.

    Since it's a strong match, it also removes any conflicting source with it.
    """

    consequence = [RemoveMatch, RenameMatch("subtitle_language")]

    properties = {"subtitle_language": [None]}

    def enabled(self, context: dict[str, Any] | None) -> bool:
        return not is_disabled(context, "subtitle_language")

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        subtitle_extension = matches.named(
            "container", lambda match: "extension" in match.tags and "subtitle" in match.tags, 0
        )
        if subtitle_extension:
            subtitle_lang = matches.previous(subtitle_extension, lambda match: match.name == "language", 0)
            if subtitle_lang:
                for weak in matches.named("subtitle_language", predicate=lambda m: "weak-language" in m.tags):
                    weak.private = True

                return matches.conflicting(subtitle_lang, lambda m: m.name == "source"), subtitle_lang
        return None


class RemoveLanguage(Rule):
    """Remove language matches that were not converted to subtitle_language when language is disabled."""

    consequence = RemoveMatch

    def enabled(self, context: dict[str, Any] | None) -> bool:
        return is_disabled(context, "language")

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return matches.named("language")


class RemoveInvalidLanguages(Rule):
    """Remove language matches that matches the blacklisted common words."""

    consequence = RemoveMatch
    priority = 32

    def __init__(self, common_words: frozenset[str]) -> None:
        """Constructor."""
        super().__init__()
        self.common_words = common_words

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove = []
        for match in matches.range(
            0, len(matches.input_string or ""), predicate=lambda m: m.name in ("language", "subtitle_language")
        ):
            if match.raw is not None and match.raw.lower() not in self.common_words:
                continue

            # A lowercase language code glued to a subtitle extension (".no.srt") is a deliberate
            # subtitle tag, not a stray common word — keep it even when blacklisted (#668). A
            # Title-Case token ("Dr.No.srt", "Garfield.It.srt") is the last word of the title, so
            # the casing check leaves it for the title.
            following = matches.next(match, predicate=lambda m: not m.private and bool(m.value), index=0)
            if (
                match.raw is not None
                and match.raw.islower()
                and following is not None
                and following.name == "container"
                and "subtitle" in following.tags
                and not (matches.input_string or "")[match.end : following.start].strip(seps)
            ):
                continue

            group = matches.markers.at_match(match, index=0, predicate=lambda m: m.name == "group")
            if group and (
                not matches.range(
                    group.start, group.end, predicate=lambda m: m.name not in ("language", "subtitle_language")
                )
                and (not matches.holes(group.start, group.end, predicate=lambda m: m.value.strip(seps)))
            ):
                continue

            to_remove.append(match)

        return to_remove


class RemoveUndeterminedLanguages(Rule):
    """Remove "und" language matches when next other language if found."""

    consequence = RemoveMatch
    priority = 32

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove = []
        for match in matches.range(
            0, len(matches.input_string or ""), predicate=lambda m: m.name in ("language", "subtitle_language")
        ):
            if match.value == "und":
                previous = matches.previous(match, index=0)
                next_ = matches.next(match, index=0)
                if (previous and previous.name == "language") or (next_ and next_.name == "language"):
                    to_remove.append(match)

        return to_remove

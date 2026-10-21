#!/usr/bin/env python
"""
country property
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import babelfish
from rebulk import Rebulk

from ..common.pattern import is_disabled
from ..common.words import iter_words

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


def country(config: dict[str, Any], common_words: frozenset[str]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :param common_words: common words
    :type common_words: set
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, "country"))
    rebulk = rebulk.defaults(name="country")

    def find_countries(string: str, context: dict[str, Any] | None = None) -> Iterator[tuple[int, int, dict[str, Any]]]:
        """
        Find countries in given string.
        """
        allowed_countries = context.get("allowed_countries") if context else None
        return CountryFinder(allowed_countries, common_words).find(string)

    rebulk.functional(
        find_countries,
        # Prefer language and any other property over country if not US or GB.
        conflict_solver=lambda match, other: (
            match
            if other.name != "language" or match.value not in (babelfish.Country("US"), babelfish.Country("GB"))
            else other
        ),
        properties={"country": [None]},
        disabled=lambda context: not context.get("allowed_countries"),
    )

    babelfish.country_converters["guessit"] = GuessitCountryConverter(config["synonyms"])

    return rebulk


class GuessitCountryConverter(babelfish.CountryReverseConverter):  # type: ignore[misc]
    def __init__(self, synonyms: dict[str, Any]) -> None:
        self.guessit_exceptions: dict[str, str] = {}

        for alpha2, synlist in synonyms.items():
            for syn in synlist:
                self.guessit_exceptions[syn.lower()] = alpha2

    @property
    def codes(self) -> Any:
        return (
            babelfish.country_converters["name"].codes
            | frozenset(babelfish.COUNTRIES.values())
            | frozenset(self.guessit_exceptions.keys())
        )

    def convert(self, alpha2: str) -> str:
        if alpha2 == "GB":
            return "UK"
        return str(babelfish.Country(alpha2))

    def reverse(self, name: str) -> Any:
        # exceptions come first, as they need to override a potential match
        # with any of the other guessers
        try:
            return self.guessit_exceptions[name.lower()]
        except KeyError:
            pass

        try:
            return babelfish.Country(name.upper()).alpha2
        except ValueError:
            pass

        for conv in [babelfish.Country.fromname]:
            try:
                return conv(name).alpha2
            except babelfish.CountryReverseError:
                pass

        raise babelfish.CountryReverseError(name)


class CountryFinder:
    """Helper class to search and return country matches."""

    def __init__(self, allowed_countries: Iterable[str] | None, common_words: frozenset[str]) -> None:
        self.allowed_countries = {country.lower() for country in allowed_countries or []}
        self.common_words = common_words

    def find(self, string: str) -> Iterator[tuple[int, int, dict[str, Any]]]:
        """Return all matches for country."""
        for word_match in iter_words(string.strip().lower()):
            word = word_match.value
            if word.lower() in self.common_words:
                continue

            try:
                country_object = babelfish.Country.fromguessit(word)
                if (
                    country_object.name.lower() in self.allowed_countries
                    or country_object.alpha2.lower() in self.allowed_countries
                ):
                    yield self._to_rebulk_match(word_match, country_object)
            except babelfish.Error:
                continue

    @classmethod
    def _to_rebulk_match(cls, word: Any, value: Any) -> tuple[int, int, dict[str, Any]]:
        return word.span[0], word.span[1], {"value": value}

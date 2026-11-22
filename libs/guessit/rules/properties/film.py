#!/usr/bin/env python
"""
film property
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rebulk import AppendMatch, Rebulk, RemoveMatch, Rule
from rebulk.remodule import re

from ...config import load_config_patterns
from ..common import dash
from ..common.formatters import cleanup
from ..common.keys import FILM
from ..common.pattern import is_disabled
from ..common.validators import seps_surround

if TYPE_CHECKING:
    from rebulk.match import Matches


def film(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, "film"))
    rebulk.regex_defaults(flags=re.IGNORECASE, abbreviations=[dash]).string_defaults(ignore_case=True)
    rebulk.defaults(name="film", validator=seps_surround)
    rebulk.declare_keys(FILM)

    load_config_patterns(rebulk, config.get("film"))

    rebulk.rules(LeadingFilmNumberRule, FilmTitleRule)

    return rebulk


class LeadingFilmNumberRule(Rule):
    """
    Discard a film number that leads the file part with nothing before it.

    A collection number only makes sense after a collection title
    (e.g. ``James Bond f17``). When ``f\\d`` opens the name with no title
    ahead of it, it belongs to the title itself (e.g. ``F1 The Movie``).
    """

    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Any] = []
        for film_match in matches.named("film", lambda match: not match.private):
            filepath = matches.markers.at_match(film_match, lambda marker: marker.name == "path", 0)
            if not filepath:
                continue
            hole = matches.holes(filepath.start, film_match.start + 1, formatter=cleanup, index=0)
            if not (hole and hole.value):
                to_remove.append(film_match)
                if film_match.parent:
                    to_remove.append(film_match.parent)
        return to_remove


class FilmTitleRule(Rule):
    """
    Rule to find out film_title (hole after film property
    """

    consequence = AppendMatch

    properties = {"film_title": [None]}

    def enabled(self, context: dict[str, Any] | None) -> bool:
        return not is_disabled(context, "film_title")

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        bonus_number = matches.named("film", lambda match: not match.private, index=0)
        if bonus_number:
            filepath = matches.markers.at_match(bonus_number, lambda marker: marker.name == "path", 0)
            if filepath:
                hole = matches.holes(filepath.start, bonus_number.start + 1, formatter=cleanup, index=0)
                if hole and hole.value:
                    hole.name = "film_title"
                    return hole
        return None

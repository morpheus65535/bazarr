#!/usr/bin/env python
"""
date, week and year properties
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from rebulk import Rebulk, RemoveMatch, Rule

from ...reutils import build_or_pattern
from ..common import dash, seps
from ..common.date import search_date, valid_week, valid_year
from ..common.pattern import is_disabled
from ..common.validators import seps_surround

if TYPE_CHECKING:
    from rebulk.match import Match, Matches


def date(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().defaults(validator=seps_surround)

    rebulk.regex(
        r"\d{4}",
        name="year",
        formatter=int,
        disabled=lambda context: is_disabled(context, "year"),
        conflict_solver=lambda match, other: (
            other if other.name in ("episode", "season") and len(other.raw) < len(match.raw) else "__default__"
        ),
        validator=lambda match: seps_surround(match) and valid_year(match.value),
    )

    rebulk.regex(
        build_or_pattern(config["week_words"]) + r"-?(\d{1,2})",
        name="week",
        formatter=int,
        children=True,
        flags=re.IGNORECASE,
        abbreviations=[dash],
        conflict_solver=lambda match, other: (
            other if other.name in ("episode", "season") and len(other.raw) < len(match.raw) else "__default__"
        ),
        validator=lambda match: seps_surround(match) and valid_week(match.value),
    )

    def date_functional(string: str, context: dict[str, Any]) -> tuple[int, int, dict[str, Any]] | None:
        """
        Search for date in the string and retrieves match

        :param string:
        :return:
        """

        ret = search_date(string, context.get("date_year_first"), context.get("date_day_first"))
        if ret:
            return ret[0], ret[1], {"value": ret[2]}
        return None

    rebulk.functional(
        date_functional,
        name="date",
        properties={"date": [None]},
        disabled=lambda context: is_disabled(context, "date"),
        conflict_solver=lambda match, other: other if other.name in ("episode", "season", "crc32") else "__default__",
    )

    rebulk.rules(KeepMarkedYearInFilepart, AbsorbWeekdayPrefix(config["weekday_words"]))

    return rebulk


class AbsorbWeekdayPrefix(Rule):
    """
    Absorb a weekday word glued to a date into the ``date`` match (upstream #794).

    ``A.Place.in.the.Sun.S2025E01.Thu.2.Jan.2025.Mar.Menor.Spain...`` parses ``2 Jan 2025`` as the
    air date but the leading "Thu" is the broadcast weekday, not the title. The interior date splits
    the title hole in two, so ``EpisodeTitleFromPosition`` fills the first hole ("Thu") and drops the
    real title after the date ("Mar Menor Spain"). Growing the date span to cover the adjacent weekday
    removes that first hole, so the title after the date is reclaimed instead.

    Only a weekday directly preceding the date (separators only between, and not already claimed by
    another match) is absorbed; the parsed date value is unchanged.
    """

    consequence = RemoveMatch

    def __init__(self, weekday_words: list[str]) -> None:
        super().__init__()
        seps_class = "[" + re.escape(seps) + "]"
        self.weekday_re = re.compile(
            r"(?:^|" + seps_class + r")(" + build_or_pattern(weekday_words) + r")" + seps_class + r"*$",
            re.IGNORECASE,
        )

    def enabled(self, context: dict[str, Any] | None) -> bool:
        return not is_disabled(context, "date")

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        input_string = matches.input_string or ""
        ret: list[tuple[Match, int]] = []
        for date_match in matches.named("date"):
            filepart = matches.markers.at_match(date_match, lambda m: m.name == "path", 0)
            lower = filepart.start if filepart else 0
            weekday = self.weekday_re.search(input_string[lower : date_match.start])
            if not weekday:
                continue
            new_start = lower + weekday.start(1)
            # Only absorb a free weekday word; never swallow a token already claimed by a match.
            if matches.range(new_start, date_match.start, predicate=lambda m: not m.private):
                continue
            ret.append((date_match, new_start))
        return ret

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> None:
        for date_match, new_start in when_response:
            matches.remove(date_match)
            date_match.start = new_start
            matches.append(date_match)


class KeepMarkedYearInFilepart(Rule):
    """
    Keep first years marked with [](){} in filepart, or if no year is marked, ensure it won't override titles.
    """

    priority = 64
    consequence = RemoveMatch

    def enabled(self, context: dict[str, Any] | None) -> bool:
        return not is_disabled(context, "year")

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        ret: list[Match] = []
        if len(matches.named("year")) > 1:
            for filepart in matches.markers.named("path"):
                years = matches.range(filepart.start, filepart.end, lambda match: match.name == "year")
                if len(years) > 1:
                    group_years: list[Match] = []
                    ungroup_years: list[Match] = []
                    for year in years:
                        if matches.markers.at_match(year, lambda marker: marker.name == "group"):
                            group_years.append(year)
                        else:
                            ungroup_years.append(year)
                    if group_years and ungroup_years:
                        ret.extend(ungroup_years)
                        ret.extend(group_years[1:])  # Keep the first year in marker.
                    elif not group_years:
                        ret.append(ungroup_years[0])  # Keep first year for title.
                        if len(ungroup_years) > 2:
                            ret.extend(ungroup_years[2:])
        return ret

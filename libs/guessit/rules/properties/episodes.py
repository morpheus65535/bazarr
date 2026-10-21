#!/usr/bin/env python
"""
episode, season, disc, episode_count, season_count and episode_details properties
"""

from __future__ import annotations

import copy
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from rebulk import AppendMatch, Rebulk, RemoveMatch, RenameMatch, Rule
from rebulk.match import Match
from rebulk.processors import PRE_PROCESS
from rebulk.remodule import re
from rebulk.utils import is_iterable

from guessit.rules import match_processors
from guessit.rules.common.numeral import numeral, parse_numeral

from ...reutils import build_or_pattern
from ..common import alt_dash, dash, seps, seps_no_fs
from ..common.formatters import strip
from ..common.keys import COUNT, EPISODE, SEASON, VERSION
from ..common.pattern import is_disabled
from ..common.validators import and_, int_coercable, seps_surround
from .title import TitleFromPosition

if TYPE_CHECKING:
    from rebulk.match import Matches


_CJK_DIGITS = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}

_SEPS_RE = re.compile(rf"[{re.escape(seps)}]+")

# ASCII digits or Han numerals up to 99 (十一 -> 11, 二十三 -> 23, single digit otherwise).
cjk_number = r"(?:\d{1,4}|[一二两三四五六七八九]?十[一二两三四五六七八九]?|[零一二两三四五六七八九])"


def parse_cjk_number(value: str) -> int:
    """Parse a season/episode number written as ASCII digits or CJK numerals.

    Handles Han numerals up to 99 so Chinese markers such as ``第二季`` (#779)
    resolve to a numeric value (二 -> 2, 十一 -> 11, 二十三 -> 23).
    """
    if value.isdigit():
        return int(value)
    if "十" in value:
        tens, _, ones = value.partition("十")
        tens_value = _CJK_DIGITS[tens] if tens else 1
        ones_value = _CJK_DIGITS[ones] if ones else 0
        return tens_value * 10 + ones_value
    return _CJK_DIGITS[value]


def _split_words(entries: list[Any]) -> tuple[list[str], list[str]]:
    """Split a season/episode word config into (word-first values, number-first values).

    Each entry is either a plain string (word-first only) or a mapping
    ``{"value": str, "numfirst": bool}``. A flat list of strings stays supported
    for backward compatibility (and for user configs merged into the default one).
    """
    words: list[str] = []
    numfirst: list[str] = []
    for entry in entries:
        if isinstance(entry, dict):
            value = entry["value"]
            if entry.get("numfirst"):
                numfirst.append(value)
        else:
            value = entry
        words.append(value)
    return words, numfirst


def episodes(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """

    def is_season_episode_disabled(context: dict[str, Any] | None) -> bool:
        """Whether season and episode rules should be enabled."""
        return is_disabled(context, "episode") or is_disabled(context, "season")

    def episodes_season_chain_breaker(matches: Matches) -> bool:
        """
        Break chains if there's more than 100 offset between two neighbor values.
        :param matches:
        :type matches:
        :return:
        :rtype:
        """
        eps = matches.named("episode")
        if len(eps) > 1 and abs(eps[-1].value - eps[-2].value) > episode_max_range:
            return True

        seasons = matches.named("season")
        return bool(len(seasons) > 1 and abs(seasons[-1].value - seasons[-2].value) > season_max_range)

    def season_episode_conflict_solver(match: Match, other: Match) -> Any:
        """
        Conflict solver for episode/season patterns

        :param match:
        :param other:
        :return:
        """
        if match.name != other.name:
            if match.name == "episode" and other.name == "year":
                return match
            if match.name in ("season", "episode"):
                if other.name in ("video_codec", "audio_codec", "container", "date"):
                    return match
                if (
                    other.name == "audio_channels"
                    and "weak-audio_channels" not in other.tags
                    and not match.initiator.children.named(match.name + "Marker")
                ) or (other.name == "screen_size" and (other.raw is None or not int_coercable(other.raw))):
                    return match
                if other.name in ("season", "episode") and match.initiator != other.initiator:
                    if match.initiator.name in ("weak_episode", "weak_duplicate") and other.initiator.name in (
                        "weak_episode",
                        "weak_duplicate",
                    ):
                        return "__default__"
                    for current in (match, other):
                        if "weak-episode" in current.tags or (
                            current.initiator.raw is not None and "x" in current.initiator.raw.lower()
                        ):
                            return current
        return "__default__"

    def ordering_validator(match: Match) -> bool:
        """
        Validator for season list. They should be in natural order to be validated.

        episode/season separated by a weak discrete separator should be consecutive, unless a strong discrete separator
        or a range separator is present in the chain (1.3&5 is valid, but 1.3-5 is not valid and 1.3.5 is not valid)
        """
        values = match.children.to_dict()
        if "season" in values and is_iterable(values["season"]):
            # Season numbers must be in natural order to be validated.
            if sorted(values["season"]) != values["season"]:
                return False
        if "episode" in values and is_iterable(values["episode"]):
            # Season numbers must be in natural order to be validated.
            if sorted(values["episode"]) != values["episode"]:
                return False

        def is_consecutive(property_name: str) -> bool:
            """
            Check if the property season or episode has valid consecutive values.
            :param property_name:
            :type property_name:
            :return:
            :rtype:
            """
            previous_match: Match | None = None
            valid = True
            for current_match in match.children.named(property_name):
                if previous_match:
                    match.children.previous(current_match, lambda m: m.name == property_name + "Separator")
                    separator = match.children.previous(
                        current_match, lambda m: m.name == property_name + "Separator", 0
                    )
                    if separator:
                        if separator.raw not in range_separators and separator.raw in weak_discrete_separators:
                            if not 0 < current_match.value - previous_match.value <= max_range_gap + 1:
                                valid = False
                        if separator.raw in strong_discrete_separators:
                            valid = True
                            break
                previous_match = current_match
            return valid

        return is_consecutive("episode") and is_consecutive("season")

    def validate_roman(match: Match) -> bool:
        """
        Validate a roman match if surrounded by separators
        :param match:
        :type match:
        :return:
        :rtype:
        """
        if match.raw is not None and int_coercable(match.raw):
            return True
        return bool(seps_surround(match))

    def season_word_not_year(match: Match) -> bool:
        """
        Validate a season-word number, rejecting a 4-digit year (e.g. "Season 2025").

        Only applies to the season WORD chain ("Season N"), not SxxExx, so
        "S2013E14 -> season 2013" stays unaffected (#800).
        """
        raw = match.raw or ""
        if re.match(r"^\d{4}$", raw) and 1900 <= int(raw) <= 2100:
            return False
        return validate_roman(match)

    season_words, season_words_numfirst = _split_words(config["season_words"])
    episode_words, episode_words_numfirst = _split_words(config["episode_words"])
    ordinal_suffix = config["ordinal_suffix"]
    of_words = config["of_words"]
    all_words = config["all_words"]
    season_markers = config["season_markers"]
    season_ep_markers = config["season_ep_markers"]
    disc_markers = config["disc_markers"]
    episode_markers = config["episode_markers"]
    range_separators = config["range_separators"]
    weak_discrete_separators = [sep for sep in seps_no_fs if sep not in range_separators]
    strong_discrete_separators = config["discrete_separators"]
    discrete_separators = strong_discrete_separators + weak_discrete_separators
    episode_max_range = config["episode_max_range"]
    season_max_range = config["season_max_range"]
    max_range_gap = config["max_range_gap"]

    season_ep_marker_pattern = build_or_pattern(season_ep_markers, name="episodeMarker")
    asymmetric_season_ep_marker = r"(?!@" + build_or_pattern(season_ep_markers) + r"\d)"

    rebulk = (
        Rebulk()
        .regex_defaults(flags=re.IGNORECASE)
        .string_defaults(ignore_case=True)
        .chain_defaults(chain_breaker=episodes_season_chain_breaker)
        .declare_keys(SEASON, EPISODE, VERSION, COUNT)
        .defaults(
            private_names=["episodeSeparator", "seasonSeparator", "episodeMarker", "seasonMarker"],
            children=True,
            private_parent=True,
            conflict_solver=season_episode_conflict_solver,
            abbreviations=[alt_dash],
        )
    )

    # CJK episode/season markers (Japanese: upstream #671, #763; Chinese: #779).
    # The glyphs never appear in Latin tokens, so no seps-surround validation is needed.
    # Numbers may be ASCII digits or Han numerals (二 -> 2), e.g. 第二季 -> season 2.
    rebulk.regex(
        r"第(?P<episode>" + cjk_number + r")[話话集]",
        tags=["SxxExx"],
        formatter={"episode": parse_cjk_number},
        disabled=is_season_episode_disabled,
    )
    rebulk.regex(
        r"第(?P<season>" + cjk_number + r")季",
        tags=["SxxExx"],
        formatter={"season": parse_cjk_number},
        disabled=is_season_episode_disabled,
    )
    rebulk.regex(
        r"(?:シーズン|シリーズ)(?P<season>\d{1,2})(?!\d)", tags=["SxxExx"], disabled=is_season_episode_disabled
    )
    rebulk.regex(r"(?<!\d)(?P<season>\d{1,2})期", tags=["SxxExx"], disabled=is_season_episode_disabled)

    # S01E02, 01x02, S01S02S03
    rebulk.chain(
        tags=["SxxExx"],
        validate_all=True,
        validator={"__parent__": and_(seps_surround, ordering_validator)},
        disabled=is_season_episode_disabled,
    ).defaults(tags=["SxxExx"]).regex(
        build_or_pattern(season_markers, name="seasonMarker")
        + r"(?P<season>\d+)@?"
        + build_or_pattern(episode_markers + disc_markers, name="episodeMarker")
        + r"@?(?P<episode>\d+)"
    ).repeater("+").regex(
        build_or_pattern(
            episode_markers + disc_markers + discrete_separators + range_separators,
            name="episodeSeparator",
            escape=True,
        )
        + r"(?P<episode>\d+)"
    ).repeater("*")

    rebulk.chain(
        tags=["SxxExx"],
        validate_all=True,
        validator={"__parent__": and_(seps_surround, ordering_validator)},
        disabled=is_season_episode_disabled,
    ).defaults(tags=["SxxExx"]).regex(
        # A separator before the marker requires one after it too: "1x03" and "1 x 03" are episodes,
        # while "1080.x264" is a number followed by a codec token (#933).
        r"(?P<season>\d+)" + asymmetric_season_ep_marker + r"@?" + season_ep_marker_pattern + r"@?(?P<episode>\d+)"
    ).repeater("+")

    rebulk.chain(
        tags=["SxxExx"],
        validate_all=True,
        validator={"__parent__": and_(seps_surround, ordering_validator)},
        disabled=is_season_episode_disabled,
    ).defaults(tags=["SxxExx"]).regex(
        r"(?P<season>\d+)" + asymmetric_season_ep_marker + r"@?" + season_ep_marker_pattern + r"@?(?P<episode>\d+)"
    ).regex(
        build_or_pattern(
            season_ep_markers + discrete_separators + range_separators, name="episodeSeparator", escape=True
        )
        + r"(?P<episode>\d+)"
    ).repeater("*")

    rebulk.chain(
        tags=["SxxExx"],
        validate_all=True,
        validator={"__parent__": and_(seps_surround, ordering_validator)},
        disabled=is_season_episode_disabled,
    ).defaults(tags=["SxxExx"]).regex(build_or_pattern(season_markers, name="seasonMarker") + r"(?P<season>\d+)").regex(
        "(?P<other>Extras)", name="other", value="Extras", tags=["no-release-group-prefix"]
    ).repeater("?").regex(
        build_or_pattern(season_markers + discrete_separators + range_separators, name="seasonSeparator", escape=True)
        + r"(?P<season>\d+)"
    ).repeater("*")

    # Compact non-English season/episode marker: "T02E22", "T01XE08" (Spanish/Portuguese).
    # Restricted to a "t" prefix immediately followed by an episode marker so a lone
    # "T1" stays a title token.
    rebulk.regex(
        r"t(?P<season>\d{1,2})@?" + build_or_pattern(episode_markers, name="episodeMarker") + r"@?(?P<episode>\d{1,4})",
        tags=["SxxExx"],
        disabled=is_season_episode_disabled,
    )

    # episode_details property
    for episode_detail in ("Special", "Pilot", "Unaired", "Final"):
        rebulk.string(
            episode_detail,
            private_parent=False,
            children=False,
            value=episode_detail,
            name="episode_details",
            disabled=lambda context: is_disabled(context, "episode_details"),
        )

    rebulk.defaults(
        private_names=["episodeSeparator", "seasonSeparator", "episodeMarker", "seasonMarker"],
        validate_all=True,
        validator={"__parent__": and_(seps_surround, ordering_validator)},
        children=True,
        private_parent=True,
        conflict_solver=season_episode_conflict_solver,
    )

    rebulk.chain(
        validate_all=True,
        conflict_solver=season_episode_conflict_solver,
        formatter={"season": parse_numeral, "count": parse_numeral},
        validator={
            "__parent__": and_(seps_surround, ordering_validator),
            "season": season_word_not_year,
            "count": validate_roman,
        },
        disabled=lambda context: context.get("type") == "movie" or is_disabled(context, "season"),
    ).defaults(
        formatter={"season": parse_numeral, "count": parse_numeral},
        validator={"season": season_word_not_year, "count": validate_roman},
        conflict_solver=season_episode_conflict_solver,
    ).regex(
        build_or_pattern(season_words, name="seasonMarker") + "@?@?(?:(?:№|#)@?)?(?P<season>" + numeral + ")"
    ).regex(r"" + build_or_pattern(of_words) + "@?(?P<count>" + numeral + ")").repeater("?").regex(
        r"@?"
        + build_or_pattern(range_separators + discrete_separators + ["@"], name="seasonSeparator", escape=True)
        + r"@?(?P<season>\d+)"
    ).repeater("*")

    # Non-English convention where the number precedes the keyword:
    #   "1ª Temporada", "3 сезон", "5-й сезон", "2.Sezon" (season); "24 серия", "7.Bölüm" (episode).
    # An optional ordinal suffix (ª/º/°, Portuguese a/o, Russian -й/-я/…) may sit between the two,
    # and the total may follow the keyword ("5 серия из 12"), as it does in the word-first patterns.
    of_count = r"(?:@?" + build_or_pattern(of_words) + r"@?(?P<count>\d+))?"
    rebulk.regex(
        r"(?P<season>\d{1,2})"
        + ordinal_suffix
        + r"@?@?"
        + build_or_pattern(season_words_numfirst, name="seasonMarker")
        + r"(?![^\W\d_])"
        + of_count,
        tags=["SxxExx", "numfirst"],
        formatter={"season": parse_numeral},
        disabled=is_season_episode_disabled,
    )
    rebulk.regex(
        r"(?P<episode>\d{1,3})"
        + ordinal_suffix
        + r"@?@?"
        + build_or_pattern(episode_words_numfirst, name="episodeMarker")
        + r"(?![^\W\d_])"
        + of_count,
        tags=["SxxExx", "numfirst"],
        formatter={"episode": parse_numeral},
        disabled=lambda context: is_disabled(context, "episode"),
    )

    rebulk.defaults(abbreviations=[dash])

    rebulk.regex(
        build_or_pattern(episode_words, name="episodeMarker")
        + r"-?-?(?:(?:№|#)-?)?(?P<episode>\d+)"
        + r"(?:v(?P<version>\d+))?"
        + r"(?:-?"
        + build_or_pattern(of_words)
        + r"-?(?P<count>\d+))?",  # Episode 4
        disabled=lambda context: context.get("type") == "episode" or is_disabled(context, "episode"),
    )

    # A roman numeral can be read out of the letters a longer marker continues with ("Ep" then
    # "i" of "Episodio"), so the marker only counts when it ends on a word boundary. The digit
    # variant above needs no such guard: a letter can never start its number.
    rebulk.regex(
        build_or_pattern(episode_words, name="episodeMarker")
        + r"(?![^\W\d_])"
        + r"-?-?(?:(?:№|#)-?)?(?P<episode>"
        + numeral
        + ")"
        + r"(?:v(?P<version>\d+))?"
        + r"(?:-?"
        + build_or_pattern(of_words)
        + r"-?(?P<count>\d+))?",  # Episode 4
        validator={"episode": validate_roman},
        formatter={"episode": parse_numeral},
        disabled=lambda context: context.get("type") != "episode" or is_disabled(context, "episode"),
    )

    rebulk.regex(
        r"S?(?P<season>\d+)-?(?:xE|Ex|E|x)-?(?P<other>" + build_or_pattern(all_words) + ")",
        tags=["SxxExx"],
        formatter={"other": lambda match: "Complete"},
        disabled=lambda context: is_disabled(context, "season"),
    )

    # 12, 13
    rebulk.chain(
        tags=["weak-episode"],
        disabled=lambda context: context.get("type") == "movie" or is_disabled(context, "episode"),
    ).defaults(validator=None, tags=["weak-episode"]).regex(r"(?P<episode>\d{2})").regex(r"v(?P<version>\d+)").repeater(
        "?"
    ).regex(r"(?P<episodeSeparator>[x-])(?P<episode>\d{2})", abbreviations=None).repeater("*")

    # 012, 013
    rebulk.chain(
        tags=["weak-episode"],
        disabled=lambda context: context.get("type") == "movie" or is_disabled(context, "episode"),
    ).defaults(validator=None, tags=["weak-episode"]).regex(r"0(?P<episode>\d{1,2})").regex(
        r"v(?P<version>\d+)"
    ).repeater("?").regex(r"(?P<episodeSeparator>[x-])0(?P<episode>\d{1,2})", abbreviations=None).repeater("*")

    # 112, 113
    rebulk.chain(
        tags=["weak-episode"],
        name="weak_episode",
        disabled=lambda context: context.get("type") == "movie" or is_disabled(context, "episode"),
    ).defaults(validator=None, tags=["weak-episode"], name="weak_episode").regex(r"(?P<episode>\d{3,4})").regex(
        r"v(?P<version>\d+)"
    ).repeater("?").regex(r"(?P<episodeSeparator>[x-])(?P<episode>\d{3,4})", abbreviations=None).repeater("*")

    # 1, 2, 3
    # The negative lookahead keeps a lone digit immediately glued to a "-<word>" out of the
    # episode list: that digit is the prefix of a dash-separated release group (e.g. the
    # obfuscation prefix in "x264.1-URANiME-Obfuscated", #627), not a single-digit episode.
    # A range ("1-2", digit-dash-digit) is unaffected.
    rebulk.chain(
        tags=["weak-episode"],
        disabled=lambda context: context.get("type") != "episode" or is_disabled(context, "episode"),
    ).defaults(validator=None, tags=["weak-episode"]).regex(r"(?P<episode>\d)(?!-[a-z])", abbreviations=None).regex(
        r"v(?P<version>\d+)"
    ).repeater("?").regex(r"(?P<episodeSeparator>[x-])(?P<episode>\d{1,2})", abbreviations=None).repeater("*")

    # e112, e113, 1e18, 3e19
    rebulk.chain(disabled=lambda context: is_disabled(context, "episode")).defaults(validator=None).regex(
        r"(?P<season>\d{1,2})?(?P<episodeMarker>e)(?P<episode>\d{1,4})"
    ).regex(r"v(?P<version>\d+)").repeater("?").regex(
        r"(?P<episodeSeparator>e|x|-)(?P<episode>\d{1,4})", abbreviations=None
    ).repeater("*")

    # ep 112, ep113, ep112, ep113
    rebulk.chain(disabled=lambda context: is_disabled(context, "episode")).defaults(validator=None).regex(
        r"ep-?(?P<episode>\d{1,4})"
    ).regex(r"v(?P<version>\d+)").repeater("?").regex(
        r"(?P<episodeSeparator>ep|e|x|-)(?P<episode>\d{1,4})", abbreviations=None
    ).repeater("*")

    # cap 112, cap 112_114
    rebulk.chain(tags=["see-pattern"], disabled=is_season_episode_disabled).defaults(
        validator=None, tags=["see-pattern"]
    ).regex(r"(?P<seasonMarker>cap)-?(?P<season>\d{1,2})(?P<episode>\d{2})").regex(
        r"(?P<episodeSeparator>-)(?P<season>\d{1,2})(?P<episode>\d{2})"
    ).repeater("?")

    # 102, 0102
    rebulk.chain(
        tags=["weak-episode", "weak-duplicate"],
        name="weak_duplicate",
        conflict_solver=season_episode_conflict_solver,
        disabled=lambda context: (
            (context.get("episode_prefer_number", False) or context.get("type") == "movie")
            or is_season_episode_disabled(context)
        ),
    ).defaults(
        tags=["weak-episode", "weak-duplicate"],
        name="weak_duplicate",
        validator=None,
        conflict_solver=season_episode_conflict_solver,
    ).regex(r"(?P<season>\d{1,2})(?P<episode>\d{2})").regex(r"v(?P<version>\d+)").repeater("?").regex(
        r"(?P<episodeSeparator>x|-)(?P<episode>\d{2})", abbreviations=None
    ).repeater("*")

    rebulk.regex(r"v(?P<version>\d+)", disabled=lambda context: is_disabled(context, "version"))

    rebulk.defaults(private_names=["episodeSeparator", "seasonSeparator"])

    # detached of X count (season/episode)
    rebulk.regex(
        r"(?P<episode>\d+)-?"
        + build_or_pattern(of_words)
        + r"-?(?P<count>\d+)-?"
        + build_or_pattern(episode_words)
        + "?",
        pre_match_processor=match_processors.strip,
        disabled=lambda context: is_disabled(context, "episode"),
    )

    rebulk.regex(
        r"Minisodes?",
        children=False,
        private_parent=False,
        name="episode_format",
        value="Minisode",
        disabled=lambda context: is_disabled(context, "episode_format"),
    )

    rebulk.rules(
        NumberFirstConflict(seps),
        WeakConflictSolver,
        RemoveInvalidSeason,
        RemoveInvalidEpisode,
        SeePatternRange([*range_separators, "_"]),
        EpisodeNumberSeparatorRange(range_separators),
        SeasonSeparatorRange(range_separators),
        RemoveWeakIfMovie(episode_words),
        RemoveMisleadingLoneDigitEpisode,
        RemoveWeakIfSxxExx,
        RemoveWeakDuplicate,
        EpisodeDetailValidator,
        RemoveDetachedEpisodeNumber,
        VersionValidator,
        RemoveWeak(episode_words),
        RenameToAbsoluteEpisode,
        CountValidator,
        EpisodeSingleDigitValidator,
        RenameToDiscMatch,
    )

    return rebulk


class NumberFirstConflict(Rule):
    """
    Arbitrate a number shared by a number-first keyword ("N KW2") and a
    word-first keyword ("KW1 N"), before the default conflict solver runs.

    A number sitting between two keywords binds to the following keyword only
    when the preceding word-first keyword itself owns a leading number-first
    match ("2 Sezon 7 Bölüm" -> the 7 is Bölüm's); otherwise it stays on the
    preceding keyword ("Temporada 1 Capitulo 25", "Show 2019 Сезон 1 Серия 5"
    -> the 1 is the season, the year is not a number-first marker). A
    number-first match also always wins over a weak guess on the same span.
    """

    priority = PRE_PROCESS + 1
    consequence = RemoveMatch

    def __init__(self, seps: str) -> None:
        super().__init__()
        self.seps = seps

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []

        def drop(match: Match) -> None:
            for item in (match.initiator, *match.initiator.children):
                if item not in to_remove:
                    to_remove.append(item)

        numfirst_matches = matches.tagged("numfirst", lambda m: m.name in ("season", "episode"))

        # A leading number-first number is a stray title number when its keyword is
        # directly followed by its own word-first number that no later keyword claims:
        # "Studio 60 Сезон 5" -> season 5, the 60 belongs to the title.
        for numfirst in numfirst_matches:
            marker = next(
                (child for child in numfirst.initiator.children if child.name in ("seasonMarker", "episodeMarker")),
                None,
            )
            if not marker:
                continue
            trailing = matches.next(
                marker,
                lambda m: (
                    m.name in ("season", "episode")
                    and not any(tag in m.tags for tag in ("numfirst", "weak-episode", "weak-duplicate"))
                ),
                index=0,
            )
            if (
                trailing
                and trailing.initiator.start <= marker.end
                and not matches.holes(marker.end, trailing.start, predicate=lambda h: (h.raw or "").strip(self.seps))
                and not matches.conflicting(trailing, lambda m: "numfirst" in m.tags or m.name == "year")
            ):
                drop(numfirst)

        # A number between two keywords binds to the following keyword only when the
        # preceding keyword owns a leading number-first match ("2 Sezon 7 Bölüm" ->
        # the 7 is Bölüm's); otherwise it stays on the preceding keyword. A
        # number-first match also always wins over a weak guess on the same span.
        for numfirst in numfirst_matches:
            if numfirst.initiator in to_remove:
                continue
            for other in matches.conflicting(
                numfirst, lambda m: m.name in ("season", "episode") and "numfirst" not in m.tags
            ):
                if other in to_remove:
                    continue
                if "weak-episode" in other.tags or "weak-duplicate" in other.tags:
                    to_remove.append(other)
                    continue
                leading = matches.previous(
                    other.initiator,
                    lambda m: m.name in ("season", "episode") and "numfirst" in m.tags,
                    index=0,
                )
                keyword_owns_number = bool(
                    leading
                    and leading.initiator not in to_remove
                    and not matches.holes(
                        leading.end, other.initiator.start, predicate=lambda h: (h.raw or "").strip(self.seps)
                    )
                )
                if keyword_owns_number:
                    drop(other)
                else:
                    drop(numfirst)
                    break

        return to_remove


class WeakConflictSolver(Rule):
    """
    Rule to decide whether weak-episode or weak-duplicate matches should be kept.

    If an anime is detected:
        - weak-duplicate matches should be removed
        - weak-episode matches should be tagged as anime
    Otherwise:
        - weak-episode matches are removed unless they're part of an episode range match.
    """

    priority = 128
    consequence = [RemoveMatch, AppendMatch]

    def enabled(self, context: dict[str, Any] | None) -> bool:
        return bool(context and context.get("type") != "movie")

    @classmethod
    def is_anime(cls, matches: Matches) -> bool:
        """Return True if it seems to be an anime.

        Anime characteristics:
            - version, crc32 matches
            - opening/ending credits (NCOP/NCED…), near-exclusive to anime
            - screen_size inside brackets
            - release_group at start and inside brackets
        """
        if matches.named("version") or matches.named("crc32"):
            return True

        if matches.named("other", predicate=lambda m: m.value in ("Opening Credits", "Ending Credits")):
            return True

        for group in matches.markers.named("group"):
            if matches.range(group.start, group.end, predicate=lambda m: m.name == "screen_size"):
                return True
            if matches.markers.starting(group.start, predicate=lambda m: m.name == "path"):
                hole = matches.holes(group.start, group.end, index=0)
                if hole and hole.raw == group.raw:
                    return True

        return False

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        to_append: list[Match] = []
        anime_detected = self.is_anime(matches)
        for filepart in matches.markers.named("path"):
            weak_matches = matches.range(
                filepart.start, filepart.end, predicate=(lambda m: m.initiator.name == "weak_episode")
            )
            weak_dup_matches = matches.range(
                filepart.start, filepart.end, predicate=(lambda m: m.initiator.name == "weak_duplicate")
            )
            if anime_detected:
                if weak_matches:
                    to_remove.extend(weak_dup_matches)
                    for match in matches.range(
                        filepart.start,
                        filepart.end,
                        predicate=(lambda m: m.name == "episode" and m.initiator.name != "weak_duplicate"),
                    ):
                        episode = copy.copy(match)
                        episode.tags = [*episode.tags, "anime"]
                        to_append.append(episode)
                        to_remove.append(match)
            elif weak_dup_matches:
                episodes_in_range = matches.range(
                    filepart.start,
                    filepart.end,
                    predicate=(
                        lambda m: (
                            m.name == "episode"
                            and m.initiator.name == "weak_episode"
                            and m.initiator.children.named("episodeSeparator")
                        )
                    ),
                )
                if not episodes_in_range and not matches.range(
                    filepart.start, filepart.end, predicate=lambda m: "SxxExx" in m.tags
                ):
                    to_remove.extend(weak_matches)
                else:
                    for match in episodes_in_range:
                        episode = copy.copy(match)
                        episode.tags = []
                        to_append.append(episode)
                        to_remove.append(match)

                if to_append:
                    to_remove.extend(weak_dup_matches)

        if to_remove or to_append:
            return to_remove, to_append
        return False


class CountValidator(Rule):
    """
    Validate count property and rename it
    """

    priority = 64
    consequence = [RemoveMatch, RenameMatch("episode_count"), RenameMatch("season_count")]

    properties = {"episode_count": [None], "season_count": [None]}

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        episode_count: list[Match] = []
        season_count: list[Match] = []

        for count in matches.named("count"):
            numbered = self._numbered_by(matches, count)
            if numbered is None:
                to_remove.append(count)
            elif numbered.name == "episode":
                episode_count.append(count)
            else:
                season_count.append(count)
        if to_remove or episode_count or season_count:
            return to_remove, episode_count, season_count
        return False

    @staticmethod
    def _numbered_by(matches: Matches, count: Match) -> Match | None:
        """The episode or season the count belongs to: the last one its own match holds.

        Scoped to the count's match rather than to the nearest neighbour, because another property
        can sit on the linking word itself — "de" is the German language code as much as it is the
        Spanish "of" — and would then hide the number the count completes.
        """
        numbers = matches.range(
            count.initiator.start, count.start, predicate=lambda match: match.name in ("episode", "season")
        )
        return numbers[-1] if numbers else None


class SeePatternRange(Rule):
    """
    Create matches for episode range for SEE pattern. E.g.: Cap.102_104
    """

    priority = 128
    consequence = [RemoveMatch, AppendMatch]

    def __init__(self, range_separators: list[str]) -> None:
        super().__init__()
        self.range_separators = range_separators

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        to_append: list[Match] = []

        for separator in matches.tagged("see-pattern", lambda m: m.name == "episodeSeparator"):
            previous_match = matches.previous(separator, lambda m: m.name == "episode" and "see-pattern" in m.tags, 0)
            next_match = matches.next(separator, lambda m: m.name == "season" and "see-pattern" in m.tags, 0)
            if not next_match:
                continue

            next_match = matches.next(next_match, lambda m: m.name == "episode" and "see-pattern" in m.tags, 0)
            if previous_match and next_match and separator.value in self.range_separators:
                to_remove.append(next_match)

                for episode_number in range(previous_match.value + 1, next_match.value + 1):
                    match = copy.copy(next_match)
                    match.value = episode_number
                    to_append.append(match)

            to_remove.append(separator)

        if to_remove or to_append:
            return to_remove, to_append
        return False


class AbstractSeparatorRange(Rule):
    """
    Remove separator matches and create matches for season range.
    """

    consequence = [RemoveMatch, AppendMatch]

    def __init__(self, range_separators: list[str], property_name: str) -> None:
        super().__init__()
        self.range_separators = range_separators
        self.property_name = property_name

    def _can_start_range(self, match: Match) -> bool:
        return True

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        to_append: list[Match] = []

        for separator in matches.named(self.property_name + "Separator"):
            previous_match = matches.previous(separator, lambda m: m.name == self.property_name, 0)
            next_match = matches.next(separator, lambda m: m.name == self.property_name, 0)
            initiator = separator.initiator

            if previous_match and next_match and separator.value in self.range_separators:
                to_remove.append(next_match)
                for episode_number in range(previous_match.value + 1, next_match.value):
                    match = copy.copy(next_match)
                    match.value = episode_number
                    initiator.children.append(match)
                    to_append.append(match)
                to_append.append(next_match)
            to_remove.append(separator)

        previous_match = None
        sorted_matches = sorted(matches.named(self.property_name), key=lambda x: x.span[0])
        for next_match in sorted_matches:
            if not previous_match and not self._can_start_range(next_match):
                continue
            if previous_match:
                gap = (matches.input_string or "")[previous_match.initiator.end : next_match.initiator.start]
                if gap not in self.range_separators:
                    gap = strip(gap)
                if gap in self.range_separators:
                    initiator = previous_match.initiator
                    for episode_number in range(previous_match.value + 1, next_match.value):
                        match = copy.copy(next_match)
                        match.value = episode_number
                        initiator.children.append(match)
                        to_append.append(match)
                    to_append.append(
                        Match(
                            previous_match.end,
                            next_match.start - 1,
                            name=self.property_name + "Separator",
                            private=True,
                            input_string=matches.input_string,
                        )
                    )
                to_remove.append(next_match)  # Remove and append match to support proper ordering
                to_append.append(next_match)

            previous_match = next_match

        if to_remove or to_append:
            return to_remove, to_append
        return False


class RenameToAbsoluteEpisode(Rule):
    """
    Rename episode to absolute_episodes.

    Absolute episodes are only used if two groups of episodes are detected:
        S02E04-06 25-27
        25-27 S02E04-06
        2x04-06  25-27
        28. Anime Name S02E05
    The matches in the group with higher episode values are renamed to absolute_episode.
    """

    consequence = [RenameMatch("absolute_episode"), RemoveMatch]

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        initiators = {
            match.initiator for match in matches.named("episode") if len(match.initiator.children.named("episode")) > 1
        }
        if len(initiators) != 2:
            ret: tuple[list[Match], list[Match]] = ([], [])
            for filepart in matches.markers.named("path"):
                sxxexx_episode_matches = matches.range(
                    filepart.start + 1, filepart.end, predicate=lambda m: m.name == "episode" and "SxxExx" in m.tags
                )
                if matches.range(filepart.start + 1, filepart.end, predicate=lambda m: m.name == "episode"):
                    absolute_episode_candidate = matches.starting(
                        filepart.start, predicate=lambda m: m.initiator.name == "weak_episode"
                    )
                    if sxxexx_episode_matches:
                        ret[1].extend(absolute_episode_candidate)
                    else:
                        ret[0].extend(absolute_episode_candidate)
            return ret

        sorted_initiators = sorted(initiators, key=lambda item: item.end)
        if not matches.holes(
            sorted_initiators[0].end, sorted_initiators[1].start, predicate=lambda m: (m.raw or "").strip(seps)
        ):
            first_range = matches.named("episode", predicate=lambda m: m.initiator == sorted_initiators[0])
            second_range = matches.named("episode", predicate=lambda m: m.initiator == sorted_initiators[1])
            if len(first_range) == len(second_range):
                if second_range[0].value > first_range[0].value:
                    return second_range, []
                if first_range[0].value > second_range[0].value:
                    return first_range, []
        return None


class EpisodeNumberSeparatorRange(AbstractSeparatorRange):
    """
    Remove separator matches and create matches for episoderNumber range.
    """

    priority = 128

    def __init__(self, range_separators: list[str]) -> None:
        super().__init__(range_separators, "episode")

    def _can_start_range(self, match: Match) -> bool:
        return "weak-episode" not in match.tags


class SeasonSeparatorRange(AbstractSeparatorRange):
    """
    Remove separator matches and create matches for season range.
    """

    priority = 128

    def __init__(self, range_separators: list[str]) -> None:
        super().__init__(range_separators, "season")


class RemoveWeakIfMovie(Rule):
    """
    Remove weak-episode tagged matches if it seems to be a movie.

    A year in the part is a movie signal strong enough to drop the weak readings, whatever the
    requested type: forcing `type=episode` must not turn the leading number of a title into an
    episode ("12.Angry.Men.1957" stays "12 Angry Men" + year 1957). Weak matches carrying an
    explicit marker ("Episodio 13") are numbered on purpose and stay (#939).
    """

    priority = 64
    consequence = RemoveMatch

    def __init__(self, episode_words: list[str]) -> None:
        super().__init__()
        self.episode_words = episode_words

    def _is_numbered_on_purpose(self, matches: Matches, match: Match) -> bool:
        """Whether the number carries an explicit marker ("Episodio 13", "S01E02")."""
        initiator = match.initiator
        if initiator is not None and (
            initiator.children.named("episodeMarker") or initiator.children.named("seasonMarker")
        ):
            return True

        # The word must sit in the same filepart: a parent directory named "Episode" says nothing
        # about a number in the filename below it.
        filepart = matches.markers.at_match(match, lambda marker: marker.name == "path", 0)
        start = filepart.start if filepart else 0
        preceding = (match.input_string or "")[start : match.start].strip(seps)
        if not preceding:
            return False
        return _SEPS_RE.split(preceding)[-1].lower() in self.episode_words

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        to_ignore: set[Match] = set()
        remove = False
        for filepart in matches.markers.named("path"):
            year = matches.range(filepart.start, filepart.end, predicate=lambda m: m.name == "year", index=0)
            if year:
                remove = True
                next_match = matches.range(year.end, filepart.end, predicate=lambda m: m.private, index=0)
                if (
                    next_match
                    and not matches.holes(year.end, next_match.start, predicate=lambda m: (m.raw or "").strip(seps))
                    and not matches.at_match(next_match, predicate=lambda m: m.name == "year")
                ):
                    to_ignore.add(next_match.initiator)

                to_ignore.update(
                    matches.range(
                        filepart.start, filepart.end, predicate=lambda m: len(m.children.named("episode")) > 1
                    )
                )

                to_remove.extend(matches.conflicting(year))
        if remove:
            to_remove.extend(
                matches.tagged(
                    "weak-episode",
                    predicate=(
                        lambda m: (
                            m.initiator not in to_ignore
                            and "anime" not in m.tags
                            and not self._is_numbered_on_purpose(matches, m)
                        )
                    ),
                )
            )

        return to_remove


class RemoveWeak(Rule):
    """
    Remove weak-episode matches which appears after video, source, and audio matches.
    """

    priority = 16
    consequence = RemoveMatch, AppendMatch

    def __init__(self, episode_words: list[str]) -> None:
        super().__init__()
        self.episode_words = episode_words

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        to_append: list[Match] = []
        for filepart in matches.markers.named("path"):
            weaks = matches.range(filepart.start, filepart.end, predicate=lambda m: "weak-episode" in m.tags)
            if weaks:
                weak = weaks[0]
                previous = matches.previous(
                    weak,
                    predicate=lambda m: (
                        m.name
                        in (
                            "audio_codec",
                            "screen_size",
                            "streaming_service",
                            "source",
                            "video_profile",
                            "audio_channels",
                            "audio_profile",
                        )
                    ),
                    index=0,
                )
                if previous and not matches.holes(
                    previous.end, weak.start, predicate=lambda m: (m.raw or "").strip(seps)
                ):
                    if (previous.raw or "").lower() in self.episode_words:
                        try:
                            episode = copy.copy(weak)
                            episode.name = "episode"
                            episode.value = int(weak.value)
                            episode.start = previous.start
                            episode.private = False
                            episode.tags = []

                            to_append.append(episode)
                        except ValueError:
                            pass

                    to_remove.extend(weaks)
        if to_remove or to_append:
            return to_remove, to_append
        return False


class RemoveMisleadingLoneDigitEpisode(Rule):
    """
    Remove a lone digit read as an episode while it plainly numbers something else.

    Only a forced `type=episode` reads a single digit as an episode, and that pattern fires
    wherever a digit sits — including inside a release group, in a parent directory, or in the
    tail of a title — where it then evicts whatever owned that span. Such a digit is discarded
    when it cannot be part of the episode numbering: quoted in a bracketed group, sitting in a
    non-final path part, behind the dot of a decimal number, or unable to extend a marked episode
    list (a list grows rightwards from its marker and stays glued to it, as in "E01 02 03")
    (#943, #948).

    Runs before anything is carved out of the name (rebulk executes rules by decreasing priority),
    so the freed span goes back to the title instead of leaving a hole behind.
    """

    priority = PRE_PROCESS + 1
    consequence = RemoveMatch

    def enabled(self, context: dict[str, Any] | None) -> bool:
        return bool(context and context.get("type") == "episode")

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        fileparts = matches.markers.named("path")
        for index, filepart in enumerate(fileparts):
            episodes_ = sorted(
                matches.range(filepart.start, filepart.end, predicate=lambda m: m.name == "episode"),
                key=lambda m: (m.start, m.end),
            )
            in_final_part = index == len(fileparts) - 1
            misplaced = [
                episode
                for episode in episodes_
                if self._is_lone_digit(episode)
                and (
                    self._numbers_something_else(matches, episode, in_final_part) or self._fraction_of_a_number(episode)
                )
            ]
            kept = [episode for episode in episodes_ if episode not in misplaced]
            misplaced.extend(self._detached_from_list(kept))

            for episode in misplaced:
                to_remove.extend(self._whole_match(matches, episode))

        return to_remove

    @staticmethod
    def _is_lone_digit(episode: Match) -> bool:
        return "weak-episode" in episode.tags and len(episode.raw or "") == 1

    @staticmethod
    def _numbers_something_else(matches: Matches, episode: Match, in_final_part: bool) -> bool:
        """A digit numbering a parent directory ("/Volumes/data-1/…") or a quoted group ("[t.3.3.d]")."""
        quoted = matches.markers.at_match(episode, lambda marker: marker.name == "group", 0)
        return not in_final_part or bool(quoted)

    @staticmethod
    def _fraction_of_a_number(episode: Match) -> bool:
        """A digit behind the dot of a decimal number ("02.5"): a half episode, not a second one."""
        before = (episode.input_string or "")[: episode.start]
        return len(before) > 1 and before[-1] == "." and before[-2].isdigit()

    @classmethod
    def _detached_from_list(cls, episodes_: list[Match]) -> list[Match]:
        """Lone digits that cannot extend the marked episode list of their filepart."""
        anchor = next((episode for episode in episodes_ if "weak-episode" not in episode.tags), None)
        if anchor is None:
            return []

        detached: list[Match] = []
        previous = anchor
        for episode in episodes_:
            if episode.end <= anchor.start:
                if cls._is_lone_digit(episode):
                    detached.append(episode)
                continue

            between = (episode.input_string or "")[previous.end : episode.start].strip(seps)
            if between and cls._is_lone_digit(episode):
                detached.append(episode)
            else:
                previous = episode

        return detached

    @staticmethod
    def _whole_match(matches: Matches, episode: Match) -> list[Match]:
        """The match and the private ones holding its span, so the freed text becomes a hole again."""
        return matches.range(
            episode.start,
            episode.end,
            predicate=lambda m: "weak-episode" in m.tags and m.start >= episode.start and m.end <= episode.end,
        )


class RemoveWeakIfSxxExx(Rule):
    """
    Remove weak-episode tagged matches if SxxExx pattern is matched.

    Weak episodes at beginning of filepart are kept.
    """

    priority = 64
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        for filepart in matches.markers.named("path"):
            if matches.range(filepart.start, filepart.end, predicate=lambda m: not m.private and "SxxExx" in m.tags):
                for match in matches.range(filepart.start, filepart.end, predicate=lambda m: "weak-episode" in m.tags):
                    if match.start != filepart.start or match.initiator.name != "weak_episode":
                        to_remove.append(match)
        return to_remove


class RemoveInvalidSeason(Rule):
    """
    Remove invalid season matches.
    """

    priority = 64
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        for filepart in matches.markers.named("path"):
            strong_season = matches.range(
                filepart.start,
                filepart.end,
                index=0,
                predicate=lambda m: m.name == "season" and not m.private and "SxxExx" in m.tags,
            )
            if strong_season and strong_season.initiator.children.named("episode"):
                for season in matches.range(
                    strong_season.end, filepart.end, predicate=lambda m: m.name == "season" and not m.private
                ):
                    # remove weak season or seasons without episode matches
                    if "SxxExx" not in season.tags or not season.initiator.children.named("episode"):
                        if season.initiator:
                            to_remove.append(season.initiator)
                            to_remove.extend(season.initiator.children)
                        else:
                            to_remove.append(season)

        return to_remove


class RemoveInvalidEpisode(Rule):
    """
    Remove invalid episode matches.
    """

    priority = 64
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        for filepart in matches.markers.named("path"):
            strong_episode = matches.range(
                filepart.start,
                filepart.end,
                index=0,
                predicate=lambda m: m.name == "episode" and not m.private and "SxxExx" in m.tags,
            )
            if strong_episode:
                strong_ep_marker = RemoveInvalidEpisode.get_episode_prefix(matches, strong_episode)
                for episode in matches.range(
                    strong_episode.end, filepart.end, predicate=lambda m: m.name == "episode" and not m.private
                ):
                    ep_marker = RemoveInvalidEpisode.get_episode_prefix(matches, episode)
                    if strong_ep_marker and ep_marker and strong_ep_marker.value.lower() != ep_marker.value.lower():
                        if episode.initiator:
                            to_remove.append(episode.initiator)
                            to_remove.extend(episode.initiator.children)
                        else:
                            to_remove.append(ep_marker)
                            to_remove.append(episode)

        return to_remove

    @staticmethod
    def get_episode_prefix(matches: Matches, episode: Match) -> Any:
        """
        Return episode prefix: episodeMarker or episodeSeparator
        """
        return matches.previous(episode, index=0, predicate=lambda m: m.name in ("episodeMarker", "episodeSeparator"))


class RemoveWeakDuplicate(Rule):
    """
    Remove weak-duplicate tagged matches if duplicate patterns, for example The 100.109
    """

    priority = 64
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        for filepart in matches.markers.named("path"):
            patterns: defaultdict[Any, list[Any]] = defaultdict(list)
            for match in reversed(
                matches.range(filepart.start, filepart.end, predicate=lambda m: "weak-duplicate" in m.tags)
            ):
                if match.pattern in patterns[match.name]:
                    to_remove.append(match)
                else:
                    patterns[match.name].append(match.pattern)
        return to_remove


class EpisodeDetailValidator(Rule):
    """
    Validate episode_details if they are detached or next to season or episode.
    """

    priority = 64
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        ret: list[Match] = []
        for detail in matches.named("episode_details"):
            if (
                not seps_surround(detail)
                and not matches.previous(detail, lambda match: match.name in ["season", "episode"])
                and not matches.next(detail, lambda match: match.name in ["season", "episode"])
            ):
                ret.append(detail)
        return ret


class RemoveDetachedEpisodeNumber(Rule):
    """
    If multiple episode are found, remove those that are not detached from a range and less than 10.

    Fairy Tail 2 - 16-20, 2 should be removed.
    """

    priority = 64
    consequence = RemoveMatch
    dependency = [RemoveWeakIfSxxExx, RemoveWeakDuplicate]

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        ret: list[Match] = []

        episode_numbers: list[Match] = []
        episode_values: set[Any] = set()
        for match in matches.named("episode", lambda m: not m.private and "weak-episode" in m.tags):
            if match.value not in episode_values:
                episode_numbers.append(match)
                episode_values.add(match.value)

        episode_numbers = sorted(episode_numbers, key=lambda m: m.value)
        if (
            len(episode_numbers) > 1
            and episode_numbers[0].value < 10
            and episode_numbers[1].value - episode_numbers[0].value != 1
        ):
            parent: Match | None = episode_numbers[0]
            while parent:
                ret.append(parent)
                parent = parent.parent
        return ret


class VersionValidator(Rule):
    """
    Validate version if previous match is episode or if surrounded by separators.
    """

    priority = 64
    dependency = [RemoveWeakIfMovie, RemoveWeakIfSxxExx]
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        ret: list[Match] = []
        for version in matches.named("version"):
            episode_number = matches.previous(version, lambda match: match.name == "episode", 0)
            if not episode_number and not seps_surround(version.initiator):
                ret.append(version)
        return ret


class EpisodeSingleDigitValidator(Rule):
    """
    Remove single digit episode when inside a group that doesn't own title.
    """

    dependency = [TitleFromPosition]

    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        ret: list[Match] = []
        for episode in matches.named("episode", lambda match: len(match.initiator) == 1):
            group = matches.markers.at_match(episode, lambda marker: marker.name == "group", index=0)
            if group and not matches.range(group.span[0], group.span[1], predicate=lambda match: match.name == "title"):
                ret.append(episode)
        return ret


class RenameToDiscMatch(Rule):
    """
    Rename episodes detected with `d` episodeMarkers to `disc`.
    """

    consequence = [RenameMatch("disc"), RenameMatch("discMarker"), RemoveMatch]

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        discs: list[Match] = []
        markers: list[Match] = []
        to_remove: list[Match] = []

        disc_disabled = is_disabled(context, "disc")

        for marker in matches.named("episodeMarker", predicate=lambda m: m.value.lower() == "d"):
            if disc_disabled:
                to_remove.append(marker)
                to_remove.extend(marker.initiator.children)
                continue

            markers.append(marker)
            discs.extend(sorted(marker.initiator.children.named("episode"), key=lambda m: m.value))

        if discs or markers or to_remove:
            return discs, markers, to_remove
        return False

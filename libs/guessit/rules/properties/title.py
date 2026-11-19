#!/usr/bin/env python
"""
title property
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from rebulk import POST_PROCESS, AppendMatch, AppendTags, Rebulk, RemoveMatch, Rule
from rebulk.formatters import formatters
from rebulk.match import Match
from rebulk.remodule import re

from ..common import seps, title_seps
from ..common.comparators import marker_sorted
from ..common.expected import build_expected_function
from ..common.formatters import cleanup, reorder_title
from ..common.pattern import is_disabled
from ..common.validators import seps_surround
from .film import FilmTitleRule
from .language import (
    NON_SPECIFIC_LANGUAGES,
    SubtitleExtensionRule,
    SubtitlePrefixLanguageRule,
    SubtitleSuffixLanguageRule,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from rebulk.match import Matches

# Tags that mark a country/other match as a recognized release tag (edition, scene or
# streaming-service keyword) rather than a real title word — such a token must never be
# relabelled as the title even when it sits at the title position.
RELEASE_TAG_MARKERS = ("release-group-prefix", "streaming_service.prefix", "streaming_service.suffix")

# Non-Latin scripts used for original-language titles glued in front of a romanized title
# (CJK, kana, hangul, Cyrillic, Greek, Arabic, Hebrew, Thai, fullwidth forms). Latin-1 accented
# letters (à, ñ, …) are deliberately excluded — they are Latin-script title characters.
NON_LATIN_SCRIPT_RE = re.compile(
    r"[Ͱ-ϿЀ-ӿ֐-׿؀-ۿ฀-๿"
    r"　-〿぀-ヿ㐀-䶿一-鿿가-힯＀-￯]"
)


def title(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    articles = frozenset(config.get("articles", ()))
    title_stop_words = frozenset(config.get("title_stop_words", ()))

    rebulk = Rebulk(disabled=lambda context: is_disabled(context, "title"))
    rebulk.rules(
        CountryAtTitlePosition,
        TitleWordAtTitlePosition,
        TitleFromPosition,
        PreferTitleWithYear,
        ExtendLoneArticleTitle(articles),
        PropertyAtTitlePositionAsTitle,
        KeepTrailingStopWordTitle(title_stop_words),
        SplitOriginalScriptTitle,
    )

    expected_title = build_expected_function("expected_title")

    rebulk.functional(
        expected_title,
        name="title",
        tags=["expected", "title"],
        validator=seps_surround,
        formatter=formatters(cleanup, reorder_title),
        conflict_solver=lambda match, other: other,
        disabled=lambda context: not context.get("expected_title"),
    )

    return rebulk


class TitleBaseRule(Rule):
    """
    Add title match in existing matches
    """

    consequence = [AppendMatch, RemoveMatch]

    def __init__(
        self, match_name: str, match_tags: list[str] | None = None, alternative_match_name: str | None = None
    ) -> None:
        super().__init__()
        self.match_name = match_name
        self.match_tags = match_tags
        self.alternative_match_name = alternative_match_name

    def hole_filter(self, hole: Match, matches: Matches) -> bool:
        """
        Filter holes for titles.
        :param hole:
        :type hole:
        :param matches:
        :type matches:
        :return:
        :rtype:
        """
        return True

    def filepart_filter(self, filepart: Match, matches: Matches) -> bool:
        """
        Filter filepart for titles.
        :param filepart:
        :type filepart:
        :param matches:
        :type matches:
        :return:
        :rtype:
        """
        return True

    def holes_process(self, holes: list[Match], matches: Matches) -> list[Match]:
        """
        process holes
        :param holes:
        :type holes:
        :param matches:
        :type matches:
        :return:
        :rtype:
        """
        cropped_holes: list[Match] = []
        group_markers = matches.markers.named("group")
        for group_marker in group_markers:
            path_marker = matches.markers.at_match(group_marker, predicate=lambda m: m.name == "path", index=0)
            if path_marker and path_marker.span == group_marker.span:
                group_markers.remove(group_marker)

        for hole in holes:
            cropped_holes.extend(hole.crop(group_markers))

        return cropped_holes

    @staticmethod
    def _hole_has_title_text(hole: Match, ignored_matches: list[Match]) -> bool:
        """
        Whether a title hole holds any real title text once the ignored matches
        (languages/countries) are removed. A hole fully covered by ignored matches
        is just a language/country enumeration, not a title.
        """
        input_string = hole.input_string or ""
        covered: set[int] = set()
        for ignored in ignored_matches:
            covered.update(range(ignored.start, ignored.end))
        return any(index not in covered and input_string[index] not in seps for index in range(hole.start, hole.end))

    @staticmethod
    def is_ignored(match: Match) -> bool:
        """
        Ignore matches when scanning for title (hole).

        Full word language and countries won't be ignored if they are uppercase.
        """
        return not (len(match) > 3 and match.raw is not None and match.raw.isupper()) and match.name in (
            "language",
            "country",
            "episode_details",
        )

    def should_keep(
        self, match: Match, to_keep: list[Match], matches: Matches, filepart: Match, hole: Match, starting: bool
    ) -> Any:
        """
        Check if this match should be accepted when ending or starting a hole.
        :param match:
        :type match:
        :param to_keep:
        :type to_keep: list[Match]
        :param matches:
        :type matches: Matches
        :param hole: the filepart match
        :type hole: Match
        :param hole: the hole match
        :type hole: Match
        :param starting: true if match is starting the hole
        :type starting: bool
        :return:
        :rtype:
        """
        if match.name in ("language", "country"):
            # Keep language if exactly matching the hole.
            if len(hole.value) == len(match.raw or ""):
                return True

            # Keep language if other languages exists in the filepart.
            outside_matches = filepart.crop(hole)
            other_languages: list[Match] = []
            for outside in outside_matches:
                other_languages.extend(
                    matches.range(
                        outside.start,
                        outside.end,
                        lambda c_match: (
                            c_match.name == match.name
                            and c_match not in to_keep
                            and c_match.value not in NON_SPECIFIC_LANGUAGES
                        ),
                    )
                )

            if not other_languages and (not starting or len(match.raw or "") <= 3):
                return True

        return False

    def should_remove(
        self, match: Match, matches: Matches, filepart: Match, hole: Match, context: dict[str, Any] | None
    ) -> bool:
        """
        Check if this match should be removed after beeing ignored.
        :param match:
        :param matches:
        :param filepart:
        :param hole:
        :return:
        """
        if context and context.get("type") == "episode" and match.name == "episode_details":
            return match.start >= hole.start and match.end <= hole.end
        return True

    def check_titles_in_filepart(
        self,
        filepart: Match,
        matches: Matches,
        context: dict[str, Any] | None,
        additional_ignored: Callable[[Match], bool] | None = None,
    ) -> Any:
        """
        Find title in filepart (ignoring language)
        """
        start, end = filepart.span

        holes = matches.holes(
            start,
            end + 1,
            formatter=formatters(cleanup, reorder_title),
            ignore=self.is_ignored
            if additional_ignored is None
            else lambda m: self.is_ignored(m) or additional_ignored(m),
            predicate=lambda m: m.value,
        )

        holes = self.holes_process(holes, matches)

        for hole in holes:
            if not hole or not self.hole_filter(hole, matches):
                continue

            to_remove: list[Match] = []
            to_keep: list[Match] = []

            ignored_matches = matches.range(hole.start, hole.end, self.is_ignored)

            # A hole made up entirely of languages/countries is not a real title
            # (e.g. "Ita Eng" between codecs, #751): keep the languages rather than
            # fabricating a title out of them and deleting them. episode_details
            # ("Pilot", "Special") are excluded: those legitimately become episode_title.
            if (
                ignored_matches
                and all(ignored.name in ("language", "country") for ignored in ignored_matches)
                and not self._hole_has_title_text(hole, ignored_matches)
            ):
                continue

            if ignored_matches:
                for ignored_match in reversed(ignored_matches):
                    # Closure consumed within this iteration; late binding (B023) is intentional.
                    trailing = matches.chain_before(hole.end, seps, predicate=lambda m: m == ignored_match)  # noqa: B023
                    if trailing:
                        should_keep = self.should_keep(ignored_match, to_keep, matches, filepart, hole, False)
                        if should_keep:
                            try:
                                append, crop = should_keep
                            except TypeError:
                                append, crop = should_keep, should_keep
                            if append:
                                to_keep.append(ignored_match)
                            if crop:
                                hole.end = ignored_match.start

                for ignored_match in ignored_matches:
                    if ignored_match not in to_keep:
                        starting = matches.chain_after(hole.start, seps, predicate=lambda m: m == ignored_match)  # noqa: B023
                        if starting:
                            should_keep = self.should_keep(ignored_match, to_keep, matches, filepart, hole, True)
                            if should_keep:
                                try:
                                    append, crop = should_keep
                                except TypeError:
                                    append, crop = should_keep, should_keep
                                if append:
                                    to_keep.append(ignored_match)
                                if crop:
                                    hole.start = ignored_match.end

            for match in ignored_matches:
                if self.should_remove(match, matches, filepart, hole, context):
                    to_remove.append(match)
            for keep_match in to_keep:
                if keep_match in to_remove:
                    to_remove.remove(keep_match)

            if hole and hole.value:
                hole.name = self.match_name
                hole.tags = list(self.match_tags or [])
                if self.alternative_match_name and not is_disabled(context, self.alternative_match_name):
                    # Split and keep values that can be a title
                    titles = hole.split(title_seps, lambda m: m.value)
                    for title_match in list(titles[1:]):
                        previous_title = titles[titles.index(title_match) - 1]
                        separator = (matches.input_string or "")[previous_title.end : title_match.start]
                        if (
                            len(separator) == 1
                            and separator == "-"
                            and previous_title.raw is not None
                            and previous_title.raw[-1] not in seps
                            and title_match.raw is not None
                            and title_match.raw[0] not in seps
                        ):
                            titles[titles.index(title_match) - 1].end = title_match.end
                            titles.remove(title_match)
                        else:
                            title_match.name = self.alternative_match_name

                else:
                    titles = [hole]
                return titles, to_remove
        return None

    def _serie_name_filepart(self, matches: Matches, fileparts: list[Match]) -> Match | None:
        # Try to get show title from subdirectory of a season only directory (Show Name/Season 1/episode_title.avi)
        for index in range(len(fileparts) - 1):
            if index == 0:
                continue
            filepart = fileparts[index]
            filepart_matches = [m for m in matches.range(filepart.start, filepart.end) if not m.private]
            if (
                len(filepart_matches) == 1
                and filepart_matches[0].name == "season"
                and (
                    filepart_matches[0].span == filepart.span
                    or (filepart_matches[0].parent and filepart_matches[0].parent.span == filepart.span)
                )
            ):
                # Filepath match season match exactly
                return fileparts[index + 1]
        return None

    def _serie_name_filepart_match(
        self,
        matches: Matches,
        context: dict[str, Any] | None,
        serie_name_filepart: Match,
        to_append: list[Match],
        to_remove: list[Match],
    ) -> Any:
        def serie_name_filepart_ignored(match: Match) -> bool:
            return any(tag == "weak" or tag.startswith("weak-") for tag in match.tags)

        titles = self.check_titles_in_filepart(serie_name_filepart, matches, context, serie_name_filepart_ignored)
        if titles:
            titles, to_remove_c = titles
            if len(titles) == 1:
                to_append.extend(titles)
                to_remove.extend(to_remove_c)
                return titles[0]
        return None

    def _year_fileparts(self, matches: Matches, fileparts: list[Match]) -> list[Match]:
        year_fileparts: list[Match] = []
        for filepart in fileparts:
            year_match = matches.range(filepart.start, filepart.end, lambda match: match.name == "year", 0)
            if year_match:
                year_fileparts.append(filepart)
        return year_fileparts

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_append: list[Match] = []
        to_remove: list[Match] = []

        if matches.named(self.match_name, lambda match: "expected" in match.tags):
            return False

        fileparts = [
            filepart
            for filepart in list(marker_sorted(matches.markers.named("path"), matches))
            if self.filepart_filter(filepart, matches)
        ]

        serie_name_filepart = self._serie_name_filepart(matches, fileparts)

        serie_name_filepath_match = None
        if serie_name_filepart:
            serie_name_filepath_match = self._serie_name_filepart_match(
                matches, context, serie_name_filepart, to_append, to_remove
            )

        # Force inclusion of fileparts containing the year
        year_fileparts = self._year_fileparts(matches, fileparts)

        for filepart in fileparts:
            with contextlib.suppress(ValueError):
                year_fileparts.remove(filepart)
            titles = self.check_titles_in_filepart(filepart, matches, context)
            if titles:
                titles, to_remove_c = titles
                if serie_name_filepath_match:
                    for title_match in titles:
                        if title_match.value != serie_name_filepath_match.value:
                            title_match.name = "episode_title"
                to_append.extend(titles)
                to_remove.extend(to_remove_c)
                break

        # Add title match in all fileparts containing the year.
        for filepart in year_fileparts:
            titles = self.check_titles_in_filepart(filepart, matches, context)
            if titles:
                titles, to_remove_c = titles
                to_append.extend(titles)
                to_remove.extend(to_remove_c)

        if to_append or to_remove:
            return to_append, to_remove
        return False


class TitleFromPosition(TitleBaseRule):
    """
    Add title match in existing matches
    """

    dependency = [FilmTitleRule, SubtitlePrefixLanguageRule, SubtitleSuffixLanguageRule, SubtitleExtensionRule]

    properties = {"title": [None], "alternative_title": [None]}

    def __init__(self) -> None:
        super().__init__("title", ["title"], "alternative_title")


class PreferTitleWithYear(Rule):
    """
    Prefer title where filepart contains year.
    """

    dependency = TitleFromPosition
    consequence = [RemoveMatch, AppendTags(["equivalent-ignore"])]

    properties = {"title": [None]}

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        with_year_in_group: list[Match] = []
        with_year: list[Match] = []
        titles = matches.named("title")

        for title_match in titles:
            filepart = matches.markers.at_match(title_match, lambda marker: marker.name == "path", 0)
            if filepart:
                year_match = matches.range(filepart.start, filepart.end, lambda match: match.name == "year", 0)
                if year_match:
                    group = matches.markers.at_match(year_match, lambda m: m.name == "group")
                    if group:
                        with_year_in_group.append(title_match)
                    else:
                        with_year.append(title_match)

        to_tag: list[Match] = []
        if with_year_in_group:
            title_values = {title_match.value for title_match in with_year_in_group}
            to_tag.extend(with_year_in_group)
        elif with_year:
            title_values = {title_match.value for title_match in with_year}
            to_tag.extend(with_year)
        else:
            title_values = {title_match.value for title_match in titles}

        to_remove: list[Match] = []
        for title_match in titles:
            if title_match.value not in title_values:
                to_remove.append(title_match)
        if to_remove or to_tag:
            return to_remove, to_tag
        return False


class CountryAtTitlePosition(Rule):
    """
    A Title-Case country/other word that starts the filepart and opens the title is really
    part of the title, not a tag (upstream #638, #928).

    It qualifies when the word is followed, before the next year/season/episode/date anchor,
    by only separators ("Us.2019...") or by plain title text ("Au bout c'est la mer - 8x01").
    Another property in that gap ("Au.HDTV.8x01") means the word is a genuine tag.

    The casing anchor is load-bearing: "Us" (Title-Case) is the title, but "US" (a real
    country tag) is kept, so "The.Office.(US).1x03" keeps country: US. An ``edition`` or a
    scene/streaming release tag (e.g. Extended, Proper) is a property, never a title.
    """

    priority = 64
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        input_string = matches.input_string or ""
        to_remove: list[Match] = []
        for candidate in matches.range(
            0, len(input_string), lambda m: not m.private and m.name in ("country", "other")
        ):
            if not re.match(r"^[A-Z][a-z]+$", candidate.raw or ""):
                continue
            if candidate.tagged(*RELEASE_TAG_MARKERS):
                continue
            # A bracketed token ([Us]) is a deliberate tag/group, not the title.
            if matches.markers.at_match(candidate, lambda marker: marker.name == "group", 0):
                continue
            filepart = matches.markers.at_match(candidate, lambda m: m.name == "path", 0)
            if not filepart:
                continue
            if not all(ch in seps for ch in input_string[filepart.start : candidate.start]):
                continue
            anchor = matches.range(
                candidate.end,
                filepart.end,
                lambda m: not m.private and m.name in ("year", "season", "episode", "date"),
                0,
            )
            if not anchor:
                continue
            if not all(ch in seps for ch in input_string[candidate.end : anchor.start]):
                # Plain title text between the leading word and the anchor means the word
                # opens that title ("Au bout c'est la mer - 8x01"). Another property in the
                # gap ("Au.HDTV.8x01") means the word is a real tag, not the title.
                if matches.range(candidate.end, anchor.start, lambda m: not m.private and m.value is not None, 0):
                    continue
            to_remove.append(candidate)
        return to_remove


class TitleWordAtTitlePosition(Rule):
    """
    A property value whose spelling is also a plain title word (tagged ``title-word`` in the
    vocabulary, e.g. audio_codec "Opus") is really part of the title when it sits in the title
    zone -- before the first year/season/episode/date anchor of the file part. Removing the
    property match reopens the title hole so the normal title logic keeps the word, whether it
    leads, ends or sits in the middle of the title: ``Opus.2025...`` -> "Opus",
    ``Foo.Opus.2025...`` -> "Foo Opus", ``Foo.Opus.Bar.2025...`` -> "Foo Opus Bar".

    Property-agnostic: any property can opt a value in by tagging it ``title-word``. The anchor
    is load-bearing (not the casing): a real codec/tag always sits *after* the year/episode
    marker, so a ``title-word`` before the anchor cannot be the property regardless of case
    ("opus", "Opus" or "OPUS" all read as the title here). A spelling that appears after the
    anchor, among the other tags, stays the property.
    """

    priority = 64
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        for candidate in matches.tagged("title-word"):
            if candidate.private:
                continue
            filepart = matches.markers.at_match(candidate, lambda marker: marker.name == "path", 0)
            if not filepart:
                continue
            anchor = matches.range(
                filepart.start,
                filepart.end,
                lambda m: not m.private and m.name in ("year", "season", "episode", "date"),
                0,
            )
            if not anchor or candidate.start >= anchor.start:
                continue
            to_remove.append(candidate)
        return to_remove


class ExtendLoneArticleTitle(Rule):
    """
    A title or episode_title made of a single article ("The") swallows the following edition/
    language/country/other/source word (upstream #652, #737, #743): "The" + edition "Collector"
    -> "The Collector"; "Chapter.19.The.Convert" -> episode_title "The Convert".
    """

    priority = -32
    consequence = RemoveMatch

    def __init__(self, articles: frozenset[str]) -> None:
        super().__init__()
        self.articles = articles

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        input_string = matches.input_string or ""
        ret: list[tuple[Match, Match]] = []
        for title_match in matches.named("title", "episode_title"):
            if str(title_match.value or "").strip().lower() not in self.articles:
                continue
            filepart = matches.markers.at_match(title_match, lambda m: m.name == "path", 0)
            if not filepart:
                continue
            prop = matches.range(
                title_match.end,
                filepart.end,
                lambda m: not m.private and m.name in ("edition", "language", "country", "other", "source"),
                0,
            )
            if not prop:
                continue
            # A bracketed property ([Collector]) is a deliberate tag/group, not part of the title.
            if matches.markers.at_match(prop, lambda marker: marker.name == "group", 0):
                continue
            if not all(ch in seps for ch in input_string[title_match.end : prop.start]):
                continue
            following = matches.range(
                prop.end,
                filepart.end,
                lambda m: not m.private and m.name in ("year", "season", "episode", "date"),
                0,
            )
            if following:
                # The gap may hold season/episode marker letters (S/E/x/d) and separators,
                # but no real title text — otherwise the article is not a lone title.
                gap = re.sub(r"[sexd]", "", input_string[prop.end : following.start], flags=re.IGNORECASE)
                if any(ch not in seps for ch in gap):
                    continue
            ret.append((title_match, prop))
        return ret

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> None:
        input_string = matches.input_string or ""
        for title_match, prop in when_response:
            matches.remove(title_match)
            matches.remove(prop)
            title_match.end = prop.end
            title_match.value = cleanup(input_string[title_match.start : title_match.end])
            matches.append(title_match)


class PropertyAtTitlePositionAsTitle(Rule):
    """
    A leading other/country word becomes the title when the filepart has no title but does
    have a year/season/episode/date anchor after it (upstream #722, #773).

    Excludes editions and scene/streaming release tags (Extended, Proper, ...) which are
    properties, never titles; a leading country must be Title-Case ("Us", not "US").
    """

    priority = -48
    consequence = AppendMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        input_string = matches.input_string or ""
        to_replace: list[Match] = []
        for filepart in matches.markers.named("path"):
            if matches.range(filepart.start, filepart.end, lambda m: m.name == "title", 0):
                continue
            anchor = matches.range(
                filepart.start,
                filepart.end,
                lambda m: not m.private and m.name in ("year", "season", "episode", "date"),
                0,
            )
            if not anchor:
                continue
            lead = matches.range(filepart.start, filepart.end, lambda m: not m.private and m.value, 0)
            if not lead or lead.name not in ("other", "country"):
                continue
            # Only an alphabetic token reads as a real title; a technical "other" such as "3D"
            # stays a property, and so does a recognized scene/streaming release tag.
            if not (lead.raw or "").isalpha():
                continue
            if lead.tagged(*RELEASE_TAG_MARKERS):
                continue
            # A country is the title only when Title-Case ("Us"); an uppercase "US" stays country.
            if lead.name == "country" and not re.match(r"^[A-Z][a-z]+$", lead.raw or ""):
                continue
            # A bracketed token ([Us]) is a deliberate tag/group, not the title.
            if matches.markers.at_match(lead, lambda marker: marker.name == "group", 0):
                continue
            if lead.start >= anchor.start:
                continue
            if not all(ch in seps for ch in input_string[filepart.start : lead.start]):
                continue
            to_replace.append(lead)
        return to_replace

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> None:
        input_string = matches.input_string or ""
        for lead in when_response:
            matches.remove(lead)
            matches.append(
                Match(
                    lead.start,
                    lead.end,
                    name="title",
                    value=cleanup(input_string[lead.start : lead.end]),
                    input_string=input_string,
                )
            )


class KeepTrailingStopWordTitle(Rule):
    """
    Do not crop a trailing language/country out of the title when doing so would leave the
    title ending on a stop-word (upstream #745 "Oshi no Ko", #789 "It Ends With Us"):
    keep the word in the title and drop the language/country match instead.
    """

    priority = POST_PROCESS
    consequence = RemoveMatch

    def __init__(self, title_stop_words: frozenset[str]) -> None:
        super().__init__()
        self.title_stop_words = title_stop_words

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        input_string = matches.input_string or ""
        ret: list[tuple[Match, Match]] = []
        for title_match in matches.named("title"):
            filepart = matches.markers.at_match(title_match, lambda m: m.name == "path", 0)
            if not filepart:
                continue
            trailing = matches.range(
                title_match.end,
                filepart.end,
                lambda m: not m.private and m.name in ("language", "country"),
                0,
            )
            if not trailing:
                continue
            # Only a Title-Case token ("Us", "Ko") is a cropped title word; an uppercase tag
            # ("US") is a genuine country/language, so keep it.
            if not re.match(r"^[A-Z][a-z]+$", trailing.raw or ""):
                continue
            # A bracketed country/language ([Us]) is a deliberate tag, not a cropped title word.
            if matches.markers.at_match(trailing, lambda marker: marker.name == "group", 0):
                continue
            if not all(ch in seps for ch in input_string[title_match.end : trailing.start]):
                continue
            words = re.split(r"[^a-z0-9]+", str(title_match.value or "").lower())
            words = [w for w in words if w]
            if not words or words[-1] not in self.title_stop_words:
                continue
            ret.append((title_match, trailing))
        return ret

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> None:
        input_string = matches.input_string or ""
        for title_match, trailing in when_response:
            matches.remove(title_match)
            matches.remove(trailing)
            title_match.end = trailing.end
            title_match.value = cleanup(input_string[title_match.start : title_match.end])
            matches.append(title_match)


class SplitOriginalScriptTitle(Rule):
    """
    A title glued as "<original-language title> <romanized title>" — a leading non-Latin script
    run in front of a Latin run — yields the Latin part as the title and the original-language run
    as ``alternative_title`` (#890): "超能警探 Memorist" -> title "Memorist", alternative_title
    "超能警探".

    Only a *leading* non-Latin run is split. An all-non-Latin title is kept as the title, and dual
    titles already separated on "/" are untouched (each side is its own segment).
    """

    priority = POST_PROCESS
    consequence = [RemoveMatch, AppendMatch]

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        input_string = matches.input_string or ""
        to_remove: list[Match] = []
        to_append: list[Match] = []
        for title_match in matches.named("title"):
            if "expected" in title_match.tags:
                continue  # a user-forced expected_title is verbatim, never split
            raw = input_string[title_match.start : title_match.end]
            # The Latin part must start a word (preceded by a separator or the string start), so a
            # stray Latin-homoglyph letter inside a Cyrillic word is not treated as a split point.
            latin = re.search(rf"(?:^|[{re.escape(seps)}])([A-Za-z])", raw)
            if not latin:
                continue  # no romanized run starting a word: keep it as the title
            latin_offset = latin.start(1)
            prefix = raw[:latin_offset]
            if not NON_LATIN_SCRIPT_RE.search(prefix):
                continue  # numeric / Latin lead: nothing to strip
            prefix_end = title_match.start + len(prefix.rstrip(seps))
            latin_start = title_match.start + latin_offset
            if prefix_end <= title_match.start:
                continue
            to_remove.append(title_match)
            to_append.append(
                Match(
                    title_match.start,
                    prefix_end,
                    name="alternative_title",
                    value=cleanup(input_string[title_match.start : prefix_end]),
                    input_string=input_string,
                )
            )
            to_append.append(
                Match(
                    latin_start,
                    title_match.end,
                    name="title",
                    tags=["title"],
                    value=cleanup(input_string[latin_start : title_match.end]),
                    input_string=input_string,
                )
            )
        return to_remove, to_append

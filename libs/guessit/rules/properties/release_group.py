#!/usr/bin/env python
"""
release_group property
"""

from __future__ import annotations

import copy
import re
from typing import TYPE_CHECKING, Any

from rebulk import AppendMatch, Rebulk, RemoveMatch, Rule
from rebulk.match import Match

from ..common import seps
from ..common.comparators import marker_sorted
from ..common.expected import build_expected_function
from ..common.formatters import cleanup
from ..common.pattern import is_disabled
from ..common.validators import int_coercable, seps_surround
from ..properties.title import TitleFromPosition

if TYPE_CHECKING:
    from collections.abc import Callable

    from rebulk.match import Matches


def release_group(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    forbidden_groupnames = config["forbidden_names"]

    groupname_ignore_seps = config["ignored_seps"]
    groupname_seps = "".join([c for c in seps if c not in groupname_ignore_seps])

    def clean_groupname(string: str) -> str:
        """
        Removes and strip separators from input_string
        :param string:
        :type string:
        :return:
        :rtype:
        """
        string = string.strip(groupname_seps)
        if not (
            string.endswith(tuple(groupname_ignore_seps)) and string.startswith(tuple(groupname_ignore_seps))
        ) and not any(i in string.strip(groupname_ignore_seps) for i in groupname_ignore_seps):
            string = string.strip(groupname_ignore_seps)
        for forbidden in forbidden_groupnames:
            if string.lower().startswith(forbidden) and string[len(forbidden) : len(forbidden) + 1] in seps:
                string = string[len(forbidden) :]
                string = string.strip(groupname_seps)
            if string.lower().endswith(forbidden) and string[-len(forbidden) - 1 : -len(forbidden)] in seps:
                string = string[: len(forbidden)]
                string = string.strip(groupname_seps)

        # Release groups that credit individual members often use a format like "Title (MediaInfo Individual) [Group]".
        # This results in a group name of "Individual) [Group]", which should be transformed to "Individual Group".
        return re.sub(r"(.+)\)\s?\[(.+)\]", r"\1 \2", string.strip())

    rebulk = Rebulk(disabled=lambda context: is_disabled(context, "release_group"))

    expected_group = build_expected_function("expected_group")

    rebulk.functional(
        expected_group,
        name="release_group",
        tags=["expected"],
        validator=seps_surround,
        conflict_solver=lambda match, other: other,
        disabled=lambda context: not context.get("expected_group"),
    )

    return rebulk.rules(
        DashSeparatedReleaseGroup(clean_groupname), SceneReleaseGroup(clean_groupname), AnimeReleaseGroup
    )


_scene_previous_names = (
    "video_codec",
    "source",
    "video_api",
    "audio_codec",
    "audio_profile",
    "video_profile",
    "audio_channels",
    "screen_size",
    "other",
    "container",
    "language",
    "subtitle_language",
    "subtitle_language.suffix",
    "subtitle_language.prefix",
    "language.suffix",
)

_scene_previous_tags = ("release-group-prefix",)

_scene_no_previous_tags = ("no-release-group-prefix",)


def is_anime_group(matches: Matches, marker: Match, filepart_start: int) -> bool:
    """An "empty" anime group holds no real title text, only ignorable matches.

    A leading bracket whose only content is a subtitle-format container name
    ([SSA]/[ASS]) is an anime release group, not a container (upstream #670).
    """
    inner = matches.range(marker.start, marker.end, lambda m: "weak-language" not in m.tags)
    if not inner:
        return True
    return marker.start == filepart_start and all(m.name == "container" and "subtitle" in m.tags for m in inner)


def leading_anime_group(matches: Matches, filepart: Match) -> Match | None:
    """Return the filepart's leading ``[bracket]`` group when it is an anime release-group tag.

    These releases carry the group in the first bracket (``[ASW] Title - 01 …``); a trailing
    ``(English Title)`` parenthetical must not be claimed as the release_group instead (#696/#757).
    """
    first_group = matches.markers.range(
        filepart.start,
        filepart.end,
        lambda marker: marker.name == "group" and marker.start == filepart.start,
        0,
    )
    if (
        first_group
        and is_anime_group(matches, first_group, filepart.start)
        and first_group.value.strip(seps)
        and not int_coercable(first_group.value.strip(seps))
    ):
        return first_group
    return None


_SEPS_CHARS = re.escape(seps)

#: A trailing hole made of a numeric run and a final dash-separated word, e.g. ``.313-314-GROUP``.
#: Digits and separators alone cannot be a title, so the last word stays a release group even when
#: nothing claimed the numbers.
_NUMERIC_RUN_THEN_GROUP = re.compile(
    rf"^[{_SEPS_CHARS}]?\d+(?:[{_SEPS_CHARS}]+\d+)*-(?P<group>[^{_SEPS_CHARS}]{{2,}})$"
)


class DashSeparatedReleaseGroup(Rule):
    """
    Detect dash separated release groups that might appear at the end or at the beginning of a release name.

    Series.S01E02.Pilot.DVDRip.x264-CS.mkv
        release_group: CS
    abc-the.title.name.1983.1080p.bluray.x264.mkv
        release_group: abc

    At the end: Release groups should be dash-separated and shouldn't contain spaces nor
    appear in a group with other matches. The preceding matches should be separated by dot.
    If a release group is found, the conflicting matches are removed.

    At the beginning: Release groups should be dash-separated and shouldn't contain spaces nor appear in a group.
    It should be followed by a hole with dot-separated words.
    Detection only happens if no matches exist at the beginning.
    """

    consequence = [RemoveMatch, AppendMatch]

    def __init__(self, value_formatter: Callable[[str], str]) -> None:
        """Default constructor."""
        super().__init__()
        self.value_formatter = value_formatter

    @classmethod
    def is_valid(cls, matches: Matches, candidate: Match, start: int, end: int, at_end: bool) -> Any:
        """
        Whether a candidate is a valid release group.
        """
        if not at_end:
            if len(candidate.value) <= 1:
                return False

            if matches.markers.at_match(candidate, predicate=lambda m: m.name == "group"):
                return False

            # A leading token that is already an episode number is the episode, not a group.
            if matches.range(candidate.start, candidate.end, predicate=lambda m: m.name == "episode", index=0):
                return False

            first_hole = matches.holes(candidate.end, end, predicate=lambda m: m.start == candidate.end, index=0)
            if not first_hole:
                return False

            raw_value = first_hole.raw

            # A candidate at the filepart start, joined by a dash to a single word (no internal
            # separator) and followed by a season/episode/date anchor, is the first half of a
            # hyphenated title ("grown-ish.s03e01" -> "grown-ish"), not a release group
            # (upstream #634/#640). A multi-word remainder ("FoV-Show.Name.S01E01") keeps the
            # leading scene group.
            if (
                candidate.start == start
                and raw_value is not None
                and "." not in raw_value.strip(seps)
                and " " not in raw_value.strip(seps)
                and matches.range(
                    candidate.end,
                    end,
                    predicate=lambda m: m.name in ("season", "episode", "date") and not m.private,
                    index=0,
                )
            ):
                return False

            return (
                raw_value is not None
                and raw_value[0] == "-"
                and "-" not in raw_value[1:]
                and "." in raw_value
                and " " not in raw_value
            )

        group = matches.markers.at_match(candidate, predicate=lambda m: m.name == "group", index=0)
        if group and matches.at_match(group, predicate=lambda m: not m.private and m.span != candidate.span):
            return False

        count = 0
        match = candidate
        while match:
            current = matches.range(
                start, match.start, index=-1, predicate=lambda m: not m.private and "expected" not in m.tags
            )
            if not current:
                break

            separator = (match.input_string or "")[current.end : match.start]
            if not separator and match.raw and match.raw[0] == "-":
                separator = "-"

            match = current

            if count == 0:
                if separator != "-":
                    break

                count += 1
                continue

            if separator == ".":
                return True
        return None

    def detect(self, matches: Matches, start: int, end: int, at_end: bool) -> Any:
        """
        Detect release group at the end or at the beginning of a filepart.
        """
        candidate = None
        if at_end:
            container = matches.ending(end, lambda m: m.name == "container", index=0)
            if container:
                end = container.start

            candidate = matches.ending(
                end,
                index=0,
                predicate=(
                    lambda m: (
                        not m.private
                        and not (m.name == "other" and "not-a-release-group" in m.tags)
                        and m.raw is not None
                        and "-" not in m.raw
                        and m.raw.strip() == m.raw
                    )
                ),
            )

        if not candidate:
            if at_end:
                candidate = matches.holes(
                    start,
                    end,
                    seps=seps,
                    index=-1,
                    predicate=lambda m: m.end == end and m.raw is not None and m.raw.strip(seps) and m.raw[0] == "-",
                )
            else:
                candidate = matches.holes(
                    start,
                    end,
                    seps=seps,
                    index=0,
                    predicate=lambda m: m.start == start and m.raw is not None and m.raw.strip(seps),
                )

        if candidate and self.is_valid(matches, candidate, start, end, at_end):
            return candidate
        if at_end:
            return self.detect_after_numeric_run(matches, start, end)
        return None

    @classmethod
    def detect_after_numeric_run(cls, matches: Matches, start: int, end: int) -> Match | None:
        """
        Detach a trailing dash separated group from an unclaimed numeric run.

        ``Bleach.s16e03-04.313-314-GROUP`` leaves ``.313-314-GROUP`` as a single hole whenever no
        rule claims the absolute episode run — the weak episode chains are off under a forced
        ``type=movie`` (#944). The run is anchored on the season/episode markers it follows, so the
        trailing word behind it is a release group rather than the tail of a title.
        """
        hole = matches.holes(start, end, index=-1, predicate=lambda m: m.end == end and m.raw)
        if not hole or hole.raw is None:
            return None

        numeric_run = _NUMERIC_RUN_THEN_GROUP.match(hole.raw)
        if not numeric_run or int_coercable(numeric_run.group("group")):
            return None

        previous = matches.range(start, hole.start, index=-1, predicate=lambda m: not m.private)
        if not previous or previous.name not in ("season", "episode"):
            return None

        # The candidate keeps its leading dash, as the ones the branches above return do.
        return Match(hole.start + numeric_run.start("group") - 1, hole.end, input_string=hole.input_string)

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        if matches.named("release_group"):
            return None

        to_remove: list[Match] = []
        to_append: list[Match] = []
        for filepart in matches.markers.named("path"):
            candidate = self.detect(matches, filepart.start, filepart.end, True)
            if candidate:
                to_remove.extend(matches.at_match(candidate))
            else:
                candidate = self.detect(matches, filepart.start, filepart.end, False)

            if candidate:
                releasegroup = Match(
                    candidate.start,
                    candidate.end,
                    name="release_group",
                    formatter=self.value_formatter,
                    input_string=candidate.input_string,
                )

                if releasegroup.value:
                    to_append.append(releasegroup)
                if to_remove or to_append:
                    return to_remove, to_append
        return None


class SceneReleaseGroup(Rule):
    """
    Add release_group match in existing matches (scene format).

    Something.XViD-ReleaseGroup.mkv
    """

    dependency = [TitleFromPosition]
    consequence = AppendMatch

    properties = {"release_group": [None]}

    def __init__(self, value_formatter: Callable[[str], str]) -> None:
        """Default constructor."""
        super().__init__()
        self.value_formatter = value_formatter

    @staticmethod
    def is_previous_match(match: Match) -> Any:
        """
        Check if match can precede release_group

        :param match:
        :return:
        """
        return (
            not match.tagged(*_scene_no_previous_tags)
            if match.name in _scene_previous_names
            else match.tagged(*_scene_previous_tags)
        )

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        # If a release_group is found before, ignore this kind of release_group rule.

        ret: list[Match] = []

        for filepart in marker_sorted(matches.markers.named("path"), matches):
            # The closures below are consumed within this same iteration, so binding the loop
            # variables late (B023) is intentional and safe.
            start, end = filepart.span
            if matches.named("release_group", predicate=lambda m: m.start >= start and m.end <= end):  # noqa: B023
                continue

            titles = matches.named("title", predicate=lambda m: m.start >= start and m.end <= end)  # noqa: B023

            def keep_only_first_title(match: Match) -> bool:
                """
                Keep only first title from this filepart, as other ones are most likely release group.

                :param match:
                :type match:
                :return:
                :rtype:
                """
                return match in titles[1:]  # noqa: B023

            last_hole = matches.holes(
                start,
                end + 1,
                formatter=self.value_formatter,
                ignore=keep_only_first_title,
                predicate=lambda hole: cleanup(hole.value),
                index=-1,
            )

            if last_hole:
                # Anime episode releases carry the group in the leading [bracket]; a trailing
                # (English title) parenthetical must not be claimed as the release_group instead —
                # leave it for AnimeReleaseGroup to pick the leading bracket (#696/#757). Gate on an
                # episode/season match so a movie's trailing (group) (e.g. YTS/YIFY) is left untouched.
                hole_group = matches.markers.at_match(last_hole, lambda marker: marker.name == "group", 0)
                if (
                    hole_group
                    and (hole_group.raw or "").startswith("(")
                    and matches.range(start, end, predicate=lambda m: m.name in ("episode", "season"))
                    and leading_anime_group(matches, filepart)
                ):
                    continue

                def previous_match_filter(match: Match) -> bool:
                    """
                    Filter to apply to find previous match

                    :param match:
                    :type match:
                    :return:
                    :rtype:
                    """

                    if match.start < filepart.start:  # noqa: B023
                        return False
                    return not match.private or self.is_previous_match(match)

                previous_match = matches.previous(last_hole, previous_match_filter, index=0)
                if (
                    previous_match
                    and (self.is_previous_match(previous_match))
                    and not (matches.input_string or "")[previous_match.end : last_hole.start].strip(seps)
                    and not int_coercable(last_hole.value.strip(seps))
                ):
                    last_hole.name = "release_group"
                    last_hole.tags = ["scene"]

                    # if hole is inside a group marker with same value, remove [](){} ...
                    group = matches.markers.at_match(last_hole, lambda marker: marker.name == "group", 0)
                    if group:
                        group.formatter = self.value_formatter
                        if group.value == last_hole.value:
                            last_hole.start = group.start + 1
                            last_hole.end = group.end - 1
                            last_hole.tags = ["anime"]

                    ignored_matches = matches.range(last_hole.start, last_hole.end, keep_only_first_title)

                    for ignored_match in ignored_matches:
                        matches.remove(ignored_match)

                    ret.append(last_hole)
        return ret


class AnimeReleaseGroup(Rule):
    """
    Add release_group match in existing matches (anime format)
    ...[ReleaseGroup] Something.mkv
    """

    dependency = [SceneReleaseGroup, TitleFromPosition]
    consequence = [RemoveMatch, AppendMatch]

    properties = {"release_group": [None]}

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        to_append: list[Match] = []

        # If a release_group is found before, ignore this kind of release_group rule.
        if matches.named("release_group"):
            return False

        if not matches.named("episode") and not matches.named("season") and matches.named("release_group"):
            # This doesn't seems to be an anime, and we already found another release_group.
            return False

        for filepart in marker_sorted(matches.markers.named("path"), matches):
            empty_group = matches.markers.range(
                filepart.start,
                filepart.end,
                lambda marker: (
                    marker.name == "group"
                    and is_anime_group(matches, marker, filepart.start)  # noqa: B023
                    and marker.value.strip(seps)
                    and not int_coercable(marker.value.strip(seps))
                ),
                0,
            )

            if empty_group:
                group = copy.copy(empty_group)
                group.marker = False
                group.raw_start += 1
                group.raw_end -= 1
                group.tags = ["anime"]
                group.name = "release_group"
                to_append.append(group)
                to_remove.extend(
                    matches.range(
                        empty_group.start,
                        empty_group.end,
                        lambda m: "weak-language" in m.tags or (m.name == "container" and "subtitle" in m.tags),
                    )
                )

        if to_remove or to_append:
            return to_remove, to_append
        return False

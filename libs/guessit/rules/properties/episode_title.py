#!/usr/bin/env python
"""
Episode title
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any

from rebulk import POST_PROCESS, AppendMatch, Rebulk, RemoveMatch, RenameMatch, Rule
from rebulk.remodule import re

from ..common import seps, title_seps
from ..common.formatters import cleanup
from ..common.pattern import is_disabled
from ..common.validators import or_
from ..properties.title import TitleBaseRule, TitleFromPosition
from ..properties.type import TypeProcessor

if TYPE_CHECKING:
    from rebulk.match import Match, Matches


def _parent_title_hole(matches: Matches, start: int, end: int) -> Match | None:
    """Title hole in a parent filepart, keeping a dash-joined name (e.g. "Adam-12") whole.

    ``matches.holes`` splits on ``title_seps`` (the dash included), so without this a
    name like "Adam-12" is truncated to its first hole "Adam"; merge the consecutive
    leading holes joined by a single "-" the same way :class:`TitleBaseRule` does when it
    builds a title in place (upstream #796).
    """
    holes = matches.holes(
        start,
        end,
        ignore=or_(lambda match: "weak-episode" in match.tags, TitleBaseRule.is_ignored),
        formatter=cleanup,
        seps=title_seps,
        predicate=lambda match: match.value,
    )
    if not holes:
        return None
    hole = holes[0]
    input_string = matches.input_string or ""
    for next_hole in holes[1:]:
        separator = input_string[hole.end : next_hole.start]
        if (
            len(separator) == 1
            and separator == "-"
            and hole.raw is not None
            and hole.raw[-1] not in seps
            and next_hole.raw is not None
            and next_hole.raw[0] not in seps
        ):
            hole.end = next_hole.end
        else:
            break
    return hole


def episode_title(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    previous_names = ("episode", "episode_count", "season", "season_count", "date", "title", "year")

    rebulk = Rebulk(disabled=lambda context: is_disabled(context, "episode_title"))
    return rebulk.rules(
        RemoveConflictsWithEpisodeTitle(previous_names),
        ReclaimCameraEpisodeTitle,
        EpisodeTitleFromPosition(previous_names),
        AlternativeTitleReplace(previous_names),
        TitleToEpisodeTitle,
        Filepart3EpisodeTitle,
        Filepart2EpisodeTitle,
        NumericEpisodeTitleToEpisode,
        RenameEpisodeTitleWhenMovieType,
    )


class RemoveConflictsWithEpisodeTitle(Rule):
    """
    Remove conflicting matches that might lead to wrong episode_title parsing.
    """

    priority = 64
    consequence = RemoveMatch

    def __init__(self, previous_names: tuple[str, ...]) -> None:
        super().__init__()
        self.previous_names = previous_names
        self.next_names = (
            "streaming_service",
            "screen_size",
            "source",
            "video_codec",
            "audio_codec",
            "other",
            "container",
        )
        self.affected_if_holes_after = ("part",)
        self.affected_names = ("part", "year")

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        for filepart in matches.markers.named("path"):
            for match in matches.range(filepart.start, filepart.end, predicate=lambda m: m.name in self.affected_names):
                before = matches.range(filepart.start, match.start, predicate=lambda m: not m.private, index=-1)
                if not before or before.name not in self.previous_names:
                    continue

                after = matches.range(match.end, filepart.end, predicate=lambda m: not m.private, index=0)
                if not after or after.name not in self.next_names:
                    continue

                group = matches.markers.at_match(match, predicate=lambda m: m.name == "group", index=0)

                def has_value_in_same_group(current_match: Match, current_group: Any = group) -> Any:
                    """Return true if current match has value and belongs to the current group."""
                    return current_match.value.strip(seps) and (
                        current_group
                        == matches.markers.at_match(current_match, predicate=lambda mm: mm.name == "group", index=0)
                    )

                holes_before = matches.holes(before.end, match.start, predicate=has_value_in_same_group)
                holes_after = matches.holes(match.end, after.start, predicate=has_value_in_same_group)

                if not holes_before and not holes_after:
                    continue

                if match.name in self.affected_if_holes_after and not holes_after:
                    continue

                to_remove.append(match)
                if match.parent:
                    to_remove.append(match.parent)

        return to_remove


class TitleToEpisodeTitle(Rule):
    """
    If multiple different title are found, convert the one following episode number to episode_title.
    """

    dependency = TitleFromPosition

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        titles = matches.named("title")
        title_groups: defaultdict[Any, list[Match]] = defaultdict(list)
        for title in titles:
            title_groups[title.value].append(title)

        episode_titles: list[Match] = []
        if len(title_groups) < 2:
            return episode_titles

        for title in titles:
            if matches.previous(title, lambda match: match.name == "episode"):
                episode_titles.append(title)

        return episode_titles

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> None:
        for title in when_response:
            matches.remove(title)
            title.name = "episode_title"
            matches.append(title)


class ReclaimCameraEpisodeTitle(Rule):
    """
    A bare "Cam" right after an episode/season marker, with no other release metadata in the
    filepart, is the episode title, not ``source: Camera`` (upstream #732):
    ``Show.S01E01.Cam.mkv`` -> episode_title "Cam".

    Scoped to the ambiguous bare-CAM source ("Camera"): the spurious source match is removed so
    the normal episode-title hole-filling reclaims the word. Unambiguous sources (HDTV, WEB, ...)
    and real CAM releases ("720p CAM x264", "...HDCAM XviD") are left untouched because the source
    word is then either not at the episode-title slot or surrounded by other release metadata.

    Runs before :class:`EpisodeTitleFromPosition` so the freed hole becomes the episode title.
    """

    priority = 32
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        input_string = matches.input_string or ""
        to_remove: list[Match] = []
        for source in matches.named("source"):
            if source.value != "Camera":
                continue
            filepart = matches.markers.at_match(source, lambda m: m.name == "path", 0)
            if not filepart:
                continue
            # Must directly follow an episode/season marker (only separators in between).
            before = matches.range(filepart.start, source.start, lambda m: not m.private and m.value, -1)
            if not before or before.name not in ("episode", "season", "episode_count", "season_count"):
                continue
            if any(ch not in seps for ch in input_string[before.end : source.start]):
                continue
            # Must be the trailing word: nothing meaningful after it but a container.
            after = matches.range(
                source.end,
                filepart.end,
                lambda m: not m.private and m.value and m.name != "container",
                0,
            )
            if after:
                continue
            to_remove.append(source)
            if source.parent:
                to_remove.append(source.parent)
        return to_remove


class EpisodeTitleFromPosition(TitleBaseRule):
    """
    Add episode title match in existing matches
    Must run after TitleFromPosition rule.
    """

    dependency = TitleToEpisodeTitle

    def __init__(self, previous_names: tuple[str, ...]) -> None:
        super().__init__("episode_title", ["title"])
        self.previous_names = previous_names

    def hole_filter(self, hole: Match, matches: Matches) -> bool:
        episode = matches.previous(hole, lambda previous: previous.named(*self.previous_names), 0)

        crc32 = matches.named("crc32")

        if episode or crc32:
            return True

        # A release tag (REPACK -> Proper, INTERNAL, ...) can sit between the episode marker and
        # the episode title (upstream #775: "...S00E01.REPACK.Episode.Title..."). Such a tag is the
        # hole's immediate predecessor, so the adjacency check above misses the marker; look past it.
        for previous in reversed(matches.range(0, hole.start, lambda m: not m.private and bool(m.value))):
            if previous.name in ("other", "proper_count"):
                continue
            return previous.named(*self.previous_names)
        return False

    def filepart_filter(self, filepart: Match, matches: Matches) -> bool:
        # Filepart where title was found.
        return bool(matches.range(filepart.start, filepart.end, lambda match: match.name == "title"))

    def should_remove(
        self, match: Match, matches: Matches, filepart: Match, hole: Match, context: dict[str, Any] | None
    ) -> bool:
        if match.name == "episode_details":
            return False
        return super().should_remove(match, matches, filepart, hole, context)

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        if matches.named("episode_title"):
            return None
        return super().when(matches, context)


class AlternativeTitleReplace(Rule):
    """
    If alternateTitle was found and title is next to episode, season or date, replace it with episode_title.
    """

    dependency = EpisodeTitleFromPosition
    consequence = RenameMatch

    def __init__(self, previous_names: tuple[str, ...]) -> None:
        super().__init__()
        self.previous_names = previous_names

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        if matches.named("episode_title"):
            return None

        alternative_title = matches.range(predicate=lambda match: match.name == "alternative_title", index=0)
        if alternative_title:
            main_title = matches.chain_before(
                alternative_title.start, seps=seps, predicate=lambda match: "title" in match.tags, index=0
            )
            if main_title:
                episode = matches.previous(main_title, lambda previous: previous.named(*self.previous_names), 0)

                crc32 = matches.named("crc32")

                if episode or crc32:
                    return alternative_title
        return None

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> None:
        matches.remove(when_response)
        when_response.name = "episode_title"
        when_response.tags.append("alternative-replaced")
        matches.append(when_response)


class NumericEpisodeTitleToEpisode(Rule):
    """
    Convert a numeric episode_title into episode when a season is present but no episode was found.

    Anime such as ``Show S2 - 01`` would otherwise yield ``episode_title: "01"`` (upstream #667).
    """

    priority = POST_PROCESS
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        ret: list[Match] = []
        for filepart in matches.markers.named("path"):
            if matches.range(filepart.start, filepart.end, lambda m: m.name == "episode" and not m.private, index=0):
                continue
            if not matches.range(filepart.start, filepart.end, lambda m: m.name == "season" and not m.private, index=0):
                continue
            for episode_title in matches.range(filepart.start, filepart.end, lambda m: m.name == "episode_title"):
                if re.match(r"^\d{1,3}$", str(episode_title.value).strip()):
                    ret.append(episode_title)
        return ret

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> None:
        for episode_title in when_response:
            matches.remove(episode_title)
            episode_title.name = "episode"
            episode_title.value = int(str(episode_title.value).strip())
            matches.append(episode_title)


class RenameEpisodeTitleWhenMovieType(Rule):
    """
    Rename episode_title by alternative_title when type is movie.
    """

    priority = POST_PROCESS

    dependency = TypeProcessor
    consequence = RenameMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        if matches.named("episode_title", lambda m: "alternative-replaced" not in m.tags) and not matches.named(
            "type", lambda m: m.value == "episode"
        ):
            return matches.named("episode_title")
        return None

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> None:
        for match in when_response:
            matches.remove(match)
            match.name = "alternative_title"
            matches.append(match)


class Filepart3EpisodeTitle(Rule):
    """
    If we have at least 3 filepart structured like this:

    Serie name/SO1/E01-episode_title.mkv
    AAAAAAAAAA/BBB/CCCCCCCCCCCCCCCCCCCC

    Serie name/SO1/episode_title-E01.mkv
    AAAAAAAAAA/BBB/CCCCCCCCCCCCCCCCCCCC

    If CCCC contains episode and BBB contains seasonNumber
    Then title is to be found in AAAA.
    """

    consequence = AppendMatch("title")

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        if matches.tagged("filepart-title"):
            return None

        fileparts = matches.markers.named("path")
        if len(fileparts) < 3:
            return None

        filename = fileparts[-1]
        directory = fileparts[-2]
        subdirectory = fileparts[-3]

        episode_number = matches.range(filename.start, filename.end, lambda match: match.name == "episode", 0)
        if episode_number:
            season = matches.range(directory.start, directory.end, lambda match: match.name == "season", 0)

            if season:
                hole = _parent_title_hole(matches, subdirectory.start, subdirectory.end)
                if hole:
                    return hole
        return None


class Filepart2EpisodeTitle(Rule):
    """
    If we have at least 2 filepart structured like this:

    Serie name SO1/E01-episode_title.mkv
    AAAAAAAAAAAAA/BBBBBBBBBBBBBBBBBBBBB

    If BBBB contains episode and AAA contains a hole followed by seasonNumber
    then title is to be found in AAAA.

    or

    Serie name/SO1E01-episode_title.mkv
    AAAAAAAAAA/BBBBBBBBBBBBBBBBBBBBB

    If BBBB contains season and episode and AAA contains a hole
    then title is to be found in AAAA.

    or (absolute numbering, common for anime)

    Serie name/01 - episode_title.mkv
    AAAAAAAAAA/BBBBBBBBBBBBBBBBBBBB

    If BBBB contains an episode and no season exists anywhere
    then title is to be found in AAAA.
    """

    consequence = AppendMatch("title")

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        if matches.tagged("filepart-title"):
            return None

        fileparts = matches.markers.named("path")
        if len(fileparts) < 2:
            return None

        filename = fileparts[-1]
        directory = fileparts[-2]

        episode_number = matches.range(filename.start, filename.end, lambda match: match.name == "episode", 0)
        if episode_number:
            season = matches.range(
                directory.start, directory.end, lambda match: match.name == "season", 0
            ) or matches.range(filename.start, filename.end, lambda match: match.name == "season", 0)
            # Absolute numbering (no season anywhere) still puts the title in the parent directory.
            if season or not matches.named("season"):
                hole = _parent_title_hole(matches, directory.start, directory.end)
                if hole:
                    hole.tags.append("filepart-title")
                    return hole
        return None

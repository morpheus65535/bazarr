#!/usr/bin/env python
"""
screen_size property
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rebulk import AppendMatch, Rebulk, RemoveMatch, Rule
from rebulk.match import Match
from rebulk.remodule import re

from ...reutils import build_or_pattern
from ..common import dash, seps
from ..common.pattern import is_disabled
from ..common.quantity import FrameRate
from ..common.validators import seps_surround

if TYPE_CHECKING:
    from rebulk.match import Matches


def screen_size(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    interlaced = frozenset(config["interlaced"])
    progressive = frozenset(config["progressive"])
    frame_rates = frozenset(config["frame_rates"])
    min_ar = config["min_ar"]
    max_ar = config["max_ar"]

    rebulk = Rebulk()
    rebulk = rebulk.string_defaults(ignore_case=True).regex_defaults(flags=re.IGNORECASE)

    rebulk.defaults(
        name="screen_size",
        validator=seps_surround,
        abbreviations=[dash],
        disabled=lambda context: is_disabled(context, "screen_size"),
    )

    frame_rate_pattern = build_or_pattern(frame_rates, name="frame_rate")
    interlaced_pattern = build_or_pattern(interlaced, name="height")
    progressive_pattern = build_or_pattern(progressive, name="height")

    res_separator = r"(?:x|\*|×)"  # noqa: RUF001  # U+00D7 resolution separator
    res_pattern = r"(?:(?P<width>\d{3,4})" + res_separator + r")?"
    upscaled = r"(?:up)?"  # tolerate a trailing "up" (upscaled) marker glued to the resolution (#741)
    rebulk.regex(res_pattern + interlaced_pattern + r"(?P<scan_type>i)" + frame_rate_pattern + "?")
    rebulk.regex(res_pattern + progressive_pattern + r"(?P<scan_type>p)" + frame_rate_pattern + "?")
    rebulk.regex(res_pattern + progressive_pattern + r"(?P<scan_type>p)?(?:hd)")
    rebulk.regex(res_pattern + progressive_pattern + r"(?P<scan_type>p)?x?")
    rebulk.string(
        "4k",
        value="2160p",
        conflict_solver=lambda match, other: "__default__" if other.name == "screen_size" else match,
    )
    # The separators around the "x" must be symmetric: "1920x1080" and "1920 x 1080" are resolutions,
    # while a leading-only separator ("1080.x264") is a resolution followed by a codec (#933).
    rebulk.regex(
        r"(?P<width>\d{3,4})(?:" + res_separator + r"|-" + res_separator + r"-)(?P<height>\d{3,4})" + upscaled,
        conflict_solver=lambda match, other: "__default__" if other.name == "screen_size" else other,
    )

    rebulk.regex(
        frame_rate_pattern + "-?(?:p|fps)",
        name="frame_rate",
        formatter=FrameRate.fromstring,
        disabled=lambda context: is_disabled(context, "frame_rate"),
    )

    rebulk.rules(PostProcessScreenSize(progressive, min_ar, max_ar), ScreenSizeOnlyOne, ResolveScreenSizeConflicts)

    return rebulk


class PostProcessScreenSize(Rule):
    """
    Process the screen size calculating the aspect ratio if available.

    Convert to a standard notation (720p, 1080p, etc) when it's a standard resolution and
    aspect ratio is valid or not available.

    It also creates an aspect_ratio match when available.
    """

    consequence = AppendMatch

    def __init__(self, standard_heights: frozenset[str], min_ar: float, max_ar: float) -> None:
        super().__init__()
        self.standard_heights = standard_heights
        self.min_ar = min_ar
        self.max_ar = max_ar

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_append: list[Match] = []
        for match in matches.named("screen_size"):
            if not is_disabled(context, "frame_rate"):
                for frame_rate in match.children.named("frame_rate"):
                    frame_rate.formatter = FrameRate.fromstring
                    to_append.append(frame_rate)

            values = match.children.to_dict()
            if "height" not in values:
                continue

            scan_type = (values.get("scan_type") or "p").lower()
            height = values["height"]
            if "width" not in values:
                match.value = f"{height}{scan_type}"
                continue

            width = values["width"]
            calculated_ar = float(width) / float(height)

            aspect_ratio = Match(
                match.start,
                match.end,
                input_string=match.input_string,
                name="aspect_ratio",
                value=round(calculated_ar, 3),
            )

            if not is_disabled(context, "aspect_ratio"):
                to_append.append(aspect_ratio)

            if height in self.standard_heights and self.min_ar < calculated_ar < self.max_ar:
                match.value = f"{height}{scan_type}"
            else:
                match.value = f"{width}x{height}"

        return to_append


class ScreenSizeOnlyOne(Rule):
    """
    Keep a single screen_size per filepath part.
    """

    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        for filepart in matches.markers.named("path"):
            screensize = list(
                reversed(matches.range(filepart.start, filepart.end, lambda match: match.name == "screen_size"))
            )
            if len(screensize) > 1 and len({match.value for match in screensize}) > 1:
                to_remove.extend(screensize[1:])

        return to_remove


class ResolveScreenSizeConflicts(Rule):
    """
    Resolve screen_size conflicts with season and episode matches.
    """

    consequence = RemoveMatch

    @staticmethod
    def _same_group(matches: Matches, first: Match, second: Match) -> bool:
        """Whether both matches sit in the same bracketed group (or both outside of any)."""

        def group_of(match: Match) -> Match | None:
            return matches.markers.at_match(match, lambda marker: marker.name == "group", 0)

        return group_of(first) == group_of(second)

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        for filepart in matches.markers.named("path"):
            screensizes = matches.range(filepart.start, filepart.end, lambda match: match.name == "screen_size")
            if not screensizes:
                continue

            screensize = screensizes[0]
            conflicts = matches.conflicting(screensize, lambda match: match.name in ("season", "episode"))
            if not conflicts:
                continue

            has_neighbor = False
            following = matches.range(
                screensize.end, filepart.end, lambda match: match.name in ("video_profile", "video_codec"), 0
            )
            if following and not matches.holes(
                screensize.end, following.start, predicate=lambda h: h.value and h.value.strip(seps)
            ):
                # A video_codec marks the number as a resolution ("1080.x264" -> 1080p) only when both
                # sit in the same tag block and the part spells no other resolution: a codec quoted in
                # its own group says nothing about the number ("One Piece - 1080 [x264]") (#933).
                if following.name == "video_profile" or (
                    len(screensizes) == 1 and self._same_group(matches, screensize, following)
                ):
                    to_remove.extend(conflicts)
                    has_neighbor = True

            previous = matches.previous(
                screensize, index=0, predicate=(lambda m: m.name in ("date", "source", "other", "streaming_service"))
            )
            if previous and not matches.holes(
                previous.end, screensize.start, predicate=lambda h: h.value and h.value.strip(seps)
            ):
                to_remove.extend(conflicts)
                has_neighbor = True

            if not has_neighbor:
                to_remove.append(screensize)

        return to_remove

#!/usr/bin/env python
"""
other property
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rebulk import POST_PROCESS, AppendMatch, Rebulk, RemoveMatch, RenameMatch, Rule
from rebulk.match import Match
from rebulk.remodule import re

from ...config import load_config_patterns
from ...reutils import build_or_pattern
from ...rules.common.formatters import raw_cleanup
from ..common import dash, seps
from ..common.pattern import is_disabled
from ..common.validators import and_, seps_after, seps_before, seps_surround

if TYPE_CHECKING:
    from collections.abc import Iterable

    from rebulk.match import Matches


def other(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, "other"))
    rebulk = rebulk.regex_defaults(flags=re.IGNORECASE, abbreviations=[dash]).string_defaults(ignore_case=True)
    rebulk.defaults(name="other", validator=seps_surround)

    load_config_patterns(rebulk, config.get("other"))

    opening_ending_credits(rebulk)

    art_keywords = config.get("art", {})

    rebulk.rules(
        RenameAnotherToOther,
        AppendCreditless,
        AppendOpedEndingCredits,
        ValidateHasNeighbor,
        ValidateHasNeighborAfter,
        ValidateHasNeighborBefore,
        ValidateScreenerRule,
        ValidateMuxRule,
        ValidateHardcodedSubs,
        ValidateStreamingServiceNeighbor,
        ValidateAtEnd,
        ValidateReal,
        ValidateStereoVRContext,
        ImageArtKeywordToOther(art_keywords),
        ProperCountRule,
    )

    return rebulk


#: Tag carried by stereoscopic-3D abbreviations that are too ambiguous to trust on
#: their own (``SBS`` is also a broadcaster, ``TB``/``OU``/``LR`` are common letter
#: pairs). They are only kept when their filepart already carries a VR/3D signal.
STEREO_VR_CONTEXT_TAG = "stereo-vr-context"

#: ``other`` values that establish a VR/3D context within a filepart. Only the
#: generic "this is VR/3D content" markers count: a specific stereoscopic layout
#: does not license a *different* ambiguous layout token in the same filepart.
VR_CONTEXT_VALUES = frozenset({"Virtual Reality", "3D"})


def _has_vr_context(matches: Matches, filepart: Match) -> bool:
    """Whether ``filepart`` carries an unambiguous VR/3D ``other`` signal."""
    return bool(
        matches.range(
            filepart.start,
            filepart.end,
            predicate=lambda m: m.name == "other" and m.value in VR_CONTEXT_VALUES,
        )
    )


#: Ordinal of an opening/ending sequence, e.g. ``2`` in ``OP02`` or ``4a`` in
#: ``OP4a``. Kept as a string because of the variant-letter forms (``4a``, ``1a``).
#: The leading version ``v`` is excluded so ``ED2v2`` yields number ``2``, version ``2``.
#: ``[^\W\d_]`` (a letter) avoids a ``-`` range, which the ``dash`` abbreviation
#: would otherwise rewrite into a broken nested character set.
_CREDITS_NUMBER = r"(?P<credits_number>\d+(?:(?![vV]\d)[^\W\d_])?)?"
#: Optional version suffix glued to an opening/ending token, e.g. ``v2`` in ``ED2v2``.
_CREDITS_VERSION = r"(?:-?[vV](?P<version>\d+))?"
_CREDITS_SUFFIX = _CREDITS_NUMBER + _CREDITS_VERSION


def _format_credits_number(value: str) -> str:
    """Normalize an opening/ending ordinal: drop leading zeros, keep the variant letter."""
    match = re.match(r"(\d+)(\w?)$", value)
    if not match:
        return value
    number, letter = str(match.group(1)), str(match.group(2))
    return str(int(number)) + letter.lower()


def opening_ending_credits(rebulk: Rebulk) -> None:
    """
    Match anime opening/ending credit sequences (OP/ED, NCOP/NCED, creditless…).

    Emits ``other: Opening Credits`` / ``Ending Credits`` plus, when present, the
    sequence ordinal as ``credits_number`` (string, e.g. ``4a``) and the ``version``.
    The bare two-letter ``OP``/``ED`` tokens are matched case-sensitively (uppercase
    only) so common mixed-case words such as the name "Ed" are never captured; the
    unambiguous NC*/creditless forms stay case-insensitive.
    """

    def add(pattern: str, value: str, *, ignore_case: bool) -> None:
        rebulk.regex(
            "(?P<other>" + pattern + ")" + _CREDITS_SUFFIX,
            flags=re.IGNORECASE if ignore_case else 0,
            name="other",
            children=True,
            private_parent=True,
            validate_all=True,
            validator={"__parent__": seps_surround},
            formatter={
                "other": lambda _match, value=value: value,
                "credits_number": _format_credits_number,
                "version": int,
            },
            disabled=lambda context: is_disabled(context, "other"),
        )

    # NC*/creditless forms are unambiguous — match them case-insensitively.
    add(r"NC-?OP|creditless-?op(?:ening)?", "Opening Credits", ignore_case=True)
    add(r"NC-?ED|creditless-?(?:ed|ending)", "Ending Credits", ignore_case=True)
    # Bare uppercase tokens. OPED is the combined opening+ending sequence (not creditless).
    add(r"OPED|OP", "Opening Credits", ignore_case=False)
    add(r"ED", "Ending Credits", ignore_case=False)


#: A match may only start on a token boundary. Without it a leading word part is a valid starting
#: point for the regex — the "the" of "Breathe.Complete.Series" opens an article group — and the
#: whole match is then dropped by ``seps_surround``, taking the real marker down with it: the
#: scan resumes *after* the rejected span, so "Complete.Series" is never tried.
_TOKEN_START = r"(?<![^\W_])"


def complete_words(
    rebulk: Rebulk,
    complete_marker_words: Iterable[str],
    season_words: Iterable[str],
    complete_article_words: Iterable[str],
    complete_prefix_words: Iterable[str],
    season_number_separators: Iterable[str],
) -> None:
    """
    Custom pattern to find complete seasons from words.

    ``complete_marker_words`` are the completeness markers themselves, ``Complete`` and its
    equivalents in other languages. ``complete_article_words`` only qualify a marker that a season
    word already anchors ("The Complete Series"), whereas ``complete_prefix_words`` carry the
    completeness on their own ("L'Intégrale", "Coffret Intégrale"). ``season_number_separators``
    are the tokens that may join the season numbers a marker spans, e.g. the ``&`` of
    "Seasons 1 & 2 - Complete"; plain separators are always allowed.
    """
    complete_marker_pattern = build_or_pattern(complete_marker_words)
    season_words_pattern = build_or_pattern(season_words)
    complete_article_words_pattern = build_or_pattern(complete_article_words)
    # The season numbers listed between the season word and the marker: "1", "1 & 2", "1 and 2".
    season_numbers_pattern = r"(?:-+(?:\d+|" + build_or_pattern(season_number_separators, escape=True) + r"))+-+"

    def validate_complete(match: Match) -> bool:
        """
        Make sure season word is are defined.
        :param match:
        :type match:
        :return:
        :rtype:
        """
        children = match.children
        return not (not children.named("completeWordsBefore") and not children.named("completeWordsAfter"))

    rebulk.regex(
        _TOKEN_START
        + "(?P<completeArticle>"
        + complete_article_words_pattern
        + "-)?"
        + "(?P<completeWordsBefore>"
        + season_words_pattern
        + "-)?"
        + complete_marker_pattern
        + "(?P<completeWordsAfter>-"
        + season_words_pattern
        + ")?",
        private_names=["completeArticle", "completeWordsBefore", "completeWordsAfter"],
        value={"other": "Complete"},
        tags=["release-group-prefix"],
        validator={"__parent__": and_(seps_surround, validate_complete)},
    )

    # "Season 1 Complete", "Seasons 1 & 2 - Complete": the season numbers sit between the season
    # word and the marker, so the adjacency pattern above cannot see the word. Anchoring on the
    # numbered season word keeps the marker alive even when nothing matched the numbers — the
    # season chain is off under a forced ``type=movie`` (#944).
    rebulk.regex(
        season_words_pattern + season_numbers_pattern + "(?P<other>" + complete_marker_pattern + ")",
        children=True,
        private_parent=True,
        validate_all=True,
        value={"other": "Complete"},
        tags=["release-group-prefix"],
        validator={"__parent__": seps_surround},
    )

    # "L'Intégrale", "Coffret Intégrale": the prefix carries the completeness with no season word
    # to anchor on, so the first pattern rejects it. The separator is optional because the French
    # elided article glues to the marker — the apostrophe is not a separator, so "L'Intégrale" is
    # a single token that has to be matched whole for the marker to leave the title.
    rebulk.regex(
        _TOKEN_START
        + "(?P<completePrefix>"
        + build_or_pattern(complete_prefix_words)
        + "-?)"
        + complete_marker_pattern,
        private_names=["completePrefix"],
        value={"other": "Complete"},
        tags=["release-group-prefix"],
        validator={"__parent__": seps_surround},
    )


class ProperCountRule(Rule):
    """
    Add proper_count property
    """

    priority = POST_PROCESS

    consequence = AppendMatch

    properties = {"proper_count": [None]}

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        propers = matches.named("other", lambda match: match.value == "Proper")
        if propers:
            raws: dict[str, Match] = {}  # Count distinct raw values
            for proper in propers:
                raws[raw_cleanup(proper.raw or "")] = proper

            value = 0
            start: int | None = None
            end: int | None = None

            proper_count_matches: list[Match] = []

            for proper in raws.values():
                if not start or start > proper.start:
                    start = proper.start
                if not end or end < proper.end:
                    end = proper.end
                proper_count = proper.children.named("proper_count", 0)
                if proper_count:
                    value += int(proper_count.value)
                elif "real" in proper.tags:
                    value += 2
                else:
                    value += 1

            assert start is not None
            assert end is not None
            proper_count_match = Match(name="proper_count", start=start, end=end, input_string=matches.input_string)
            proper_count_match.value = value
            proper_count_matches.append(proper_count_match)

            return proper_count_matches
        return None


class ImageArtKeywordToOther(Rule):
    """
    Reclassify an artwork keyword (poster, fanart, …) as `other` when it is the
    title of an image filepart, so artwork files aren't mistaken for real titles.

    Scoped strictly to fileparts that hold an `image`-tagged container, so a real
    video whose title contains "cover"/"logo" is never reclassified.
    """

    priority = POST_PROCESS
    consequence = [RemoveMatch, AppendMatch]

    properties: dict[str, Any]  # type: ignore[misc]  # instance-level, populated from config

    def __init__(self, art_keywords: dict[str, str]) -> None:
        super().__init__()
        self.art_keywords = art_keywords
        self.properties = {"other": list(dict.fromkeys(art_keywords.values()))}

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        to_append: list[Match] = []
        for filepart in matches.markers.named("path"):
            if not matches.range(
                filepart.start,
                filepart.end,
                predicate=lambda match: match.name == "container" and "image" in match.tags,
                index=0,
            ):
                continue
            for candidate in matches.range(
                filepart.start,
                filepart.end,
                predicate=lambda match: match.name in ("title", "alternative_title", "episode_title"),
            ):
                key = re.sub(r"[\s._-]+", "", str(candidate.value or "").strip().lower())
                canonical = self.art_keywords.get(key)
                if not canonical:
                    continue
                to_remove.append(candidate)
                other_match = Match(
                    candidate.start, candidate.end, name="other", value=canonical, input_string=matches.input_string
                )
                to_append.append(other_match)
        if to_remove or to_append:
            return to_remove, to_append
        return None


class AppendCreditless(Rule):
    """
    Surface a `Creditless` other value for creditless opening/ending tokens.

    The `Opening Credits` / `Ending Credits` matches conflate two facts: which
    sequence it is (opening vs ending) and whether it is creditless (no text
    overlay, the ``NC``/``creditless`` forms). This rule keeps opening/ending in
    its existing match and adds a separate `Creditless` value over the same span
    so the creditless attribute is distinguishable. The combined ``OPED`` token
    is opening+ending, not creditless, so it is left untouched.

    Runs at POST_PROCESS so a credits match removed by the has-neighbor
    validators never leaves an orphan `Creditless` behind.
    """

    priority = POST_PROCESS
    consequence = AppendMatch

    properties = {"other": ["Creditless"]}

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_append: list[Match] = []
        for match in matches.named("other", predicate=lambda m: m.value in ("Opening Credits", "Ending Credits")):
            raw = re.sub(r"[\s._-]+", "", (match.raw or "").lower())
            if raw.startswith("nc") or "creditless" in raw:
                to_append.append(
                    Match(match.start, match.end, name="other", value="Creditless", input_string=matches.input_string)
                )
        return to_append


class AppendOpedEndingCredits(Rule):
    """
    ``OPED`` is the combined opening *and* ending sequence, so it carries both
    `Opening Credits` (already matched) and `Ending Credits`. This adds the
    missing `Ending Credits` value over the same span.
    """

    priority = POST_PROCESS
    consequence = AppendMatch

    properties = {"other": ["Ending Credits"]}

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_append: list[Match] = []
        for match in matches.named("other", predicate=lambda m: m.value == "Opening Credits"):
            if re.sub(r"[\s._-]+", "", (match.raw or "").lower()) == "oped":
                to_append.append(
                    Match(
                        match.start, match.end, name="other", value="Ending Credits", input_string=matches.input_string
                    )
                )
        return to_append


class RenameAnotherToOther(Rule):
    """
    Rename `another` properties to `other`
    """

    priority = 32
    consequence = RenameMatch("other")

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        return matches.named("another")


class ValidateHasNeighbor(Rule):
    """
    Validate tag has-neighbor
    """

    consequence = RemoveMatch
    priority = 64

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        ret: list[Match] = []
        for to_check in matches.range(predicate=lambda match: "has-neighbor" in match.tags):
            previous_match = matches.previous(to_check, index=0)
            previous_group = matches.markers.previous(to_check, lambda marker: marker.name == "group", 0)
            if previous_group and (not previous_match or previous_group.end > previous_match.end):
                previous_match = previous_group
            if previous_match and not (matches.input_string or "")[previous_match.end : to_check.start].strip(seps):
                break
            next_match = matches.next(to_check, index=0)
            next_group = matches.markers.next(to_check, lambda marker: marker.name == "group", 0)
            if next_group and (not next_match or next_group.start < next_match.start):
                next_match = next_group
            if next_match and not (matches.input_string or "")[to_check.end : next_match.start].strip(seps):
                break
            ret.append(to_check)
        return ret


class ValidateHasNeighborBefore(Rule):
    """
    Validate tag has-neighbor-before that previous match exists.
    """

    consequence = RemoveMatch
    priority = 64

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        ret: list[Match] = []
        for to_check in matches.range(predicate=lambda match: "has-neighbor-before" in match.tags):
            next_match = matches.next(to_check, index=0)
            next_group = matches.markers.next(to_check, lambda marker: marker.name == "group", 0)
            if next_group and (not next_match or next_group.start < next_match.start):
                next_match = next_group
            if next_match and not (matches.input_string or "")[to_check.end : next_match.start].strip(seps):
                break
            ret.append(to_check)
        return ret


class ValidateHasNeighborAfter(Rule):
    """
    Validate tag has-neighbor-after that next match exists.
    """

    consequence = RemoveMatch
    priority = 64

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        ret: list[Match] = []
        for to_check in matches.range(predicate=lambda match: "has-neighbor-after" in match.tags):
            previous_match = matches.previous(to_check, index=0)
            previous_group = matches.markers.previous(to_check, lambda marker: marker.name == "group", 0)
            if previous_group and (not previous_match or previous_group.end > previous_match.end):
                previous_match = previous_group
            if previous_match and not (matches.input_string or "")[previous_match.end : to_check.start].strip(seps):
                break
            ret.append(to_check)
        return ret


class ValidateScreenerRule(Rule):
    """
    Validate tag other.validate.screener
    """

    consequence = RemoveMatch
    priority = 64

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        ret: list[Match] = []
        for screener in matches.named("other", lambda match: "other.validate.screener" in match.tags):
            source_match = matches.previous(screener, lambda match: match.initiator.name == "source", 0)
            if not source_match or (matches.input_string or "")[source_match.end : screener.start].strip(seps):
                ret.append(screener)
        return ret


class ValidateMuxRule(Rule):
    """
    Validate tag other.validate.mux
    """

    consequence = RemoveMatch
    priority = 64

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        ret: list[Match] = []
        for mux in matches.named("other", lambda match: "other.validate.mux" in match.tags):
            source_match = matches.previous(mux, lambda match: match.initiator.name == "source", 0)
            if not source_match:
                ret.append(mux)
        return ret


class ValidateHardcodedSubs(Rule):
    """Validate HC matches."""

    priority = 32
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        for hc_match in matches.named("other", predicate=lambda match: match.value == "Hardcoded Subtitles"):
            next_match = matches.next(hc_match, predicate=lambda match: match.name == "subtitle_language", index=0)
            if next_match and not matches.holes(
                hc_match.end, next_match.start, predicate=lambda match: match.value.strip(seps)
            ):
                continue

            previous_match = matches.previous(
                hc_match, predicate=lambda match: match.name == "subtitle_language", index=0
            )
            if previous_match and not matches.holes(
                previous_match.end, hc_match.start, predicate=lambda match: match.value.strip(seps)
            ):
                continue

            to_remove.append(hc_match)

        return to_remove


class ValidateStreamingServiceNeighbor(Rule):
    """Validate streaming service's neighbors."""

    priority = 32
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        for match in matches.named(
            "other",
            predicate=lambda m: (
                m.initiator.name != "source"
                and ("streaming_service.prefix" in m.tags or "streaming_service.suffix" in m.tags)
            ),
        ):
            match = match.initiator
            if not seps_after(match):
                if "streaming_service.prefix" in match.tags:
                    next_match = matches.next(match, lambda m: m.name == "streaming_service", 0)
                    if next_match and not matches.holes(
                        match.end, next_match.start, predicate=lambda m: m.value.strip(seps)
                    ):
                        continue
                if match.children:
                    to_remove.extend(match.children)
                to_remove.append(match)

            elif not seps_before(match):
                if "streaming_service.suffix" in match.tags:
                    previous_match = matches.previous(match, lambda m: m.name == "streaming_service", 0)
                    if previous_match and not matches.holes(
                        previous_match.end, match.start, predicate=lambda m: m.value.strip(seps)
                    ):
                        continue

                if match.children:
                    to_remove.extend(match.children)
                to_remove.append(match)

        return to_remove


class ValidateAtEnd(Rule):
    """Validate other which should occur at the end of a filepart."""

    priority = 32
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        for filepart in matches.markers.named("path"):
            for match in matches.range(
                filepart.start, filepart.end, predicate=lambda m: m.name == "other" and "at-end" in m.tags
            ):
                if matches.holes(match.end, filepart.end, predicate=lambda m: m.value.strip(seps)) or matches.range(
                    match.end, filepart.end, predicate=lambda m: m.name not in ("other", "container")
                ):
                    to_remove.append(match)

        return to_remove


class ValidateStereoVRContext(Rule):
    """
    A stereoscopic abbreviation (``SBS``/``LR``/``TB``/``OU``) is ambiguous on its
    own (``SBS`` is also a broadcaster, the others are common letter pairs). Keep it
    as a stereoscopic ``other`` only when its filepart carries a VR/3D signal, and
    then let it win its span over a colliding ``streaming_service`` (so ``VR.SBS``
    means Side By Side, not the SBS broadcaster). Without such a signal, drop it so
    the token falls back to whatever it would otherwise be (broadcaster, release
    group, title…).
    """

    consequence = RemoveMatch
    priority = 64

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        to_remove: list[Match] = []
        for filepart in matches.markers.named("path"):
            gated = matches.range(
                filepart.start,
                filepart.end,
                predicate=lambda m: m.name == "other" and STEREO_VR_CONTEXT_TAG in m.tags,
            )
            if not gated:
                continue
            if _has_vr_context(matches, filepart):
                for stereo in gated:
                    to_remove.extend(
                        matches.range(
                            stereo.start,
                            stereo.end,
                            predicate=lambda m: m.name == "streaming_service",
                        )
                    )
            else:
                to_remove.extend(gated)
        return to_remove


class ValidateReal(Rule):
    """
    Validate Real
    """

    consequence = RemoveMatch
    priority = 64

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        ret: list[Match] = []
        for filepart in matches.markers.named("path"):
            for match in matches.range(filepart.start, filepart.end, lambda m: m.name == "other" and "real" in m.tags):
                if not matches.range(filepart.start, match.start):
                    ret.append(match)

        return ret

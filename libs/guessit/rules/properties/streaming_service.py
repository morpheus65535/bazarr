#!/usr/bin/env python
"""
streaming_service property
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rebulk import Rebulk
from rebulk.remodule import re
from rebulk.rules import RemoveMatch, Rule

from ...config import load_config_patterns
from ...rules.common import dash, seps
from ...rules.common.validators import seps_after, seps_before
from ..common.pattern import is_disabled

if TYPE_CHECKING:
    from rebulk.match import Match, Matches


def streaming_service(config: dict[str, Any]) -> Rebulk:
    """Streaming service property.

    :param config: rule configuration
    :type config: dict
    :return:
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, "streaming_service"))
    rebulk = rebulk.string_defaults(ignore_case=True).regex_defaults(flags=re.IGNORECASE, abbreviations=[dash])
    rebulk.defaults(name="streaming_service", tags=["source-prefix"])

    load_config_patterns(rebulk, config)

    rebulk.rules(ValidateStreamingService)

    return rebulk


class ValidateStreamingService(Rule):
    """Validate streaming service matches."""

    priority = 128
    consequence = RemoveMatch

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        """Streaming service is always before source.

        :param matches:
        :type matches: rebulk.match.Matches
        :param context:
        :type context: dict
        :return:
        """
        to_remove: list[Match] = []
        input_string = matches.input_string or ""
        for service in matches.named("streaming_service"):
            # A short service code (e.g. CN) glued inside a larger token (CNHD) is a
            # substring of that token, not a real streaming service (upstream #651).
            raw = service.raw or ""
            if len(raw) <= 3:
                char_after = input_string[service.end : service.end + 1]
                char_before = input_string[service.start - 1 : service.start] if service.start > 0 else ""
                if (char_after and re.match(r"[a-z0-9]", char_after, re.IGNORECASE)) or (
                    char_before and re.match(r"[a-z0-9]", char_before, re.IGNORECASE)
                ):
                    to_remove.append(service)
                    continue

            next_match = matches.next(service, lambda match: "streaming_service.suffix" in match.tags, 0)
            previous_match = matches.previous(service, lambda match: "streaming_service.prefix" in match.tags, 0)
            has_other = service.initiator and service.initiator.children.named("other")

            if (
                not has_other
                and (
                    not next_match
                    or matches.holes(service.end, next_match.start, predicate=lambda match: match.value.strip(seps))
                    or not seps_before(service)
                )
                and (
                    not previous_match
                    or matches.holes(previous_match.end, service.start, predicate=lambda match: match.value.strip(seps))
                    or not seps_after(service)
                )
            ):
                to_remove.append(service)
                continue

            if service.value == "Comedy Central":
                # Current match is a valid streaming service, removing invalid Criterion Collection (CC) matches
                to_remove.extend(matches.named("edition", predicate=lambda match: match.value == "Criterion"))

        return to_remove

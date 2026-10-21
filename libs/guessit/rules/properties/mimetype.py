#!/usr/bin/env python
"""
mimetype property
"""

from __future__ import annotations

import mimetypes
from typing import TYPE_CHECKING, Any

from rebulk import POST_PROCESS, CustomRule, Rebulk
from rebulk.match import Match

from ...rules.processors import Processors
from ..common.pattern import is_disabled

if TYPE_CHECKING:
    from rebulk.match import Matches


def mimetype(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, "mimetype"))
    # Register .svg deterministically (stdlib mimetypes is OS-dependent for it). #305
    mimetypes.add_type("image/svg+xml", ".svg")
    rebulk.rules(Mimetype)

    return rebulk


class Mimetype(CustomRule):
    """
    Mimetype post processor
    :param matches:
    :type matches:
    :return:
    :rtype:
    """

    priority = POST_PROCESS

    dependency = Processors

    def when(self, matches: Matches, context: dict[str, Any] | None) -> Any:
        assert matches.input_string is not None
        mime, _ = mimetypes.guess_type(matches.input_string, strict=False)
        return mime

    def then(self, matches: Matches, when_response: Any, context: dict[str, Any] | None) -> None:
        mime = when_response
        assert matches.input_string is not None
        matches.append(Match(len(matches.input_string), len(matches.input_string), name="mimetype", value=mime))

    @property
    def properties(self) -> dict[str, list[None]]:  # type: ignore[override]
        """
        Properties for this rule.
        """
        return {"mimetype": [None]}

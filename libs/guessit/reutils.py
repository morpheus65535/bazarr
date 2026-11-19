#!/usr/bin/env python
"""
Utils for re module
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rebulk.remodule import re

if TYPE_CHECKING:
    from collections.abc import Iterable


def build_or_pattern(patterns: Iterable[str], name: str | None = None, escape: bool = False) -> str:
    """
    Build a or pattern string from a list of possible patterns

    :param patterns:
    :type patterns:
    :param name:
    :type name:
    :param escape:
    :type escape:
    :return:
    :rtype:
    """
    or_pattern: list[str] = []
    for pattern in patterns:
        if not or_pattern:
            or_pattern.append("(?")
            if name:
                or_pattern.append(f"P<{name}>")
            else:
                or_pattern.append(":")
        else:
            or_pattern.append("|")
        or_pattern.append(f"(?:{re.escape(pattern)})" if escape else pattern)
    or_pattern.append(")")
    return "".join(or_pattern)

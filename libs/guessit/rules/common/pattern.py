#!/usr/bin/env python
"""
Pattern utility functions
"""

from __future__ import annotations

from typing import Any


def is_disabled(context: dict[str, Any] | None, name: str) -> bool:
    """Whether a specific pattern is disabled.

    The context object might define an inclusion list (includes) or an exclusion list (excludes)
    A pattern is considered disabled if it's found in the exclusion list or
    it's not found in the inclusion list and the inclusion list is not empty or not defined.

    :param context:
    :param name:
    :return:
    """
    if not context:
        return False

    excludes = context.get("excludes")
    if excludes and name in excludes:
        return True

    includes = context.get("includes")
    if includes:
        return name not in includes
    return False

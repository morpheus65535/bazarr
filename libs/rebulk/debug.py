#!/usr/bin/env python
"""
Debug tools.

Can be configured by changing values of those variable.

DEBUG = False
Enable this variable to activate debug features (like defined_at parameters). It can slow down Rebulk

LOG_LEVEL = 0
Default log level of generated rebulk logs.
"""

from __future__ import annotations

import inspect
import logging
import os
from collections import namedtuple
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from types import FrameType

DEBUG: bool = False
LOG_LEVEL: int = logging.DEBUG


def _truthy_env(name: str) -> bool:
    """True when environment variable ``name`` holds an affirmative value."""
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


# Optional, opt-in contract check (off by default, no cost in production): when
# enabled, ``Rebulk.matches`` asserts that every named match value produced by a
# pattern matches the ``value_type`` of the same-named declared ``Key`` (see
# ``declare_keys``), turning the declared type into an enforced contract. Flip it
# on from the environment (``REBULK_CHECK_DECLARED_KEYS=1``) — e.g. in CI or for a
# downstream corpus run — or by setting this flag directly.
CHECK_DECLARED_KEYS: bool = _truthy_env("REBULK_CHECK_DECLARED_KEYS")


class Frame(namedtuple("Frame", ["lineno", "package", "name", "filename"])):
    """
    Stack frame representation.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return f"{os.path.basename(self.filename)}#L{self.lineno}"


def defined_at() -> Frame | None:
    """
    Get definition location of a pattern or a match (outside of rebulk package).
    :return:
    :rtype:
    """
    if DEBUG:
        frame: FrameType | None = inspect.currentframe()
        while frame:
            try:
                if frame.f_globals["__package__"] != __package__:
                    break
            except KeyError:  # pragma:no cover
                # If package is missing, consider we are in. Workaround for python 3.3.
                break
            frame = frame.f_back
        frame = cast("FrameType", frame)
        ret = Frame(
            frame.f_lineno,
            frame.f_globals.get("__package__"),
            frame.f_globals.get("__name__"),
            frame.f_code.co_filename,
        )
        del frame
        return ret
    return None

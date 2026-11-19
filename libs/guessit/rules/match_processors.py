"""
Match processors
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from guessit.rules.common import seps

if TYPE_CHECKING:
    from rebulk.match import Match


def strip(match: Match, chars: str = seps) -> bool | None:
    """
    Strip given characters from match.

    :param chars:
    :param match:
    :return:
    """
    assert match.input_string is not None
    while match.input_string[match.start] in chars:
        match.start += 1
    while match.input_string[match.end - 1] in chars:
        match.end -= 1
    if not match:
        return False
    return None

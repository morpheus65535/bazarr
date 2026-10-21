#!/usr/bin/env python
"""
Validator functions to use in patterns.

All those function have last argument as match, so it's possible to use functools.partial to bind previous arguments.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Container

    from .match import Match


def chars_before(chars: Container[str], match: Match) -> bool:
    """
    Validate the match if left character is in a given sequence.

    :param chars:
    :type chars:
    :param match:
    :type match:
    :return:
    :rtype:
    """
    if match.start <= 0:
        return True
    return cast("str", match.input_string)[match.start - 1] in chars


def chars_after(chars: Container[str], match: Match) -> bool:
    """
    Validate the match if right character is in a given sequence.

    :param chars:
    :type chars:
    :param match:
    :type match:
    :return:
    :rtype:
    """
    input_string = cast("str", match.input_string)
    if match.end >= len(input_string):
        return True
    return input_string[match.end] in chars


def chars_surround(chars: Container[str], match: Match) -> bool:
    """
    Validate the match if surrounding characters are in a given sequence.

    :param chars:
    :type chars:
    :param match:
    :type match:
    :return:
    :rtype:
    """
    return chars_before(chars, match) and chars_after(chars, match)


def validators(*chained_validators: Callable[[Match], bool]) -> Callable[[Match], bool]:
    """
    Creates a validator chain from several validator functions.

    :param chained_validators:
    :type chained_validators:
    :return:
    :rtype:
    """

    def validator_chain(match: Match) -> bool:
        return all(chained_validator(match) for chained_validator in chained_validators)

    return validator_chain


def allways_true(match: Match) -> bool:
    """
    A validator which is allways true
    :param match:
    :return:
    """
    return True

#!/usr/bin/env python
"""
Validators
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, TypeVar

from rebulk.validators import chars_after, chars_before, chars_surround

from . import seps

if TYPE_CHECKING:
    from collections.abc import Callable

_T = TypeVar("_T")

seps_before = partial(chars_before, seps)
seps_after = partial(chars_after, seps)
seps_surround = partial(chars_surround, seps)


def int_coercable(string: str) -> bool:
    """
    Check if string can be coerced to int
    :param string:
    :type string:
    :return:
    :rtype:
    """
    try:
        int(string)
        return True
    except ValueError:
        return False


def and_(*validators: Callable[[_T], bool]) -> Callable[[_T], bool]:
    """
    Compose validators functions
    :param validators:
    :type validators:
    :return:
    :rtype:
    """

    def composed(string: _T) -> bool:
        """
        Composed validators function
        :param string:
        :type string:
        :return:
        :rtype:
        """
        return all(validator(string) for validator in validators)

    return composed


def or_(*validators: Callable[[_T], bool]) -> Callable[[_T], bool]:
    """
    Compose validators functions
    :param validators:
    :type validators:
    :return:
    :rtype:
    """

    def composed(string: _T) -> bool:
        """
        Composed validators function
        :param string:
        :type string:
        :return:
        :rtype:
        """
        return any(validator(string) for validator in validators)

    return composed

# pragma: no cover
"""
Implement basic assertions to be used in assertion action
"""

from __future__ import annotations

import re
from types import UnionType
from typing import get_args
from typing import get_origin
from typing import Union


def eq(value, other) -> bool:
    """Equals"""
    return value == other


def ne(value, other) -> bool:
    """Not equals"""
    return value != other


def gt(value, other) -> bool:
    """Greater than"""
    return value > other


def lt(value, other) -> bool:
    """Lower than"""
    return value < other


def ge(value, other) -> bool:
    """Greater than or equal"""
    return value >= other


def gte(value, other) -> bool:
    """backwards compatibility"""
    return ge(value, other)


def le(value, other) -> bool:
    """Lower than or equal"""
    return value <= other


def lte(value, other) -> bool:
    """backwards compatibility"""
    return le(value, other)


def identity(value, other) -> bool:
    """Identity check using ID"""
    return value is other


def is_type_of(value, other) -> bool:
    """Type check that performs lookup on parameterized generic types.
    For singular primary types this check is very fast ans just
    calls isinstance.
    For SpecialForm annotations like Union and Parametrized types like T[T]
    or T[T, T] then this is a bit more costly.
    NOTE: Find ways to improve the execution time on this, like
    caching same value -> same type
    """

    origin = get_origin(other)
    args = get_args(other)

    if not args and isinstance(other, tuple):
        # Got (T[T],) from recursive call
        return any(is_type_of(value, item) for item in other)

    if args:
        if origin in [Union, UnionType]:
            return any(is_type_of(value, arg) for arg in args)
        elif origin in (list, tuple):
            return isinstance(value, (list, tuple)) and all(
                is_type_of(item, args) for item in value
            )
        elif origin is dict:
            k_type, v_type = args
            return isinstance(value, dict) and all(
                is_type_of(k, k_type) and is_type_of(v, v_type)
                for k, v in value.items()
            )

    if getattr(other, "_dynaconf_dictvalue", None):
        other = dict

    return isinstance(value, other)


def is_in(value, other) -> bool:
    """Existence"""
    return value in other


def is_not_in(value, other) -> bool:
    """Inexistence"""
    return value not in other


def contains(value, other) -> bool:
    """Contains"""
    return other in value


def cont(value, other) -> bool:
    """backwards compatibility"""
    return contains(value, other)


def not_contains(value, other) -> bool:
    """Not Contains"""
    return other not in value


def len_eq(value, other) -> bool:
    """Length Equal"""
    return len(value) == other


def len_ne(value, other) -> bool:
    """Length Not equal"""
    return len(value) != other


def len_min(value, other) -> bool:
    """Minimum length"""
    return len(value) >= other


def len_max(value, other) -> bool:
    """Maximum length"""
    return len(value) <= other


def startswith(value, term) -> bool:
    """returns value.startswith(term) result"""
    return value.startswith(term)


def endswith(value, term) -> bool:
    """returns value.endswith(term) result"""
    return value.endswith(term)


def not_startswith(value, term) -> bool:
    """returns not value.startswith(term) result"""
    return not value.startswith(term)


def not_endswith(value, term) -> bool:
    """returns not value.endswith(term) result"""
    return not value.endswith(term)


def regex(value, pattern: str | re.Pattern) -> bool:
    """Matches a regexp against the value"""
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
    return bool(pattern.match(value))


def not_regex(value, pattern: str | re.Pattern) -> bool:
    """Not Matches a regexp against the value"""
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
    return not pattern.match(value)

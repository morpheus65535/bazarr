#!/usr/bin/env python
"""
Various utilities functions
"""

from __future__ import annotations

from collections.abc import Container, Iterable, Iterator, MutableSet
from types import GeneratorType
from typing import Any, TypeVar

_T = TypeVar("_T")


def find_all(
    string: str,
    sub: str,
    start: int | None = None,
    end: int | None = None,
    ignore_case: bool = False,
    **kwargs: Any,
) -> Iterator[int]:
    """
    Return all indices in string s where substring sub is
    found, such that sub is contained in the slice s[start:end].

    >>> list(find_all('The quick brown fox jumps over the lazy dog', 'fox'))
    [16]

    >>> list(find_all('The quick brown fox jumps over the lazy dog', 'mountain'))
    []

    >>> list(find_all('The quick brown fox jumps over the lazy dog', 'The'))
    [0]

    >>> list(find_all(
    ... 'Carved symbols in a mountain hollow on the bank of an inlet irritated an eccentric person',
    ... 'an'))
    [44, 51, 70]

    >>> list(find_all(
    ... 'Carved symbols in a mountain hollow on the bank of an inlet irritated an eccentric person',
    ... 'an',
    ... 50,
    ... 60))
    [51]

    :param string: the input string
    :type string: str
    :param sub: the substring
    :type sub: str
    :return: all indices in the input string
    :rtype: __generator[str]
    """
    if ignore_case:
        sub = sub.lower()
        string = string.lower()
    while True:
        start = string.find(sub, start, end)
        if start == -1:
            return
        yield start
        start += len(sub)


def get_first_defined(
    data: Container[_T],
    keys: Iterable[_T],
    default_value: Any = None,
) -> Any:
    """
    Get the first defined key in data.
    :param data:
    :type data:
    :param keys:
    :type keys:
    :param default_value:
    :type default_value:
    :return:
    :rtype:
    """
    for key in keys:
        if key in data:
            return data[key]  # type: ignore[index]
    return default_value


def is_iterable(obj: Any) -> bool:
    """
    Are we being asked to look up a list of things, instead of a single thing?
    We check for the `__iter__` attribute so that this can cover types that
    don't have to be known by this module, such as NumPy arrays.

    Strings, however, should be considered as atomic values to look up, not
    iterables.

    We don't need to check for the Python 2 `unicode` type, because it doesn't
    have an `__iter__` attribute anyway.
    """
    return (hasattr(obj, "__iter__") and not isinstance(obj, str)) or isinstance(obj, GeneratorType)


def extend_safe(target: list[_T], source: Iterable[_T]) -> None:
    """
    Extends target with elements from source that are not already present.

    Uses a set for O(1) membership checks when elements are hashable (the common
    case: patterns and rules are deduplicated on every ``matches()`` call), and
    falls back to linear membership when they are not (e.g. unhashable
    introspected property values).

    :param target:
    :type target: list
    :param source:
    :type source: list
    """
    try:
        seen = set(target)
        for elt in source:
            if elt not in seen:
                target.append(elt)
                seen.add(elt)
    except TypeError:  # unhashable element: fall back to linear membership checks
        for elt in source:
            if elt not in target:
                target.append(elt)


class _Ref:
    """
    Reference for IdentitySet
    """

    def __init__(self, value: Any) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        return self.value is other.value  # type: ignore[attr-defined]

    def __hash__(self) -> int:
        return id(self.value)


class IdentitySet(MutableSet[Any]):  # pragma: no cover
    """
    Set based on identity
    """

    def __init__(self, items: Iterable[Any] | None = None) -> None:
        if items is None:
            items = []
        self.refs = set(map(_Ref, items))

    def __contains__(self, elem: object) -> bool:
        return _Ref(elem) in self.refs

    def __iter__(self) -> Iterator[Any]:
        return (ref.value for ref in self.refs)

    def __len__(self) -> int:
        return len(self.refs)

    def add(self, value: Any) -> None:
        self.refs.add(_Ref(value))

    def discard(self, value: Any) -> None:
        self.refs.discard(_Ref(value))

    def update(self, iterable: Iterable[Any]) -> None:
        """
        Update set with iterable
        :param iterable:
        :type iterable:
        :return:
        :rtype:
        """
        for elem in iterable:
            self.add(elem)

    def __repr__(self) -> str:  # pragma: no cover
        return f"{type(self).__name__}({list(self)})"

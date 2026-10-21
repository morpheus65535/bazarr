#!/usr/bin/env python
# Vendored from toposort 1.4 (https://bitbucket.org/ericvsmith/toposort),
# Copyright 2014 True Blade Systems, Inc., licensed under the Apache License,
# Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0).
#
# Local changes: CyclicDependency error (upstream pull request #2), Python 3
# only, fully type-annotated.

from __future__ import annotations

from functools import reduce
from typing import TYPE_CHECKING, Any, TypeVar, cast

if TYPE_CHECKING:
    from collections.abc import Iterator

_T = TypeVar("_T")


class CyclicDependency(ValueError):
    def __init__(self, cyclic: dict[_T, set[_T]]) -> None:
        s = f"Cyclic dependencies exist among these items: {', '.join(repr(x) for x in cyclic.items())}"
        super().__init__(s)
        self.cyclic = cyclic


def toposort(data: dict[_T, set[_T]]) -> Iterator[set[_T]]:
    """
    Dependencies are expressed as a dictionary whose keys are items
    and whose values are a set of dependent items. Output is a list of
    sets in topological order. The first set consists of items with no
    dependences, each subsequent set consists of items that depend upon
    items in the preceding sets.
    :param data:
    :type data:
    :return:
    :rtype:
    """

    # Special case empty input.
    if len(data) == 0:
        return

    # Copy the input so as to leave it unmodified.
    data = data.copy()

    # Ignore self dependencies.
    for k, v in data.items():
        v.discard(k)
    # Find all items that don't depend on anything.
    extra_items_in_deps = reduce(set.union, data.values()) - set(data.keys())
    # Add empty dependences where needed.
    data.update({item: set() for item in extra_items_in_deps})
    while True:
        ordered = {item for item, dep in data.items() if len(dep) == 0}
        if not ordered:
            break
        yield ordered
        data = {item: (dep - ordered) for item, dep in data.items() if item not in ordered}
    if len(data) != 0:
        raise CyclicDependency(data)


def toposort_flatten(data: dict[_T, set[_T]], sort: bool = True) -> list[_T]:
    """
    Returns a single list of dependencies. For any set returned by
    toposort(), those items are sorted and appended to the result (just to
    make the results deterministic).
    :param data:
    :type data:
    :param sort:
    :type sort:
    :return: Single list of dependencies.
    :rtype: list
    """

    result: list[_T] = []
    for d in toposort(data):
        result.extend(cast("list[_T]", sorted(cast("Any", d))) if sort else list(d))
    return result

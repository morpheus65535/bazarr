#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 True Blade Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Original:
#   - https://bitbucket.org/ericvsmith/toposort (1.4)
# Modifications:
#   - merged Pull request #2 for CyclicDependency error
#   - import reduce as original name
#   - support python 2.6 dict comprehension

# pylint: skip-file
from functools import reduce


class CyclicDependency(ValueError):
    def __init__(self, cyclic):
        s = 'Cyclic dependencies exist among these items: {0}'.format(', '.join(repr(x) for x in cyclic.items()))
        super(CyclicDependency, self).__init__(s)
        self.cyclic = cyclic


def toposort(data):
    """
    Dependencies are expressed as a dictionary whose keys are items
    and whose values are a set of dependent items. Output is a list of
    sets in topological order. The first set consists of items with no
    dependences, each subsequent set consists of items that depend upon
    items in the preceeding sets.
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
    data.update(dict((item, set()) for item in extra_items_in_deps))
    while True:
        ordered = set(item for item, dep in data.items() if len(dep) == 0)
        if not ordered:
            break
        yield ordered
        data = dict((item, (dep - ordered))
                for item, dep in data.items()
                if item not in ordered)
    if len(data) != 0:
        raise CyclicDependency(data)


def toposort_flatten(data, sort=True):
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

    result = []
    for d in toposort(data):
        result.extend((sorted if sort else list)(d))
    return result

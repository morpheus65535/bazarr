#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Various utilities functions
"""
try:
    from collections.abc import MutableSet
except ImportError:
    from collections import MutableSet

from types import GeneratorType


def find_all(string, sub, start=None, end=None, ignore_case=False, **kwargs):
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
    #pylint: disable=unused-argument
    if ignore_case:
        sub = sub.lower()
        string = string.lower()
    while True:
        start = string.find(sub, start, end)
        if start == -1:
            return
        yield start
        start += len(sub)


def get_first_defined(data, keys, default_value=None):
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
            return data[key]
    return default_value


def is_iterable(obj):
    """
    Are we being asked to look up a list of things, instead of a single thing?
    We check for the `__iter__` attribute so that this can cover types that
    don't have to be known by this module, such as NumPy arrays.

    Strings, however, should be considered as atomic values to look up, not
    iterables.

    We don't need to check for the Python 2 `unicode` type, because it doesn't
    have an `__iter__` attribute anyway.
    """
    # pylint: disable=consider-using-ternary
    return hasattr(obj, '__iter__') and not isinstance(obj, str) or isinstance(obj, GeneratorType)


def extend_safe(target, source):
    """
    Extends source list to target list only if elements doesn't exists in target list.
    :param target:
    :type target: list
    :param source:
    :type source: list
    """
    for elt in source:
        if elt not in target:
            target.append(elt)


class _Ref(object):
    """
    Reference for IdentitySet
    """
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value is other.value

    def __hash__(self):
        return id(self.value)


class IdentitySet(MutableSet):  # pragma: no cover
    """
    Set based on identity
    """
    def __init__(self, items=None):  # pylint: disable=super-init-not-called
        if items is None:
            items = []
        self.refs = set(map(_Ref, items))

    def __contains__(self, elem):
        return _Ref(elem) in self.refs

    def __iter__(self):
        return (ref.value for ref in self.refs)

    def __len__(self):
        return len(self.refs)

    def add(self, value):
        self.refs.add(_Ref(value))

    def discard(self, value):
        self.refs.discard(_Ref(value))

    def update(self, iterable):
        """
        Update set with iterable
        :param iterable:
        :type iterable:
        :return:
        :rtype:
        """
        for elem in iterable:
            self.add(elem)

    def __repr__(self):  # pragma: no cover
        return "%s(%s)" % (type(self).__name__, list(self))

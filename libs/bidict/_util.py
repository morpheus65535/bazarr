# -*- coding: utf-8 -*-
# Copyright 2009-2019 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Useful functions for working with bidirectional mappings and related data."""

from itertools import chain, repeat

from .compat import iteritems, Mapping


_NULL_IT = repeat(None, 0)  # repeat 0 times -> raise StopIteration from the start


def _iteritems_mapping_or_iterable(arg):
    """Yield the items in *arg*.

    If *arg* is a :class:`~collections.abc.Mapping`, return an iterator over its items.
    Otherwise return an iterator over *arg* itself.
    """
    return iteritems(arg) if isinstance(arg, Mapping) else iter(arg)


def _iteritems_args_kw(*args, **kw):
    """Yield the items from the positional argument (if given) and then any from *kw*.

    :raises TypeError: if more than one positional argument is given.
    """
    args_len = len(args)
    if args_len > 1:
        raise TypeError('Expected at most 1 positional argument, got %d' % args_len)
    itemchain = None
    if args:
        arg = args[0]
        if arg:
            itemchain = _iteritems_mapping_or_iterable(arg)
    if kw:
        iterkw = iteritems(kw)
        itemchain = chain(itemchain, iterkw) if itemchain else iterkw
    return itemchain or _NULL_IT


def inverted(arg):
    """Yield the inverse items of the provided object.

    If *arg* has a :func:`callable` ``__inverted__`` attribute,
    return the result of calling it.

    Otherwise, return an iterator over the items in `arg`,
    inverting each item on the fly.

    *See also* :attr:`bidict.BidirectionalMapping.__inverted__`
    """
    inv = getattr(arg, '__inverted__', None)
    if callable(inv):
        return inv()
    return ((val, key) for (key, val) in _iteritems_mapping_or_iterable(arg))

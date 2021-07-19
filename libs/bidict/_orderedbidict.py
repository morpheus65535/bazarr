# -*- coding: utf-8 -*-
# Copyright 2009-2019 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


#==============================================================================
#                    * Welcome to the bidict source code *
#==============================================================================

# Doing a code review? You'll find a "Code review nav" comment like the one
# below at the top and bottom of the most important source files. This provides
# a suggested initial path through the source when reviewing.
#
# Note: If you aren't reading this on https://github.com/jab/bidict, you may be
# viewing an outdated version of the code. Please head to GitHub to review the
# latest version, which contains important improvements over older versions.
#
# Thank you for reading and for any feedback you provide.

#                             * Code review nav *
#==============================================================================
#  ← Prev: _frozenordered.py  Current: _orderedbidict.py                <FIN>
#==============================================================================


"""Provides :class:`OrderedBidict`."""

from ._mut import MutableBidict
from ._orderedbase import OrderedBidictBase


class OrderedBidict(OrderedBidictBase, MutableBidict):
    """Mutable bidict type that maintains items in insertion order."""

    __slots__ = ()
    __hash__ = None  # since this class is mutable; explicit > implicit.

    def clear(self):
        """Remove all items."""
        self._fwdm.clear()
        self._invm.clear()
        self._sntl.nxt = self._sntl.prv = self._sntl

    def popitem(self, last=True):  # pylint: disable=arguments-differ
        u"""*x.popitem() → (k, v)*

        Remove and return the most recently added item as a (key, value) pair
        if *last* is True, else the least recently added item.

        :raises KeyError: if *x* is empty.
        """
        if not self:
            raise KeyError('mapping is empty')
        key = next((reversed if last else iter)(self))
        val = self._pop(key)
        return key, val

    def move_to_end(self, key, last=True):
        """Move an existing key to the beginning or end of this ordered bidict.

        The item is moved to the end if *last* is True, else to the beginning.

        :raises KeyError: if the key does not exist
        """
        node = self._fwdm[key]
        node.prv.nxt = node.nxt
        node.nxt.prv = node.prv
        sntl = self._sntl
        if last:
            last = sntl.prv
            node.prv = last
            node.nxt = sntl
            sntl.prv = last.nxt = node
        else:
            first = sntl.nxt
            node.prv = sntl
            node.nxt = first
            sntl.nxt = first.prv = node


#                             * Code review nav *
#==============================================================================
#  ← Prev: _frozenordered.py  Current: _orderedbidict.py                <FIN>
#==============================================================================

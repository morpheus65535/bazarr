# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
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


"""Provide :class:`OrderedBidict`."""

import typing as _t

from ._mut import MutableBidict
from ._orderedbase import OrderedBidictBase
from ._typing import KT, VT


class OrderedBidict(OrderedBidictBase[KT, VT], MutableBidict[KT, VT]):
    """Mutable bidict type that maintains items in insertion order."""

    __slots__ = ()

    if _t.TYPE_CHECKING:
        @property
        def inverse(self) -> 'OrderedBidict[VT, KT]': ...

    def clear(self) -> None:
        """Remove all items."""
        self._fwdm.clear()
        self._invm.clear()
        self._sntl.nxt = self._sntl.prv = self._sntl

    def popitem(self, last: bool = True) -> _t.Tuple[KT, VT]:
        """*x.popitem() → (k, v)*

        Remove and return the most recently added item as a (key, value) pair
        if *last* is True, else the least recently added item.

        :raises KeyError: if *x* is empty.
        """
        if not self:
            raise KeyError('mapping is empty')
        key = next((reversed if last else iter)(self))  # type: ignore
        val = self._pop(key)
        return key, val

    def move_to_end(self, key: KT, last: bool = True) -> None:
        """Move an existing key to the beginning or end of this ordered bidict.

        The item is moved to the end if *last* is True, else to the beginning.

        :raises KeyError: if the key does not exist
        """
        node = self._fwdm[key]
        node.prv.nxt = node.nxt
        node.nxt.prv = node.prv
        sntl = self._sntl
        if last:
            lastnode = sntl.prv
            node.prv = lastnode
            node.nxt = sntl
            sntl.prv = lastnode.nxt = node
        else:
            firstnode = sntl.nxt
            node.prv = sntl
            node.nxt = firstnode
            sntl.nxt = firstnode.prv = node


#                             * Code review nav *
#==============================================================================
#  ← Prev: _frozenordered.py  Current: _orderedbidict.py                <FIN>
#==============================================================================

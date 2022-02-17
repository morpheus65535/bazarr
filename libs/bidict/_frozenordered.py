# -*- coding: utf-8 -*-
# Copyright 2009-2021 Joshua Bronson. All Rights Reserved.
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
#← Prev: _orderedbase.py  Current: _frozenordered.py  Next: _orderedbidict.py →
#==============================================================================

"""Provide :class:`FrozenOrderedBidict`, an immutable, hashable, ordered bidict."""

import typing as _t

from ._frozenbidict import frozenbidict
from ._orderedbase import OrderedBidictBase
from ._typing import KT, VT


class FrozenOrderedBidict(OrderedBidictBase[KT, VT]):
    """Hashable, immutable, ordered bidict type.

    Like a hashable :class:`bidict.OrderedBidict`
    without the mutating APIs, or like a
    reversible :class:`bidict.frozenbidict` even on Python < 3.8.
    (All bidicts are order-preserving when never mutated, so frozenbidict is
    already order-preserving, but only on Python 3.8+, where dicts are
    reversible, are all bidicts (including frozenbidict) also reversible.)

    If you are using Python 3.8+, frozenbidict gives you everything that
    FrozenOrderedBidict gives you, but with less space overhead.
    """

    __slots__ = ('_hash',)
    __hash__ = frozenbidict.__hash__

    if _t.TYPE_CHECKING:
        @property
        def inverse(self) -> 'FrozenOrderedBidict[VT, KT]': ...

    # Delegate to backing dicts for more efficient implementations of keys() and values().
    # Possible with FrozenOrderedBidict but not OrderedBidict since FrozenOrderedBidict
    # is immutable, i.e. these can't get out of sync after initialization due to mutation.
    def keys(self) -> _t.KeysView[KT]:
        """A set-like object providing a view on the contained keys."""
        return self._fwdm._fwdm.keys()  # type: ignore [return-value]

    def values(self) -> _t.KeysView[VT]:  # type: ignore [override]
        """A set-like object providing a view on the contained values."""
        return self._invm._fwdm.keys()  # type: ignore [return-value]

    # Can't delegate for items() because values in _fwdm and _invm are nodes.

    # On Python 3.8+, delegate to backing dicts for a more efficient implementation
    # of __iter__ and __reversed__ (both of which call this _iter() method):
    if hasattr(dict, '__reversed__'):
        def _iter(self, *, reverse: bool = False) -> _t.Iterator[KT]:
            itfn = reversed if reverse else iter
            return itfn(self._fwdm._fwdm)  # type: ignore [operator,no-any-return]
    else:
        # On Python < 3.8, just optimize __iter__:
        def _iter(self, *, reverse: bool = False) -> _t.Iterator[KT]:
            if not reverse:
                return iter(self._fwdm._fwdm)
            return super()._iter(reverse=True)


#                             * Code review nav *
#==============================================================================
#← Prev: _orderedbase.py  Current: _frozenordered.py  Next: _orderedbidict.py →
#==============================================================================

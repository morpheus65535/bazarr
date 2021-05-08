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
#← Prev: _orderedbase.py  Current: _frozenordered.py  Next: _orderedbidict.py →
#==============================================================================

"""Provides :class:`FrozenOrderedBidict`, an immutable, hashable, ordered bidict."""

from ._delegating_mixins import _DelegateKeysToFwdm
from ._frozenbidict import frozenbidict
from ._orderedbase import OrderedBidictBase
from .compat import DICTS_ORDERED, PY2, izip


# If the Python implementation's dict type is ordered (e.g. PyPy or CPython >= 3.6), then
# `FrozenOrderedBidict` can delegate to `_fwdm` for keys: Both `_fwdm` and `_invm` will always
# be initialized with the provided items in the correct order, and since `FrozenOrderedBidict`
# is immutable, their respective orders can't get out of sync after a mutation. (Can't delegate
# to `_fwdm` for items though because values in `_fwdm` are nodes.)
_BASES = ((_DelegateKeysToFwdm,) if DICTS_ORDERED else ()) + (OrderedBidictBase,)
_CLSDICT = dict(
    __slots__=(),
    # Must set __hash__ explicitly, Python prevents inheriting it.
    # frozenbidict.__hash__ can be reused for FrozenOrderedBidict:
    # FrozenOrderedBidict inherits BidictBase.__eq__ which is order-insensitive,
    # and frozenbidict.__hash__ is consistent with BidictBase.__eq__.
    __hash__=frozenbidict.__hash__.__func__ if PY2 else frozenbidict.__hash__,
    __doc__='Hashable, immutable, ordered bidict type.',
    __module__=__name__,  # Otherwise unpickling fails in Python 2.
)

# When PY2 (so we provide iteritems) and DICTS_ORDERED, e.g. on PyPy, the following implementation
# of iteritems may be more efficient than that inherited from `Mapping`. This exploits the property
# that the keys in `_fwdm` and `_invm` are already in the right order:
if PY2 and DICTS_ORDERED:
    _CLSDICT['iteritems'] = lambda self: izip(self._fwdm, self._invm)  # noqa: E501; pylint: disable=protected-access

FrozenOrderedBidict = type('FrozenOrderedBidict', _BASES, _CLSDICT)  # pylint: disable=invalid-name


#                             * Code review nav *
#==============================================================================
#← Prev: _orderedbase.py  Current: _frozenordered.py  Next: _orderedbidict.py →
#==============================================================================

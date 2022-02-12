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
#  ← Prev: _mut.py            Current: _bidict.py     Next: _orderedbase.py →
#==============================================================================


"""Provide :class:`bidict`."""

import typing as _t

from ._delegating import _DelegatingBidict
from ._mut import MutableBidict
from ._typing import KT, VT


class bidict(_DelegatingBidict[KT, VT], MutableBidict[KT, VT]):
    """Base class for mutable bidirectional mappings."""

    __slots__ = ()

    if _t.TYPE_CHECKING:
        @property
        def inverse(self) -> 'bidict[VT, KT]': ...


#                             * Code review nav *
#==============================================================================
#  ← Prev: _mut.py            Current: _bidict.py     Next: _orderedbase.py →
#==============================================================================

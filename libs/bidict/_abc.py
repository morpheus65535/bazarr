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
#  ← Prev: __init__.py         Current: _abc.py              Next: _base.py →
#==============================================================================


"""Provide the :class:`BidirectionalMapping` abstract base class."""

import typing as _t
from abc import abstractmethod

from ._typing import KT, VT


class BidirectionalMapping(_t.Mapping[KT, VT]):
    """Abstract base class (ABC) for bidirectional mapping types.

    Extends :class:`collections.abc.Mapping` primarily by adding the
    (abstract) :attr:`inverse` property,
    which implementors of :class:`BidirectionalMapping`
    should override to return a reference to the inverse
    :class:`BidirectionalMapping` instance.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def inverse(self) -> 'BidirectionalMapping[VT, KT]':
        """The inverse of this bidirectional mapping instance.

        *See also* :attr:`bidict.BidictBase.inverse`, :attr:`bidict.BidictBase.inv`

        :raises NotImplementedError: Meant to be overridden in subclasses.
        """
        # The @abstractproperty decorator prevents BidirectionalMapping subclasses from being
        # instantiated unless they override this method. So users shouldn't be able to get to the
        # point where they can unintentionally call this implementation of .inverse on something
        # anyway. Could leave the method body empty, but raise NotImplementedError so it's extra
        # clear there's no reason to call this implementation (e.g. via super() after overriding).
        raise NotImplementedError

    def __inverted__(self) -> _t.Iterator[_t.Tuple[VT, KT]]:
        """Get an iterator over the items in :attr:`inverse`.

        This is functionally equivalent to iterating over the items in the
        forward mapping and inverting each one on the fly, but this provides a
        more efficient implementation: Assuming the already-inverted items
        are stored in :attr:`inverse`, just return an iterator over them directly.

        Providing this default implementation enables external functions,
        particularly :func:`~bidict.inverted`, to use this optimized
        implementation when available, instead of having to invert on the fly.

        *See also* :func:`bidict.inverted`
        """
        return iter(self.inverse.items())

    def values(self) -> _t.KeysView[VT]:  # type: ignore [override]  # https://github.com/python/typeshed/issues/4435
        """A set-like object providing a view on the contained values.

        Override the implementation inherited from
        :class:`~collections.abc.Mapping`.
        Because the values of a :class:`~bidict.BidirectionalMapping`
        are the keys of its inverse,
        this returns a :class:`~collections.abc.KeysView`
        rather than a :class:`~collections.abc.ValuesView`,
        which has the advantages of constant-time containment checks
        and supporting set operations.
        """
        return self.inverse.keys()  # type: ignore [return-value]


class MutableBidirectionalMapping(BidirectionalMapping[KT, VT], _t.MutableMapping[KT, VT]):
    """Abstract base class (ABC) for mutable bidirectional mapping types."""

    __slots__ = ()


#                             * Code review nav *
#==============================================================================
#  ← Prev: __init__.py         Current: _abc.py              Next: _base.py →
#==============================================================================

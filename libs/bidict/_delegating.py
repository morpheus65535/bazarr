# -*- coding: utf-8 -*-
# Copyright 2009-2021 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Provide :class:`_DelegatingBidict`."""

import typing as _t

from ._base import BidictBase
from ._typing import KT, VT


class _DelegatingBidict(BidictBase[KT, VT]):
    """Provide optimized implementations of several methods by delegating to backing dicts.

    Used to override less efficient implementations inherited by :class:`~collections.abc.Mapping`.
    """

    __slots__ = ()

    def __iter__(self) -> _t.Iterator[KT]:
        """Iterator over the contained keys."""
        return iter(self._fwdm)

    def keys(self) -> _t.KeysView[KT]:
        """A set-like object providing a view on the contained keys."""
        return self._fwdm.keys()  # type: ignore [return-value]

    def values(self) -> _t.KeysView[VT]:  # type: ignore [override]  # https://github.com/python/typeshed/issues/4435
        """A set-like object providing a view on the contained values."""
        return self._invm.keys()  # type: ignore [return-value]

    def items(self) -> _t.ItemsView[KT, VT]:
        """A set-like object providing a view on the contained items."""
        return self._fwdm.items()  # type: ignore [return-value]

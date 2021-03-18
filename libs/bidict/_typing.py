# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Provide typing-related objects."""

import typing as _t


KT = _t.TypeVar('KT')
VT = _t.TypeVar('VT')
IterItems = _t.Iterable[_t.Tuple[KT, VT]]
MapOrIterItems = _t.Union[_t.Mapping[KT, VT], IterItems[KT, VT]]

DT = _t.TypeVar('DT')   #: for default arguments
VDT = _t.Union[VT, DT]


class _BareReprMeta(type):
    def __repr__(cls) -> str:
        return f'<{cls.__name__}>'


class _NONE(metaclass=_BareReprMeta):
    """Sentinel type used to represent 'missing'."""


OKT = _t.Union[KT, _NONE]    #: optional key type
OVT = _t.Union[VT, _NONE]    #: optional value type

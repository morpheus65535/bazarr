# Copyright 2009-2022 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Provide typing-related objects."""

import typing as t
from enum import Enum


KT = t.TypeVar('KT')
VT = t.TypeVar('VT')
IterItems = t.Iterable[t.Tuple[KT, VT]]
MapOrIterItems = t.Union[t.Mapping[KT, VT], IterItems[KT, VT]]


class MissingT(Enum):
    """Sentinel used to represent none/missing when None itself can't be used."""

    MISSING = 'MISSING'

    def __repr__(self) -> str:
        return '<MISSING>'


MISSING = MissingT.MISSING
OKT = t.Union[KT, MissingT]  #: optional key type
OVT = t.Union[VT, MissingT]  #: optional value type

DT = t.TypeVar('DT')  #: for default arguments
ODT = t.Union[DT, MissingT]

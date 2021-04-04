# -*- coding: utf-8 -*-
# Copyright 2009-2019 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Provides bidict duplication policies and the :class:`_OnDup` class."""


from collections import namedtuple

from ._marker import _Marker


_OnDup = namedtuple('_OnDup', 'key val kv')


class DuplicationPolicy(_Marker):
    """Base class for bidict's duplication policies.

    *See also* :ref:`basic-usage:Values Must Be Unique`
    """

    __slots__ = ()


#: Raise an exception when a duplication is encountered.
RAISE = DuplicationPolicy('DUP_POLICY.RAISE')

#: Overwrite an existing item when a duplication is encountered.
OVERWRITE = DuplicationPolicy('DUP_POLICY.OVERWRITE')

#: Keep the existing item and ignore the new item when a duplication is encountered.
IGNORE = DuplicationPolicy('DUP_POLICY.IGNORE')

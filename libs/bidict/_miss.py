# -*- coding: utf-8 -*-
# Copyright 2009-2019 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Provides the :obj:`_MISS` sentinel, for internally signaling "missing/not found"."""

from ._marker import _Marker


_MISS = _Marker('MISSING')

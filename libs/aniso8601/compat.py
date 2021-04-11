# -*- coding: utf-8 -*-

# Copyright (c) 2021, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

import sys

PY2 = sys.version_info[0] == 2

if PY2:
    range = xrange
else:
    range = range

def is_string(tocheck):
    if PY2:
        return isinstance(tocheck, str) or isinstance(tocheck, unicode)

    return isinstance(tocheck, str)

# -*- coding: utf-8 -*-

# Copyright (c) 2021, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

def find_separator(value):
    """Returns the decimal separator index if found else -1."""
    return normalize(value).find('.')

def normalize(value):
    """Returns the string that the decimal separators are normalized."""
    return value.replace(',', '.')

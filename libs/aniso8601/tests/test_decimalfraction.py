# -*- coding: utf-8 -*-

# Copyright (c) 2021, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

import unittest

from aniso8601.decimalfraction import find_separator, normalize

class TestDecimalFractionFunctions(unittest.TestCase):
    def test_find_separator(self):
        self.assertEqual(find_separator(''), -1)
        self.assertEqual(find_separator('1234'), -1)
        self.assertEqual(find_separator('12.345'), 2)
        self.assertEqual(find_separator('123,45'), 3)

    def test_normalize(self):
        self.assertEqual(normalize(''), '')
        self.assertEqual(normalize('12.34'), '12.34')
        self.assertEqual(normalize('123,45'), '123.45')
        self.assertEqual(normalize('123,45,67'), '123.45.67')

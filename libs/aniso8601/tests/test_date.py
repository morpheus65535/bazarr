# -*- coding: utf-8 -*-

# Copyright (c) 2021, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

import unittest
import aniso8601

from aniso8601.exceptions import ISOFormatError
from aniso8601.date import (parse_date, _parse_year, _parse_calendar_day,
                            _parse_calendar_month, _parse_week_day,
                            _parse_week, _parse_ordinal_date,
                            get_date_resolution)
from aniso8601.resolution import DateResolution
from aniso8601.tests.compat import mock

class TestDateResolutionFunctions(unittest.TestCase):
    def test_get_date_resolution_year(self):
        self.assertEqual(get_date_resolution('2013'), DateResolution.Year)
        self.assertEqual(get_date_resolution('0001'), DateResolution.Year)
        self.assertEqual(get_date_resolution('19'), DateResolution.Year)

    def test_get_date_resolution_month(self):
        self.assertEqual(get_date_resolution('1981-04'), DateResolution.Month)

    def test_get_date_resolution_week(self):
        self.assertEqual(get_date_resolution('2004-W53'), DateResolution.Week)
        self.assertEqual(get_date_resolution('2009-W01'), DateResolution.Week)
        self.assertEqual(get_date_resolution('2004W53'), DateResolution.Week)

    def test_get_date_resolution_year_weekday(self):
        self.assertEqual(get_date_resolution('2004-W53-6'),
                         DateResolution.Weekday)
        self.assertEqual(get_date_resolution('2004W536'),
                         DateResolution.Weekday)

    def test_get_date_resolution_year_ordinal(self):
        self.assertEqual(get_date_resolution('1981-095'),
                         DateResolution.Ordinal)
        self.assertEqual(get_date_resolution('1981095'),
                         DateResolution.Ordinal)

    def test_get_date_resolution_badtype(self):
        testtuples = (None, 1, False, 1.234)

        for testtuple in testtuples:
            with self.assertRaises(ValueError):
                get_date_resolution(testtuple)

    def test_get_date_resolution_extended_year(self):
        testtuples = ('+2000', '+30000')

        for testtuple in testtuples:
            with self.assertRaises(NotImplementedError):
                get_date_resolution(testtuple)

    def test_get_date_resolution_badweek(self):
        testtuples = ('2004-W1', '2004W1')

        for testtuple in testtuples:
            with self.assertRaises(ISOFormatError):
                get_date_resolution(testtuple)

    def test_get_date_resolution_badweekday(self):
        testtuples = ('2004-W53-67', '2004W5367')

        for testtuple in testtuples:
            with self.assertRaises(ISOFormatError):
                get_date_resolution(testtuple)

    def test_get_date_resolution_badstr(self):
        testtuples = ('W53', '2004-W', '2014-01-230', '2014-012-23',
                      '201-01-23', '201401230', '201401', 'bad', '')

        for testtuple in testtuples:
            with self.assertRaises(ISOFormatError):
                get_date_resolution(testtuple)

class TestDateParserFunctions(unittest.TestCase):
    def test_parse_date(self):
        testtuples = (('2013', {'YYYY': '2013'}),
                      ('0001', {'YYYY': '0001'}),
                      ('19', {'YYYY': '19'}),
                      ('1981-04-05', {'YYYY': '1981', 'MM': '04', 'DD': '05'}),
                      ('19810405', {'YYYY': '1981', 'MM': '04', 'DD': '05'}),
                      ('1981-04', {'YYYY': '1981', 'MM': '04'}),
                      ('2004-W53', {'YYYY': '2004', 'Www': '53'}),
                      ('2009-W01', {'YYYY': '2009', 'Www': '01'}),
                      ('2004-W53-6', {'YYYY': '2004', 'Www': '53', 'D': '6'}),
                      ('2004W53', {'YYYY': '2004', 'Www': '53'}),
                      ('2004W536', {'YYYY': '2004', 'Www': '53', 'D': '6'}),
                      ('1981-095', {'YYYY': '1981', 'DDD': '095'}),
                      ('1981095', {'YYYY': '1981', 'DDD': '095'}))

        for testtuple in testtuples:
            with mock.patch.object(aniso8601.date.PythonTimeBuilder,
                                   'build_date') as mockBuildDate:
                mockBuildDate.return_value = testtuple[1]

                result = parse_date(testtuple[0])

                self.assertEqual(result, testtuple[1])
                mockBuildDate.assert_called_once_with(**testtuple[1])

    def test_parse_date_badtype(self):
        testtuples = (None, 1, False, 1.234)

        for testtuple in testtuples:
            with self.assertRaises(ValueError):
                parse_date(testtuple, builder=None)

    def test_parse_date_badstr(self):
        testtuples = ('W53', '2004-W', '2014-01-230', '2014-012-23',
                      '201-01-23', '201401230', '201401', 'bad', '')

        for testtuple in testtuples:
            with self.assertRaises(ISOFormatError):
                parse_date(testtuple, builder=None)

    def test_parse_date_mockbuilder(self):
        mockBuilder = mock.Mock()

        expectedargs = {'YYYY': '1981', 'MM': '04', 'DD':'05'}

        mockBuilder.build_date.return_value = expectedargs

        result = parse_date('1981-04-05', builder=mockBuilder)

        self.assertEqual(result, expectedargs)
        mockBuilder.build_date.assert_called_once_with(**expectedargs)

    def test_parse_year(self):
        testtuples = (('2013', {'YYYY': '2013'}),
                      ('0001', {'YYYY': '0001'}),
                      ('1', {'YYYY': '1'}),
                      ('19', {'YYYY': '19'}))

        for testtuple in testtuples:
            mockBuilder = mock.Mock()
            mockBuilder.build_date.return_value = testtuple[1]

            result = _parse_year(testtuple[0], mockBuilder)

            self.assertEqual(result, testtuple[1])
            mockBuilder.build_date.assert_called_once_with(**testtuple[1])

    def test_parse_calendar_day(self):
        testtuples = (('1981-04-05', {'YYYY': '1981', 'MM': '04', 'DD': '05'}),
                      ('19810405', {'YYYY': '1981', 'MM': '04', 'DD': '05'}))

        for testtuple in testtuples:
            mockBuilder = mock.Mock()
            mockBuilder.build_date.return_value = testtuple[1]

            result = _parse_calendar_day(testtuple[0], mockBuilder)

            self.assertEqual(result, testtuple[1])
            mockBuilder.build_date.assert_called_once_with(**testtuple[1])

    def test_parse_calendar_month(self):
        testtuples = (('1981-04', {'YYYY': '1981', 'MM': '04'}),)

        for testtuple in testtuples:
            mockBuilder = mock.Mock()
            mockBuilder.build_date.return_value = testtuple[1]

            result = _parse_calendar_month(testtuple[0], mockBuilder)

            self.assertEqual(result, testtuple[1])
            mockBuilder.build_date.assert_called_once_with(**testtuple[1])

    def test_parse_calendar_month_nohyphen(self):
        #Hyphen is required
        with self.assertRaises(ISOFormatError):
            _parse_calendar_month('198104', None)

    def test_parse_week_day(self):
        testtuples = (('2004-W53-6', {'YYYY': '2004', 'Www': '53', 'D': '6'}),
                      ('2009-W01-1', {'YYYY': '2009', 'Www': '01', 'D': '1'}),
                      ('2009-W53-7', {'YYYY': '2009', 'Www': '53', 'D': '7'}),
                      ('2010-W01-1', {'YYYY': '2010', 'Www': '01', 'D': '1'}),
                      ('2004W536', {'YYYY': '2004', 'Www': '53', 'D': '6'}),
                      ('2009W011', {'YYYY': '2009', 'Www': '01', 'D': '1'}),
                      ('2009W537', {'YYYY': '2009', 'Www': '53', 'D': '7'}),
                      ('2010W011', {'YYYY': '2010', 'Www': '01', 'D': '1'}))

        for testtuple in testtuples:
            mockBuilder = mock.Mock()
            mockBuilder.build_date.return_value = testtuple[1]

            result = _parse_week_day(testtuple[0], mockBuilder)

            self.assertEqual(result, testtuple[1])
            mockBuilder.build_date.assert_called_once_with(**testtuple[1])

    def test_parse_week(self):
        testtuples = (('2004-W53', {'YYYY': '2004', 'Www': '53'}),
                      ('2009-W01', {'YYYY': '2009', 'Www': '01'}),
                      ('2009-W53', {'YYYY': '2009', 'Www': '53'}),
                      ('2010-W01', {'YYYY': '2010', 'Www': '01'}),
                      ('2004W53', {'YYYY': '2004', 'Www': '53'}),
                      ('2009W01', {'YYYY': '2009', 'Www': '01'}),
                      ('2009W53', {'YYYY': '2009', 'Www': '53'}),
                      ('2010W01', {'YYYY': '2010', 'Www': '01'}))

        for testtuple in testtuples:
            mockBuilder = mock.Mock()
            mockBuilder.build_date.return_value = testtuple[1]

            result = _parse_week(testtuple[0], mockBuilder)

            self.assertEqual(result, testtuple[1])
            mockBuilder.build_date.assert_called_once_with(**testtuple[1])

    def test_parse_ordinal_date(self):
        testtuples = (('1981-095', {'YYYY': '1981', 'DDD': '095'}),
                      ('1981095', {'YYYY': '1981', 'DDD': '095'}),
                      ('1981365', {'YYYY': '1981', 'DDD': '365'}),
                      ('1980366', {'YYYY': '1980', 'DDD': '366'}))

        for testtuple in testtuples:
            mockBuilder = mock.Mock()
            mockBuilder.build_date.return_value = testtuple[1]

            result = _parse_ordinal_date(testtuple[0], mockBuilder)

            self.assertEqual(result, testtuple[1])
            mockBuilder.build_date.assert_called_once_with(**testtuple[1])

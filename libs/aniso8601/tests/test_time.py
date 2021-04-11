# -*- coding: utf-8 -*-

# Copyright (c) 2021, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

import unittest
import aniso8601

from aniso8601.exceptions import ISOFormatError
from aniso8601.resolution import TimeResolution
from aniso8601.time import (get_time_resolution, parse_datetime, parse_time,
                            _parse_hour, _parse_minute_time,
                            _parse_second_time, _split_tz)
from aniso8601.tests.compat import mock

class TestTimeResolutionFunctions(unittest.TestCase):
    def test_get_time_resolution(self):
        self.assertEqual(get_time_resolution('01:23:45'),
                         TimeResolution.Seconds)
        self.assertEqual(get_time_resolution('24:00:00'),
                         TimeResolution.Seconds)
        self.assertEqual(get_time_resolution('23:21:28,512400'),
                         TimeResolution.Seconds)
        self.assertEqual(get_time_resolution('23:21:28.512400'),
                         TimeResolution.Seconds)
        self.assertEqual(get_time_resolution('01:23'), TimeResolution.Minutes)
        self.assertEqual(get_time_resolution('24:00'), TimeResolution.Minutes)
        self.assertEqual(get_time_resolution('01:23,4567'),
                         TimeResolution.Minutes)
        self.assertEqual(get_time_resolution('01:23.4567'),
                         TimeResolution.Minutes)
        self.assertEqual(get_time_resolution('012345'), TimeResolution.Seconds)
        self.assertEqual(get_time_resolution('240000'), TimeResolution.Seconds)
        self.assertEqual(get_time_resolution('0123'), TimeResolution.Minutes)
        self.assertEqual(get_time_resolution('2400'), TimeResolution.Minutes)
        self.assertEqual(get_time_resolution('01'), TimeResolution.Hours)
        self.assertEqual(get_time_resolution('24'), TimeResolution.Hours)
        self.assertEqual(get_time_resolution('12,5'), TimeResolution.Hours)
        self.assertEqual(get_time_resolution('12.5'), TimeResolution.Hours)
        self.assertEqual(get_time_resolution('232128.512400+00:00'),
                         TimeResolution.Seconds)
        self.assertEqual(get_time_resolution('0123.4567+00:00'),
                         TimeResolution.Minutes)
        self.assertEqual(get_time_resolution('01.4567+00:00'),
                         TimeResolution.Hours)
        self.assertEqual(get_time_resolution('01:23:45+00:00'),
                         TimeResolution.Seconds)
        self.assertEqual(get_time_resolution('24:00:00+00:00'),
                         TimeResolution.Seconds)
        self.assertEqual(get_time_resolution('23:21:28.512400+00:00'),
                         TimeResolution.Seconds)
        self.assertEqual(get_time_resolution('01:23+00:00'),
                         TimeResolution.Minutes)
        self.assertEqual(get_time_resolution('24:00+00:00'),
                         TimeResolution.Minutes)
        self.assertEqual(get_time_resolution('01:23.4567+00:00'),
                         TimeResolution.Minutes)
        self.assertEqual(get_time_resolution('23:21:28.512400+11:15'),
                         TimeResolution.Seconds)
        self.assertEqual(get_time_resolution('23:21:28.512400-12:34'),
                         TimeResolution.Seconds)
        self.assertEqual(get_time_resolution('23:21:28.512400Z'),
                         TimeResolution.Seconds)
        self.assertEqual(get_time_resolution('06:14:00.000123Z'),
                         TimeResolution.Seconds)

    def test_get_time_resolution_badtype(self):
        testtuples = (None, 1, False, 1.234)

        for testtuple in testtuples:
            with self.assertRaises(ValueError):
                get_time_resolution(testtuple)

    def test_get_time_resolution_badstr(self):
        testtuples = ('A6:14:00.000123Z', '06:14:0B', 'bad', '')

        for testtuple in testtuples:
            with self.assertRaises(ISOFormatError):
                get_time_resolution(testtuple)

class TestTimeParserFunctions(unittest.TestCase):
    def test_parse_time(self):
        testtuples = (('01:23:45', {'hh': '01', 'mm': '23',
                                    'ss': '45', 'tz': None}),
                      ('24:00:00', {'hh': '24', 'mm': '00',
                                    'ss': '00', 'tz': None}),
                      ('23:21:28,512400', {'hh': '23', 'mm': '21',
                                           'ss': '28.512400', 'tz': None}),
                      ('23:21:28.512400', {'hh': '23', 'mm': '21',
                                           'ss': '28.512400', 'tz': None}),
                      ('01:03:11.858714', {'hh': '01', 'mm': '03',
                                           'ss': '11.858714', 'tz': None}),
                      ('14:43:59.9999997', {'hh': '14', 'mm': '43',
                                            'ss': '59.9999997', 'tz': None}),
                      ('01:23', {'hh': '01', 'mm': '23', 'tz': None}),
                      ('24:00', {'hh': '24', 'mm': '00', 'tz': None}),
                      ('01:23,4567', {'hh': '01', 'mm': '23.4567',
                                      'tz': None}),
                      ('01:23.4567', {'hh': '01', 'mm': '23.4567',
                                      'tz': None}),
                      ('012345', {'hh': '01', 'mm': '23',
                                  'ss': '45', 'tz': None}),
                      ('240000', {'hh': '24', 'mm': '00',
                                  'ss': '00', 'tz': None}),
                      ('232128,512400', {'hh': '23', 'mm': '21',
                                         'ss': '28.512400', 'tz': None}),
                      ('232128.512400', {'hh': '23', 'mm': '21',
                                         'ss': '28.512400', 'tz': None}),
                      ('010311.858714', {'hh': '01', 'mm': '03',
                                         'ss': '11.858714', 'tz': None}),
                      ('144359.9999997', {'hh': '14', 'mm': '43',
                                          'ss': '59.9999997', 'tz': None}),
                      ('0123', {'hh': '01', 'mm': '23', 'tz': None}),
                      ('2400', {'hh': '24', 'mm': '00', 'tz': None}),
                      ('01', {'hh': '01', 'tz': None}),
                      ('24', {'tz': None}),
                      ('12,5', {'hh': '12.5', 'tz': None}),
                      ('12.5', {'hh': '12.5', 'tz': None}),
                      ('232128,512400+00:00', {'hh': '23', 'mm': '21',
                                               'ss': '28.512400',
                                               'tz': (False, None,
                                                      '00', '00',
                                                      '+00:00', 'timezone')}),
                      ('232128.512400+00:00', {'hh': '23', 'mm': '21',
                                               'ss': '28.512400',
                                               'tz': (False, None,
                                                      '00', '00',
                                                      '+00:00', 'timezone')}),
                      ('0123,4567+00:00', {'hh': '01', 'mm': '23.4567',
                                           'tz': (False, None,
                                                  '00', '00',
                                                  '+00:00', 'timezone')}),
                      ('0123.4567+00:00', {'hh': '01', 'mm': '23.4567',
                                           'tz': (False, None,
                                                  '00', '00',
                                                  '+00:00', 'timezone')}),
                      ('01,4567+00:00', {'hh': '01.4567',
                                         'tz': (False, None,
                                                '00', '00',
                                                '+00:00', 'timezone')}),
                      ('01.4567+00:00', {'hh': '01.4567',
                                         'tz': (False, None,
                                                '00', '00',
                                                '+00:00', 'timezone')}),
                      ('01:23:45+00:00', {'hh': '01', 'mm': '23',
                                          'ss': '45',
                                          'tz': (False, None,
                                                 '00', '00',
                                                 '+00:00', 'timezone')}),
                      ('24:00:00+00:00', {'hh': '24', 'mm': '00',
                                          'ss': '00',
                                          'tz': (False, None,
                                                 '00', '00',
                                                 '+00:00', 'timezone')}),
                      ('23:21:28.512400+00:00', {'hh': '23', 'mm': '21',
                                                 'ss': '28.512400',
                                                 'tz': (False, None,
                                                        '00', '00',
                                                        '+00:00',
                                                        'timezone')}),
                      ('01:23+00:00', {'hh': '01', 'mm': '23',
                                       'tz': (False, None,
                                              '00', '00',
                                              '+00:00', 'timezone')}),
                      ('24:00+00:00', {'hh': '24', 'mm': '00',
                                       'tz': (False, None,
                                              '00', '00',
                                              '+00:00', 'timezone')}),
                      ('01:23.4567+00:00', {'hh': '01', 'mm': '23.4567',
                                            'tz': (False, None,
                                                   '00', '00',
                                                   '+00:00', 'timezone')}),
                      ('23:21:28.512400+11:15', {'hh': '23', 'mm': '21',
                                                 'ss': '28.512400',
                                                 'tz': (False, None,
                                                        '11', '15',
                                                        '+11:15',
                                                        'timezone')}),
                      ('23:21:28.512400-12:34', {'hh': '23', 'mm': '21',
                                                 'ss': '28.512400',
                                                 'tz': (True, None,
                                                        '12', '34',
                                                        '-12:34',
                                                        'timezone')}),
                      ('23:21:28.512400Z', {'hh': '23', 'mm': '21',
                                            'ss': '28.512400',
                                            'tz': (False, True,
                                                   None, None,
                                                   'Z', 'timezone')}),
                      ('06:14:00.000123Z', {'hh': '06', 'mm': '14',
                                            'ss': '00.000123',
                                            'tz': (False, True,
                                                   None, None,
                                                   'Z', 'timezone')}))

        for testtuple in testtuples:
            with mock.patch.object(aniso8601.time.PythonTimeBuilder,
                                   'build_time') as mockBuildTime:

                mockBuildTime.return_value = testtuple[1]

                result = parse_time(testtuple[0])

                self.assertEqual(result, testtuple[1])
                mockBuildTime.assert_called_once_with(**testtuple[1])

    def test_parse_time_badtype(self):
        testtuples = (None, 1, False, 1.234)

        for testtuple in testtuples:
            with self.assertRaises(ValueError):
                parse_time(testtuple, builder=None)

    def test_parse_time_badstr(self):
        testtuples = ('A6:14:00.000123Z', '06:14:0B', 'bad', '')

        for testtuple in testtuples:
            with self.assertRaises(ISOFormatError):
                parse_time(testtuple, builder=None)

    def test_parse_time_mockbuilder(self):
        mockBuilder = mock.Mock()

        expectedargs = {'hh': '01', 'mm': '23', 'ss': '45', 'tz': None}

        mockBuilder.build_time.return_value = expectedargs

        result = parse_time('01:23:45', builder=mockBuilder)

        self.assertEqual(result, expectedargs)
        mockBuilder.build_time.assert_called_once_with(**expectedargs)

        mockBuilder = mock.Mock()

        expectedargs = {'hh': '23', 'mm': '21', 'ss': '28.512400',
                        'tz': (False, None, '00', '00', '+00:00', 'timezone')}

        mockBuilder.build_time.return_value = expectedargs

        result = parse_time('232128.512400+00:00', builder=mockBuilder)

        self.assertEqual(result, expectedargs)
        mockBuilder.build_time.assert_called_once_with(**expectedargs)

        mockBuilder = mock.Mock()

        expectedargs = {'hh': '23', 'mm': '21', 'ss': '28.512400',
                        'tz': (False, None, '11', '15', '+11:15', 'timezone')}

        mockBuilder.build_time.return_value = expectedargs

        result = parse_time('23:21:28.512400+11:15', builder=mockBuilder)

        self.assertEqual(result, expectedargs)
        mockBuilder.build_time.assert_called_once_with(**expectedargs)

    def test_parse_datetime(self):
        testtuples = (('2019-06-05T01:03:11,858714',
                       (('2019', '06', '05', None, None, None, 'date'),
                        ('01', '03', '11.858714',
                         None, 'time'))),
                      ('2019-06-05T01:03:11.858714',
                       (('2019', '06', '05', None, None, None, 'date'),
                        ('01', '03', '11.858714',
                         None, 'time'))),
                      ('1981-04-05T23:21:28.512400Z',
                       (('1981', '04', '05', None, None, None, 'date'),
                        ('23', '21', '28.512400',
                         (False, True, None, None, 'Z', 'timezone'),
                         'time'))),
                      ('1981095T23:21:28.512400-12:34',
                       (('1981', None, None, None, None, '095', 'date'),
                        ('23', '21', '28.512400',
                         (True, None, '12', '34', '-12:34', 'timezone'),
                         'time'))),
                      ('19810405T23:21:28+00',
                       (('1981', '04', '05', None, None, None, 'date'),
                        ('23', '21', '28',
                         (False, None, '00', None, '+00', 'timezone'),
                         'time'))),
                      ('19810405T23:21:28+00:00',
                       (('1981', '04', '05', None, None, None, 'date'),
                        ('23', '21', '28',
                         (False, None, '00', '00', '+00:00', 'timezone'),
                         'time'))))

        for testtuple in testtuples:
            with mock.patch.object(aniso8601.time.PythonTimeBuilder,
                                   'build_datetime') as mockBuildDateTime:

                mockBuildDateTime.return_value = testtuple[1]

                result = parse_datetime(testtuple[0])

            self.assertEqual(result, testtuple[1])
            mockBuildDateTime.assert_called_once_with(*testtuple[1])

    def test_parse_datetime_spacedelimited(self):
        expectedargs = (('2004', None, None, '53', '6', None, 'date'),
                        ('23', '21', '28.512400',
                         (True, None, '12', '34', '-12:34', 'timezone'),
                         'time'))

        with mock.patch.object(aniso8601.time.PythonTimeBuilder,
                               'build_datetime') as mockBuildDateTime:

            mockBuildDateTime.return_value = expectedargs

            result = parse_datetime('2004-W53-6 23:21:28.512400-12:34',
                                    delimiter=' ')

        self.assertEqual(result, expectedargs)
        mockBuildDateTime.assert_called_once_with(*expectedargs)

    def test_parse_datetime_commadelimited(self):
        expectedargs = (('1981', '04', '05', None, None, None, 'date'),
                        ('23', '21', '28.512400',
                         (False, True, None, None, 'Z', 'timezone'),
                         'time'))

        with mock.patch.object(aniso8601.time.PythonTimeBuilder,
                               'build_datetime') as mockBuildDateTime:

            mockBuildDateTime.return_value = expectedargs

            result = parse_datetime('1981-04-05,23:21:28,512400Z',
                                    delimiter=',')

        self.assertEqual(result, expectedargs)
        mockBuildDateTime.assert_called_once_with(*expectedargs)

    def test_parse_datetime_baddelimiter(self):
        testtuples = ('1981-04-05,23:21:28,512400Z',
                      '2004-W53-6 23:21:28.512400-12:3',
                      '1981040523:21:28')

        for testtuple in testtuples:
            with self.assertRaises(ISOFormatError):
                parse_datetime(testtuple, builder=None)

    def test_parse_datetime_badtype(self):
        testtuples = (None, 1, False, 1.234)

        for testtuple in testtuples:
            with self.assertRaises(ValueError):
                parse_datetime(testtuple, builder=None)

    def test_parse_datetime_badstr(self):
        testtuples = ('1981-04-05TA6:14:00.000123Z',
                      '2004-W53-6T06:14:0B',
                      '2014-01-230T23:21:28+00',
                      '201401230T01:03:11.858714',
                      'bad',
                      '')

        for testtuple in testtuples:
            with self.assertRaises(ISOFormatError):
                parse_time(testtuple, builder=None)

    def test_parse_datetime_mockbuilder(self):
        mockBuilder = mock.Mock()

        expectedargs = (('1981', None, None, None, None, '095', 'date'),
                        ('23', '21', '28.512400',
                         (True, None, '12', '34', '-12:34', 'timezone'),
                         'time'))

        mockBuilder.build_datetime.return_value = expectedargs

        result = parse_datetime('1981095T23:21:28.512400-12:34',
                                builder=mockBuilder)

        self.assertEqual(result, expectedargs)
        mockBuilder.build_datetime.assert_called_once_with(*expectedargs)

    def test_parse_hour(self):
        testtuples = (('01', None, {'hh': '01', 'tz': None}),
                      ('24', None, {'tz': None}),
                      ('01.4567', None, {'hh': '01.4567', 'tz': None}),
                      ('12.5', None, {'hh': '12.5', 'tz': None}),
                      ('08', (True, None, '12', '34', '-12:34', 'timezone'),
                       {'hh': '08', 'tz':
                        (True, None, '12', '34', '-12:34', 'timezone')}))

        for testtuple in testtuples:
            mockBuilder = mock.Mock()

            mockBuilder.build_time.return_value = testtuple[2]

            result = _parse_hour(testtuple[0], testtuple[1], mockBuilder)

            self.assertEqual(result, testtuple[2])
            mockBuilder.build_time.assert_called_once_with(**testtuple[2])

    def test_parse_minute_time(self):
        testtuples = (('01:23', None, {'hh': '01', 'mm': '23', 'tz': None}),
                      ('24:00', None, {'hh': '24', 'mm': '00', 'tz': None}),
                      ('01:23.4567', None, {'hh': '01', 'mm': '23.4567',
                                            'tz': None}),
                      ('0123', None, {'hh': '01', 'mm': '23', 'tz': None}),
                      ('2400', None, {'hh': '24', 'mm': '00', 'tz': None}),
                      ('0123.4567', None, {'hh': '01', 'mm': '23.4567',
                                           'tz': None}),
                      ('08:13', (True, None, '12', '34', '-12:34', 'timezone'),
                       {'hh': '08', 'mm': '13',
                        'tz': (True, None, '12', '34', '-12:34', 'timezone')}))

        for testtuple in testtuples:
            mockBuilder = mock.Mock()

            mockBuilder.build_time.return_value = testtuple[2]

            result = _parse_minute_time(testtuple[0], testtuple[1],
                                        mockBuilder)

            self.assertEqual(result, testtuple[2])
            mockBuilder.build_time.assert_called_once_with(**testtuple[2])

    def test_parse_second_time(self):
        testtuples = (('01:23:45', None, {'hh': '01', 'mm': '23',
                                          'ss': '45', 'tz': None}),
                      ('24:00:00', None, {'hh': '24', 'mm': '00',
                                          'ss': '00', 'tz': None}),
                      ('23:21:28.512400', None, {'hh': '23', 'mm': '21',
                                                 'ss': '28.512400',
                                                 'tz': None}),
                      ('14:43:59.9999997', None, {'hh': '14', 'mm': '43',
                                                  'ss': '59.9999997',
                                                  'tz': None}),
                      ('012345', None, {'hh': '01', 'mm': '23',
                                        'ss': '45', 'tz': None}),
                      ('240000', None, {'hh': '24', 'mm': '00',
                                        'ss': '00', 'tz': None}),
                      ('232128.512400', None, {'hh': '23', 'mm': '21',
                                               'ss': '28.512400', 'tz': None}),
                      ('144359.9999997', None, {'hh': '14', 'mm': '43',
                                                'ss': '59.9999997',
                                                'tz': None}),
                      ('08:22:21',
                       (True, None, '12', '34', '-12:34', 'timezone'),
                       {'hh': '08', 'mm': '22', 'ss': '21',
                        'tz': (True, None, '12', '34', '-12:34', 'timezone')}))

        for testtuple in testtuples:
            mockBuilder = mock.Mock()

            mockBuilder.build_time.return_value = testtuple[2]

            result = _parse_second_time(testtuple[0], testtuple[1],
                                        mockBuilder)

            self.assertEqual(result, testtuple[2])
            mockBuilder.build_time.assert_called_once_with(**testtuple[2])

    def test_split_tz(self):
        self.assertEqual(_split_tz('01:23:45'), ('01:23:45', None))

        self.assertEqual(_split_tz('24:00:00'), ('24:00:00', None))

        self.assertEqual(_split_tz('23:21:28.512400'),
                         ('23:21:28.512400', None))

        self.assertEqual(_split_tz('01:23'), ('01:23', None))

        self.assertEqual(_split_tz('24:00'), ('24:00', None))

        self.assertEqual(_split_tz('01:23.4567'), ('01:23.4567', None))

        self.assertEqual(_split_tz('012345'), ('012345', None))

        self.assertEqual(_split_tz('240000'), ('240000', None))

        self.assertEqual(_split_tz('0123'), ('0123', None))

        self.assertEqual(_split_tz('2400'), ('2400', None))

        self.assertEqual(_split_tz('01'), ('01', None))

        self.assertEqual(_split_tz('24'), ('24', None))

        self.assertEqual(_split_tz('12.5'), ('12.5', None))

        self.assertEqual(_split_tz('232128.512400+00:00'),
                         ('232128.512400', '+00:00'))

        self.assertEqual(_split_tz('0123.4567+00:00'), ('0123.4567', '+00:00'))

        self.assertEqual(_split_tz('01.4567+00:00'), ('01.4567', '+00:00'))

        self.assertEqual(_split_tz('01:23:45+00:00'), ('01:23:45', '+00:00'))

        self.assertEqual(_split_tz('24:00:00+00:00'), ('24:00:00', '+00:00'))

        self.assertEqual(_split_tz('23:21:28.512400+00:00'),
                         ('23:21:28.512400', '+00:00'))

        self.assertEqual(_split_tz('01:23+00:00'), ('01:23', '+00:00'))

        self.assertEqual(_split_tz('24:00+00:00'), ('24:00', '+00:00'))

        self.assertEqual(_split_tz('01:23.4567+00:00'),
                         ('01:23.4567', '+00:00'))

        self.assertEqual(_split_tz('23:21:28.512400+11:15'),
                         ('23:21:28.512400', '+11:15'))

        self.assertEqual(_split_tz('23:21:28.512400-12:34'),
                         ('23:21:28.512400', '-12:34'))

        self.assertEqual(_split_tz('23:21:28.512400Z'),
                         ('23:21:28.512400', 'Z'))

        self.assertEqual(_split_tz('06:14:00.000123Z'),
                         ('06:14:00.000123', 'Z'))

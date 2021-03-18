# -*- coding: utf-8 -*-

# Copyright (c) 2021, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

import unittest
import aniso8601

from aniso8601.builders import BaseTimeBuilder, TupleBuilder
from aniso8601.exceptions import ISOFormatError
from aniso8601.tests.compat import mock

class TestBaseTimeBuilder(unittest.TestCase):
    def test_build_date(self):
        with self.assertRaises(NotImplementedError):
            BaseTimeBuilder.build_date()

    def test_build_time(self):
        with self.assertRaises(NotImplementedError):
            BaseTimeBuilder.build_time()

    def test_build_datetime(self):
        with self.assertRaises(NotImplementedError):
            BaseTimeBuilder.build_datetime(None, None)

    def test_build_duration(self):
        with self.assertRaises(NotImplementedError):
            BaseTimeBuilder.build_duration()

    def test_build_interval(self):
        with self.assertRaises(NotImplementedError):
            BaseTimeBuilder.build_interval()

    def test_build_repeating_interval(self):
        with self.assertRaises(NotImplementedError):
            BaseTimeBuilder.build_repeating_interval()

    def test_build_timezone(self):
        with self.assertRaises(NotImplementedError):
            BaseTimeBuilder.build_timezone()

    def test_cast(self):
        self.assertEqual(BaseTimeBuilder.cast('1', int), 1)
        self.assertEqual(BaseTimeBuilder.cast('-2', int), -2)
        self.assertEqual(BaseTimeBuilder.cast('3', float), float(3))
        self.assertEqual(BaseTimeBuilder.cast('-4', float), float(-4))
        self.assertEqual(BaseTimeBuilder.cast('5.6', float), 5.6)
        self.assertEqual(BaseTimeBuilder.cast('-7.8', float), -7.8)

    def test_cast_exception(self):
        with self.assertRaises(ISOFormatError):
            BaseTimeBuilder.cast('asdf', int)

        with self.assertRaises(ISOFormatError):
            BaseTimeBuilder.cast('asdf', float)

    def test_cast_caughtexception(self):
        def tester(value):
            raise RuntimeError

        with self.assertRaises(ISOFormatError):
            BaseTimeBuilder.cast('asdf', tester,
                                 caughtexceptions=(RuntimeError,))

    def test_cast_thrownexception(self):
        with self.assertRaises(RuntimeError):
            BaseTimeBuilder.cast('asdf', int,
                                 thrownexception=RuntimeError)

    def test_build_object(self):
        datetest = (('1', '2', '3', '4', '5', '6', 'date'),
                    {'YYYY': '1', 'MM': '2', 'DD': '3',
                     'Www': '4', 'D': '5', 'DDD': '6'})

        timetest = (('1', '2', '3',
                     (False, False, '4', '5', 'tz name', 'timezone'),
                     'time'),
                    {'hh': '1', 'mm': '2', 'ss': '3',
                     'tz': (False, False, '4', '5', 'tz name', 'timezone')})

        datetimetest = ((('1', '2', '3', '4', '5', '6', 'date'),
                         ('7', '8', '9',
                          (True, False, '10', '11', 'tz name', 'timezone'),
                          'time'),
                         'datetime'),
                        (('1', '2', '3', '4', '5', '6', 'date'),
                         ('7', '8', '9',
                          (True, False, '10', '11', 'tz name', 'timezone'),
                          'time')))

        durationtest = (('1', '2', '3', '4', '5', '6', '7', 'duration'),
                        {'PnY': '1', 'PnM': '2', 'PnW': '3', 'PnD': '4',
                         'TnH': '5', 'TnM': '6', 'TnS': '7'})

        intervaltests = (((('1', '2', '3', '4', '5', '6', 'date'),
                           ('7', '8', '9', '10', '11', '12', 'date'),
                           None, 'interval'),
                          {'start': ('1', '2', '3', '4', '5', '6', 'date'),
                           'end': ('7', '8', '9', '10', '11', '12', 'date'),
                           'duration': None}),
                         ((('1', '2', '3', '4', '5', '6', 'date'),
                           None,
                           ('7', '8', '9', '10', '11', '12', '13', 'duration'),
                           'interval'),
                          {'start': ('1', '2', '3', '4', '5', '6', 'date'),
                           'end': None,
                           'duration': ('7', '8', '9', '10', '11', '12', '13',
                                        'duration')}),
                         ((None,
                           ('1', '2', '3',
                            (True, False, '4', '5', 'tz name', 'timezone'),
                            'time'),
                           ('6', '7', '8', '9', '10', '11', '12', 'duration'),
                           'interval'),
                          {'start': None,
                           'end': ('1', '2', '3',
                                   (True, False, '4', '5', 'tz name',
                                    'timezone'),
                                   'time'),
                           'duration': ('6', '7', '8', '9', '10', '11', '12',
                                        'duration')}))

        repeatingintervaltests = (((True,
                                    None,
                                    (('1', '2', '3', '4', '5', '6', 'date'),
                                     ('7', '8', '9', '10', '11', '12', 'date'),
                                     None, 'interval'), 'repeatinginterval'),
                                   {'R': True,
                                    'Rnn': None,
                                    'interval': (('1', '2', '3',
                                                  '4', '5', '6', 'date'),
                                                 ('7', '8', '9',
                                                  '10', '11', '12', 'date'),
                                                 None, 'interval')}),
                                  ((False,
                                    '1',
                                    ((('2', '3', '4', '5', '6', '7', 'date'),
                                      ('8', '9', '10', None, 'time'),
                                      'datetime'),
                                     (('11', '12', '13', '14', '15', '16',
                                       'date'),
                                      ('17', '18', '19', None, 'time'),
                                      'datetime'),
                                     None, 'interval'), 'repeatinginterval'),
                                   {'R':False,
                                    'Rnn': '1',
                                    'interval': ((('2', '3', '4',
                                                   '5', '6', '7', 'date'),
                                                  ('8', '9', '10', None,
                                                   'time'), 'datetime'),
                                                 (('11', '12', '13',
                                                   '14', '15', '16', 'date'),
                                                  ('17', '18', '19', None,
                                                   'time'), 'datetime'),
                                                 None, 'interval')}))

        timezonetest = ((False, False, '1', '2', '+01:02', 'timezone'),
                        {'negative': False, 'Z': False,
                         'hh': '1', 'mm': '2', 'name': '+01:02'})

        with mock.patch.object(aniso8601.builders.BaseTimeBuilder,
                               'build_date') as mock_build:
            mock_build.return_value = datetest[0]

            result = BaseTimeBuilder._build_object(datetest[0])

            self.assertEqual(result, datetest[0])
            mock_build.assert_called_once_with(**datetest[1])

        with mock.patch.object(aniso8601.builders.BaseTimeBuilder,
                               'build_time') as mock_build:
            mock_build.return_value = timetest[0]

            result = BaseTimeBuilder._build_object(timetest[0])

            self.assertEqual(result, timetest[0])
            mock_build.assert_called_once_with(**timetest[1])

        with mock.patch.object(aniso8601.builders.BaseTimeBuilder,
                               'build_datetime') as mock_build:
            mock_build.return_value = datetimetest[0]

            result = BaseTimeBuilder._build_object(datetimetest[0])

            self.assertEqual(result, datetimetest[0])
            mock_build.assert_called_once_with(*datetimetest[1])

        with mock.patch.object(aniso8601.builders.BaseTimeBuilder,
                               'build_duration') as mock_build:
            mock_build.return_value = durationtest[0]

            result = BaseTimeBuilder._build_object(durationtest[0])

            self.assertEqual(result, durationtest[0])
            mock_build.assert_called_once_with(**durationtest[1])

        for intervaltest in intervaltests:
            with mock.patch.object(aniso8601.builders.BaseTimeBuilder,
                                   'build_interval') as mock_build:
                mock_build.return_value = intervaltest[0]

                result = BaseTimeBuilder._build_object(intervaltest[0])

                self.assertEqual(result, intervaltest[0])
                mock_build.assert_called_once_with(**intervaltest[1])

        for repeatingintervaltest in repeatingintervaltests:
            with mock.patch.object(aniso8601.builders.BaseTimeBuilder,
                                   'build_repeating_interval') as mock_build:
                mock_build.return_value = repeatingintervaltest[0]

                result = BaseTimeBuilder._build_object(repeatingintervaltest[0])

                self.assertEqual(result, repeatingintervaltest[0])
                mock_build.assert_called_once_with(**repeatingintervaltest[1])

        with mock.patch.object(aniso8601.builders.BaseTimeBuilder,
                               'build_timezone') as mock_build:
            mock_build.return_value = timezonetest[0]

            result = BaseTimeBuilder._build_object(timezonetest[0])

            self.assertEqual(result, timezonetest[0])
            mock_build.assert_called_once_with(**timezonetest[1])

class TestTupleBuilder(unittest.TestCase):
    def test_build_date(self):
        datetuple = TupleBuilder.build_date()

        self.assertEqual(datetuple, (None, None, None,
                                     None, None, None,
                                     'date'))

        datetuple = TupleBuilder.build_date(YYYY='1', MM='2', DD='3',
                                            Www='4', D='5', DDD='6')

        self.assertEqual(datetuple, ('1', '2', '3',
                                     '4', '5', '6',
                                     'date'))

    def test_build_time(self):
        testtuples = (({}, (None, None, None, None, 'time')),
                      ({'hh': '1', 'mm': '2', 'ss': '3', 'tz': None},
                       ('1', '2', '3', None, 'time')),
                      ({'hh': '1', 'mm': '2', 'ss': '3', 'tz': (False, False,
                                                                '4', '5',
                                                                'tz name',
                                                                'timezone')},
                       ('1', '2', '3', (False, False, '4', '5',
                                        'tz name', 'timezone'),
                        'time')))

        for testtuple in testtuples:
            self.assertEqual(TupleBuilder.build_time(**testtuple[0]),
                             testtuple[1])

    def test_build_datetime(self):
        testtuples = (({'date': ('1', '2', '3', '4', '5', '6', 'date'),
                        'time': ('7', '8', '9', None, 'time')},
                       (('1', '2', '3', '4', '5', '6', 'date'),
                        ('7', '8', '9', None, 'time'),
                        'datetime')),
                      ({'date': ('1', '2', '3', '4', '5', '6', 'date'),
                        'time': ('7', '8', '9',
                                 (True, False, '10', '11', 'tz name',
                                  'timezone'),
                                 'time')},
                       (('1', '2', '3', '4', '5', '6', 'date'),
                        ('7', '8', '9',
                         (True, False, '10', '11', 'tz name',
                          'timezone'),
                         'time'), 'datetime')))

        for testtuple in testtuples:
            self.assertEqual(TupleBuilder.build_datetime(**testtuple[0]),
                             testtuple[1])

    def test_build_duration(self):
        testtuples = (({}, (None, None, None, None, None, None, None,
                            'duration')),
                      ({'PnY': '1', 'PnM': '2', 'PnW': '3', 'PnD': '4',
                        'TnH': '5', 'TnM': '6', 'TnS': '7'},
                       ('1', '2', '3', '4',
                        '5', '6', '7',
                        'duration')))

        for testtuple in testtuples:
            self.assertEqual(TupleBuilder.build_duration(**testtuple[0]),
                             testtuple[1])

    def test_build_interval(self):
        testtuples = (({}, (None, None, None, 'interval')),
                      ({'start': ('1', '2', '3', '4', '5', '6', 'date'),
                        'end': ('7', '8', '9', '10', '11', '12', 'date')},
                       (('1', '2', '3', '4', '5', '6', 'date'),
                        ('7', '8', '9', '10', '11', '12', 'date'),
                        None, 'interval')),
                      ({'start': ('1', '2', '3',
                                  (True, False, '7', '8', 'tz name',
                                   'timezone'),
                                  'time'),
                        'end': ('4', '5', '6',
                                (False, False, '9', '10', 'tz name',
                                 'timezone'),
                                'time')},
                       (('1', '2', '3',
                         (True, False, '7', '8', 'tz name',
                          'timezone'),
                         'time'),
                        ('4', '5', '6',
                         (False, False, '9', '10', 'tz name',
                          'timezone'),
                         'time'),
                        None, 'interval')),
                      ({'start': (('1', '2', '3', '4', '5', '6', 'date'),
                                  ('7', '8', '9',
                                   (True, False, '10', '11', 'tz name',
                                    'timezone'),
                                   'time'),
                                  'datetime'),
                        'end': (('12', '13', '14', '15', '16', '17', 'date'),
                                ('18', '19', '20',
                                 (False, False, '21', '22', 'tz name',
                                  'timezone'),
                                 'time'),
                                'datetime')},
                       ((('1', '2', '3', '4', '5', '6', 'date'),
                         ('7', '8', '9',
                          (True, False, '10', '11', 'tz name',
                           'timezone'),
                          'time'),
                         'datetime'),
                        (('12', '13', '14', '15', '16', '17', 'date'),
                         ('18', '19', '20',
                          (False, False, '21', '22', 'tz name',
                           'timezone'),
                          'time'),
                         'datetime'),
                        None, 'interval')),
                      ({'start': ('1', '2', '3', '4', '5', '6', 'date'),
                        'end': None,
                        'duration': ('7', '8', '9', '10', '11', '12', '13',
                                     'duration')},
                       (('1', '2', '3', '4', '5', '6', 'date'),
                        None,
                        ('7', '8', '9', '10', '11', '12', '13',
                         'duration'),
                        'interval')),
                      ({'start': None,
                        'end': ('1', '2', '3',
                                (True, False, '4', '5', 'tz name',
                                 'timezone'),
                                'time'),
                        'duration': ('6', '7', '8', '9', '10', '11', '12',
                                     'duration')},
                       (None,
                        ('1', '2', '3',
                         (True, False, '4', '5', 'tz name',
                          'timezone'),
                         'time'),
                        ('6', '7', '8', '9', '10', '11', '12',
                         'duration'),
                        'interval')))

        for testtuple in testtuples:
            self.assertEqual(TupleBuilder.build_interval(**testtuple[0]),
                             testtuple[1])

    def test_build_repeating_interval(self):
        testtuples = (({}, (None, None, None, 'repeatinginterval')),
                      ({'R': True,
                        'interval':(('1', '2', '3', '4', '5', '6', 'date'),
                                    ('7', '8', '9', '10', '11', '12', 'date'),
                                    None, 'interval')},
                       (True, None, (('1', '2', '3', '4', '5', '6', 'date'),
                                     ('7', '8', '9', '10', '11', '12', 'date'),
                                     None, 'interval'),
                        'repeatinginterval')),
                      ({'R':False, 'Rnn': '1',
                        'interval': ((('2', '3', '4', '5', '6', '7',
                                       'date'),
                                      ('8', '9', '10', None, 'time'),
                                      'datetime'),
                                     (('11', '12', '13', '14', '15', '16',
                                       'date'),
                                      ('17', '18', '19', None, 'time'),
                                      'datetime'),
                                     None, 'interval')},
                       (False, '1',
                        ((('2', '3', '4', '5', '6', '7',
                           'date'),
                          ('8', '9', '10', None, 'time'),
                          'datetime'),
                         (('11', '12', '13', '14', '15', '16',
                           'date'),
                          ('17', '18', '19', None, 'time'),
                          'datetime'),
                         None, 'interval'),
                        'repeatinginterval')))

        for testtuple in testtuples:
            result = TupleBuilder.build_repeating_interval(**testtuple[0])
            self.assertEqual(result, testtuple[1])

    def test_build_timezone(self):
        testtuples = (({}, (None, None, None, None, '', 'timezone')),
                      ({'negative': False, 'Z': True, 'name': 'UTC'},
                       (False, True, None, None, 'UTC', 'timezone')),
                      ({'negative': False, 'Z': False, 'hh': '1', 'mm': '2',
                        'name': '+01:02'},
                       (False, False, '1', '2', '+01:02', 'timezone')),
                      ({'negative': True, 'Z': False, 'hh': '1', 'mm': '2',
                        'name': '-01:02'},
                       (True, False, '1', '2', '-01:02', 'timezone')))

        for testtuple in testtuples:
            result = TupleBuilder.build_timezone(**testtuple[0])
            self.assertEqual(result, testtuple[1])

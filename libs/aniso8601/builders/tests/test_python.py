# -*- coding: utf-8 -*-

# Copyright (c) 2021, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

import datetime
import unittest

from aniso8601 import compat
from aniso8601.exceptions import (DayOutOfBoundsError, HoursOutOfBoundsError,
                                  ISOFormatError, LeapSecondError,
                                  MidnightBoundsError, MinutesOutOfBoundsError,
                                  SecondsOutOfBoundsError,
                                  WeekOutOfBoundsError, YearOutOfBoundsError)
from aniso8601.builders.python import PythonTimeBuilder
from aniso8601.utcoffset import UTCOffset

class TestPythonTimeBuilder(unittest.TestCase):
    def test_build_date(self):
        testtuples = (({'YYYY': '2013', 'MM': None, 'DD': None, 'Www': None,
                        'D': None, 'DDD': None},
                       datetime.date(2013, 1, 1)),
                      ({'YYYY': '0001', 'MM': None, 'DD': None, 'Www': None,
                        'D': None, 'DDD': None},
                       datetime.date(1, 1, 1)),
                      ({'YYYY': '1900', 'MM': None, 'DD': None, 'Www': None,
                        'D': None, 'DDD': None},
                       datetime.date(1900, 1, 1)),
                      ({'YYYY': '1981', 'MM': '04', 'DD': '05', 'Www': None,
                        'D': None, 'DDD': None},
                       datetime.date(1981, 4, 5)),
                      ({'YYYY': '1981', 'MM': '04', 'DD': None, 'Www': None,
                        'D': None, 'DDD': None},
                       datetime.date(1981, 4, 1)),
                      ({'YYYY': '1981', 'MM': None, 'DD': None, 'Www': None,
                        'D': None, 'DDD': '095'},
                       datetime.date(1981, 4, 5)),
                      ({'YYYY': '1981', 'MM': None, 'DD': None, 'Www': None,
                        'D': None, 'DDD': '365'},
                       datetime.date(1981, 12, 31)),
                      ({'YYYY': '1980', 'MM': None, 'DD': None, 'Www': None,
                        'D': None, 'DDD': '366'},
                       datetime.date(1980, 12, 31)),
                      #Make sure we shift in zeros
                      ({'YYYY': '1', 'MM': None, 'DD': None, 'Www': None,
                        'D': None, 'DDD': None},
                       datetime.date(1000, 1, 1)),
                      ({'YYYY': '12', 'MM': None, 'DD': None, 'Www': None,
                        'D': None, 'DDD': None},
                       datetime.date(1200, 1, 1)),
                      ({'YYYY': '123', 'MM': None, 'DD': None, 'Www': None,
                        'D': None, 'DDD': None},
                       datetime.date(1230, 1, 1)))

        for testtuple in testtuples:
            result = PythonTimeBuilder.build_date(**testtuple[0])
            self.assertEqual(result, testtuple[1])

        #Test weekday
        testtuples = (({'YYYY': '2004', 'MM': None, 'DD': None, 'Www': '53',
                        'D': None, 'DDD': None},
                       datetime.date(2004, 12, 27), 0),
                      ({'YYYY': '2009', 'MM': None, 'DD': None, 'Www': '01',
                        'D': None, 'DDD': None},
                       datetime.date(2008, 12, 29), 0),
                      ({'YYYY': '2010', 'MM': None, 'DD': None, 'Www': '01',
                        'D': None, 'DDD': None},
                       datetime.date(2010, 1, 4), 0),
                      ({'YYYY': '2009', 'MM': None, 'DD': None, 'Www': '53',
                        'D': None, 'DDD': None},
                       datetime.date(2009, 12, 28), 0),
                      ({'YYYY': '2009', 'MM': None, 'DD': None, 'Www': '01',
                        'D': '1', 'DDD': None},
                       datetime.date(2008, 12, 29), 0),
                      ({'YYYY': '2009', 'MM': None, 'DD': None, 'Www': '53',
                        'D': '7', 'DDD': None},
                       datetime.date(2010, 1, 3), 6),
                      ({'YYYY': '2010', 'MM': None, 'DD': None, 'Www': '01',
                        'D': '1', 'DDD': None},
                       datetime.date(2010, 1, 4), 0),
                      ({'YYYY': '2004', 'MM': None, 'DD': None, 'Www': '53',
                        'D': '6', 'DDD': None},
                       datetime.date(2005, 1, 1), 5))

        for testtuple in testtuples:
            result = PythonTimeBuilder.build_date(**testtuple[0])
            self.assertEqual(result, testtuple[1])
            self.assertEqual(result.weekday(), testtuple[2])

    def test_build_date_bounds_checking(self):
        #0 isn't a valid week number
        with self.assertRaises(WeekOutOfBoundsError):
            PythonTimeBuilder.build_date(YYYY='2003', Www='00')

        #Week must not be larger than 53
        with self.assertRaises(WeekOutOfBoundsError):
            PythonTimeBuilder.build_date(YYYY='2004', Www='54')

        #0 isn't a valid day number
        with self.assertRaises(DayOutOfBoundsError):
            PythonTimeBuilder.build_date(YYYY='2001', Www='02', D='0')

        #Day must not be larger than 7
        with self.assertRaises(DayOutOfBoundsError):
            PythonTimeBuilder.build_date(YYYY='2001', Www='02', D='8')

        #0 isn't a valid year for a Python builder
        with self.assertRaises(YearOutOfBoundsError):
            PythonTimeBuilder.build_date(YYYY='0000')

        with self.assertRaises(DayOutOfBoundsError):
            PythonTimeBuilder.build_date(YYYY='1981', DDD='000')

        #Day 366 is only valid on a leap year
        with self.assertRaises(DayOutOfBoundsError):
            PythonTimeBuilder.build_date(YYYY='1981', DDD='366')

        #Day must me 365, or 366, not larger
        with self.assertRaises(DayOutOfBoundsError):
            PythonTimeBuilder.build_date(YYYY='1981', DDD='367')

    def test_build_time(self):
        testtuples = (({}, datetime.time()),
                      ({'hh': '12.5'},
                       datetime.time(hour=12, minute=30)),
                      ({'hh': '23.99999999997'},
                       datetime.time(hour=23, minute=59, second=59,
                                     microsecond=999999)),
                      ({'hh': '1', 'mm': '23'},
                       datetime.time(hour=1, minute=23)),
                      ({'hh': '1', 'mm': '23.4567'},
                       datetime.time(hour=1, minute=23, second=27,
                                     microsecond=402000)),
                      ({'hh': '14', 'mm': '43.999999997'},
                       datetime.time(hour=14, minute=43, second=59,
                                     microsecond=999999)),
                      ({'hh': '1', 'mm': '23', 'ss': '45'},
                       datetime.time(hour=1, minute=23, second=45)),
                      ({'hh': '23', 'mm': '21', 'ss': '28.512400'},
                       datetime.time(hour=23, minute=21, second=28,
                                     microsecond=512400)),
                      ({'hh': '01', 'mm': '03', 'ss': '11.858714'},
                       datetime.time(hour=1, minute=3, second=11,
                                     microsecond=858714)),
                      ({'hh': '14', 'mm': '43', 'ss': '59.9999997'},
                       datetime.time(hour=14, minute=43, second=59,
                                     microsecond=999999)),
                      ({'hh': '24'}, datetime.time(hour=0)),
                      ({'hh': '24', 'mm': '00'}, datetime.time(hour=0)),
                      ({'hh': '24', 'mm': '00', 'ss': '00'},
                       datetime.time(hour=0)),
                      ({'tz': (False, None, '00', '00', 'UTC', 'timezone')},
                       datetime.time(tzinfo=UTCOffset(name='UTC', minutes=0))),
                      ({'hh': '23', 'mm': '21', 'ss': '28.512400',
                        'tz': (False, None, '00', '00', '+00:00', 'timezone')},
                       datetime.time(hour=23, minute=21, second=28,
                                     microsecond=512400,
                                     tzinfo=UTCOffset(name='+00:00',
                                                      minutes=0))),
                      ({'hh': '1', 'mm': '23',
                        'tz': (False, None, '01', '00', '+1', 'timezone')},
                       datetime.time(hour=1, minute=23,
                                     tzinfo=UTCOffset(name='+1',
                                                      minutes=60))),
                      ({'hh': '1', 'mm': '23.4567',
                        'tz': (True, None, '01', '00', '-1', 'timezone')},
                       datetime.time(hour=1, minute=23, second=27,
                                     microsecond=402000,
                                     tzinfo=UTCOffset(name='-1',
                                                      minutes=-60))),
                      ({'hh': '23', 'mm': '21', 'ss': '28.512400',
                        'tz': (False, None, '01', '30', '+1:30', 'timezone')},
                       datetime.time(hour=23, minute=21, second=28,
                                     microsecond=512400,
                                     tzinfo=UTCOffset(name='+1:30',
                                                      minutes=90))),
                      ({'hh': '23', 'mm': '21', 'ss': '28.512400',
                        'tz': (False, None, '11', '15', '+11:15', 'timezone')},
                       datetime.time(hour=23, minute=21, second=28,
                                     microsecond=512400,
                                     tzinfo=UTCOffset(name='+11:15',
                                                      minutes=675))),
                      ({'hh': '23', 'mm': '21', 'ss': '28.512400',
                        'tz': (False, None, '12', '34', '+12:34', 'timezone')},
                       datetime.time(hour=23, minute=21, second=28,
                                     microsecond=512400,
                                     tzinfo=UTCOffset(name='+12:34',
                                                      minutes=754))),
                      ({'hh': '23', 'mm': '21', 'ss': '28.512400',
                        'tz': (False, None, '00', '00', 'UTC', 'timezone')},
                       datetime.time(hour=23, minute=21, second=28,
                                     microsecond=512400,
                                     tzinfo=UTCOffset(name='UTC',
                                                      minutes=0))),
                      #Make sure we truncate, not round
                      #https://bitbucket.org/nielsenb/aniso8601/issues/10/sub-microsecond-precision-in-durations-is
                      #https://bitbucket.org/nielsenb/aniso8601/issues/21/sub-microsecond-precision-is-lost-when
                      ({'hh': '14.9999999999999999'},
                       datetime.time(hour=14, minute=59, second=59,
                                     microsecond=999999)),
                      ({'mm': '0.00000000999'},
                       datetime.time()),
                      ({'mm': '0.0000000999'},
                       datetime.time(microsecond=5)),
                      ({'ss': '0.0000001'},
                       datetime.time()),
                      ({'ss': '2.0000048'},
                       datetime.time(second=2,
                                     microsecond=4)))

        for testtuple in testtuples:
            result = PythonTimeBuilder.build_time(**testtuple[0])
            self.assertEqual(result, testtuple[1])

    def test_build_time_bounds_checking(self):
        #Leap seconds not supported
        #https://bitbucket.org/nielsenb/aniso8601/issues/10/sub-microsecond-precision-in-durations-is
        #https://bitbucket.org/nielsenb/aniso8601/issues/13/parsing-of-leap-second-gives-wildly
        with self.assertRaises(LeapSecondError):
            PythonTimeBuilder.build_time(hh='23', mm='59', ss='60')

        with self.assertRaises(LeapSecondError):
            PythonTimeBuilder.build_time(hh='23', mm='59', ss='60',
                                         tz=UTCOffset(name='UTC', minutes=0))

        with self.assertRaises(SecondsOutOfBoundsError):
            PythonTimeBuilder.build_time(hh='00', mm='00', ss='60')

        with self.assertRaises(SecondsOutOfBoundsError):
            PythonTimeBuilder.build_time(hh='00', mm='00', ss='60',
                                         tz=UTCOffset(name='UTC', minutes=0))

        with self.assertRaises(SecondsOutOfBoundsError):
            PythonTimeBuilder.build_time(hh='00', mm='00', ss='61')

        with self.assertRaises(SecondsOutOfBoundsError):
            PythonTimeBuilder.build_time(hh='00', mm='00', ss='61',
                                         tz=UTCOffset(name='UTC', minutes=0))

        with self.assertRaises(MinutesOutOfBoundsError):
            PythonTimeBuilder.build_time(hh='00', mm='61')

        with self.assertRaises(MinutesOutOfBoundsError):
            PythonTimeBuilder.build_time(hh='00', mm='61',
                                         tz=UTCOffset(name='UTC', minutes=0))

        with self.assertRaises(MinutesOutOfBoundsError):
            PythonTimeBuilder.build_time(hh='00', mm='60')

        with self.assertRaises(MinutesOutOfBoundsError):
            PythonTimeBuilder.build_time(hh='00', mm='60.1')

        with self.assertRaises(HoursOutOfBoundsError):
            PythonTimeBuilder.build_time(hh='25')

        #Hour 24 can only represent midnight
        with self.assertRaises(MidnightBoundsError):
            PythonTimeBuilder.build_time(hh='24', mm='00', ss='01')

        with self.assertRaises(MidnightBoundsError):
            PythonTimeBuilder.build_time(hh='24', mm='00.1')

        with self.assertRaises(MidnightBoundsError):
            PythonTimeBuilder.build_time(hh='24', mm='01')

        with self.assertRaises(MidnightBoundsError):
            PythonTimeBuilder.build_time(hh='24.1')

    def test_build_datetime(self):
        testtuples = (((('2019', '06', '05', None, None, None, 'date'),
                        ('01', '03', '11.858714', None, 'time')),
                       datetime.datetime(2019, 6, 5, hour=1, minute=3,
                                         second=11, microsecond=858714)),
                      ((('1234', '02', '03', None, None, None, 'date'),
                        ('23', '21', '28.512400', None, 'time')),
                       datetime.datetime(1234, 2, 3, hour=23, minute=21,
                                         second=28, microsecond=512400)),
                      ((('1981', '04', '05', None, None, None, 'date'),
                        ('23', '21', '28.512400',
                         (False, None, '11', '15', '+11:15', 'timezone'),
                         'time')),
                       datetime.datetime(1981, 4, 5, hour=23, minute=21,
                                         second=28, microsecond=512400,
                                         tzinfo=UTCOffset(name='+11:15',
                                                          minutes=675))))

        for testtuple in testtuples:
            result = PythonTimeBuilder.build_datetime(*testtuple[0])
            self.assertEqual(result, testtuple[1])

    def test_build_datetime_bounds_checking(self):
        #Leap seconds not supported
        #https://bitbucket.org/nielsenb/aniso8601/issues/10/sub-microsecond-precision-in-durations-is
        #https://bitbucket.org/nielsenb/aniso8601/issues/13/parsing-of-leap-second-gives-wildly
        with self.assertRaises(LeapSecondError):
            PythonTimeBuilder.build_datetime(('2016', '12', '31',
                                              None, None, None, 'date'),
                                             ('23', '59', '60', None, 'time'))

        with self.assertRaises(LeapSecondError):
            PythonTimeBuilder.build_datetime(('2016', '12', '31',
                                              None, None, None, 'date'),
                                             ('23', '59', '60',
                                              (False, None, '00', '00',
                                               '+00:00', 'timezone'), 'time'))

        with self.assertRaises(SecondsOutOfBoundsError):
            PythonTimeBuilder.build_datetime(('1981', '04', '05',
                                              None, None, None, 'date'),
                                             ('00', '00', '60', None, 'time'))

        with self.assertRaises(SecondsOutOfBoundsError):
            PythonTimeBuilder.build_datetime(('1981', '04', '05',
                                              None, None, None, 'date'),
                                             ('00', '00', '60',
                                              (False, None, '00', '00',
                                               '+00:00', 'timezone'), 'time'))

        with self.assertRaises(SecondsOutOfBoundsError):
            PythonTimeBuilder.build_datetime(('1981', '04', '05',
                                              None, None, None, 'date'),
                                             ('00', '00', '61', None, 'time'))

        with self.assertRaises(SecondsOutOfBoundsError):
            PythonTimeBuilder.build_datetime(('1981', '04', '05',
                                              None, None, None, 'date'),
                                             ('00', '00', '61',
                                              (False, None, '00', '00',
                                               '+00:00', 'timezone'), 'time'))

        with self.assertRaises(SecondsOutOfBoundsError):
            PythonTimeBuilder.build_datetime(('1981', '04', '05',
                                              None, None, None, 'date'),
                                             ('00', '59', '61', None, 'time'))

        with self.assertRaises(SecondsOutOfBoundsError):
            PythonTimeBuilder.build_datetime(('1981', '04', '05',
                                              None, None, None, 'date'),
                                             ('00', '59', '61',
                                              (False, None, '00', '00',
                                               '+00:00', 'timezone'), 'time'))

        with self.assertRaises(MinutesOutOfBoundsError):
            PythonTimeBuilder.build_datetime(('1981', '04', '05',
                                              None, None, None, 'date'),
                                             ('00', '61', None, None, 'time'))

        with self.assertRaises(MinutesOutOfBoundsError):
            PythonTimeBuilder.build_datetime(('1981', '04', '05',
                                              None, None, None, 'date'),
                                             ('00', '61', None,
                                              (False, None, '00', '00',
                                               '+00:00', 'timezone'), 'time'))

    def test_build_duration(self):
        testtuples = (({'PnY': '1', 'PnM': '2', 'PnD': '3',
                        'TnH': '4', 'TnM': '54', 'TnS': '6'},
                       datetime.timedelta(days=428, hours=4,
                                          minutes=54, seconds=6)),
                      ({'PnY': '1', 'PnM': '2', 'PnD': '3',
                        'TnH': '4', 'TnM': '54', 'TnS': '6.5'},
                       datetime.timedelta(days=428, hours=4,
                                          minutes=54, seconds=6.5)),
                      ({'PnY': '1', 'PnM': '2', 'PnD': '3'},
                       datetime.timedelta(days=428)),
                      ({'PnY': '1', 'PnM': '2', 'PnD': '3.5'},
                       datetime.timedelta(days=428.5)),
                      ({'TnH': '4', 'TnM': '54', 'TnS': '6.5'},
                       datetime.timedelta(hours=4, minutes=54, seconds=6.5)),
                      ({'TnH': '1', 'TnM': '3', 'TnS': '11.858714'},
                       datetime.timedelta(hours=1, minutes=3,
                                          seconds=11, microseconds=858714)),
                      ({'TnH': '4', 'TnM': '54', 'TnS': '28.512400'},
                       datetime.timedelta(hours=4, minutes=54,
                                          seconds=28, microseconds=512400)),
                      #Make sure we truncate, not round
                      #https://bitbucket.org/nielsenb/aniso8601/issues/10/sub-microsecond-precision-in-durations-is
                      #https://bitbucket.org/nielsenb/aniso8601/issues/21/sub-microsecond-precision-is-lost-when
                      ({'PnY': '1999.9999999999999999'},
                       datetime.timedelta(days=729999, seconds=86399,
                                          microseconds=999999)),
                      ({'PnM': '1.9999999999999999'},
                       datetime.timedelta(days=59, hours=23,
                                          minutes=59, seconds=59,
                                          microseconds=999999)),
                      ({'PnW': '1.9999999999999999'},
                       datetime.timedelta(days=13, hours=23,
                                          minutes=59, seconds=59,
                                          microseconds=999999)),
                      ({'PnD': '1.9999999999999999'},
                       datetime.timedelta(days=1, hours=23,
                                          minutes=59, seconds=59,
                                          microseconds=999999)),
                      ({'TnH': '14.9999999999999999'},
                       datetime.timedelta(hours=14, minutes=59,
                                          seconds=59, microseconds=999999)),
                      ({'TnM': '0.00000000999'}, datetime.timedelta(0)),
                      ({'TnM': '0.0000000999'},
                       datetime.timedelta(microseconds=5)),
                      ({'TnS': '0.0000001'}, datetime.timedelta(0)),
                      ({'TnS': '2.0000048'},
                       datetime.timedelta(seconds=2, microseconds=4)),
                      ({'PnY': '1'}, datetime.timedelta(days=365)),
                      ({'PnY': '1.5'}, datetime.timedelta(days=547.5)),
                      ({'PnM': '1'}, datetime.timedelta(days=30)),
                      ({'PnM': '1.5'}, datetime.timedelta(days=45)),
                      ({'PnW': '1'}, datetime.timedelta(days=7)),
                      ({'PnW': '1.5'}, datetime.timedelta(days=10.5)),
                      ({'PnD': '1'}, datetime.timedelta(days=1)),
                      ({'PnD': '1.5'}, datetime.timedelta(days=1.5)),
                      ({'PnY': '0003', 'PnM': '06', 'PnD': '04',
                        'TnH': '12', 'TnM': '30', 'TnS': '05'},
                       datetime.timedelta(days=1279, hours=12,
                                          minutes=30, seconds=5)),
                      ({'PnY': '0003', 'PnM': '06', 'PnD': '04',
                        'TnH': '12', 'TnM': '30', 'TnS': '05.5'},
                       datetime.timedelta(days=1279, hours=12,
                                          minutes=30, seconds=5.5)),
                      #Make sure we truncate, not round
                      #https://bitbucket.org/nielsenb/aniso8601/issues/10/sub-microsecond-precision-in-durations-is
                      ({'PnY': '0001', 'PnM': '02', 'PnD': '03',
                        'TnH': '14', 'TnM': '43', 'TnS': '59.9999997'},
                       datetime.timedelta(days=428, hours=14,
                                          minutes=43, seconds=59,
                                          microseconds=999999)),
                      #Verify overflows
                      ({'TnH': '36'}, datetime.timedelta(days=1, hours=12)))

        for testtuple in testtuples:
            result = PythonTimeBuilder.build_duration(**testtuple[0])
            self.assertEqual(result, testtuple[1])

    def test_build_interval(self):
        testtuples = (({'end': (('1981', '04', '05', None, None, None, 'date'),
                                ('01', '01', '00', None, 'time'), 'datetime'),
                        'duration': (None, '1', None, None, None, None, None,
                                     'duration')},
                       datetime.datetime(year=1981, month=4, day=5,
                                         hour=1, minute=1),
                       datetime.datetime(year=1981, month=3, day=6,
                                         hour=1, minute=1)),
                      ({'end': ('1981', '04', '05', None, None, None, 'date'),
                        'duration': (None, '1', None, None, None, None, None,
                                     'duration')},
                       datetime.date(year=1981, month=4, day=5),
                       datetime.date(year=1981, month=3, day=6)),
                      ({'end': ('2018', '03', '06', None, None, None, 'date'),
                        'duration': ('1.5', None, None, None, None, None, None,
                                     'duration')},
                       datetime.date(year=2018, month=3, day=6),
                       datetime.datetime(year=2016, month=9, day=4,
                                         hour=12)),
                      ({'end': ('2014', '11', '12', None, None, None, 'date'),
                        'duration': (None, None, None, None, '1', None, None,
                                     'duration')},
                       datetime.date(year=2014, month=11, day=12),
                       datetime.datetime(year=2014, month=11, day=11,
                                         hour=23)),
                      ({'end': ('2014', '11', '12', None, None, None, 'date'),
                        'duration': (None, None, None, None, '4', '54', '6.5',
                                     'duration')},
                       datetime.date(year=2014, month=11, day=12),
                       datetime.datetime(year=2014, month=11, day=11,
                                         hour=19, minute=5, second=53,
                                         microsecond=500000)),
                      ({'end': (('2050', '03', '01',
                                 None, None, None, 'date'),
                                ('13', '00', '00',
                                 (False, True, None, None,
                                  'Z', 'timezone'), 'time'), 'datetime'),
                        'duration': (None, None, None,
                                     None, '10', None, None, 'duration')},
                       datetime.datetime(year=2050, month=3, day=1,
                                         hour=13,
                                         tzinfo=UTCOffset(name='UTC',
                                                          minutes=0)),
                       datetime.datetime(year=2050, month=3, day=1,
                                         hour=3,
                                         tzinfo=UTCOffset(name='UTC',
                                                          minutes=0))),
                      #Make sure we truncate, not round
                      #https://bitbucket.org/nielsenb/aniso8601/issues/10/sub-microsecond-precision-in-durations-is
                      #https://bitbucket.org/nielsenb/aniso8601/issues/21/sub-microsecond-precision-is-lost-when
                      ({'end': ('2000', '01', '01',
                                None, None, None, 'date'),
                        'duration': ('1999.9999999999999999', None, None,
                                     None, None, None,
                                     None, 'duration')},
                       datetime.date(year=2000, month=1, day=1),
                       datetime.datetime(year=1, month=4, day=30,
                                         hour=0, minute=0, second=0,
                                         microsecond=1)),
                      ({'end': ('1989', '03', '01',
                                None, None, None, 'date'),
                        'duration': (None, '1.9999999999999999', None,
                                     None, None, None,
                                     None, 'duration')},
                       datetime.date(year=1989, month=3, day=1),
                       datetime.datetime(year=1988, month=12, day=31,
                                         hour=0, minute=0, second=0,
                                         microsecond=1)),
                      ({'end': ('1989', '03', '01',
                                None, None, None, 'date'),
                        'duration': (None, None, '1.9999999999999999',
                                     None, None, None,
                                     None, 'duration')},
                       datetime.date(year=1989, month=3, day=1),
                       datetime.datetime(year=1989, month=2, day=15,
                                         hour=0, minute=0, second=0,
                                         microsecond=1)),
                      ({'end': ('1989', '03', '01',
                                None, None, None, 'date'),
                        'duration': (None, None, None,
                                     '1.9999999999999999', None, None,
                                     None, 'duration')},
                       datetime.date(year=1989, month=3, day=1),
                       datetime.datetime(year=1989, month=2, day=27,
                                         hour=0, minute=0, second=0,
                                         microsecond=1)),
                      ({'end': ('2001', '01', '01',
                                None, None, None, 'date'),
                        'duration': (None, None, None,
                                     None, '14.9999999999999999', None,
                                     None, 'duration')},
                       datetime.date(year=2001, month=1, day=1),
                       datetime.datetime(year=2000, month=12, day=31,
                                         hour=9, minute=0, second=0,
                                         microsecond=1)),
                      ({'end': ('2001', '01', '01',
                                None, None, None, 'date'),
                        'duration': (None, None, None,
                                     None, None, '0.00000000999',
                                     None, 'duration')},
                       datetime.date(year=2001, month=1, day=1),
                       datetime.datetime(year=2001, month=1, day=1)),
                      ({'end': ('2001', '01', '01',
                                None, None, None, 'date'),
                        'duration': (None, None, None,
                                     None, None, '0.0000000999',
                                     None, 'duration')},
                       datetime.date(year=2001, month=1, day=1),
                       datetime.datetime(year=2000, month=12, day=31,
                                         hour=23, minute=59, second=59,
                                         microsecond=999995)),
                      ({'end': ('2018', '03', '06', None, None, None, 'date'),
                        'duration': (None, None, None,
                                     None, None, None,
                                     '0.0000001', 'duration')},
                       datetime.date(year=2018, month=3, day=6),
                       datetime.datetime(year=2018, month=3, day=6)),
                      ({'end': ('2018', '03', '06', None, None, None, 'date'),
                        'duration': (None, None, None,
                                     None, None, None,
                                     '2.0000048', 'duration')},
                       datetime.date(year=2018, month=3, day=6),
                       datetime.datetime(year=2018, month=3, day=5,
                                         hour=23, minute=59, second=57,
                                         microsecond=999996)),
                      ({'start': (('1981', '04', '05',
                                   None, None, None, 'date'),
                                  ('01', '01', '00', None, 'time'),
                                  'datetime'),
                        'duration': (None, '1', None,
                                     '1', None, '1', None, 'duration')},
                       datetime.datetime(year=1981, month=4, day=5,
                                         hour=1, minute=1),
                       datetime.datetime(year=1981, month=5, day=6,
                                         hour=1, minute=2)),
                      ({'start': ('1981', '04', '05',
                                  None, None, None, 'date'),
                        'duration': (None, '1', None,
                                     '1', None, None, None, 'duration')},
                       datetime.date(year=1981, month=4, day=5),
                       datetime.date(year=1981, month=5, day=6)),
                      ({'start': ('2018', '03', '06',
                                  None, None, None, 'date'),
                        'duration': (None, '2.5', None,
                                     None, None, None, None, 'duration')},
                       datetime.date(year=2018, month=3, day=6),
                       datetime.date(year=2018, month=5, day=20)),
                      ({'start': ('2014', '11', '12',
                                  None, None, None, 'date'),
                        'duration': (None, None, None,
                                     None, '1', None, None, 'duration')},
                       datetime.date(year=2014, month=11, day=12),
                       datetime.datetime(year=2014, month=11, day=12,
                                         hour=1, minute=0)),
                      ({'start': ('2014', '11', '12',
                                  None, None, None, 'date'),
                        'duration': (None, None, None,
                                     None, '4', '54', '6.5', 'duration')},
                       datetime.date(year=2014, month=11, day=12),
                       datetime.datetime(year=2014, month=11, day=12,
                                         hour=4, minute=54, second=6,
                                         microsecond=500000)),
                      ({'start': (('2050', '03', '01',
                                   None, None, None, 'date'),
                                  ('13', '00', '00',
                                   (False, True, None, None,
                                    'Z', 'timezone'), 'time'), 'datetime'),
                        'duration': (None, None, None,
                                     None, '10', None, None, 'duration')},
                       datetime.datetime(year=2050, month=3, day=1,
                                         hour=13,
                                         tzinfo=UTCOffset(name='UTC',
                                                          minutes=0)),
                       datetime.datetime(year=2050, month=3, day=1,
                                         hour=23,
                                         tzinfo=UTCOffset(name='UTC',
                                                          minutes=0))),
                      #Make sure we truncate, not round
                      #https://bitbucket.org/nielsenb/aniso8601/issues/10/sub-microsecond-precision-in-durations-is
                      ({'start': ('0001', '01', '01',
                                  None, None, None, 'date'),
                        'duration': ('1999.9999999999999999', None, None,
                                     None, None, None,
                                     None, 'duration')},
                       datetime.date(year=1, month=1, day=1),
                       datetime.datetime(year=1999, month=9, day=3,
                                         hour=23, minute=59, second=59,
                                         microsecond=999999)),
                      ({'start': ('1989', '03', '01',
                                  None, None, None, 'date'),
                        'duration': (None, '1.9999999999999999', None,
                                     None, None, None,
                                     None, 'duration')},
                       datetime.date(year=1989, month=3, day=1),
                       datetime.datetime(year=1989, month=4, day=29,
                                         hour=23, minute=59, second=59,
                                         microsecond=999999)),
                      ({'start': ('1989', '03', '01',
                                  None, None, None, 'date'),
                        'duration': (None, None, '1.9999999999999999',
                                     None, None, None,
                                     None, 'duration')},
                       datetime.date(year=1989, month=3, day=1),
                       datetime.datetime(year=1989, month=3, day=14,
                                         hour=23, minute=59, second=59,
                                         microsecond=999999)),
                      ({'start': ('1989', '03', '01',
                                  None, None, None, 'date'),
                        'duration': (None, None, None,
                                     '1.9999999999999999', None, None,
                                     None, 'duration')},
                       datetime.date(year=1989, month=3, day=1),
                       datetime.datetime(year=1989, month=3, day=2,
                                         hour=23, minute=59, second=59,
                                         microsecond=999999)),
                      ({'start': ('2001', '01', '01',
                                  None, None, None, 'date'),
                        'duration': (None, None, None,
                                     None, '14.9999999999999999', None,
                                     None, 'duration')},
                       datetime.date(year=2001, month=1, day=1),
                       datetime.datetime(year=2001, month=1, day=1,
                                         hour=14, minute=59, second=59,
                                         microsecond=999999)),
                      ({'start': ('2001', '01', '01',
                                  None, None, None, 'date'),
                        'duration': (None, None, None,
                                     None, None, '0.00000000999',
                                     None, 'duration')},
                       datetime.date(year=2001, month=1, day=1),
                       datetime.datetime(year=2001, month=1, day=1)),
                      ({'start': ('2001', '01', '01',
                                  None, None, None, 'date'),
                        'duration': (None, None, None,
                                     None, None, '0.0000000999',
                                     None, 'duration')},
                       datetime.date(year=2001, month=1, day=1),
                       datetime.datetime(year=2001, month=1, day=1,
                                         hour=0, minute=0, second=0,
                                         microsecond=5)),
                      ({'start': ('2018', '03', '06',
                                  None, None, None, 'date'),
                        'duration': (None, None, None,
                                     None, None, None,
                                     '0.0000001', 'duration')},
                       datetime.date(year=2018, month=3, day=6),
                       datetime.datetime(year=2018, month=3, day=6)),
                      ({'start': ('2018', '03', '06',
                                  None, None, None, 'date'),
                        'duration': (None, None, None,
                                     None, None, None,
                                     '2.0000048', 'duration')},
                       datetime.date(year=2018, month=3, day=6),
                       datetime.datetime(year=2018, month=3, day=6,
                                         hour=0, minute=0, second=2,
                                         microsecond=4)),
                      ({'start': (('1980', '03', '05',
                                   None, None, None, 'date'),
                                  ('01', '01', '00',
                                   None, 'time'), 'datetime'),
                        'end': (('1981', '04', '05',
                                 None, None, None, 'date'),
                                ('01', '01', '00',
                                 None, 'time'), 'datetime')},
                       datetime.datetime(year=1980, month=3, day=5,
                                         hour=1, minute=1),
                       datetime.datetime(year=1981, month=4, day=5,
                                         hour=1, minute=1)),
                      ({'start': (('1980', '03', '05',
                                   None, None, None, 'date'),
                                  ('01', '01', '00',
                                   None, 'time'), 'datetime'),
                        'end': ('1981', '04', '05',
                                None, None, None, 'date')},
                       datetime.datetime(year=1980, month=3, day=5,
                                         hour=1, minute=1),
                       datetime.date(year=1981, month=4, day=5)),
                      ({'start': ('1980', '03', '05',
                                  None, None, None, 'date'),
                        'end': (('1981', '04', '05',
                                 None, None, None, 'date'),
                                ('01', '01', '00',
                                 None, 'time'), 'datetime')},
                       datetime.date(year=1980, month=3, day=5),
                       datetime.datetime(year=1981, month=4, day=5,
                                         hour=1, minute=1)),
                      ({'start': ('1980', '03', '05',
                                  None, None, None, 'date'),
                        'end': ('1981', '04', '05',
                                None, None, None, 'date')},
                       datetime.date(year=1980, month=3, day=5),
                       datetime.date(year=1981, month=4, day=5)),
                      ({'start': ('1981', '04', '05',
                                  None, None, None, 'date'),
                        'end': ('1980', '03', '05',
                                None, None, None, 'date')},
                       datetime.date(year=1981, month=4, day=5),
                       datetime.date(year=1980, month=3, day=5)),
                      ({'start': (('2050', '03', '01',
                                   None, None, None, 'date'),
                                  ('13', '00', '00',
                                   (False, True, None, None,
                                    'Z', 'timezone'), 'time'), 'datetime'),
                        'end': (('2050', '05', '11',
                                 None, None, None, 'date'),
                                ('15', '30', '00',
                                 (False, True, None, None,
                                  'Z', 'timezone'), 'time'), 'datetime')},
                       datetime.datetime(year=2050, month=3, day=1,
                                         hour=13,
                                         tzinfo=UTCOffset(name='UTC',
                                                          minutes=0)),
                       datetime.datetime(year=2050, month=5, day=11,
                                         hour=15, minute=30,
                                         tzinfo=UTCOffset(name='UTC',
                                                          minutes=0))),
                      #Make sure we truncate, not round
                      #https://bitbucket.org/nielsenb/aniso8601/issues/10/sub-microsecond-precision-in-durations-is
                      ({'start': (('1980', '03', '05',
                                   None, None, None, 'date'),
                                  ('01', '01', '00.0000001',
                                   None, 'time'), 'datetime'),
                        'end': (('1981', '04', '05',
                                 None, None, None, 'date'),
                                ('14', '43', '59.9999997', None, 'time'),
                                'datetime')},
                       datetime.datetime(year=1980, month=3, day=5,
                                         hour=1, minute=1),
                       datetime.datetime(year=1981, month=4, day=5,
                                         hour=14, minute=43, second=59,
                                         microsecond=999999)))

        for testtuple in testtuples:
            result = PythonTimeBuilder.build_interval(**testtuple[0])
            self.assertEqual(result[0], testtuple[1])
            self.assertEqual(result[1], testtuple[2])

    def test_build_repeating_interval(self):
        args = {'Rnn': '3', 'interval': (('1981', '04', '05',
                                          None, None, None, 'date'),
                                         None,
                                         (None, None, None,
                                          '1', None, None,
                                          None, 'duration'),
                                         'interval')}
        results = list(PythonTimeBuilder.build_repeating_interval(**args))

        self.assertEqual(results[0], datetime.date(year=1981, month=4, day=5))
        self.assertEqual(results[1], datetime.date(year=1981, month=4, day=6))
        self.assertEqual(results[2], datetime.date(year=1981, month=4, day=7))

        args = {'Rnn': '11', 'interval': (None,
                                          (('1980', '03', '05',
                                            None, None, None, 'date'),
                                           ('01', '01', '00',
                                            None, 'time'), 'datetime'),
                                          (None, None, None,
                                           None, '1', '2',
                                           None, 'duration'),
                                          'interval')}
        results = list(PythonTimeBuilder.build_repeating_interval(**args))

        for dateindex in compat.range(0, 11):
            self.assertEqual(results[dateindex],
                             datetime.datetime(year=1980, month=3, day=5,
                                               hour=1, minute=1)
                             - dateindex * datetime.timedelta(hours=1,
                                                              minutes=2))

        args = {'Rnn': '2', 'interval': ((('1980', '03', '05',
                                           None, None, None, 'date'),
                                          ('01', '01', '00',
                                           None, 'time'), 'datetime'),
                                         (('1981', '04', '05',
                                           None, None, None, 'date'),
                                          ('01', '01', '00',
                                           None, 'time'), 'datetime'),
                                         None,
                                         'interval')}
        results = list(PythonTimeBuilder.build_repeating_interval(**args))

        self.assertEqual(results[0],
                         datetime.datetime(year=1980, month=3, day=5,
                                           hour=1, minute=1))
        self.assertEqual(results[1],
                         datetime.datetime(year=1981, month=4, day=5,
                                           hour=1, minute=1))

        args = {'Rnn': '2', 'interval': ((('1980', '03', '05',
                                           None, None, None, 'date'),
                                          ('01', '01', '00',
                                           None, 'time'), 'datetime'),
                                         (('1981', '04', '05',
                                           None, None, None, 'date'),
                                          ('01', '01', '00',
                                           None, 'time'), 'datetime'),
                                         None,
                                         'interval')}
        results = list(PythonTimeBuilder.build_repeating_interval(**args))

        self.assertEqual(results[0],
                         datetime.datetime(year=1980, month=3, day=5,
                                           hour=1, minute=1))
        self.assertEqual(results[1],
                         datetime.datetime(year=1981, month=4, day=5,
                                           hour=1, minute=1))

        args = {'R': True, 'interval': (None,
                                        (('1980', '03', '05',
                                          None, None, None, 'date'),
                                         ('01', '01', '00',
                                          None, 'time'), 'datetime'),
                                        (None, None, None,
                                         None, '1', '2', None, 'duration'),
                                        'interval')}
        resultgenerator = PythonTimeBuilder.build_repeating_interval(**args)

        #Test the first 11 generated
        for dateindex in compat.range(0, 11):
            self.assertEqual(next(resultgenerator),
                             datetime.datetime(year=1980, month=3, day=5,
                                               hour=1, minute=1)
                             - dateindex * datetime.timedelta(hours=1,
                                                              minutes=2))

    def test_build_timezone(self):
        testtuples = (({'Z': True, 'name': 'Z'},
                       datetime.timedelta(hours=0), 'UTC'),
                      ({'negative': False, 'hh': '00', 'mm': '00',
                        'name': '+00:00'},
                       datetime.timedelta(hours=0), '+00:00'),
                      ({'negative': False, 'hh': '01', 'mm': '00',
                        'name': '+01:00'},
                       datetime.timedelta(hours=1), '+01:00'),
                      ({'negative': True, 'hh': '01', 'mm': '00',
                        'name': '-01:00'},
                       -datetime.timedelta(hours=1), '-01:00'),
                      ({'negative': False, 'hh': '00', 'mm': '12',
                        'name': '+00:12'},
                       datetime.timedelta(minutes=12), '+00:12'),
                      ({'negative': False, 'hh': '01', 'mm': '23',
                        'name': '+01:23'},
                       datetime.timedelta(hours=1, minutes=23), '+01:23'),
                      ({'negative': True, 'hh': '01', 'mm': '23',
                        'name': '-01:23'},
                       -datetime.timedelta(hours=1, minutes=23), '-01:23'),
                      ({'negative': False, 'hh': '00',
                        'name': '+00'},
                       datetime.timedelta(hours=0), '+00'),
                      ({'negative': False, 'hh': '01',
                        'name': '+01'},
                       datetime.timedelta(hours=1), '+01'),
                      ({'negative': True, 'hh': '01',
                        'name': '-01'},
                       -datetime.timedelta(hours=1), '-01'),
                      ({'negative': False, 'hh': '12',
                        'name': '+12'},
                       datetime.timedelta(hours=12), '+12'),
                      ({'negative': True, 'hh': '12',
                        'name': '-12'},
                       -datetime.timedelta(hours=12), '-12'))

        for testtuple in testtuples:
            result = PythonTimeBuilder.build_timezone(**testtuple[0])
            self.assertEqual(result.utcoffset(None), testtuple[1])
            self.assertEqual(result.tzname(None), testtuple[2])

    def test_build_week_date(self):
        weekdate = PythonTimeBuilder._build_week_date(2009, 1)
        self.assertEqual(weekdate, datetime.date(year=2008, month=12, day=29))

        weekdate = PythonTimeBuilder._build_week_date(2009, 53, isoday=7)
        self.assertEqual(weekdate, datetime.date(year=2010, month=1, day=3))

    def test_build_ordinal_date(self):
        ordinaldate = PythonTimeBuilder._build_ordinal_date(1981, 95)
        self.assertEqual(ordinaldate, datetime.date(year=1981, month=4, day=5))

    def test_build_ordinal_date_bounds_checking(self):
        with self.assertRaises(DayOutOfBoundsError):
            PythonTimeBuilder._build_ordinal_date(1234, 0)

        with self.assertRaises(DayOutOfBoundsError):
            PythonTimeBuilder._build_ordinal_date(1234, 367)

    def test_iso_year_start(self):
        yearstart = PythonTimeBuilder._iso_year_start(2004)
        self.assertEqual(yearstart, datetime.date(year=2003, month=12, day=29))

        yearstart = PythonTimeBuilder._iso_year_start(2010)
        self.assertEqual(yearstart, datetime.date(year=2010, month=1, day=4))

        yearstart = PythonTimeBuilder._iso_year_start(2009)
        self.assertEqual(yearstart, datetime.date(year=2008, month=12, day=29))

    def test_date_generator(self):
        startdate = datetime.date(year=2018, month=8, day=29)
        timedelta = datetime.timedelta(days=1)
        iterations = 10

        generator = PythonTimeBuilder._date_generator(startdate,
                                                      timedelta,
                                                      iterations)

        results = list(generator)

        for dateindex in compat.range(0, 10):
            self.assertEqual(results[dateindex],
                             datetime.date(year=2018, month=8, day=29)
                             + dateindex * datetime.timedelta(days=1))

    def test_date_generator_unbounded(self):
        startdate = datetime.date(year=2018, month=8, day=29)
        timedelta = datetime.timedelta(days=5)

        generator = PythonTimeBuilder._date_generator_unbounded(startdate,
                                                                timedelta)

        #Check the first 10 results
        for dateindex in compat.range(0, 10):
            self.assertEqual(next(generator),
                             datetime.date(year=2018, month=8, day=29)
                             + dateindex * datetime.timedelta(days=5))

    def test_split_to_microseconds(self):
        result = PythonTimeBuilder._split_to_microseconds('1.1', int(1e6), 'dummy')

        self.assertEqual(result, (1, 100000))
        self.assertIsInstance(result[0], int)
        self.assertIsInstance(result[1], int)

        result = PythonTimeBuilder._split_to_microseconds('1.000001', int(1e6), 'dummy')

        self.assertEqual(result, (1, 1))
        self.assertIsInstance(result[0], int)
        self.assertIsInstance(result[1], int)

        result = PythonTimeBuilder._split_to_microseconds('1.0000001', int(1e6), 'dummy')

        self.assertEqual(result, (1, 0))
        self.assertIsInstance(result[0], int)
        self.assertIsInstance(result[1], int)

    def test_split_to_microseconds_exception(self):
        with self.assertRaises(ISOFormatError) as e:
            PythonTimeBuilder._split_to_microseconds('b.1', int(1e6), 'exception text')

        self.assertEqual(str(e.exception), 'exception text')

        with self.assertRaises(ISOFormatError) as e:
            PythonTimeBuilder._split_to_microseconds('1.ad', int(1e6), 'exception text')

        self.assertEqual(str(e.exception), 'exception text')

    def test_distribute_microseconds(self):
        self.assertEqual(PythonTimeBuilder._distribute_microseconds(1, (), ()), (1,))
        self.assertEqual(PythonTimeBuilder._distribute_microseconds(11, (0,), (10,)), (1, 1))
        self.assertEqual(PythonTimeBuilder._distribute_microseconds(211, (0, 0), (100, 10)), (2, 1, 1))

        self.assertEqual(PythonTimeBuilder._distribute_microseconds(1, (), ()), (1,))
        self.assertEqual(PythonTimeBuilder._distribute_microseconds(11, (5,), (10,)), (6, 1))
        self.assertEqual(PythonTimeBuilder._distribute_microseconds(211, (10, 5), (100, 10)), (12, 6, 1))

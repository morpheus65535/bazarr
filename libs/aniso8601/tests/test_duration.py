# -*- coding: utf-8 -*-

# Copyright (c) 2021, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

import unittest
import aniso8601

from aniso8601.exceptions import ISOFormatError, NegativeDurationError
from aniso8601.duration import (parse_duration, _parse_duration_prescribed,
                                _parse_duration_combined,
                                _parse_duration_prescribed_notime,
                                _parse_duration_prescribed_time,
                                _parse_duration_element,
                                _has_any_component, _component_order_correct)
from aniso8601.tests.compat import mock

class TestDurationParserFunctions(unittest.TestCase):
    def test_parse_duration(self):
        testtuples = (('P1Y2M3DT4H54M6S', {'PnY': '1', 'PnM': '2',
                                           'PnD': '3', 'TnH': '4',
                                           'TnM': '54', 'TnS': '6'}),
                      ('P1Y2M3DT4H54M6,5S', {'PnY': '1', 'PnM': '2',
                                             'PnD': '3', 'TnH': '4',
                                             'TnM': '54', 'TnS': '6.5'}),
                      ('P1Y2M3DT4H54M6.5S', {'PnY': '1', 'PnM': '2',
                                             'PnD': '3', 'TnH': '4',
                                             'TnM': '54', 'TnS': '6.5'}),
                      ('P1Y2M3D', {'PnY': '1', 'PnM': '2',
                                   'PnW': None, 'PnD': '3'}),
                      ('P1Y2M3,5D', {'PnY': '1', 'PnM': '2',
                                     'PnW': None, 'PnD': '3.5'}),
                      ('P1Y2M3.5D', {'PnY': '1', 'PnM': '2',
                                     'PnW': None, 'PnD': '3.5'}),
                      ('PT4H54M6,5S', {'PnY': None, 'PnM': None, 'PnD': None,
                                       'TnH': '4', 'TnM': '54', 'TnS': '6.5'}),
                      ('PT4H54M6.5S', {'PnY': None, 'PnM': None, 'PnD': None,
                                       'TnH': '4', 'TnM': '54', 'TnS': '6.5'}),
                      ('PT0.0000001S', {'PnY': None, 'PnM': None, 'PnD': None,
                                        'TnH': None, 'TnM': None,
                                        'TnS': '0.0000001'}),
                      ('PT2.0000048S', {'PnY': None, 'PnM': None, 'PnD': None,
                                        'TnH': None, 'TnM': None,
                                        'TnS': '2.0000048'}),
                      ('P1Y', {'PnY': '1', 'PnM': None,
                               'PnW': None, 'PnD': None}),
                      ('P1,5Y', {'PnY': '1.5', 'PnM': None, 'PnW': None,
                                 'PnD': None}),
                      ('P1.5Y', {'PnY': '1.5', 'PnM': None, 'PnW': None,
                                 'PnD': None}),
                      ('P1M', {'PnY': None, 'PnM': '1', 'PnW': None,
                               'PnD': None}),
                      ('P1,5M', {'PnY': None, 'PnM': '1.5', 'PnW': None,
                                 'PnD':None}),
                      ('P1.5M', {'PnY': None, 'PnM': '1.5', 'PnW': None,
                                 'PnD':None}),
                      ('P1W', {'PnY': None, 'PnM': None, 'PnW': '1',
                               'PnD': None}),
                      ('P1,5W', {'PnY': None, 'PnM': None, 'PnW': '1.5',
                                 'PnD': None}),
                      ('P1.5W', {'PnY': None, 'PnM': None, 'PnW': '1.5',
                                 'PnD': None}),
                      ('P1D', {'PnY': None, 'PnM': None, 'PnW': None,
                               'PnD': '1'}),
                      ('P1,5D', {'PnY': None, 'PnM': None, 'PnW': None,
                                 'PnD': '1.5'}),
                      ('P1.5D', {'PnY': None, 'PnM': None, 'PnW': None,
                                 'PnD': '1.5'}),
                      ('P0003-06-04T12:30:05', {'PnY': '0003', 'PnM': '06',
                                                'PnD': '04', 'TnH': '12',
                                                'TnM': '30', 'TnS': '05'}),
                      ('P0003-06-04T12:30:05.5', {'PnY': '0003', 'PnM': '06',
                                                  'PnD': '04', 'TnH': '12',
                                                  'TnM': '30', 'TnS': '05.5'}),
                      ('P0001-02-03T14:43:59.9999997', {'PnY': '0001',
                                                        'PnM': '02',
                                                        'PnD': '03',
                                                        'TnH': '14',
                                                        'TnM': '43',
                                                        'TnS':
                                                        '59.9999997'}))

        for testtuple in testtuples:
            with mock.patch.object(aniso8601.duration.PythonTimeBuilder,
                                   'build_duration') as mockBuildDuration:
                mockBuildDuration.return_value = testtuple[1]

                result = parse_duration(testtuple[0])

                self.assertEqual(result, testtuple[1])
                mockBuildDuration.assert_called_once_with(**testtuple[1])

    def test_parse_duration_mockbuilder(self):
        mockBuilder = mock.Mock()

        expectedargs = {'PnY': '1', 'PnM': '2', 'PnD': '3',
                        'TnH': '4', 'TnM': '54', 'TnS': '6'}

        mockBuilder.build_duration.return_value = expectedargs

        result = parse_duration('P1Y2M3DT4H54M6S', builder=mockBuilder)

        self.assertEqual(result, expectedargs)
        mockBuilder.build_duration.assert_called_once_with(**expectedargs)

    def test_parse_duration_badtype(self):
        testtuples = (None, 1, False, 1.234)

        for testtuple in testtuples:
            with self.assertRaises(ValueError):
                parse_duration(testtuple, builder=None)

    def test_parse_duration_nop(self):
        with self.assertRaises(ISOFormatError):
            #Duration must start with a P
            parse_duration('1Y2M3DT4H54M6S', builder=None)

    def test_parse_duration_weekcombination(self):
        with self.assertRaises(ISOFormatError):
            #Week designator cannot be combined with other time designators
            #https://bitbucket.org/nielsenb/aniso8601/issues/2/week-designators-should-not-be-combinable
            parse_duration('P1Y2W', builder=None)

    def test_parse_duration_negative(self):
        with self.assertRaises(NegativeDurationError):
            parse_duration('P-1Y', builder=None)

        with self.assertRaises(NegativeDurationError):
            parse_duration('P-2M', builder=None)

        with self.assertRaises(NegativeDurationError):
            parse_duration('P-3D', builder=None)

        with self.assertRaises(NegativeDurationError):
            parse_duration('P-T4H', builder=None)

        with self.assertRaises(NegativeDurationError):
            parse_duration('P-T54M', builder=None)

        with self.assertRaises(NegativeDurationError):
            parse_duration('P-T6S', builder=None)

        with self.assertRaises(NegativeDurationError):
            parse_duration('P-7W', builder=None)

        with self.assertRaises(NegativeDurationError):
            parse_duration('P-1Y2M3DT4H54M6S', builder=None)

    def test_parse_duration_outoforder(self):
        #Ensure durations are required to be in the correct order
        #https://bitbucket.org/nielsenb/aniso8601/issues/7/durations-with-time-components-before-t
        #https://bitbucket.org/nielsenb/aniso8601/issues/8/durations-with-components-in-wrong-order
        with self.assertRaises(ISOFormatError):
            parse_duration('P1S', builder=None)

        with self.assertRaises(ISOFormatError):
            parse_duration('P1D1S', builder=None)

        with self.assertRaises(ISOFormatError):
            parse_duration('P1H1M', builder=None)

        with self.assertRaises(ISOFormatError):
            parse_duration('1Y2M3D1SPT1M', builder=None)

        with self.assertRaises(ISOFormatError):
            parse_duration('P1Y2M3D2MT1S', builder=None)

        with self.assertRaises(ISOFormatError):
            parse_duration('P2M3D1ST1Y1M', builder=None)

        with self.assertRaises(ISOFormatError):
            parse_duration('P1Y2M2MT3D1S', builder=None)

        with self.assertRaises(ISOFormatError):
            parse_duration('P1D1Y1M', builder=None)

        with self.assertRaises(ISOFormatError):
            parse_duration('PT1S1H', builder=None)

    def test_parse_duration_badstr(self):
        testtuples = ('bad', '')

        for testtuple in testtuples:
            with self.assertRaises(ValueError):
                parse_duration(testtuple, builder=None)

    def test_parse_duration_prescribed(self):
        testtuples = (('P1Y2M3DT4H54M6S', {'PnY': '1', 'PnM': '2',
                                           'PnD': '3', 'TnH': '4',
                                           'TnM': '54', 'TnS': '6'}),
                      ('P1Y2M3DT4H54M6,5S', {'PnY': '1', 'PnM': '2',
                                             'PnD': '3', 'TnH': '4',
                                             'TnM': '54', 'TnS': '6.5'}),
                      ('P1Y2M3DT4H54M6.5S', {'PnY': '1', 'PnM': '2',
                                             'PnD': '3', 'TnH': '4',
                                             'TnM': '54', 'TnS': '6.5'}),
                      ('PT4H54M6,5S', {'PnY': None, 'PnM': None, 'PnD': None,
                                       'TnH': '4', 'TnM': '54', 'TnS': '6.5'}),
                      ('PT4H54M6.5S', {'PnY': None, 'PnM': None, 'PnD': None,
                                       'TnH': '4', 'TnM': '54', 'TnS': '6.5'}),
                      ('P1Y2M3D', {'PnY': '1', 'PnM': '2',
                                   'PnW': None, 'PnD': '3'}),
                      ('P1Y2M3,5D', {'PnY': '1', 'PnM': '2',
                                     'PnW': None, 'PnD': '3.5'}),
                      ('P1Y2M3.5D', {'PnY': '1', 'PnM': '2',
                                     'PnW': None, 'PnD': '3.5'}),
                      ('P1Y', {'PnY': '1', 'PnM': None,
                               'PnW': None, 'PnD': None}),
                      ('P1,5Y', {'PnY': '1.5', 'PnM': None, 'PnW': None,
                                 'PnD': None}),
                      ('P1.5Y', {'PnY': '1.5', 'PnM': None, 'PnW': None,
                                 'PnD': None}),
                      ('P1M', {'PnY': None, 'PnM': '1', 'PnW': None,
                               'PnD': None}),
                      ('P1,5M', {'PnY': None, 'PnM': '1.5', 'PnW': None,
                                 'PnD':None}),
                      ('P1.5M', {'PnY': None, 'PnM': '1.5', 'PnW': None,
                                 'PnD':None}),
                      ('P1W', {'PnY': None, 'PnM': None, 'PnW': '1',
                               'PnD': None}),
                      ('P1,5W', {'PnY': None, 'PnM': None, 'PnW': '1.5',
                                 'PnD': None}),
                      ('P1.5W', {'PnY': None, 'PnM': None, 'PnW': '1.5',
                                 'PnD': None}),
                      ('P1D', {'PnY': None, 'PnM': None, 'PnW': None,
                               'PnD': '1'}),
                      ('P1,5D', {'PnY': None, 'PnM': None, 'PnW': None,
                                 'PnD': '1.5'}),
                      ('P1.5D', {'PnY': None, 'PnM': None, 'PnW': None,
                                 'PnD': '1.5'}))

        for testtuple in testtuples:
            mockBuilder = mock.Mock()
            mockBuilder.build_duration.return_value = testtuple[1]

            result = _parse_duration_prescribed(testtuple[0], mockBuilder)

            self.assertEqual(result, testtuple[1])
            mockBuilder.build_duration.assert_called_once_with(**testtuple[1])

    def test_parse_duration_prescribed_negative(self):
        with self.assertRaises(NegativeDurationError):
            _parse_duration_prescribed('P-T1H', builder=None)

        with self.assertRaises(NegativeDurationError):
            _parse_duration_prescribed('P-T2M', builder=None)

        with self.assertRaises(NegativeDurationError):
            _parse_duration_prescribed('P-T3S', builder=None)

        with self.assertRaises(NegativeDurationError):
            _parse_duration_prescribed('P-4W', builder=None)

        with self.assertRaises(NegativeDurationError):
            _parse_duration_prescribed('P-1Y2M3DT4H54M6S', builder=None)

    def test_parse_duration_prescribed_multiplefractions(self):
        with self.assertRaises(ISOFormatError):
            #Multiple fractions are not allowed
            _parse_duration_prescribed('P1Y2M3DT4H5.1234M6.1234S', None)

    def test_parse_duration_prescribed_middlefraction(self):
        with self.assertRaises(ISOFormatError):
            #Fraction only allowed on final component
            _parse_duration_prescribed('P1Y2M3DT4H5.1234M6S', None)

    def test_parse_duration_prescribed_suffixgarbage(self):
        #Don't allow garbage after the duration
        #https://bitbucket.org/nielsenb/aniso8601/issues/9/durations-with-trailing-garbage-are-parsed
        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed('P1Dasdfasdf', None)

    def test_parse_duration_prescribed_outoforder(self):
        #Ensure durations are required to be in the correct order
        #https://bitbucket.org/nielsenb/aniso8601/issues/7/durations-with-time-components-before-t
        #https://bitbucket.org/nielsenb/aniso8601/issues/8/durations-with-components-in-wrong-order
        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed('P1S', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed('P1D1S', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed('P1H1M', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed('1Y2M3D1SPT1M', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed('P1Y2M3D2MT1S', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed('P2M3D1ST1Y1M', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed('P1Y2M2MT3D1S', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed('P1D1Y1M', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed('PT1S1H', None)

    def test_parse_duration_prescribed_notime(self):
        testtuples = (('P1Y2M3D', {'PnY': '1', 'PnM': '2',
                                   'PnW': None, 'PnD': '3'}),
                      ('P1Y2M3,5D', {'PnY': '1', 'PnM': '2',
                                     'PnW': None, 'PnD': '3.5'}),
                      ('P1Y2M3.5D', {'PnY': '1', 'PnM': '2',
                                     'PnW': None, 'PnD': '3.5'}),
                      ('P1Y', {'PnY': '1', 'PnM': None,
                               'PnW': None, 'PnD': None}),
                      ('P1,5Y', {'PnY': '1.5', 'PnM': None, 'PnW': None,
                                 'PnD': None}),
                      ('P1.5Y', {'PnY': '1.5', 'PnM': None, 'PnW': None,
                                 'PnD': None}),
                      ('P1M', {'PnY': None, 'PnM': '1', 'PnW': None,
                               'PnD': None}),
                      ('P1,5M', {'PnY': None, 'PnM': '1.5', 'PnW': None,
                                 'PnD':None}),
                      ('P1.5M', {'PnY': None, 'PnM': '1.5', 'PnW': None,
                                 'PnD':None}),
                      ('P1W', {'PnY': None, 'PnM': None, 'PnW': '1',
                               'PnD': None}),
                      ('P1,5W', {'PnY': None, 'PnM': None, 'PnW': '1.5',
                                 'PnD': None}),
                      ('P1.5W', {'PnY': None, 'PnM': None, 'PnW': '1.5',
                                 'PnD': None}),
                      ('P1D', {'PnY': None, 'PnM': None, 'PnW': None,
                               'PnD': '1'}),
                      ('P1,5D', {'PnY': None, 'PnM': None, 'PnW': None,
                                 'PnD': '1.5'}),
                      ('P1.5D', {'PnY': None, 'PnM': None, 'PnW': None,
                                 'PnD': '1.5'}))

        for testtuple in testtuples:
            mockBuilder = mock.Mock()
            mockBuilder.build_duration.return_value = testtuple[1]

            result = _parse_duration_prescribed_notime(testtuple[0], mockBuilder)

            self.assertEqual(result, testtuple[1])
            mockBuilder.build_duration.assert_called_once_with(**testtuple[1])

    def test_parse_duration_prescribed_notime_timepart(self):
        #Ensure no time part is allowed
        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed_notime('P1S', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed_notime('P1D1S', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed_notime('P1H1M', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed_notime('P1Y2M3D4H', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed_notime('P1Y2M3D4H5S', None)

    def test_parse_duration_prescribed_notime_negative(self):
        with self.assertRaises(NegativeDurationError):
            _parse_duration_prescribed_notime('P-1Y', None)

        with self.assertRaises(NegativeDurationError):
            _parse_duration_prescribed_notime('P-2M', None)

        with self.assertRaises(NegativeDurationError):
            _parse_duration_prescribed_notime('P-3D', None)

        with self.assertRaises(NegativeDurationError):
            _parse_duration_prescribed_notime('P-7W', None)

        with self.assertRaises(NegativeDurationError):
            _parse_duration_prescribed_notime('P-1Y2M3D', None)

    def test_parse_duration_prescribed_notime_outoforder(self):
        #Ensure durations are required to be in the correct order
        #https://bitbucket.org/nielsenb/aniso8601/issues/8/durations-with-components-in-wrong-order
        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed_notime('P1H1M', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed_notime('P1D1Y1M', None)

    def test_parse_duration_prescribed_time(self):
        testtuples = (('P1Y2M3DT4H54M6S', {'PnY': '1', 'PnM': '2',
                                           'PnD': '3', 'TnH': '4',
                                           'TnM': '54', 'TnS': '6'}),
                      ('P1Y2M3DT4H54M6,5S', {'PnY': '1', 'PnM': '2',
                                             'PnD': '3', 'TnH': '4',
                                             'TnM': '54', 'TnS': '6.5'}),
                      ('P1Y2M3DT4H54M6.5S', {'PnY': '1', 'PnM': '2',
                                             'PnD': '3', 'TnH': '4',
                                             'TnM': '54', 'TnS': '6.5'}),
                      ('PT4H54M6,5S', {'PnY': None, 'PnM': None, 'PnD': None,
                                       'TnH': '4', 'TnM': '54', 'TnS': '6.5'}),
                      ('PT4H54M6.5S', {'PnY': None, 'PnM': None, 'PnD': None,
                                       'TnH': '4', 'TnM': '54', 'TnS': '6.5'}))

        for testtuple in testtuples:
            mockBuilder = mock.Mock()
            mockBuilder.build_duration.return_value = testtuple[1]

            result = _parse_duration_prescribed_time(testtuple[0], mockBuilder)

            self.assertEqual(result, testtuple[1])
            mockBuilder.build_duration.assert_called_once_with(**testtuple[1])

    def test_parse_duration_prescribed_time_timeindate(self):
        #Don't allow time components in date half
        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed_time('P1Y2M3D4HT54M6S', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed_time('P1Y2M3D6ST4H54M', None)

    def test_parse_duration_prescribed_time_dateintime(self):
        #Don't allow date components in time half
        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed_time('P2M3DT1Y4H54M6S', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed_time('P1Y2MT3D4H54M6S', None)

    def test_parse_duration_prescribed_time_negative(self):
        with self.assertRaises(NegativeDurationError):
            _parse_duration_prescribed_time('P-1Y2M3DT4H54M6S', None)

    def test_parse_duration_prescribed_time_outoforder(self):
        #Ensure durations are required to be in the correct order
        #https://bitbucket.org/nielsenb/aniso8601/issues/7/durations-with-time-components-before-t
        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed_time('1Y2M3D1SPT1M', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed_time('P1Y2M3D2MT1S', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed_time('P2M3D1ST1Y1M', None)

        with self.assertRaises(ISOFormatError):
            _parse_duration_prescribed_time('P1Y2M2MT3D1S', None)

    def test_parse_duration_combined(self):
        testtuples = (('P0003-06-04T12:30:05', {'PnY': '0003', 'PnM': '06',
                                                'PnD': '04', 'TnH': '12',
                                                'TnM': '30', 'TnS': '05'}),
                      ('P0003-06-04T12:30:05,5', {'PnY': '0003', 'PnM': '06',
                                                  'PnD': '04', 'TnH': '12',
                                                  'TnM': '30', 'TnS': '05.5'}),
                      ('P0003-06-04T12:30:05.5', {'PnY': '0003', 'PnM': '06',
                                                  'PnD': '04', 'TnH': '12',
                                                  'TnM': '30', 'TnS': '05.5'}),
                      ('P0001-02-03T14:43:59.9999997', {'PnY': '0001',
                                                        'PnM': '02',
                                                        'PnD': '03',
                                                        'TnH': '14',
                                                        'TnM': '43',
                                                        'TnS':
                                                        '59.9999997'}))

        for testtuple in testtuples:
            mockBuilder = mock.Mock()
            mockBuilder.build_duration.return_value = testtuple[1]

            result = _parse_duration_combined(testtuple[0], mockBuilder)

            self.assertEqual(result, testtuple[1])
            mockBuilder.build_duration.assert_called_once_with(**testtuple[1])

    def test_parse_duration_combined_suffixgarbage(self):
        #Don't allow garbage after the duration
        #https://bitbucket.org/nielsenb/aniso8601/issues/9/durations-with-trailing-garbage-are-parsed
        with self.assertRaises(ISOFormatError):
            _parse_duration_combined('P0003-06-04T12:30:05.5asdfasdf', None)

    def test_parse_duration_element(self):
        testtuples = (('P1Y2M3D', 'Y', '1'),
                      ('P1Y2M3D', 'M', '2'),
                      ('P1Y2M3D', 'D', '3'),
                      ('PT4H54M6,5S', 'H', '4'),
                      ('PT4H54M6,5S', 'M', '54'),
                      ('PT4H54M6,5S', 'S', '6.5'),
                      ('T4H5M6.1234S', 'H', '4'),
                      ('T4H5M6.1234S', 'M', '5'),
                      ('T4H5M6.1234S', 'S', '6.1234'))

        for testtuple in testtuples:
            self.assertEqual(_parse_duration_element(testtuple[0],
                                                     testtuple[1]),
                             testtuple[2])

    def test_has_any_component(self):
        self.assertTrue(_has_any_component('P1Y', ['Y', 'M']))
        self.assertFalse(_has_any_component('P1Y', ['M', 'D']))

    def test_component_order_correct(self):
        self.assertTrue(_component_order_correct('P1Y1M1D',
                                                 ['P', 'Y', 'M', 'D']))
        self.assertTrue(_component_order_correct('P1Y1M',
                                                 ['P', 'Y', 'M', 'D']))
        self.assertFalse(_component_order_correct('P1D1Y1M',
                                                  ['P', 'Y', 'M', 'D']))
        self.assertFalse(_component_order_correct('PT1S1H',
                                                  ['T', 'H', 'M', 'S']))

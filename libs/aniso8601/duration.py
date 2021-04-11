# -*- coding: utf-8 -*-

# Copyright (c) 2021, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

from aniso8601 import compat
from aniso8601.builders import TupleBuilder
from aniso8601.builders.python import PythonTimeBuilder
from aniso8601.date import parse_date
from aniso8601.decimalfraction import find_separator, normalize
from aniso8601.exceptions import ISOFormatError, NegativeDurationError
from aniso8601.time import parse_time

def parse_duration(isodurationstr, builder=PythonTimeBuilder):
    #Given a string representing an ISO 8601 duration, return a
    #a duration built by the given builder. Valid formats are:
    #
    #PnYnMnDTnHnMnS (or any reduced precision equivalent)
    #P<date>T<time>

    if compat.is_string(isodurationstr) is False:
        raise ValueError('Duration must be string.')

    if len(isodurationstr) == 0:
        raise ISOFormatError('"{0}" is not a valid ISO 8601 duration.'
                .format(isodurationstr))

    if isodurationstr[0] != 'P':
        raise ISOFormatError('ISO 8601 duration must start with a P.')

    #If Y, M, D, H, S, or W are in the string,
    #assume it is a specified duration
    if _has_any_component(isodurationstr,
                          ['Y', 'M', 'D', 'H', 'S', 'W']) is True:
        return _parse_duration_prescribed(isodurationstr, builder)

    return _parse_duration_combined(isodurationstr, builder)

def _parse_duration_prescribed(durationstr, builder):
    #durationstr can be of the form PnYnMnDTnHnMnS or PnW

    #Don't allow negative elements
    #https://bitbucket.org/nielsenb/aniso8601/issues/20/negative-duration
    if durationstr.find('-') != -1:
        raise NegativeDurationError('ISO 8601 durations must be positive.')

    #Make sure the end character is valid
    #https://bitbucket.org/nielsenb/aniso8601/issues/9/durations-with-trailing-garbage-are-parsed
    if durationstr[-1] not in ['Y', 'M', 'D', 'H', 'S', 'W']:
        raise ISOFormatError('ISO 8601 duration must end with a valid '
                             'character.')

    #Make sure only the lowest order element has decimal precision
    separator_index = find_separator(durationstr)
    if separator_index != -1:
        remaining = durationstr[separator_index + 1:]
        if find_separator(remaining) != -1:
            raise ISOFormatError('ISO 8601 allows only lowest order element to '
                             'have a decimal fraction.')

        #There should only ever be 1 letter after a decimal if there is more
        #then one, the string is invalid
        lettercount = 0

        for character in remaining:
            if character.isalpha() is True:
                lettercount += 1

                if lettercount > 1:
                    raise ISOFormatError('ISO 8601 duration must end with '
                                         'a single valid character.')

    #Do not allow W in combination with other designators
    #https://bitbucket.org/nielsenb/aniso8601/issues/2/week-designators-should-not-be-combinable
    if (durationstr.find('W') != -1
            and _has_any_component(durationstr,
                                   ['Y', 'M', 'D', 'H', 'S']) is True):
        raise ISOFormatError('ISO 8601 week designators may not be combined '
                             'with other time designators.')

    #Parse the elements of the duration
    if durationstr.find('T') == -1:
        return _parse_duration_prescribed_notime(durationstr, builder)

    return _parse_duration_prescribed_time(durationstr, builder)

def _parse_duration_prescribed_notime(durationstr, builder):
    #durationstr can be of the form PnYnMnD or PnW

    #Don't allow negative elements
    #https://bitbucket.org/nielsenb/aniso8601/issues/20/negative-duration
    if durationstr.find('-') != -1:
        raise NegativeDurationError('ISO 8601 durations must be positive.')

    #Make sure no time portion is included
    #https://bitbucket.org/nielsenb/aniso8601/issues/7/durations-with-time-components-before-t
    if _has_any_component(durationstr, ['H', 'S']):
        raise ISOFormatError('ISO 8601 time components not allowed in duration '
                             'without prescribed time.')

    if _component_order_correct(durationstr,
                                ['P', 'Y', 'M', 'D', 'W']) is False:
        raise ISOFormatError('ISO 8601 duration components must be in the '
                             'correct order.')

    if durationstr.find('Y') != -1:
        yearstr = _parse_duration_element(durationstr, 'Y')
    else:
        yearstr = None

    if durationstr.find('M') != -1:
        monthstr = _parse_duration_element(durationstr, 'M')
    else:
        monthstr = None

    if durationstr.find('W') != -1:
        weekstr = _parse_duration_element(durationstr, 'W')
    else:
        weekstr = None

    if durationstr.find('D') != -1:
        daystr = _parse_duration_element(durationstr, 'D')
    else:
        daystr = None

    return builder.build_duration(PnY=yearstr, PnM=monthstr,
                                  PnW=weekstr, PnD=daystr)

def _parse_duration_prescribed_time(durationstr, builder):
    #durationstr can be of the form PnYnMnDTnHnMnS

    #Don't allow negative elements
    #https://bitbucket.org/nielsenb/aniso8601/issues/20/negative-duration
    if durationstr.find('-') != -1:
        raise NegativeDurationError('ISO 8601 durations must be positive.')

    firsthalf = durationstr[:durationstr.find('T')]
    secondhalf = durationstr[durationstr.find('T'):]

    #Make sure no time portion is included in the date half
    #https://bitbucket.org/nielsenb/aniso8601/issues/7/durations-with-time-components-before-t
    if _has_any_component(firsthalf, ['H', 'S']):
        raise ISOFormatError('ISO 8601 time components not allowed in date '
                             'portion of duration.')

    if _component_order_correct(firsthalf, ['P', 'Y', 'M', 'D', 'W']) is False:
        raise ISOFormatError('ISO 8601 duration components must be in the '
                             'correct order.')

    #Make sure no date component is included in the time half
    if _has_any_component(secondhalf, ['Y', 'D']):
        raise ISOFormatError('ISO 8601 time components not allowed in date '
                             'portion of duration.')

    if _component_order_correct(secondhalf, ['T', 'H', 'M', 'S']) is False:
        raise ISOFormatError('ISO 8601 time components in duration must be in '
                             'the correct order.')

    if firsthalf.find('Y') != -1:
        yearstr = _parse_duration_element(firsthalf, 'Y')
    else:
        yearstr = None

    if firsthalf.find('M') != -1:
        monthstr = _parse_duration_element(firsthalf, 'M')
    else:
        monthstr = None

    if firsthalf.find('D') != -1:
        daystr = _parse_duration_element(firsthalf, 'D')
    else:
        daystr = None

    if secondhalf.find('H') != -1:
        hourstr = _parse_duration_element(secondhalf, 'H')
    else:
        hourstr = None

    if secondhalf.find('M') != -1:
        minutestr = _parse_duration_element(secondhalf, 'M')
    else:
        minutestr = None

    if secondhalf.find('S') != -1:
        secondstr = _parse_duration_element(secondhalf, 'S')
    else:
        secondstr = None

    return builder.build_duration(PnY=yearstr, PnM=monthstr, PnD=daystr,
                                  TnH=hourstr, TnM=minutestr, TnS=secondstr)

def _parse_duration_combined(durationstr, builder):
    #Period of the form P<date>T<time>

    #Split the string in to its component parts
    datepart, timepart = durationstr[1:].split('T') #We skip the 'P'

    datevalue = parse_date(datepart, builder=TupleBuilder)
    timevalue = parse_time(timepart, builder=TupleBuilder)

    return builder.build_duration(PnY=datevalue[0], PnM=datevalue[1],
                                  PnD=datevalue[2], TnH=timevalue[0],
                                  TnM=timevalue[1], TnS=timevalue[2])

def _parse_duration_element(durationstr, elementstr):
    #Extracts the specified portion of a duration, for instance, given:
    #durationstr = 'T4H5M6.1234S'
    #elementstr = 'H'
    #
    #returns 4
    #
    #Note that the string must start with a character, so its assumed the
    #full duration string would be split at the 'T'

    durationstartindex = 0
    durationendindex = durationstr.find(elementstr)

    for characterindex in compat.range(durationendindex - 1, 0, -1):
        if durationstr[characterindex].isalpha() is True:
            durationstartindex = characterindex
            break

    durationstartindex += 1

    return normalize(durationstr[durationstartindex:durationendindex])

def _has_any_component(durationstr, components):
    #Given a duration string, and a list of components, returns True
    #if any of the listed components are present, False otherwise.
    #
    #For instance:
    #durationstr = 'P1Y'
    #components = ['Y', 'M']
    #
    #returns True
    #
    #durationstr = 'P1Y'
    #components = ['M', 'D']
    #
    #returns False

    for component in components:
        if durationstr.find(component) != -1:
            return True

    return False

def _component_order_correct(durationstr, componentorder):
    #Given a duration string, and a list of components, returns
    #True if the components are in the same order as the
    #component order list, False otherwise. Characters that
    #are present in the component order list but not in the
    #duration string are ignored.
    #
    #https://bitbucket.org/nielsenb/aniso8601/issues/8/durations-with-components-in-wrong-order
    #
    #durationstr = 'P1Y1M1D'
    #components = ['P', 'Y', 'M', 'D']
    #
    #returns True
    #
    #durationstr = 'P1Y1M'
    #components = ['P', 'Y', 'M', 'D']
    #
    #returns True
    #
    #durationstr = 'P1D1Y1M'
    #components = ['P', 'Y', 'M', 'D']
    #
    #returns False

    componentindex = 0

    for characterindex in compat.range(len(durationstr)):
        character = durationstr[characterindex]

        if character in componentorder:
            #This is a character we need to check the order of
            if character in componentorder[componentindex:]:
                componentindex = componentorder.index(character)
            else:
                #A character is out of order
                return False

    return True

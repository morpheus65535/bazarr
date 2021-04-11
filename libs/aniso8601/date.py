# -*- coding: utf-8 -*-

# Copyright (c) 2021, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

from aniso8601.builders.python import PythonTimeBuilder
from aniso8601.compat import is_string
from aniso8601.exceptions import ISOFormatError
from aniso8601.resolution import DateResolution

def get_date_resolution(isodatestr):
    #Valid string formats are:
    #
    #Y[YYY]
    #YYYY-MM-DD
    #YYYYMMDD
    #YYYY-MM
    #YYYY-Www
    #YYYYWww
    #YYYY-Www-D
    #YYYYWwwD
    #YYYY-DDD
    #YYYYDDD
    if is_string(isodatestr) is False:
        raise ValueError('Date must be string.')

    if isodatestr.startswith('+') or isodatestr.startswith('-'):
        raise NotImplementedError('ISO 8601 extended year representation '
                                  'not supported.')

    if (len(isodatestr) == 0 or
            isodatestr[0].isdigit() is False
            or isodatestr[-1].isdigit() is False):
        raise ISOFormatError('"{0}" is not a valid ISO 8601 date.'
                .format(isodatestr))

    if isodatestr.find('W') != -1:
        #Handle ISO 8601 week date format
        hyphens_present = 1 if isodatestr.find('-') != -1 else 0
        week_date_len = 7 + hyphens_present
        weekday_date_len = 8 + 2 * hyphens_present

        if len(isodatestr) == week_date_len:
            #YYYY-Www
            #YYYYWww
            return DateResolution.Week
        elif len(isodatestr) == weekday_date_len:
            #YYYY-Www-D
            #YYYYWwwD
            return DateResolution.Weekday
        else:
            raise ISOFormatError('"{0}" is not a valid ISO 8601 week date.'
                                 .format(isodatestr))

    #If the size of the string of 4 or less,
    #assume its a truncated year representation
    if len(isodatestr) <= 4:
        return DateResolution.Year

    #An ISO string may be a calendar represntation if:
    # 1) When split on a hyphen, the sizes of the parts are 4, 2, 2 or 4, 2
    # 2) There are no hyphens, and the length is 8
    datestrsplit = isodatestr.split('-')

    #Check case 1
    if len(datestrsplit) == 2:
        if len(datestrsplit[0]) == 4 and len(datestrsplit[1]) == 2:
            return DateResolution.Month

    if len(datestrsplit) == 3:
        if (len(datestrsplit[0]) == 4
                and len(datestrsplit[1]) == 2
                and len(datestrsplit[2]) == 2):
            return DateResolution.Day

    #Check case 2
    if len(isodatestr) == 8 and isodatestr.find('-') == -1:
        return DateResolution.Day

    #An ISO string may be a ordinal date representation if:
    # 1) When split on a hyphen, the sizes of the parts are 4, 3
    # 2) There are no hyphens, and the length is 7

    #Check case 1
    if len(datestrsplit) == 2:
        if len(datestrsplit[0]) == 4 and len(datestrsplit[1]) == 3:
            return DateResolution.Ordinal

    #Check case 2
    if len(isodatestr) == 7 and isodatestr.find('-') == -1:
        return DateResolution.Ordinal

    #None of the date representations match
    raise ISOFormatError('"{0}" is not an ISO 8601 date, perhaps it '
                         'represents a time or datetime.'.format(isodatestr))

def parse_date(isodatestr, builder=PythonTimeBuilder):
    #Given a string in any ISO 8601 date format, return a datetime.date
    #object that corresponds to the given date. Valid string formats are:
    #
    #Y[YYY]
    #YYYY-MM-DD
    #YYYYMMDD
    #YYYY-MM
    #YYYY-Www
    #YYYYWww
    #YYYY-Www-D
    #YYYYWwwD
    #YYYY-DDD
    #YYYYDDD
    #
    #Note that the ISO 8601 date format of ±YYYYY is expressly not supported
    return _RESOLUTION_MAP[get_date_resolution(isodatestr)](isodatestr,
                                                            builder)

def _parse_year(yearstr, builder):
    #yearstr is of the format Y[YYY]
    return builder.build_date(YYYY=yearstr)

def _parse_calendar_day(datestr, builder):
    #datestr is of the format YYYY-MM-DD or YYYYMMDD
    if len(datestr) == 10:
        #YYYY-MM-DD
        yearstr = datestr[0:4]
        monthstr = datestr[5:7]
        daystr = datestr[8:]
    elif len(datestr) == 8:
        #YYYYMMDD
        yearstr = datestr[0:4]
        monthstr = datestr[4:6]
        daystr = datestr[6:]
    else:
        raise ISOFormatError('"{0}" is not a valid ISO 8601 calendar day.'
                             .format(datestr))

    return builder.build_date(YYYY=yearstr, MM=monthstr, DD=daystr)

def _parse_calendar_month(datestr, builder):
    #datestr is of the format YYYY-MM
    if len(datestr) != 7:
        raise ISOFormatError('"{0}" is not a valid ISO 8601 calendar month.'
                             .format(datestr))

    yearstr = datestr[0:4]
    monthstr = datestr[5:]

    return builder.build_date(YYYY=yearstr, MM=monthstr)

def _parse_week_day(datestr, builder):
    #datestr is of the format YYYY-Www-D, YYYYWwwD
    #
    #W is the week number prefix, ww is the week number, between 1 and 53
    #0 is not a valid week number, which differs from the Python implementation
    #
    #D is the weekday number, between 1 and 7, which differs from the Python
    #implementation which is between 0 and 6

    yearstr = datestr[0:4]

    #Week number will be the two characters after the W
    windex = datestr.find('W')
    weekstr = datestr[windex + 1:windex + 3]

    if datestr.find('-') != -1 and len(datestr) == 10:
        #YYYY-Www-D
        daystr = datestr[9:10]
    elif len(datestr) == 8:
         #YYYYWwwD
        daystr = datestr[7:8]
    else:
        raise ISOFormatError('"{0}" is not a valid ISO 8601 week date.'
                             .format(datestr))

    return builder.build_date(YYYY=yearstr, Www=weekstr, D=daystr)

def _parse_week(datestr, builder):
    #datestr is of the format YYYY-Www, YYYYWww
    #
    #W is the week number prefix, ww is the week number, between 1 and 53
    #0 is not a valid week number, which differs from the Python implementation

    yearstr = datestr[0:4]

    #Week number will be the two characters after the W
    windex = datestr.find('W')
    weekstr = datestr[windex + 1:windex + 3]

    return builder.build_date(YYYY=yearstr, Www=weekstr)

def _parse_ordinal_date(datestr, builder):
    #datestr is of the format YYYY-DDD or YYYYDDD
    #DDD can be from 1 - 36[5,6], this matches Python's definition

    yearstr = datestr[0:4]

    if datestr.find('-') != -1:
        #YYYY-DDD
        daystr = datestr[(datestr.find('-') + 1):]
    else:
        #YYYYDDD
        daystr = datestr[4:]

    return builder.build_date(YYYY=yearstr, DDD=daystr)

_RESOLUTION_MAP = {
    DateResolution.Day: _parse_calendar_day,
    DateResolution.Ordinal: _parse_ordinal_date,
    DateResolution.Month: _parse_calendar_month,
    DateResolution.Week: _parse_week,
    DateResolution.Weekday: _parse_week_day,
    DateResolution.Year: _parse_year
}

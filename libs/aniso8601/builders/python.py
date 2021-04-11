# -*- coding: utf-8 -*-

# Copyright (c) 2021, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

import datetime

from aniso8601.builders import BaseTimeBuilder, TupleBuilder
from aniso8601.exceptions import (DayOutOfBoundsError,
                                  HoursOutOfBoundsError,
                                  LeapSecondError, MidnightBoundsError,
                                  MinutesOutOfBoundsError,
                                  SecondsOutOfBoundsError,
                                  WeekOutOfBoundsError, YearOutOfBoundsError)
from aniso8601.utcoffset import UTCOffset

MICROSECONDS_PER_SECOND = int(1e6)

MICROSECONDS_PER_MINUTE = 60 * MICROSECONDS_PER_SECOND
MICROSECONDS_PER_HOUR = 60 * MICROSECONDS_PER_MINUTE
MICROSECONDS_PER_DAY = 24 * MICROSECONDS_PER_HOUR
MICROSECONDS_PER_WEEK = 7 * MICROSECONDS_PER_DAY
MICROSECONDS_PER_MONTH = 30 * MICROSECONDS_PER_DAY
MICROSECONDS_PER_YEAR = 365 * MICROSECONDS_PER_DAY

class PythonTimeBuilder(BaseTimeBuilder):
    @classmethod
    def build_date(cls, YYYY=None, MM=None, DD=None, Www=None, D=None,
                   DDD=None):

        if YYYY is not None:
            #Truncated dates, like '19', refer to 1900-1999 inclusive,
            #we simply parse to 1900
            if len(YYYY) < 4:
                #Shift 0s in from the left to form complete year
                YYYY = YYYY.ljust(4, '0')

            year = cls.cast(YYYY, int,
                            thrownmessage='Invalid year string.')

        if MM is not None:
            month = cls.cast(MM, int,
                             thrownmessage='Invalid month string.')
        else:
            month = 1

        if DD is not None:
            day = cls.cast(DD, int,
                           thrownmessage='Invalid day string.')
        else:
            day = 1

        if Www is not None:
            weeknumber = cls.cast(Www, int,
                                  thrownmessage='Invalid week string.')

            if weeknumber == 0 or weeknumber > 53:
                raise WeekOutOfBoundsError('Week number must be between '
                                           '1..53.')
        else:
            weeknumber = None

        if DDD is not None:
            dayofyear = cls.cast(DDD, int,
                                 thrownmessage='Invalid day string.')
        else:
            dayofyear = None

        if D is not None:
            dayofweek = cls.cast(D, int,
                                 thrownmessage='Invalid day string.')

            if dayofweek == 0 or dayofweek > 7:
                raise DayOutOfBoundsError('Weekday number must be between '
                                          '1..7.')
        else:
            dayofweek = None

        #0000 (1 BC) is not representable as a Python date so a ValueError is
        #raised
        if year == 0:
            raise YearOutOfBoundsError('Year must be between 1..9999.')

        if dayofyear is not None:
            return PythonTimeBuilder._build_ordinal_date(year, dayofyear)

        if weeknumber is not None:
            return PythonTimeBuilder._build_week_date(year, weeknumber,
                                                      isoday=dayofweek)

        return datetime.date(year, month, day)

    @classmethod
    def build_time(cls, hh=None, mm=None, ss=None, tz=None):
        #Builds a time from the given parts, handling fractional arguments
        #where necessary
        hours = 0
        minutes = 0
        seconds = 0
        microseconds = 0

        if hh is not None:
            if '.' in hh:
                hours, remainingmicroseconds = cls._split_to_microseconds(hh, MICROSECONDS_PER_HOUR, 'Invalid hour string.')
                microseconds += remainingmicroseconds
            else:
                hours = cls.cast(hh, int,
                                 thrownmessage='Invalid hour string.')

        if mm is not None:
            if '.' in mm:
                minutes, remainingmicroseconds = cls._split_to_microseconds(mm, MICROSECONDS_PER_MINUTE, 'Invalid minute string.')
                microseconds += remainingmicroseconds
            else:
                minutes = cls.cast(mm, int,
                                   thrownmessage='Invalid minute string.')

        if ss is not None:
            if '.' in ss:
                seconds, remainingmicroseconds = cls._split_to_microseconds(ss, MICROSECONDS_PER_SECOND, 'Invalid second string.')
                microseconds += remainingmicroseconds
            else:
                seconds = cls.cast(ss, int,
                                   thrownmessage='Invalid second string.')

        hours, minutes, seconds, microseconds = PythonTimeBuilder._distribute_microseconds(microseconds, (hours, minutes, seconds), (MICROSECONDS_PER_HOUR, MICROSECONDS_PER_MINUTE, MICROSECONDS_PER_SECOND))

        #Range checks
        if hours == 23 and minutes == 59 and seconds == 60:
            #https://bitbucket.org/nielsenb/aniso8601/issues/10/sub-microsecond-precision-in-durations-is
            raise LeapSecondError('Leap seconds are not supported.')

        if (hours == 24
                and (minutes != 0 or seconds != 0)):
            raise MidnightBoundsError('Hour 24 may only represent midnight.')

        if hours > 24:
            raise HoursOutOfBoundsError('Hour must be between 0..24 with '
                                        '24 representing midnight.')

        if minutes >= 60:
            raise MinutesOutOfBoundsError('Minutes must be less than 60.')

        if seconds >= 60:
            raise SecondsOutOfBoundsError('Seconds must be less than 60.')

        #Fix ranges that have passed range checks
        if hours == 24:
            hours = 0
            minutes = 0
            seconds = 0

        #Datetimes don't handle fractional components, so we use a timedelta
        if tz is not None:
            return (datetime.datetime(1, 1, 1,
                                      hour=hours,
                                      minute=minutes,
                                      tzinfo=cls._build_object(tz))
                    + datetime.timedelta(seconds=seconds,
                                         microseconds=microseconds)
                   ).timetz()

        return (datetime.datetime(1, 1, 1,
                                  hour=hours,
                                  minute=minutes)
                + datetime.timedelta(seconds=seconds,
                                     microseconds=microseconds)
               ).time()

    @classmethod
    def build_datetime(cls, date, time):
        return datetime.datetime.combine(cls._build_object(date),
                                         cls._build_object(time))

    @classmethod
    def build_duration(cls, PnY=None, PnM=None, PnW=None, PnD=None, TnH=None,
                       TnM=None, TnS=None):
        years = 0
        months = 0
        days = 0
        weeks = 0
        hours = 0
        minutes = 0
        seconds = 0
        microseconds = 0

        if PnY is not None:
            if '.' in PnY:
                years, remainingmicroseconds = cls._split_to_microseconds(PnY, MICROSECONDS_PER_YEAR, 'Invalid year string.')
                microseconds += remainingmicroseconds
            else:
                years = cls.cast(PnY, int,
                                 thrownmessage='Invalid year string.')

        if PnM is not None:
            if '.' in PnM:
                months, remainingmicroseconds = cls._split_to_microseconds(PnM, MICROSECONDS_PER_MONTH, 'Invalid month string.')
                microseconds += remainingmicroseconds
            else:
                months = cls.cast(PnM, int,
                                  thrownmessage='Invalid month string.')

        if PnW is not None:
            if '.' in PnW:
                weeks, remainingmicroseconds = cls._split_to_microseconds(PnW, MICROSECONDS_PER_WEEK, 'Invalid week string.')
                microseconds += remainingmicroseconds
            else:
                weeks = cls.cast(PnW, int,
                                 thrownmessage='Invalid week string.')

        if PnD is not None:
            if '.' in PnD:
                days, remainingmicroseconds = cls._split_to_microseconds(PnD, MICROSECONDS_PER_DAY, 'Invalid day string.')
                microseconds += remainingmicroseconds
            else:
                days = cls.cast(PnD, int,
                                thrownmessage='Invalid day string.')

        if TnH is not None:
            if '.' in TnH:
                hours, remainingmicroseconds = cls._split_to_microseconds(TnH, MICROSECONDS_PER_HOUR, 'Invalid hour string.')
                microseconds += remainingmicroseconds
            else:
                hours = cls.cast(TnH, int,
                                 thrownmessage='Invalid hour string.')

        if TnM is not None:
            if '.' in TnM:
                minutes, remainingmicroseconds = cls._split_to_microseconds(TnM, MICROSECONDS_PER_MINUTE, 'Invalid minute string.')
                microseconds += remainingmicroseconds
            else:
                minutes = cls.cast(TnM, int,
                                   thrownmessage='Invalid minute string.')

        if TnS is not None:
            if '.' in TnS:
                seconds, remainingmicroseconds = cls._split_to_microseconds(TnS, MICROSECONDS_PER_SECOND, 'Invalid second string.')
                microseconds += remainingmicroseconds
            else:
                seconds = cls.cast(TnS, int,
                                   thrownmessage='Invalid second string.')

        years, months, weeks, days, hours, minutes, seconds, microseconds = PythonTimeBuilder._distribute_microseconds(microseconds, (years, months, weeks, days, hours, minutes, seconds), (MICROSECONDS_PER_YEAR, MICROSECONDS_PER_MONTH, MICROSECONDS_PER_WEEK, MICROSECONDS_PER_DAY, MICROSECONDS_PER_HOUR, MICROSECONDS_PER_MINUTE, MICROSECONDS_PER_SECOND))

        #Note that weeks can be handled without conversion to days
        totaldays = years * 365 + months * 30 + days

        return datetime.timedelta(days=totaldays,
                                  seconds=seconds,
                                  microseconds=microseconds,
                                  minutes=minutes,
                                  hours=hours,
                                  weeks=weeks)

    @classmethod
    def build_interval(cls, start=None, end=None, duration=None):
        if start is not None and end is not None:
            #<start>/<end>
            startobject = cls._build_object(start)
            endobject = cls._build_object(end)

            return (startobject, endobject)

        durationobject = cls._build_object(duration)

        #Determine if datetime promotion is required
        datetimerequired = (duration[4] is not None
                            or duration[5] is not None
                            or duration[6] is not None
                            or durationobject.seconds != 0
                            or durationobject.microseconds != 0)

        if end is not None:
            #<duration>/<end>
            endobject = cls._build_object(end)
            if end[-1] == 'date' and datetimerequired is True:
                #<end> is a date, and <duration> requires datetime resolution
                return (endobject,
                        cls.build_datetime(end, TupleBuilder.build_time())
                        - durationobject)

            return (endobject,
                    endobject
                    - durationobject)

        #<start>/<duration>
        startobject = cls._build_object(start)

        if start[-1] == 'date' and datetimerequired is True:
            #<start> is a date, and <duration> requires datetime resolution
            return (startobject,
                    cls.build_datetime(start, TupleBuilder.build_time())
                    + durationobject)

        return (startobject,
                startobject
                + durationobject)

    @classmethod
    def build_repeating_interval(cls, R=None, Rnn=None, interval=None):
        startobject = None
        endobject = None

        if interval[0] is not None:
            startobject = cls._build_object(interval[0])

        if interval[1] is not None:
            endobject = cls._build_object(interval[1])

        if interval[2] is not None:
            durationobject = cls._build_object(interval[2])
        else:
            durationobject = endobject - startobject

        if R is True:
            if startobject is not None:
                return cls._date_generator_unbounded(startobject,
                                                     durationobject)

            return cls._date_generator_unbounded(endobject,
                                                 -durationobject)

        iterations = cls.cast(Rnn, int,
                              thrownmessage='Invalid iterations.')

        if startobject is not None:
            return cls._date_generator(startobject, durationobject, iterations)

        return cls._date_generator(endobject, -durationobject, iterations)

    @classmethod
    def build_timezone(cls, negative=None, Z=None, hh=None, mm=None, name=''):
        if Z is True:
            #Z -> UTC
            return UTCOffset(name='UTC', minutes=0)

        if hh is not None:
            tzhour = cls.cast(hh, int,
                              thrownmessage='Invalid hour string.')
        else:
            tzhour = 0

        if mm is not None:
            tzminute = cls.cast(mm, int,
                                thrownmessage='Invalid minute string.')
        else:
            tzminute = 0

        if negative is True:
            return UTCOffset(name=name, minutes=-(tzhour * 60 + tzminute))

        return UTCOffset(name=name, minutes=tzhour * 60 + tzminute)

    @staticmethod
    def _build_week_date(isoyear, isoweek, isoday=None):
        if isoday is None:
            return (PythonTimeBuilder._iso_year_start(isoyear)
                    + datetime.timedelta(weeks=isoweek - 1))

        return (PythonTimeBuilder._iso_year_start(isoyear)
                + datetime.timedelta(weeks=isoweek - 1, days=isoday - 1))

    @staticmethod
    def _build_ordinal_date(isoyear, isoday):
        #Day of year to a date
        #https://stackoverflow.com/questions/2427555/python-question-year-and-day-of-year-to-date
        builtdate = (datetime.date(isoyear, 1, 1)
                     + datetime.timedelta(days=isoday - 1))

        #Enforce ordinal day limitation
        #https://bitbucket.org/nielsenb/aniso8601/issues/14/parsing-ordinal-dates-should-only-allow
        if isoday == 0 or builtdate.year != isoyear:
            raise DayOutOfBoundsError('Day of year must be from 1..365, '
                                      '1..366 for leap year.')

        return builtdate

    @staticmethod
    def _iso_year_start(isoyear):
        #Given an ISO year, returns the equivalent of the start of the year
        #on the Gregorian calendar (which is used by Python)
        #Stolen from:
        #http://stackoverflow.com/questions/304256/whats-the-best-way-to-find-the-inverse-of-datetime-isocalendar

        #Determine the location of the 4th of January, the first week of
        #the ISO year is the week containing the 4th of January
        #http://en.wikipedia.org/wiki/ISO_week_date
        fourth_jan = datetime.date(isoyear, 1, 4)

        #Note the conversion from ISO day (1 - 7) and Python day (0 - 6)
        delta = datetime.timedelta(days=fourth_jan.isoweekday() - 1)

        #Return the start of the year
        return fourth_jan - delta

    @staticmethod
    def _date_generator(startdate, timedelta, iterations):
        currentdate = startdate
        currentiteration = 0

        while currentiteration < iterations:
            yield currentdate

            #Update the values
            currentdate += timedelta
            currentiteration += 1

    @staticmethod
    def _date_generator_unbounded(startdate, timedelta):
        currentdate = startdate

        while True:
            yield currentdate

            #Update the value
            currentdate += timedelta

    @classmethod
    def _split_to_microseconds(cls, floatstr, conversion, thrownmessage):
        #Splits a string with a decimal point into an int, and
        #int representing the floating point remainder as a number
        #of microseconds, determined by multiplying by conversion
        intpart, floatpart = floatstr.split('.')

        intvalue = cls.cast(intpart, int,
                            thrownmessage=thrownmessage)

        preconvertedvalue = cls.cast(floatpart, int,
                                     thrownmessage=thrownmessage)

        convertedvalue = ((preconvertedvalue * conversion) //
                          (10 ** len(floatpart)))

        return (intvalue, convertedvalue)

    @staticmethod
    def _distribute_microseconds(todistribute, recipients, reductions):
        #Given a number of microseconds as int, a tuple of ints length n
        #to distribute to, and a tuple of ints length n to divide todistribute
        #by (from largest to smallest), returns a tuple of length n + 1, with
        #todistribute divided across recipients using the reductions, with
        #the final remainder returned as the final tuple member
        results = []

        remainder = todistribute

        for index, reduction in enumerate(reductions):
            additional, remainder = divmod(remainder, reduction)

            results.append(recipients[index] + additional)

        #Always return the remaining microseconds
        results.append(remainder)

        return tuple(results)

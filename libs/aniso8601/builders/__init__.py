# -*- coding: utf-8 -*-

# Copyright (c) 2021, Brandon Nielsen
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

from aniso8601.exceptions import ISOFormatError

class BaseTimeBuilder(object):
    @classmethod
    def build_date(cls, YYYY=None, MM=None, DD=None, Www=None, D=None,
                   DDD=None):
        raise NotImplementedError

    @classmethod
    def build_time(cls, hh=None, mm=None, ss=None, tz=None):
        raise NotImplementedError

    @classmethod
    def build_datetime(cls, date, time):
        raise NotImplementedError

    @classmethod
    def build_duration(cls, PnY=None, PnM=None, PnW=None, PnD=None, TnH=None,
                       TnM=None, TnS=None):
        raise NotImplementedError

    @classmethod
    def build_interval(cls, start=None, end=None, duration=None):
        #start, end, and duration are all tuples
        raise NotImplementedError

    @classmethod
    def build_repeating_interval(cls, R=None, Rnn=None, interval=None):
        #interval is a tuple
        raise NotImplementedError

    @classmethod
    def build_timezone(cls, negative=None, Z=None, hh=None, mm=None, name=''):
        raise NotImplementedError

    @staticmethod
    def cast(value, castfunction, caughtexceptions=(ValueError,),
             thrownexception=ISOFormatError, thrownmessage=None):

        try:
            result = castfunction(value)
        except caughtexceptions:
            raise thrownexception(thrownmessage)

        return result

    @classmethod
    def _build_object(cls, parsetuple):
        #Given a TupleBuilder tuple, build the correct object
        if parsetuple[-1] == 'date':
            return cls.build_date(YYYY=parsetuple[0], MM=parsetuple[1],
                                  DD=parsetuple[2], Www=parsetuple[3],
                                  D=parsetuple[4], DDD=parsetuple[5])
        elif parsetuple[-1] == 'time':
            return cls.build_time(hh=parsetuple[0], mm=parsetuple[1],
                                  ss=parsetuple[2], tz=parsetuple[3])
        elif parsetuple[-1] == 'datetime':
            return cls.build_datetime(parsetuple[0], parsetuple[1])
        elif parsetuple[-1] == 'duration':
            return cls.build_duration(PnY=parsetuple[0], PnM=parsetuple[1],
                                      PnW=parsetuple[2], PnD=parsetuple[3],
                                      TnH=parsetuple[4], TnM=parsetuple[5],
                                      TnS=parsetuple[6])
        elif parsetuple[-1] == 'interval':
            return cls.build_interval(start=parsetuple[0], end=parsetuple[1],
                                      duration=parsetuple[2])
        elif parsetuple[-1] == 'repeatinginterval':
            return cls.build_repeating_interval(R=parsetuple[0],
                                                Rnn=parsetuple[1],
                                                interval=parsetuple[2])

        return cls.build_timezone(negative=parsetuple[0], Z=parsetuple[1],
                                  hh=parsetuple[2], mm=parsetuple[3],
                                  name=parsetuple[4])

class TupleBuilder(BaseTimeBuilder):
    #Builder used to return the arguments as a tuple, cleans up some parse methods
    @classmethod
    def build_date(cls, YYYY=None, MM=None, DD=None, Www=None, D=None,
                   DDD=None):

        return (YYYY, MM, DD, Www, D, DDD, 'date')

    @classmethod
    def build_time(cls, hh=None, mm=None, ss=None, tz=None):
        return (hh, mm, ss, tz, 'time')

    @classmethod
    def build_datetime(cls, date, time):
        return (date, time, 'datetime')

    @classmethod
    def build_duration(cls, PnY=None, PnM=None, PnW=None, PnD=None, TnH=None,
                       TnM=None, TnS=None):

        return (PnY, PnM, PnW, PnD, TnH, TnM, TnS, 'duration')

    @classmethod
    def build_interval(cls, start=None, end=None, duration=None):
        return (start, end, duration, 'interval')

    @classmethod
    def build_repeating_interval(cls, R=None, Rnn=None, interval=None):
        return (R, Rnn, interval, 'repeatinginterval')

    @classmethod
    def build_timezone(cls, negative=None, Z=None, hh=None, mm=None, name=''):
        return (negative, Z, hh, mm, name, 'timezone')

"""
pretty

Formats dates, numbers, etc. in a pretty, human readable format.
"""
__author__ = "S Anand (sanand@s-anand.net)"
__copyright__ = "Copyright 2010, S Anand"
__license__ = "WTFPL"

from datetime import datetime

def _df(seconds, denominator=1, text='', past=True):
    if past:   return         str((seconds + denominator/2)/ denominator) + text + ' ago'
    else:      return 'in ' + str((seconds + denominator/2)/ denominator) + text

def date(time=False, asdays=False, short=False):
    '''Returns a pretty formatted date.
    Inputs:
        time is a datetime object or an int timestamp
        asdays is True if you only want to measure days, not seconds
        short is True if you want "1d ago", "2d ago", etc. False if you want
    '''

    now = datetime.now()
    if type(time) is int:   time = datetime.fromtimestamp(time)
    elif not time:          time = now

    if time > now:  past, diff = False, time - now
    else:           past, diff = True,  now - time
    seconds = diff.seconds
    days    = diff.days

    if short:
        if days == 0 and not asdays:
            if   seconds < 10:          return 'now'
            elif seconds < 60:          return _df(seconds, 1, 's', past)
            elif seconds < 3600:        return _df(seconds, 60, 'm', past)
            else:                       return _df(seconds, 3600, 'h', past)
        else:
            if   days   == 0:           return 'today'
            elif days   == 1:           return past and 'yest' or 'tom'
            elif days    < 7:           return _df(days, 1, 'd', past)
            elif days    < 31:          return _df(days, 7, 'w', past)
            elif days    < 365:         return _df(days, 30, 'mo', past)
            else:                       return _df(days, 365, 'y', past)
    else:
        if days == 0 and not asdays:
            if   seconds < 10:          return 'now'
            elif seconds < 60:          return _df(seconds, 1, ' seconds', past)
            elif seconds < 120:         return past and 'a minute ago' or 'in a minute'
            elif seconds < 3600:        return _df(seconds, 60, ' minutes', past)
            elif seconds < 7200:        return past and 'an hour ago' or'in an hour'
            else:                       return _df(seconds, 3600, ' hours', past)
        else:
            if   days   == 0:           return 'today'
            elif days   == 1:           return past and 'yesterday' or'tomorrow'
            elif days   == 2:           return past and 'day before' or 'day after'
            elif days    < 7:           return _df(days, 1, ' days', past)
            elif days    < 14:          return past and 'last week' or 'next week'
            elif days    < 31:          return _df(days, 7, ' weeks', past)
            elif days    < 61:          return past and 'last month' or 'next month'
            elif days    < 365:         return _df(days, 30, ' months', past)
            elif days    < 730:         return past and 'last year' or 'next year'
            else:                       return _df(days, 365, ' years', past)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Date
"""
from dateutil import parser

from rebulk.remodule import re

_dsep = r'[-/ \.]'
_dsep_bis = r'[-/ \.x]'

date_regexps = [
    re.compile(r'%s((\d{8}))%s' % (_dsep, _dsep), re.IGNORECASE),
    re.compile(r'%s((\d{6}))%s' % (_dsep, _dsep), re.IGNORECASE),
    re.compile(r'(?:^|[^\d])((\d{2})%s(\d{1,2})%s(\d{1,2}))(?:$|[^\d])' % (_dsep, _dsep), re.IGNORECASE),
    re.compile(r'(?:^|[^\d])((\d{1,2})%s(\d{1,2})%s(\d{2}))(?:$|[^\d])' % (_dsep, _dsep), re.IGNORECASE),
    re.compile(r'(?:^|[^\d])((\d{4})%s(\d{1,2})%s(\d{1,2}))(?:$|[^\d])' % (_dsep_bis, _dsep), re.IGNORECASE),
    re.compile(r'(?:^|[^\d])((\d{1,2})%s(\d{1,2})%s(\d{4}))(?:$|[^\d])' % (_dsep, _dsep_bis), re.IGNORECASE),
    re.compile(r'(?:^|[^\d])((\d{1,2}(?:st|nd|rd|th)?%s(?:[a-z]{3,10})%s\d{4}))(?:$|[^\d])' % (_dsep, _dsep),
               re.IGNORECASE)]


def valid_year(year):
    """Check if number is a valid year"""
    return 1920 <= year < 2030


def _is_int(string):
    """
    Check if the input string is an integer

    :param string:
    :type string:
    :return:
    :rtype:
    """
    try:
        int(string)
        return True
    except ValueError:
        return False


def _guess_day_first_parameter(groups):
    """
    If day_first is not defined, use some heuristic to fix it.
    It helps to solve issues with python dateutils 2.5.3 parser changes.

    :param groups: match groups found for the date
    :type groups: list of match objects
    :return: day_first option guessed value
    :rtype: bool
    """

    # If match starts with a long year, then day_first is force to false.
    if _is_int(groups[0]) and valid_year(int(groups[0][:4])):
        return False
    # If match ends with a long year, the day_first is forced to true.
    elif _is_int(groups[-1]) and valid_year(int(groups[-1][-4:])):
        return True
    # If match starts with a short year, then day_first is force to false.
    elif _is_int(groups[0]) and int(groups[0][:2]) > 31:
        return False
    # If match ends with a short year, then day_first is force to true.
    elif _is_int(groups[-1]) and int(groups[-1][-2:]) > 31:
        return True


def search_date(string, year_first=None, day_first=None):
    """Looks for date patterns, and if found return the date and group span.

    Assumes there are sentinels at the beginning and end of the string that
    always allow matching a non-digit delimiting the date.

    Year can be defined on two digit only. It will return the nearest possible
    date from today.

    >>> search_date(' This happened on 2002-04-22. ')
    (18, 28, datetime.date(2002, 4, 22))

    >>> search_date(' And this on 17-06-1998. ')
    (13, 23, datetime.date(1998, 6, 17))

    >>> search_date(' no date in here ')
    """
    for date_re in date_regexps:
        search_match = date_re.search(string)
        if not search_match:
            continue

        start, end = search_match.start(1), search_match.end(1)
        groups = search_match.groups()[1:]
        match = '-'.join(groups)

        if match is None:
            continue

        if year_first and day_first is None:
            day_first = False

        if day_first is None:
            day_first = _guess_day_first_parameter(groups)

        # If day_first/year_first is undefined, parse is made using both possible values.
        yearfirst_opts = [False, True]
        if year_first is not None:
            yearfirst_opts = [year_first]

        dayfirst_opts = [True, False]
        if day_first is not None:
            dayfirst_opts = [day_first]

        kwargs_list = ({'dayfirst': d, 'yearfirst': y}
                       for d in dayfirst_opts for y in yearfirst_opts)
        for kwargs in kwargs_list:
            try:
                date = parser.parse(match, **kwargs)
            except (ValueError, TypeError):  # pragma: no cover
                # see https://bugs.launchpad.net/dateutil/+bug/1247643
                date = None

            # check date plausibility
            if date and valid_year(date.year):  # pylint:disable=no-member
                return start, end, date.date()  # pylint:disable=no-member

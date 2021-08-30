#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
date and year properties
"""
from rebulk import Rebulk, RemoveMatch, Rule

from ..common.date import search_date, valid_year
from ..common.pattern import is_disabled
from ..common.validators import seps_surround


def date(config):  # pylint:disable=unused-argument
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().defaults(validator=seps_surround)

    rebulk.regex(r"\d{4}", name="year", formatter=int,
                 disabled=lambda context: is_disabled(context, 'year'),
                 conflict_solver=lambda match, other: other
                 if other.name in ('episode', 'season') and len(other.raw) < len(match.raw)
                 else '__default__',
                 validator=lambda match: seps_surround(match) and valid_year(match.value))

    def date_functional(string, context):  # pylint:disable=inconsistent-return-statements
        """
        Search for date in the string and retrieves match

        :param string:
        :return:
        """

        ret = search_date(string, context.get('date_year_first'), context.get('date_day_first'))
        if ret:
            return ret[0], ret[1], {'value': ret[2]}

    rebulk.functional(date_functional, name="date", properties={'date': [None]},
                      disabled=lambda context: is_disabled(context, 'date'),
                      conflict_solver=lambda match, other: other
                      if other.name in ('episode', 'season', 'crc32')
                      else '__default__')

    rebulk.rules(KeepMarkedYearInFilepart)

    return rebulk


class KeepMarkedYearInFilepart(Rule):
    """
    Keep first years marked with [](){} in filepart, or if no year is marked, ensure it won't override titles.
    """
    priority = 64
    consequence = RemoveMatch

    def enabled(self, context):
        return not is_disabled(context, 'year')

    def when(self, matches, context):
        ret = []
        if len(matches.named('year')) > 1:
            for filepart in matches.markers.named('path'):
                years = matches.range(filepart.start, filepart.end, lambda match: match.name == 'year')
                if len(years) > 1:
                    group_years = []
                    ungroup_years = []
                    for year in years:
                        if matches.markers.at_match(year, lambda marker: marker.name == 'group'):
                            group_years.append(year)
                        else:
                            ungroup_years.append(year)
                    if group_years and ungroup_years:
                        ret.extend(ungroup_years)
                        ret.extend(group_years[1:])  # Keep the first year in marker.
                    elif not group_years:
                        ret.append(ungroup_years[0])  # Keep first year for title.
                        if len(ungroup_years) > 2:
                            ret.extend(ungroup_years[2:])
        return ret

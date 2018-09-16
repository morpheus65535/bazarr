#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Processors
"""
from collections import defaultdict
import copy

import six

from rebulk import Rebulk, Rule, CustomRule, POST_PROCESS, PRE_PROCESS, AppendMatch, RemoveMatch

from .common import seps_no_groups
from .common.formatters import cleanup
from .common.comparators import marker_sorted
from .common.date import valid_year
from .common.words import iter_words


class EnlargeGroupMatches(CustomRule):
    """
    Enlarge matches that are starting and/or ending group to include brackets in their span.
    """
    priority = PRE_PROCESS

    def when(self, matches, context):
        starting = []
        ending = []

        for group in matches.markers.named('group'):
            for match in matches.starting(group.start + 1):
                starting.append(match)

            for match in matches.ending(group.end - 1):
                ending.append(match)

        return starting, ending

    def then(self, matches, when_response, context):
        starting, ending = when_response
        for match in starting:
            matches.remove(match)
            match.start -= 1
            match.raw_start += 1
            matches.append(match)

        for match in ending:
            matches.remove(match)
            match.end += 1
            match.raw_end -= 1
            matches.append(match)


class EquivalentHoles(Rule):
    """
    Creates equivalent matches for holes that have same values than existing (case insensitive)
    """
    priority = POST_PROCESS
    consequence = AppendMatch

    def when(self, matches, context):
        new_matches = []

        for filepath in marker_sorted(matches.markers.named('path'), matches):
            holes = matches.holes(start=filepath.start, end=filepath.end, formatter=cleanup)
            for name in matches.names:
                for hole in list(holes):
                    for current_match in matches.named(name):
                        if isinstance(current_match.value, six.string_types) and \
                                        hole.value.lower() == current_match.value.lower():
                            if 'equivalent-ignore' in current_match.tags:
                                continue
                            new_value = _preferred_string(hole.value, current_match.value)
                            if hole.value != new_value:
                                hole.value = new_value
                            if current_match.value != new_value:
                                current_match.value = new_value
                            hole.name = name
                            hole.tags = ['equivalent']
                            new_matches.append(hole)
                            if hole in holes:
                                holes.remove(hole)

        return new_matches


class RemoveAmbiguous(Rule):
    """
    If multiple matches are found with same name and different values, keep the one in the most valuable filepart.
    Also keep others match with same name and values than those kept ones.
    """

    priority = POST_PROCESS
    consequence = RemoveMatch

    def __init__(self, sort_function=marker_sorted, predicate=None):
        super(RemoveAmbiguous, self).__init__()
        self.sort_function = sort_function
        self.predicate = predicate

    def when(self, matches, context):
        fileparts = self.sort_function(matches.markers.named('path'), matches)

        previous_fileparts_names = set()
        values = defaultdict(list)

        to_remove = []
        for filepart in fileparts:
            filepart_matches = matches.range(filepart.start, filepart.end, predicate=self.predicate)

            filepart_names = set()
            for match in filepart_matches:
                filepart_names.add(match.name)
                if match.name in previous_fileparts_names:
                    if match.value not in values[match.name]:
                        to_remove.append(match)
                else:
                    if match.value not in values[match.name]:
                        values[match.name].append(match.value)

            previous_fileparts_names.update(filepart_names)

        return to_remove


class RemoveLessSpecificSeasonEpisode(RemoveAmbiguous):
    """
    If multiple season/episodes matches are found with different values,
    keep the one tagged as 'SxxExx' or in the rightmost filepart.
    """
    def __init__(self, name):
        super(RemoveLessSpecificSeasonEpisode, self).__init__(
            sort_function=(lambda markers, matches:
                           marker_sorted(list(reversed(markers)), matches,
                                         lambda match: match.name == name and 'SxxExx' in match.tags)),
            predicate=lambda match: match.name == name)


def _preferred_string(value1, value2):  # pylint:disable=too-many-return-statements
    """
    Retrieves preferred title from both values.
    :param value1:
    :type value1: str
    :param value2:
    :type value2: str
    :return: The preferred title
    :rtype: str
    """
    if value1 == value2:
        return value1
    if value1.istitle() and not value2.istitle():
        return value1
    if not value1.isupper() and value2.isupper():
        return value1
    if not value1.isupper() and value1[0].isupper() and not value2[0].isupper():
        return value1
    if _count_title_words(value1) > _count_title_words(value2):
        return value1
    return value2


def _count_title_words(value):
    """
    Count only many words are titles in value.
    :param value:
    :type value:
    :return:
    :rtype:
    """
    ret = 0
    for word in iter_words(value):
        if word.value.istitle():
            ret += 1
    return ret


class SeasonYear(Rule):
    """
    If a season is a valid year and no year was found, create an match with year.
    """
    priority = POST_PROCESS
    consequence = AppendMatch

    def when(self, matches, context):
        ret = []
        if not matches.named('year'):
            for season in matches.named('season'):
                if valid_year(season.value):
                    year = copy.copy(season)
                    year.name = 'year'
                    ret.append(year)
        return ret


class Processors(CustomRule):
    """
    Empty rule for ordering post_processing properly.
    """
    priority = POST_PROCESS

    def when(self, matches, context):
        pass

    def then(self, matches, when_response, context):  # pragma: no cover
        pass


class StripSeparators(CustomRule):
    """
    Strip separators from matches. Keep separators if they are from acronyms, like in ".S.H.I.E.L.D."
    """
    priority = POST_PROCESS

    def when(self, matches, context):
        return matches

    def then(self, matches, when_response, context):  # pragma: no cover
        for match in matches:
            for _ in range(0, len(match.span)):
                if match.raw[0] in seps_no_groups and (len(match.raw) < 3 or match.raw[2] not in seps_no_groups):
                    match.raw_start += 1

            for _ in reversed(range(0, len(match.span))):
                if match.raw[-1] in seps_no_groups and (len(match.raw) < 3 or match.raw[-3] not in seps_no_groups):
                    match.raw_end -= 1


def processors(config):  # pylint:disable=unused-argument
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    return Rebulk().rules(EnlargeGroupMatches, EquivalentHoles,
                          RemoveLessSpecificSeasonEpisode('season'),
                          RemoveLessSpecificSeasonEpisode('episode'),
                          RemoveAmbiguous, SeasonYear, Processors, StripSeparators)

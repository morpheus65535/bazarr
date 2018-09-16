#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comparators
"""
try:
    from functools import cmp_to_key
except ImportError:
    from ...backports import cmp_to_key


def marker_comparator_predicate(match):
    """
    Match predicate used in comparator
    """
    return (
        not match.private
        and match.name not in ('proper_count', 'title')
        and not (match.name == 'container' and 'extension' in match.tags)
        and not (match.name == 'other' and match.value == 'Rip')
    )


def marker_weight(matches, marker, predicate):
    """
    Compute the comparator weight of a marker
    :param matches:
    :param marker:
    :param predicate:
    :return:
    """
    return len(set(match.name for match in matches.range(*marker.span, predicate=predicate)))


def marker_comparator(matches, markers, predicate):
    """
    Builds a comparator that returns markers sorted from the most valuable to the less.

    Take the parts where matches count is higher, then when length is higher, then when position is at left.

    :param matches:
    :type matches:
    :param markers:
    :param predicate:
    :return:
    :rtype:
    """

    def comparator(marker1, marker2):
        """
        The actual comparator function.
        """
        matches_count = marker_weight(matches, marker2, predicate) - marker_weight(matches, marker1, predicate)
        if matches_count:
            return matches_count

        # give preference to rightmost path
        return markers.index(marker2) - markers.index(marker1)

    return comparator


def marker_sorted(markers, matches, predicate=marker_comparator_predicate):
    """
    Sort markers from matches, from the most valuable to the less.

    :param markers:
    :type markers:
    :param matches:
    :type matches:
    :param predicate:
    :return:
    :rtype:
    """
    return sorted(markers, key=cmp_to_key(marker_comparator(matches, markers, predicate=predicate)))

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
release_group property
"""
import copy

from rebulk import Rebulk, Rule, AppendMatch, RemoveMatch

from ..common import seps
from ..common.expected import build_expected_function
from ..common.comparators import marker_sorted
from ..common.formatters import cleanup
from ..common.validators import int_coercable, seps_surround
from ..properties.title import TitleFromPosition


def release_group():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk()

    expected_group = build_expected_function('expected_group')

    rebulk.functional(expected_group, name='release_group', tags=['expected'],
                      validator=seps_surround,
                      conflict_solver=lambda match, other: other,
                      disabled=lambda context: not context.get('expected_group'))

    return rebulk.rules(SceneReleaseGroup, AnimeReleaseGroup)


forbidden_groupnames = ['rip', 'by', 'for', 'par', 'pour', 'bonus']

groupname_ignore_seps = '[]{}()'
groupname_seps = ''.join([c for c in seps if c not in groupname_ignore_seps])


def clean_groupname(string):
    """
    Removes and strip separators from input_string
    :param string:
    :type string:
    :return:
    :rtype:
    """
    string = string.strip(groupname_seps)
    if not (string.endswith(tuple(groupname_ignore_seps)) and string.startswith(tuple(groupname_ignore_seps))) \
            and not any(i in string.strip(groupname_ignore_seps) for i in groupname_ignore_seps):
        string = string.strip(groupname_ignore_seps)
    for forbidden in forbidden_groupnames:
        if string.lower().startswith(forbidden) and string[len(forbidden):len(forbidden)+1] in seps:
            string = string[len(forbidden):]
            string = string.strip(groupname_seps)
        if string.lower().endswith(forbidden) and string[-len(forbidden)-1:-len(forbidden)] in seps:
            string = string[:len(forbidden)]
            string = string.strip(groupname_seps)
    return string


_scene_previous_names = ['video_codec', 'format', 'video_api', 'audio_codec', 'audio_profile', 'video_profile',
                         'audio_channels', 'screen_size', 'other', 'container', 'language', 'subtitle_language',
                         'subtitle_language.suffix', 'subtitle_language.prefix', 'language.suffix']

_scene_previous_tags = ['release-group-prefix']


class SceneReleaseGroup(Rule):
    """
    Add release_group match in existing matches (scene format).

    Something.XViD-ReleaseGroup.mkv
    """
    dependency = [TitleFromPosition]
    consequence = AppendMatch

    properties = {'release_group': [None]}

    def when(self, matches, context):
        # If a release_group is found before, ignore this kind of release_group rule.

        ret = []

        for filepart in marker_sorted(matches.markers.named('path'), matches):
            # pylint:disable=cell-var-from-loop
            start, end = filepart.span

            titles = matches.named('title', predicate=lambda m: m.start >= start and m.end <= end)

            def keep_only_first_title(match):
                """
                Keep only first title from this filepart, as other ones are most likely release group.

                :param match:
                :type match:
                :return:
                :rtype:
                """
                return match in titles[1:]

            last_hole = matches.holes(start, end + 1, formatter=clean_groupname,
                                      ignore=keep_only_first_title,
                                      predicate=lambda hole: cleanup(hole.value), index=-1)

            if last_hole:
                def previous_match_filter(match):
                    """
                    Filter to apply to find previous match

                    :param match:
                    :type match:
                    :return:
                    :rtype:
                    """

                    if match.start < filepart.start:
                        return False
                    return not match.private or match.name in _scene_previous_names

                previous_match = matches.previous(last_hole,
                                                  previous_match_filter,
                                                  index=0)
                if previous_match and (previous_match.name in _scene_previous_names or
                                       any(tag in previous_match.tags for tag in _scene_previous_tags)) and \
                        not matches.input_string[previous_match.end:last_hole.start].strip(seps) \
                        and not int_coercable(last_hole.value.strip(seps)):

                    last_hole.name = 'release_group'
                    last_hole.tags = ['scene']

                    # if hole is inside a group marker with same value, remove [](){} ...
                    group = matches.markers.at_match(last_hole, lambda marker: marker.name == 'group', 0)
                    if group:
                        group.formatter = clean_groupname
                        if group.value == last_hole.value:
                            last_hole.start = group.start + 1
                            last_hole.end = group.end - 1
                            last_hole.tags = ['anime']

                    ignored_matches = matches.range(last_hole.start, last_hole.end, keep_only_first_title)

                    for ignored_match in ignored_matches:
                        matches.remove(ignored_match)

                    ret.append(last_hole)
        return ret


class AnimeReleaseGroup(Rule):
    """
    Add release_group match in existing matches (anime format)
    ...[ReleaseGroup] Something.mkv
    """
    dependency = [SceneReleaseGroup, TitleFromPosition]
    consequence = [RemoveMatch, AppendMatch]

    properties = {'release_group': [None]}

    def when(self, matches, context):
        to_remove = []
        to_append = []

        # If a release_group is found before, ignore this kind of release_group rule.
        if matches.named('release_group'):
            return

        if not matches.named('episode') and not matches.named('season') and matches.named('release_group'):
            # This doesn't seems to be an anime, and we already found another release_group.
            return

        for filepart in marker_sorted(matches.markers.named('path'), matches):

            # pylint:disable=bad-continuation
            empty_group = matches.markers.range(filepart.start,
                                                filepart.end,
                                                lambda marker: (marker.name == 'group'
                                                                and not matches.range(marker.start, marker.end,
                                                                                      lambda m:
                                                                                      'weak-language' not in m.tags)
                                                                and marker.value.strip(seps)
                                                                and not int_coercable(marker.value.strip(seps))), 0)

            if empty_group:
                group = copy.copy(empty_group)
                group.marker = False
                group.raw_start += 1
                group.raw_end -= 1
                group.tags = ['anime']
                group.name = 'release_group'
                to_append.append(group)
                to_remove.extend(matches.range(empty_group.start, empty_group.end,
                                               lambda m: 'weak-language' in m.tags))
        return to_remove, to_append

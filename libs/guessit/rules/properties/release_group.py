#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
release_group property
"""
import copy

from rebulk import Rebulk, Rule, AppendMatch, RemoveMatch
from rebulk.match import Match

from ..common import seps
from ..common.comparators import marker_sorted
from ..common.expected import build_expected_function
from ..common.formatters import cleanup
from ..common.pattern import is_disabled
from ..common.validators import int_coercable, seps_surround
from ..properties.title import TitleFromPosition


def release_group(config):
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    forbidden_groupnames = config['forbidden_names']

    groupname_ignore_seps = config['ignored_seps']
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
            if string.lower().startswith(forbidden) and string[len(forbidden):len(forbidden) + 1] in seps:
                string = string[len(forbidden):]
                string = string.strip(groupname_seps)
            if string.lower().endswith(forbidden) and string[-len(forbidden) - 1:-len(forbidden)] in seps:
                string = string[:len(forbidden)]
                string = string.strip(groupname_seps)
        return string.strip()

    rebulk = Rebulk(disabled=lambda context: is_disabled(context, 'release_group'))

    expected_group = build_expected_function('expected_group')

    rebulk.functional(expected_group, name='release_group', tags=['expected'],
                      validator=seps_surround,
                      conflict_solver=lambda match, other: other,
                      disabled=lambda context: not context.get('expected_group'))

    return rebulk.rules(
        DashSeparatedReleaseGroup(clean_groupname),
        SceneReleaseGroup(clean_groupname),
        AnimeReleaseGroup
    )


_scene_previous_names = ('video_codec', 'source', 'video_api', 'audio_codec', 'audio_profile', 'video_profile',
                         'audio_channels', 'screen_size', 'other', 'container', 'language', 'subtitle_language',
                         'subtitle_language.suffix', 'subtitle_language.prefix', 'language.suffix')

_scene_previous_tags = ('release-group-prefix',)

_scene_no_previous_tags = ('no-release-group-prefix',)


class DashSeparatedReleaseGroup(Rule):
    """
    Detect dash separated release groups that might appear at the end or at the beginning of a release name.

    Series.S01E02.Pilot.DVDRip.x264-CS.mkv
        release_group: CS
    abc-the.title.name.1983.1080p.bluray.x264.mkv
        release_group: abc

    At the end: Release groups should be dash-separated and shouldn't contain spaces nor
    appear in a group with other matches. The preceding matches should be separated by dot.
    If a release group is found, the conflicting matches are removed.

    At the beginning: Release groups should be dash-separated and shouldn't contain spaces nor appear in a group.
    It should be followed by a hole with dot-separated words.
    Detection only happens if no matches exist at the beginning.
    """
    consequence = [RemoveMatch, AppendMatch]

    def __init__(self, value_formatter):
        """Default constructor."""
        super().__init__()
        self.value_formatter = value_formatter

    @classmethod
    def is_valid(cls, matches, candidate, start, end, at_end):  # pylint:disable=inconsistent-return-statements
        """
        Whether a candidate is a valid release group.
        """
        if not at_end:
            if len(candidate.value) <= 1:
                return False

            if matches.markers.at_match(candidate, predicate=lambda m: m.name == 'group'):
                return False

            first_hole = matches.holes(candidate.end, end, predicate=lambda m: m.start == candidate.end, index=0)
            if not first_hole:
                return False

            raw_value = first_hole.raw
            return raw_value[0] == '-' and '-' not in raw_value[1:] and '.' in raw_value and ' ' not in raw_value

        group = matches.markers.at_match(candidate, predicate=lambda m: m.name == 'group', index=0)
        if group and matches.at_match(group, predicate=lambda m: not m.private and m.span != candidate.span):
            return False

        count = 0
        match = candidate
        while match:
            current = matches.range(start,
                                    match.start,
                                    index=-1,
                                    predicate=lambda m: not m.private and not 'expected' in m.tags)
            if not current:
                break

            separator = match.input_string[current.end:match.start]
            if not separator and match.raw[0] == '-':
                separator = '-'

            match = current

            if count == 0:
                if separator != '-':
                    break

                count += 1
                continue

            if separator == '.':
                return True

    def detect(self, matches, start, end, at_end):  # pylint:disable=inconsistent-return-statements
        """
        Detect release group at the end or at the beginning of a filepart.
        """
        candidate = None
        if at_end:
            container = matches.ending(end, lambda m: m.name == 'container', index=0)
            if container:
                end = container.start

            candidate = matches.ending(end, index=0, predicate=(
                lambda m: not m.private and not (
                    m.name == 'other' and 'not-a-release-group' in m.tags
                ) and '-' not in m.raw and m.raw.strip() == m.raw))

        if not candidate:
            if at_end:
                candidate = matches.holes(start, end, seps=seps, index=-1,
                                          predicate=lambda m: m.end == end and m.raw.strip(seps) and m.raw[0] == '-')
            else:
                candidate = matches.holes(start, end, seps=seps, index=0,
                                          predicate=lambda m: m.start == start and m.raw.strip(seps))

        if candidate and self.is_valid(matches, candidate, start, end, at_end):
            return candidate

    def when(self, matches, context):  # pylint:disable=inconsistent-return-statements
        if matches.named('release_group'):
            return

        to_remove = []
        to_append = []
        for filepart in matches.markers.named('path'):
            candidate = self.detect(matches, filepart.start, filepart.end, True)
            if candidate:
                to_remove.extend(matches.at_match(candidate))
            else:
                candidate = self.detect(matches, filepart.start, filepart.end, False)

            if candidate:
                releasegroup = Match(candidate.start, candidate.end, name='release_group',
                                     formatter=self.value_formatter, input_string=candidate.input_string)

                if releasegroup.value:
                    to_append.append(releasegroup)
                if to_remove or to_append:
                    return to_remove, to_append


class SceneReleaseGroup(Rule):
    """
    Add release_group match in existing matches (scene format).

    Something.XViD-ReleaseGroup.mkv
    """
    dependency = [TitleFromPosition]
    consequence = AppendMatch

    properties = {'release_group': [None]}

    def __init__(self, value_formatter):
        """Default constructor."""
        super().__init__()
        self.value_formatter = value_formatter

    @staticmethod
    def is_previous_match(match):
        """
        Check if match can precede release_group

        :param match:
        :return:
        """
        return not match.tagged(*_scene_no_previous_tags) if match.name in _scene_previous_names else \
            match.tagged(*_scene_previous_tags)

    def when(self, matches, context):  # pylint:disable=too-many-locals
        # If a release_group is found before, ignore this kind of release_group rule.

        ret = []

        for filepart in marker_sorted(matches.markers.named('path'), matches):
            # pylint:disable=cell-var-from-loop
            start, end = filepart.span
            if matches.named('release_group', predicate=lambda m: m.start >= start and m.end <= end):
                continue

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

            last_hole = matches.holes(start, end + 1, formatter=self.value_formatter,
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
                    return not match.private or self.is_previous_match(match)

                previous_match = matches.previous(last_hole,
                                                  previous_match_filter,
                                                  index=0)
                if previous_match and (self.is_previous_match(previous_match)) and \
                        not matches.input_string[previous_match.end:last_hole.start].strip(seps) \
                        and not int_coercable(last_hole.value.strip(seps)):

                    last_hole.name = 'release_group'
                    last_hole.tags = ['scene']

                    # if hole is inside a group marker with same value, remove [](){} ...
                    group = matches.markers.at_match(last_hole, lambda marker: marker.name == 'group', 0)
                    if group:
                        group.formatter = self.value_formatter
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
            return False

        if not matches.named('episode') and not matches.named('season') and matches.named('release_group'):
            # This doesn't seems to be an anime, and we already found another release_group.
            return False

        for filepart in marker_sorted(matches.markers.named('path'), matches):

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

        if to_remove or to_append:
            return to_remove, to_append
        return False

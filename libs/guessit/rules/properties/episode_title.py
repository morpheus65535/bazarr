#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Episode title
"""
from collections import defaultdict

from rebulk import Rebulk, Rule, AppendMatch, RemoveMatch, RenameMatch, POST_PROCESS

from ..common import seps, title_seps
from ..common.formatters import cleanup
from ..common.pattern import is_disabled
from ..properties.title import TitleFromPosition, TitleBaseRule
from ..properties.type import TypeProcessor


def episode_title(config):  # pylint:disable=unused-argument
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    previous_names = ('episode', 'episode_details', 'episode_count',
                      'season', 'season_count', 'date', 'title', 'year')

    rebulk = Rebulk(disabled=lambda context: is_disabled(context, 'episode_title'))
    rebulk = rebulk.rules(RemoveConflictsWithEpisodeTitle(previous_names),
                          EpisodeTitleFromPosition(previous_names),
                          AlternativeTitleReplace(previous_names),
                          TitleToEpisodeTitle,
                          Filepart3EpisodeTitle,
                          Filepart2EpisodeTitle,
                          RenameEpisodeTitleWhenMovieType)
    return rebulk


class RemoveConflictsWithEpisodeTitle(Rule):
    """
    Remove conflicting matches that might lead to wrong episode_title parsing.
    """

    priority = 64
    consequence = RemoveMatch

    def __init__(self, previous_names):
        super(RemoveConflictsWithEpisodeTitle, self).__init__()
        self.previous_names = previous_names
        self.next_names = ('streaming_service', 'screen_size', 'source',
                           'video_codec', 'audio_codec', 'other', 'container')
        self.affected_if_holes_after = ('part', )
        self.affected_names = ('part', 'year')

    def when(self, matches, context):
        to_remove = []
        for filepart in matches.markers.named('path'):
            for match in matches.range(filepart.start, filepart.end,
                                       predicate=lambda m: m.name in self.affected_names):
                before = matches.range(filepart.start, match.start, predicate=lambda m: not m.private, index=-1)
                if not before or before.name not in self.previous_names:
                    continue

                after = matches.range(match.end, filepart.end, predicate=lambda m: not m.private, index=0)
                if not after or after.name not in self.next_names:
                    continue

                group = matches.markers.at_match(match, predicate=lambda m: m.name == 'group', index=0)

                def has_value_in_same_group(current_match, current_group=group):
                    """Return true if current match has value and belongs to the current group."""
                    return current_match.value.strip(seps) and (
                        current_group == matches.markers.at_match(current_match,
                                                                  predicate=lambda mm: mm.name == 'group', index=0)
                    )

                holes_before = matches.holes(before.end, match.start, predicate=has_value_in_same_group)
                holes_after = matches.holes(match.end, after.start, predicate=has_value_in_same_group)

                if not holes_before and not holes_after:
                    continue

                if match.name in self.affected_if_holes_after and not holes_after:
                    continue

                to_remove.append(match)
                if match.parent:
                    to_remove.append(match.parent)

        return to_remove


class TitleToEpisodeTitle(Rule):
    """
    If multiple different title are found, convert the one following episode number to episode_title.
    """
    dependency = TitleFromPosition

    def when(self, matches, context):
        titles = matches.named('title')
        title_groups = defaultdict(list)
        for title in titles:
            title_groups[title.value].append(title)

        episode_titles = []
        if len(title_groups) < 2:
            return episode_titles

        for title in titles:
            if matches.previous(title, lambda match: match.name == 'episode'):
                episode_titles.append(title)

        return episode_titles

    def then(self, matches, when_response, context):
        for title in when_response:
            matches.remove(title)
            title.name = 'episode_title'
            matches.append(title)


class EpisodeTitleFromPosition(TitleBaseRule):
    """
    Add episode title match in existing matches
    Must run after TitleFromPosition rule.
    """
    dependency = TitleToEpisodeTitle

    def __init__(self, previous_names):
        super(EpisodeTitleFromPosition, self).__init__('episode_title', ['title'])
        self.previous_names = previous_names

    def hole_filter(self, hole, matches):
        episode = matches.previous(hole,
                                   lambda previous: any(name in previous.names
                                                        for name in self.previous_names),
                                   0)

        crc32 = matches.named('crc32')

        return episode or crc32

    def filepart_filter(self, filepart, matches):
        # Filepart where title was found.
        if matches.range(filepart.start, filepart.end, lambda match: match.name == 'title'):
            return True
        return False

    def should_remove(self, match, matches, filepart, hole, context):
        if match.name == 'episode_details':
            return False
        return super(EpisodeTitleFromPosition, self).should_remove(match, matches, filepart, hole, context)

    def when(self, matches, context):  # pylint:disable=inconsistent-return-statements
        if matches.named('episode_title'):
            return
        return super(EpisodeTitleFromPosition, self).when(matches, context)


class AlternativeTitleReplace(Rule):
    """
    If alternateTitle was found and title is next to episode, season or date, replace it with episode_title.
    """
    dependency = EpisodeTitleFromPosition
    consequence = RenameMatch

    def __init__(self, previous_names):
        super(AlternativeTitleReplace, self).__init__()
        self.previous_names = previous_names

    def when(self, matches, context):  # pylint:disable=inconsistent-return-statements
        if matches.named('episode_title'):
            return

        alternative_title = matches.range(predicate=lambda match: match.name == 'alternative_title', index=0)
        if alternative_title:
            main_title = matches.chain_before(alternative_title.start, seps=seps,
                                              predicate=lambda match: 'title' in match.tags, index=0)
            if main_title:
                episode = matches.previous(main_title,
                                           lambda previous: any(name in previous.names
                                                                for name in self.previous_names),
                                           0)

                crc32 = matches.named('crc32')

                if episode or crc32:
                    return alternative_title

    def then(self, matches, when_response, context):
        matches.remove(when_response)
        when_response.name = 'episode_title'
        when_response.tags.append('alternative-replaced')
        matches.append(when_response)


class RenameEpisodeTitleWhenMovieType(Rule):
    """
    Rename episode_title by alternative_title when type is movie.
    """
    priority = POST_PROCESS

    dependency = TypeProcessor
    consequence = RenameMatch

    def when(self, matches, context):  # pylint:disable=inconsistent-return-statements
        if matches.named('episode_title', lambda m: 'alternative-replaced' not in m.tags) \
                and not matches.named('type', lambda m: m.value == 'episode'):
            return matches.named('episode_title')

    def then(self, matches, when_response, context):
        for match in when_response:
            matches.remove(match)
            match.name = 'alternative_title'
            matches.append(match)


class Filepart3EpisodeTitle(Rule):
    """
    If we have at least 3 filepart structured like this:

    Serie name/SO1/E01-episode_title.mkv
    AAAAAAAAAA/BBB/CCCCCCCCCCCCCCCCCCCC

    If CCCC contains episode and BBB contains seasonNumber
    Then title is to be found in AAAA.
    """
    consequence = AppendMatch('title')

    def when(self, matches, context):  # pylint:disable=inconsistent-return-statements
        fileparts = matches.markers.named('path')
        if len(fileparts) < 3:
            return

        filename = fileparts[-1]
        directory = fileparts[-2]
        subdirectory = fileparts[-3]

        episode_number = matches.range(filename.start, filename.end, lambda match: match.name == 'episode', 0)
        if episode_number:
            season = matches.range(directory.start, directory.end, lambda match: match.name == 'season', 0)

            if season:
                hole = matches.holes(subdirectory.start, subdirectory.end,
                                     formatter=cleanup, seps=title_seps, predicate=lambda match: match.value,
                                     index=0)
                if hole:
                    return hole


class Filepart2EpisodeTitle(Rule):
    """
    If we have at least 2 filepart structured like this:

    Serie name SO1/E01-episode_title.mkv
    AAAAAAAAAAAAA/BBBBBBBBBBBBBBBBBBBBB

    If BBBB contains episode and AAA contains a hole followed by seasonNumber
    then title is to be found in AAAA.

    or

    Serie name/SO1E01-episode_title.mkv
    AAAAAAAAAA/BBBBBBBBBBBBBBBBBBBBB

    If BBBB contains season and episode and AAA contains a hole
    then title is to be found in AAAA.
    """
    consequence = AppendMatch('title')

    def when(self, matches, context):  # pylint:disable=inconsistent-return-statements
        fileparts = matches.markers.named('path')
        if len(fileparts) < 2:
            return

        filename = fileparts[-1]
        directory = fileparts[-2]

        episode_number = matches.range(filename.start, filename.end, lambda match: match.name == 'episode', 0)
        if episode_number:
            season = (matches.range(directory.start, directory.end, lambda match: match.name == 'season', 0) or
                      matches.range(filename.start, filename.end, lambda match: match.name == 'season', 0))
            if season:
                hole = matches.holes(directory.start, directory.end, formatter=cleanup, seps=title_seps,
                                     predicate=lambda match: match.value, index=0)
                if hole:
                    return hole

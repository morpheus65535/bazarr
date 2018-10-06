#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
episode, season, episode_count, season_count and episode_details properties
"""
import copy
from collections import defaultdict

from rebulk import Rebulk, RemoveMatch, Rule, AppendMatch, RenameMatch
from rebulk.match import Match
from rebulk.remodule import re
from rebulk.utils import is_iterable

from .title import TitleFromPosition
from ..common import dash, alt_dash, seps
from ..common.formatters import strip
from ..common.numeral import numeral, parse_numeral
from ..common.validators import compose, seps_surround, seps_before, int_coercable
from ...reutils import build_or_pattern


def episodes():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    rebulk = Rebulk()
    rebulk.regex_defaults(flags=re.IGNORECASE).string_defaults(ignore_case=True)
    rebulk.defaults(private_names=['episodeSeparator', 'seasonSeparator', 'episodeMarker', 'seasonMarker'])

    def episodes_season_chain_breaker(matches):
        """
        Break chains if there's more than 100 offset between two neighbor values.
        :param matches:
        :type matches:
        :return:
        :rtype:
        """
        eps = matches.named('episode')
        if len(eps) > 1 and abs(eps[-1].value - eps[-2].value) > 100:
            return True

        seasons = matches.named('season')
        if len(seasons) > 1 and abs(seasons[-1].value - seasons[-2].value) > 100:
            return True
        return False

    rebulk.chain_defaults(chain_breaker=episodes_season_chain_breaker)

    def season_episode_conflict_solver(match, other):
        """
        Conflict solver for episode/season patterns

        :param match:
        :param other:
        :return:
        """
        if match.name == 'episode' and other.name in \
                ['screen_size', 'video_codec', 'audio_codec', 'audio_channels', 'container', 'date', 'year'] \
                and 'weak-audio_channels' not in other.tags:
            return match
        if match.name == 'season' and other.name in \
                ['screen_size', 'video_codec', 'audio_codec', 'audio_channels', 'container', 'date'] \
                and 'weak-audio_channels' not in other.tags:
            return match
        if match.name in ['season', 'episode'] and other.name in ['season', 'episode'] \
                and match.initiator != other.initiator:
            if 'weak-episode' in match.tags or 'x' in match.initiator.raw.lower():
                return match
            if 'weak-episode' in other.tags or 'x' in other.initiator.raw.lower():
                return other
        return '__default__'

    season_episode_seps = []
    season_episode_seps.extend(seps)
    season_episode_seps.extend(['x', 'X', 'e', 'E'])

    season_words = ['season', 'saison', 'seizoen', 'serie', 'seasons', 'saisons', 'series',
                    'tem', 'temp', 'temporada', 'temporadas', 'stagione']
    episode_words = ['episode', 'episodes', 'eps', 'ep', 'episodio',
                     'episodios', 'capitulo', 'capitulos']
    of_words = ['of', 'sur']
    all_words = ['All']
    season_markers = ["S"]
    season_ep_markers = ["x"]
    episode_markers = ["xE", "Ex", "EP", "E", "x"]
    range_separators = ['-', '~', 'to', 'a']
    weak_discrete_separators = list(sep for sep in seps if sep not in range_separators)
    strong_discrete_separators = ['+', '&', 'and', 'et']
    discrete_separators = strong_discrete_separators + weak_discrete_separators

    def ordering_validator(match):
        """
        Validator for season list. They should be in natural order to be validated.

        episode/season separated by a weak discrete separator should be consecutive, unless a strong discrete separator
        or a range separator is present in the chain (1.3&5 is valid, but 1.3-5 is not valid and 1.3.5 is not valid)
        """
        values = match.children.to_dict()
        if 'season' in values and is_iterable(values['season']):
            # Season numbers must be in natural order to be validated.
            if not list(sorted(values['season'])) == values['season']:
                return False
        if 'episode' in values and is_iterable(values['episode']):
            # Season numbers must be in natural order to be validated.
            if not list(sorted(values['episode'])) == values['episode']:
                return False

        def is_consecutive(property_name):
            """
            Check if the property season or episode has valid consecutive values.
            :param property_name:
            :type property_name:
            :return:
            :rtype:
            """
            previous_match = None
            valid = True
            for current_match in match.children.named(property_name):
                if previous_match:
                    match.children.previous(current_match,
                                            lambda m: m.name == property_name + 'Separator')
                    separator = match.children.previous(current_match,
                                                        lambda m: m.name == property_name + 'Separator', 0)
                    if separator.raw not in range_separators and separator.raw in weak_discrete_separators:
                        if not current_match.value - previous_match.value == 1:
                            valid = False
                    if separator.raw in strong_discrete_separators:
                        valid = True
                        break
                previous_match = current_match
            return valid

        return is_consecutive('episode') and is_consecutive('season')

    # S01E02, 01x02, S01S02S03
    rebulk.chain(formatter={'season': int, 'episode': int},
                 tags=['SxxExx'],
                 abbreviations=[alt_dash],
                 children=True,
                 private_parent=True,
                 validate_all=True,
                 validator={'__parent__': ordering_validator},
                 conflict_solver=season_episode_conflict_solver) \
        .regex(build_or_pattern(season_markers, name='seasonMarker') + r'(?P<season>\d+)@?' +
               build_or_pattern(episode_markers, name='episodeMarker') + r'@?(?P<episode>\d+)',
               validate_all=True,
               validator={'__parent__': seps_before}).repeater('+') \
        .regex(build_or_pattern(episode_markers + discrete_separators + range_separators,
                                name='episodeSeparator',
                                escape=True) +
               r'(?P<episode>\d+)').repeater('*') \
        .chain() \
        .regex(r'(?P<season>\d+)@?' +
               build_or_pattern(season_ep_markers, name='episodeMarker') +
               r'@?(?P<episode>\d+)',
               validate_all=True,
               validator={'__parent__': seps_before}) \
        .chain() \
        .regex(r'(?P<season>\d+)@?' +
               build_or_pattern(season_ep_markers, name='episodeMarker') +
               r'@?(?P<episode>\d+)',
               validate_all=True,
               validator={'__parent__': seps_before}) \
        .regex(build_or_pattern(season_ep_markers + discrete_separators + range_separators,
                                name='episodeSeparator',
                                escape=True) +
               r'(?P<episode>\d+)').repeater('*') \
        .chain() \
        .regex(build_or_pattern(season_markers, name='seasonMarker') + r'(?P<season>\d+)',
               validate_all=True,
               validator={'__parent__': seps_before}) \
        .regex(build_or_pattern(season_markers + discrete_separators + range_separators,
                                name='seasonSeparator',
                                escape=True) +
               r'(?P<season>\d+)').repeater('*')

    # episode_details property
    for episode_detail in ('Special', 'Bonus', 'Omake', 'Ova', 'Oav', 'Pilot', 'Unaired'):
        rebulk.string(episode_detail, value=episode_detail, name='episode_details')
    rebulk.regex(r'Extras?', name='episode_details', value='Extras')

    def validate_roman(match):
        """
        Validate a roman match if surrounded by separators
        :param match:
        :type match:
        :return:
        :rtype:
        """
        if int_coercable(match.raw):
            return True
        return seps_surround(match)

    rebulk.defaults(private_names=['episodeSeparator', 'seasonSeparator', 'episodeMarker', 'seasonMarker'],
                    validate_all=True, validator={'__parent__': seps_surround}, children=True, private_parent=True,
                    conflict_solver=season_episode_conflict_solver)

    rebulk.chain(abbreviations=[alt_dash],
                 formatter={'season': parse_numeral, 'count': parse_numeral},
                 validator={'__parent__': compose(seps_surround, ordering_validator),
                            'season': validate_roman,
                            'count': validate_roman}) \
        .defaults(validator=None) \
        .regex(build_or_pattern(season_words, name='seasonMarker') + '@?(?P<season>' + numeral + ')') \
        .regex(r'' + build_or_pattern(of_words) + '@?(?P<count>' + numeral + ')').repeater('?') \
        .regex(r'@?' + build_or_pattern(range_separators + discrete_separators + ['@'],
                                        name='seasonSeparator', escape=True) +
               r'@?(?P<season>\d+)').repeater('*')

    rebulk.regex(build_or_pattern(episode_words, name='episodeMarker') + r'-?(?P<episode>\d+)' +
                 r'(?:v(?P<version>\d+))?' +
                 r'(?:-?' + build_or_pattern(of_words) + r'-?(?P<count>\d+))?',  # Episode 4
                 abbreviations=[dash], formatter={'episode': int, 'version': int, 'count': int},
                 disabled=lambda context: context.get('type') == 'episode')

    rebulk.regex(build_or_pattern(episode_words, name='episodeMarker') + r'-?(?P<episode>' + numeral + ')' +
                 r'(?:v(?P<version>\d+))?' +
                 r'(?:-?' + build_or_pattern(of_words) + r'-?(?P<count>\d+))?',  # Episode 4
                 abbreviations=[dash],
                 validator={'episode': validate_roman},
                 formatter={'episode': parse_numeral, 'version': int, 'count': int},
                 disabled=lambda context: context.get('type') != 'episode')

    rebulk.regex(r'S?(?P<season>\d+)-?(?:xE|Ex|E|x)-?(?P<other>' + build_or_pattern(all_words) + ')',
                 tags=['SxxExx'],
                 abbreviations=[dash],
                 validator=None,
                 formatter={'season': int, 'other': lambda match: 'Complete'})

    # 12, 13
    rebulk.chain(tags=['bonus-conflict', 'weak-movie', 'weak-episode'], formatter={'episode': int, 'version': int},
                 disabled=lambda context: context.get('type') == 'movie') \
        .defaults(validator=None) \
        .regex(r'(?P<episode>\d{2})') \
        .regex(r'v(?P<version>\d+)').repeater('?') \
        .regex(r'(?P<episodeSeparator>[x-])(?P<episode>\d{2})').repeater('*')

    # 012, 013
    rebulk.chain(tags=['bonus-conflict', 'weak-movie', 'weak-episode'], formatter={'episode': int, 'version': int},
                 disabled=lambda context: context.get('type') == 'movie') \
        .defaults(validator=None) \
        .regex(r'0(?P<episode>\d{1,2})') \
        .regex(r'v(?P<version>\d+)').repeater('?') \
        .regex(r'(?P<episodeSeparator>[x-])0(?P<episode>\d{1,2})').repeater('*')

    # 112, 113
    rebulk.chain(tags=['bonus-conflict', 'weak-movie', 'weak-episode'], formatter={'episode': int, 'version': int},
                 disabled=lambda context: (not context.get('episode_prefer_number', False) or
                                           context.get('type') == 'movie')) \
        .defaults(validator=None) \
        .regex(r'(?P<episode>\d{3,4})') \
        .regex(r'v(?P<version>\d+)').repeater('?') \
        .regex(r'(?P<episodeSeparator>[x-])(?P<episode>\d{3,4})').repeater('*')

    # 1, 2, 3
    rebulk.chain(tags=['bonus-conflict', 'weak-movie', 'weak-episode'], formatter={'episode': int, 'version': int},
                 disabled=lambda context: context.get('type') != 'episode') \
        .defaults(validator=None) \
        .regex(r'(?P<episode>\d)') \
        .regex(r'v(?P<version>\d+)').repeater('?') \
        .regex(r'(?P<episodeSeparator>[x-])(?P<episode>\d{1,2})').repeater('*')

    # e112, e113
    # TODO: Enhance rebulk for validator to be used globally (season_episode_validator)
    rebulk.chain(formatter={'episode': int, 'version': int}) \
        .defaults(validator=None) \
        .regex(r'(?P<episodeMarker>e)(?P<episode>\d{1,4})') \
        .regex(r'v(?P<version>\d+)').repeater('?') \
        .regex(r'(?P<episodeSeparator>e|x|-)(?P<episode>\d{1,4})').repeater('*')

    # ep 112, ep113, ep112, ep113
    rebulk.chain(abbreviations=[dash], formatter={'episode': int, 'version': int}) \
        .defaults(validator=None) \
        .regex(r'ep-?(?P<episode>\d{1,4})') \
        .regex(r'v(?P<version>\d+)').repeater('?') \
        .regex(r'(?P<episodeSeparator>ep|e|x|-)(?P<episode>\d{1,4})').repeater('*')

    # cap 112, cap 112_114
    rebulk.chain(abbreviations=[dash],
                 tags=['see-pattern'],
                 formatter={'season': int, 'episode': int}) \
        .defaults(validator=None) \
        .regex(r'(?P<seasonMarker>cap)-?(?P<season>\d{1,2})(?P<episode>\d{2})') \
        .regex(r'(?P<episodeSeparator>-)(?P<season>\d{1,2})(?P<episode>\d{2})').repeater('?')

    # 102, 0102
    rebulk.chain(tags=['bonus-conflict', 'weak-movie', 'weak-episode', 'weak-duplicate'],
                 formatter={'season': int, 'episode': int, 'version': int},
                 conflict_solver=lambda match, other: match if other.name == 'year' else '__default__',
                 disabled=lambda context: (context.get('episode_prefer_number', False) or
                                           context.get('type') == 'movie')) \
        .defaults(validator=None) \
        .regex(r'(?P<season>\d{1,2})(?P<episode>\d{2})') \
        .regex(r'v(?P<version>\d+)').repeater('?') \
        .regex(r'(?P<episodeSeparator>x|-)(?P<episode>\d{2})').repeater('*')

    rebulk.regex(r'v(?P<version>\d+)', children=True, private_parent=True, formatter=int)

    rebulk.defaults(private_names=['episodeSeparator', 'seasonSeparator'])

    # TODO: List of words
    # detached of X count (season/episode)
    rebulk.regex(r'(?P<episode>\d+)-?' + build_or_pattern(of_words) +
                 r'-?(?P<count>\d+)-?' + build_or_pattern(episode_words) + '?',
                 abbreviations=[dash], children=True, private_parent=True, formatter=int)

    rebulk.regex(r'Minisodes?', name='episode_format', value="Minisode")

    rebulk.rules(RemoveInvalidSeason, RemoveInvalidEpisode,
                 SeePatternRange(range_separators + ['_']), EpisodeNumberSeparatorRange(range_separators),
                 SeasonSeparatorRange(range_separators), RemoveWeakIfMovie, RemoveWeakIfSxxExx,
                 RemoveWeakDuplicate, EpisodeDetailValidator, RemoveDetachedEpisodeNumber, VersionValidator,
                 CountValidator, EpisodeSingleDigitValidator)

    return rebulk


class CountValidator(Rule):
    """
    Validate count property and rename it
    """
    priority = 64
    consequence = [RemoveMatch, RenameMatch('episode_count'), RenameMatch('season_count')]

    properties = {'episode_count': [None], 'season_count': [None]}

    def when(self, matches, context):
        to_remove = []
        episode_count = []
        season_count = []

        for count in matches.named('count'):
            previous = matches.previous(count, lambda match: match.name in ['episode', 'season'], 0)
            if previous:
                if previous.name == 'episode':
                    episode_count.append(count)
                elif previous.name == 'season':
                    season_count.append(count)
            else:
                to_remove.append(count)
        return to_remove, episode_count, season_count


class SeePatternRange(Rule):
    """
    Create matches for episode range for SEE pattern. E.g.: Cap.102_104
    """
    priority = 128
    consequence = [RemoveMatch, AppendMatch]

    def __init__(self, range_separators):
        super(SeePatternRange, self).__init__()
        self.range_separators = range_separators

    def when(self, matches, context):
        to_remove = []
        to_append = []

        for separator in matches.tagged('see-pattern', lambda m: m.name == 'episodeSeparator'):
            previous_match = matches.previous(separator, lambda m: m.name == 'episode' and 'see-pattern' in m.tags, 0)
            next_match = matches.next(separator, lambda m: m.name == 'season' and 'see-pattern' in m.tags, 0)
            if not next_match:
                continue

            next_match = matches.next(next_match, lambda m: m.name == 'episode' and 'see-pattern' in m.tags, 0)
            if previous_match and next_match and separator.value in self.range_separators:
                to_remove.append(next_match)

                for episode_number in range(previous_match.value + 1, next_match.value + 1):
                    match = copy.copy(next_match)
                    match.value = episode_number
                    to_append.append(match)

            to_remove.append(separator)

        return to_remove, to_append


class AbstractSeparatorRange(Rule):
    """
    Remove separator matches and create matches for season range.
    """
    priority = 128
    consequence = [RemoveMatch, AppendMatch]

    def __init__(self, range_separators, property_name):
        super(AbstractSeparatorRange, self).__init__()
        self.range_separators = range_separators
        self.property_name = property_name

    def when(self, matches, context):
        to_remove = []
        to_append = []

        for separator in matches.named(self.property_name + 'Separator'):
            previous_match = matches.previous(separator, lambda match: match.name == self.property_name, 0)
            next_match = matches.next(separator, lambda match: match.name == self.property_name, 0)

            if previous_match and next_match and separator.value in self.range_separators:
                to_remove.append(next_match)
                for episode_number in range(previous_match.value + 1, next_match.value):
                    match = copy.copy(next_match)
                    match.value = episode_number
                    to_append.append(match)
                to_append.append(next_match)
            to_remove.append(separator)

        previous_match = None
        for next_match in matches.named(self.property_name):
            if previous_match:
                separator = matches.input_string[previous_match.initiator.end:next_match.initiator.start]
                if separator not in self.range_separators:
                    separator = strip(separator)
                if separator in self.range_separators:
                    for episode_number in range(previous_match.value + 1, next_match.value):
                        match = copy.copy(next_match)
                        match.value = episode_number
                        to_append.append(match)
                    to_append.append(Match(previous_match.end, next_match.start - 1,
                                           name=self.property_name + 'Separator',
                                           private=True,
                                           input_string=matches.input_string))
                to_remove.append(next_match)  # Remove and append match to support proper ordering
                to_append.append(next_match)

            previous_match = next_match

        return to_remove, to_append


class EpisodeNumberSeparatorRange(AbstractSeparatorRange):
    """
    Remove separator matches and create matches for episoderNumber range.
    """
    priority = 128
    consequence = [RemoveMatch, AppendMatch]

    def __init__(self, range_separators):
        super(EpisodeNumberSeparatorRange, self).__init__(range_separators, "episode")


class SeasonSeparatorRange(AbstractSeparatorRange):
    """
    Remove separator matches and create matches for season range.
    """
    priority = 128
    consequence = [RemoveMatch, AppendMatch]

    def __init__(self, range_separators):
        super(SeasonSeparatorRange, self).__init__(range_separators, "season")


class RemoveWeakIfMovie(Rule):
    """
    Remove weak-movie tagged matches if it seems to be a movie.
    """
    priority = 64
    consequence = RemoveMatch

    def enabled(self, context):
        return context.get('type') != 'episode'

    def when(self, matches, context):
        to_remove = []
        to_ignore = set()
        remove = False
        for filepart in matches.markers.named('path'):
            year = matches.range(filepart.start, filepart.end, predicate=lambda m: m.name == 'year', index=0)
            if year:
                remove = True
                next_match = matches.next(year, predicate=lambda m, fp=filepart: m.private and m.end <= fp.end, index=0)
                if next_match and not matches.at_match(next_match, predicate=lambda m: m.name == 'year'):
                    to_ignore.add(next_match.initiator)

        if remove:
            to_remove.extend(matches.tagged('weak-movie', predicate=lambda m: m.initiator not in to_ignore))

        return to_remove


class RemoveWeakIfSxxExx(Rule):
    """
    Remove weak-movie tagged matches if SxxExx pattern is matched.
    """
    priority = 64
    consequence = RemoveMatch

    def when(self, matches, context):
        to_remove = []
        for filepart in matches.markers.named('path'):
            if matches.range(filepart.start, filepart.end,
                             predicate=lambda match: not match.private and 'SxxExx' in match.tags):
                to_remove.extend(matches.range(
                    filepart.start, filepart.end, predicate=lambda match: 'weak-movie' in match.tags))
        return to_remove


class RemoveInvalidSeason(Rule):
    """
    Remove invalid season matches.
    """
    priority = 64
    consequence = RemoveMatch

    def when(self, matches, context):
        to_remove = []
        for filepart in matches.markers.named('path'):
            strong_season = matches.range(filepart.start, filepart.end, index=0,
                                          predicate=lambda m: m.name == 'season'
                                          and not m.private and 'SxxExx' in m.tags)
            if strong_season:
                if strong_season.initiator.children.named('episode'):
                    for season in matches.range(strong_season.end, filepart.end,
                                                predicate=lambda m: m.name == 'season' and not m.private):
                        # remove weak season or seasons without episode matches
                        if 'SxxExx' not in season.tags or not season.initiator.children.named('episode'):
                            if season.initiator:
                                to_remove.append(season.initiator)
                                to_remove.extend(season.initiator.children)
                            else:
                                to_remove.append(season)

        return to_remove


class RemoveInvalidEpisode(Rule):
    """
    Remove invalid episode matches.
    """
    priority = 64
    consequence = RemoveMatch

    def when(self, matches, context):
        to_remove = []
        for filepart in matches.markers.named('path'):
            strong_episode = matches.range(filepart.start, filepart.end, index=0,
                                           predicate=lambda m: m.name == 'episode'
                                           and not m.private and 'SxxExx' in m.tags)
            if strong_episode:
                strong_ep_marker = RemoveInvalidEpisode.get_episode_prefix(matches, strong_episode)
                for episode in matches.range(strong_episode.end, filepart.end,
                                             predicate=lambda m: m.name == 'episode' and not m.private):
                    ep_marker = RemoveInvalidEpisode.get_episode_prefix(matches, episode)
                    if strong_ep_marker and ep_marker and strong_ep_marker.value.lower() != ep_marker.value.lower():
                        if episode.initiator:
                            to_remove.append(episode.initiator)
                            to_remove.extend(episode.initiator.children)
                        else:
                            to_remove.append(ep_marker)
                            to_remove.append(episode)

        return to_remove

    @staticmethod
    def get_episode_prefix(matches, episode):
        """
        Return episode prefix: episodeMarker or episodeSeparator
        """
        return matches.previous(episode, index=0,
                                predicate=lambda m: m.name in ('episodeMarker', 'episodeSeparator'))


class RemoveWeakDuplicate(Rule):
    """
    Remove weak-duplicate tagged matches if duplicate patterns, for example The 100.109
    """
    priority = 64
    consequence = RemoveMatch

    def when(self, matches, context):
        to_remove = []
        for filepart in matches.markers.named('path'):
            patterns = defaultdict(list)
            for match in reversed(matches.range(filepart.start, filepart.end,
                                                predicate=lambda match: 'weak-duplicate' in match.tags)):
                if match.pattern in patterns[match.name]:
                    to_remove.append(match)
                else:
                    patterns[match.name].append(match.pattern)
        return to_remove


class EpisodeDetailValidator(Rule):
    """
    Validate episode_details if they are detached or next to season or episode.
    """
    priority = 64
    consequence = RemoveMatch

    def when(self, matches, context):
        ret = []
        for detail in matches.named('episode_details'):
            if not seps_surround(detail) \
                    and not matches.previous(detail, lambda match: match.name in ['season', 'episode']) \
                    and not matches.next(detail, lambda match: match.name in ['season', 'episode']):
                ret.append(detail)
        return ret


class RemoveDetachedEpisodeNumber(Rule):
    """
    If multiple episode are found, remove those that are not detached from a range and less than 10.

    Fairy Tail 2 - 16-20, 2 should be removed.
    """
    priority = 64
    consequence = RemoveMatch
    dependency = [RemoveWeakIfSxxExx, RemoveWeakDuplicate]

    def when(self, matches, context):
        ret = []

        episode_numbers = []
        episode_values = set()
        for match in matches.named('episode', lambda match: not match.private and 'weak-movie' in match.tags):
            if match.value not in episode_values:
                episode_numbers.append(match)
                episode_values.add(match.value)

        episode_numbers = list(sorted(episode_numbers, key=lambda match: match.value))
        if len(episode_numbers) > 1 and \
                        episode_numbers[0].value < 10 and \
                                episode_numbers[1].value - episode_numbers[0].value != 1:
            parent = episode_numbers[0]
            while parent:  # TODO: Add a feature in rebulk to avoid this ...
                ret.append(parent)
                parent = parent.parent
        return ret


class VersionValidator(Rule):
    """
    Validate version if previous match is episode or if surrounded by separators.
    """
    priority = 64
    dependency = [RemoveWeakIfMovie, RemoveWeakIfSxxExx]
    consequence = RemoveMatch

    def when(self, matches, context):
        ret = []
        for version in matches.named('version'):
            episode_number = matches.previous(version, lambda match: match.name == 'episode', 0)
            if not episode_number and not seps_surround(version.initiator):
                ret.append(version)
        return ret


class EpisodeSingleDigitValidator(Rule):
    """
    Remove single digit episode when inside a group that doesn't own title.
    """
    dependency = [TitleFromPosition]

    consequence = RemoveMatch

    def when(self, matches, context):
        ret = []
        for episode in matches.named('episode', lambda match: len(match.initiator) == 1):
            group = matches.markers.at_match(episode, lambda marker: marker.name == 'group', index=0)
            if group:
                if not matches.range(*group.span, predicate=lambda match: match.name == 'title'):
                    ret.append(episode)
        return ret

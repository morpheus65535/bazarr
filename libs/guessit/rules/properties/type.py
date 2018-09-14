#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
type property
"""
from rebulk import CustomRule, Rebulk, POST_PROCESS
from rebulk.match import Match

from ..common.pattern import is_disabled
from ...rules.processors import Processors


def _type(matches, value):
    """
    Define type match with given value.
    :param matches:
    :param value:
    :return:
    """
    matches.append(Match(len(matches.input_string), len(matches.input_string), name='type', value=value))


def type_(config):  # pylint:disable=unused-argument
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, 'type'))
    rebulk = rebulk.rules(TypeProcessor)

    return rebulk


class TypeProcessor(CustomRule):
    """
    Post processor to find file type based on all others found matches.
    """
    priority = POST_PROCESS

    dependency = Processors

    properties = {'type': ['episode', 'movie']}

    def when(self, matches, context):  # pylint:disable=too-many-return-statements
        option_type = context.get('type', None)
        if option_type:
            return option_type

        episode = matches.named('episode')
        season = matches.named('season')
        absolute_episode = matches.named('absolute_episode')
        episode_details = matches.named('episode_details')

        if episode or season or episode_details or absolute_episode:
            return 'episode'

        film = matches.named('film')
        if film:
            return 'movie'

        year = matches.named('year')
        date = matches.named('date')

        if date and not year:
            return 'episode'

        bonus = matches.named('bonus')
        if bonus and not year:
            return 'episode'

        crc32 = matches.named('crc32')
        anime_release_group = matches.named('release_group', lambda match: 'anime' in match.tags)
        if crc32 and anime_release_group:
            return 'episode'

        return 'movie'

    def then(self, matches, when_response, context):
        _type(matches, when_response)

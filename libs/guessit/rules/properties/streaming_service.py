#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
streaming_service property
"""
import re

from rebulk import Rebulk
from rebulk.rules import Rule, RemoveMatch

from ...rules.common import seps, dash


def streaming_service():
    """Streaming service property.

    :return:
    :rtype: Rebulk
    """
    rebulk = Rebulk().string_defaults(ignore_case=True).regex_defaults(flags=re.IGNORECASE, abbreviations=[dash])
    rebulk.defaults(name='streaming_service', tags=['format-prefix'])

    rebulk.string('AE', 'A&E', value='A&E')
    rebulk.string('AMBC', value='ABC')
    rebulk.string('AMC', value='AMC')
    rebulk.string('AMZN', 'AmazonPrime', value='Amazon Prime')
    rebulk.regex('Amazon-Prime', value='Amazon Prime')
    rebulk.string('AS', 'AdultSwim', value='Adult Swim')
    rebulk.regex('Adult-Swim', value='Adult Swim')
    rebulk.string('iP', 'BBCiPlayer', value='BBC iPlayer')
    rebulk.regex('BBC-iPlayer', value='BBC iPlayer')
    rebulk.string('CBS', value='CBS')
    rebulk.string('CC', 'ComedyCentral', value='Comedy Central')
    rebulk.regex('Comedy-Central', value='Comedy Central')
    rebulk.string('CR', 'CrunchyRoll', value='Crunchy Roll')
    rebulk.regex('Crunchy-Roll', value='Crunchy Roll')
    rebulk.string('CW', 'TheCW', value='The CW')
    rebulk.regex('The-CW', value='The CW')
    rebulk.string('DISC', 'Discovery', value='Discovery')
    rebulk.string('DIY', value='DIY Network')
    rebulk.string('DSNY', 'Disney', value='Disney')
    rebulk.string('EPIX', 'ePix', value='ePix')
    rebulk.string('HBO', 'HBOGo', value='HBO Go')
    rebulk.regex('HBO-Go', value='HBO Go')
    rebulk.string('HIST', 'History', value='History')
    rebulk.string('ID', value='Investigation Discovery')
    rebulk.string('IFC', 'IFC', value='IFC')
    rebulk.string('PBS', 'PBS', value='PBS')
    rebulk.string('NATG', 'NationalGeographic', value='National Geographic')
    rebulk.regex('National-Geographic', value='National Geographic')
    rebulk.string('NBA', 'NBATV', value='NBA TV')
    rebulk.regex('NBA-TV', value='NBA TV')
    rebulk.string('NBC', value='NBC')
    rebulk.string('NFL', value='NFL')
    rebulk.string('NICK', 'Nickelodeon', value='Nickelodeon')
    rebulk.string('NF', 'Netflix', value='Netflix')
    rebulk.string('iTunes', value='iTunes')
    rebulk.string('RTE', value='RTÉ One')
    rebulk.string('SESO', 'SeeSo', value='SeeSo')
    rebulk.string('SPKE', 'SpikeTV', 'Spike TV', value='Spike TV')
    rebulk.string('SYFY', 'Syfy', value='Syfy')
    rebulk.string('TFOU', 'TFou', value='TFou')
    rebulk.string('TLC', value='TLC')
    rebulk.string('TV3', value='TV3 Ireland')
    rebulk.string('TV4', value='TV4 Sweeden')
    rebulk.string('TVL', 'TVLand', 'TV Land', value='TV Land')
    rebulk.string('UFC', value='UFC')
    rebulk.string('USAN', value='USA Network')

    rebulk.rules(ValidateStreamingService)

    return rebulk


class ValidateStreamingService(Rule):
    """Validate streaming service matches."""

    priority = 32
    consequence = RemoveMatch

    def when(self, matches, context):
        """Streaming service is always before format.

        :param matches:
        :type matches: rebulk.match.Matches
        :param context:
        :type context: dict
        :return:
        """
        to_remove = []
        for service in matches.named('streaming_service'):
            next_match = matches.next(service, lambda match: 'streaming_service.suffix' in match.tags, 0)
            previous_match = matches.previous(service, lambda match: 'streaming_service.prefix' in match.tags, 0)
            has_other = service.initiator and service.initiator.children.named('other')

            if not has_other and \
                (not next_match or matches.holes(service.end, next_match.start,
                                                 predicate=lambda match: match.value.strip(seps))) and \
                (not previous_match or matches.holes(previous_match.end, service.start,
                                                     predicate=lambda match: match.value.strip(seps))):
                to_remove.append(service)
                continue

            if service.value == 'Comedy Central':
                # Current match is a valid streaming service, removing invalid closed caption (CC) matches
                to_remove.extend(matches.named('other', predicate=lambda match: match.value == 'CC'))

        return to_remove

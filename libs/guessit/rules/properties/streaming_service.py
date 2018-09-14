#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
streaming_service property
"""
import re

from rebulk import Rebulk
from rebulk.rules import Rule, RemoveMatch

from ..common.pattern import is_disabled
from ...rules.common import seps, dash
from ...rules.common.validators import seps_before, seps_after


def streaming_service(config):  # pylint: disable=too-many-statements,unused-argument
    """Streaming service property.

    :param config: rule configuration
    :type config: dict
    :return:
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, 'streaming_service'))
    rebulk = rebulk.string_defaults(ignore_case=True).regex_defaults(flags=re.IGNORECASE, abbreviations=[dash])
    rebulk.defaults(name='streaming_service', tags=['source-prefix'])

    rebulk.string('AE', 'A&E', value='A&E')
    rebulk.string('AMBC', value='ABC')
    rebulk.string('AUBC', value='ABC Australia')
    rebulk.string('AJAZ', value='Al Jazeera English')
    rebulk.string('AMC', value='AMC')
    rebulk.string('AMZN', 'Amazon', value='Amazon Prime')
    rebulk.regex('Amazon-?Prime', value='Amazon Prime')
    rebulk.string('AS', value='Adult Swim')
    rebulk.regex('Adult-?Swim', value='Adult Swim')
    rebulk.string('ATK', value="America's Test Kitchen")
    rebulk.string('ANPL', value='Animal Planet')
    rebulk.string('ANLB', value='AnimeLab')
    rebulk.string('AOL', value='AOL')
    rebulk.string('ARD', value='ARD')
    rebulk.string('iP', value='BBC iPlayer')
    rebulk.regex('BBC-?iPlayer', value='BBC iPlayer')
    rebulk.string('BRAV', value='BravoTV')
    rebulk.string('CNLP', value='Canal+')
    rebulk.string('CN', value='Cartoon Network')
    rebulk.string('CBC', value='CBC')
    rebulk.string('CBS', value='CBS')
    rebulk.string('CNBC', value='CNBC')
    rebulk.string('CC', value='Comedy Central')
    rebulk.string('4OD', value='Channel 4')
    rebulk.string('CHGD', value='CHRGD')
    rebulk.string('CMAX', value='Cinemax')
    rebulk.string('CMT', value='Country Music Television')
    rebulk.regex('Comedy-?Central', value='Comedy Central')
    rebulk.string('CCGC', value='Comedians in Cars Getting Coffee')
    rebulk.string('CR', value='Crunchy Roll')
    rebulk.string('CRKL', value='Crackle')
    rebulk.regex('Crunchy-?Roll', value='Crunchy Roll')
    rebulk.string('CSPN', value='CSpan')
    rebulk.string('CTV', value='CTV')
    rebulk.string('CUR', value='CuriosityStream')
    rebulk.string('CWS', value='CWSeed')
    rebulk.string('DSKI', value='Daisuki')
    rebulk.string('DHF', value='Deadhouse Films')
    rebulk.string('DDY', value='Digiturk Diledigin Yerde')
    rebulk.string('DISC', 'Discovery', value='Discovery')
    rebulk.string('DSNY', 'Disney', value='Disney')
    rebulk.string('DIY', value='DIY Network')
    rebulk.string('DOCC', value='Doc Club')
    rebulk.string('DPLY', value='DPlay')
    rebulk.string('ETV', value='E!')
    rebulk.string('EPIX', value='ePix')
    rebulk.string('ETTV', value='El Trece')
    rebulk.string('ESPN', value='ESPN')
    rebulk.string('ESQ', value='Esquire')
    rebulk.string('FAM', value='Family')
    rebulk.string('FJR', value='Family Jr')
    rebulk.string('FOOD', value='Food Network')
    rebulk.string('FOX', value='Fox')
    rebulk.string('FREE', value='Freeform')
    rebulk.string('FYI', value='FYI Network')
    rebulk.string('GLBL', value='Global')
    rebulk.string('GLOB', value='GloboSat Play')
    rebulk.string('HLMK', value='Hallmark')
    rebulk.string('HBO', value='HBO Go')
    rebulk.regex('HBO-?Go', value='HBO Go')
    rebulk.string('HGTV', value='HGTV')
    rebulk.string('HIST', 'History', value='History')
    rebulk.string('HULU', value='Hulu')
    rebulk.string('ID', value='Investigation Discovery')
    rebulk.string('IFC', value='IFC')
    rebulk.string('iTunes', 'iT', value='iTunes')
    rebulk.string('ITV', value='ITV')
    rebulk.string('KNOW', value='Knowledge Network')
    rebulk.string('LIFE', value='Lifetime')
    rebulk.string('MTOD', value='Motor Trend OnDemand')
    rebulk.string('MNBC', value='MSNBC')
    rebulk.string('MTV', value='MTV')
    rebulk.string('NATG', value='National Geographic')
    rebulk.regex('National-?Geographic', value='National Geographic')
    rebulk.string('NBA', value='NBA TV')
    rebulk.regex('NBA-?TV', value='NBA TV')
    rebulk.string('NBC', value='NBC')
    rebulk.string('NF', 'Netflix', value='Netflix')
    rebulk.string('NFL', value='NFL')
    rebulk.string('NFLN', value='NFL Now')
    rebulk.string('GC', value='NHL GameCenter')
    rebulk.string('NICK', 'Nickelodeon', value='Nickelodeon')
    rebulk.string('NRK', value='Norsk Rikskringkasting')
    rebulk.string('PBS', value='PBS')
    rebulk.string('PBSK', value='PBS Kids')
    rebulk.string('PSN', value='Playstation Network')
    rebulk.string('PLUZ', value='Pluzz')
    rebulk.string('RTE', value='RTE One')
    rebulk.string('SBS', value='SBS (AU)')
    rebulk.string('SESO', 'SeeSo', value='SeeSo')
    rebulk.string('SHMI', value='Shomi')
    rebulk.string('SPIK', value='Spike')
    rebulk.string('SPKE', value='Spike TV')
    rebulk.regex('Spike-?TV', value='Spike TV')
    rebulk.string('SNET', value='Sportsnet')
    rebulk.string('SPRT', value='Sprout')
    rebulk.string('STAN', value='Stan')
    rebulk.string('STZ', value='Starz')
    rebulk.string('SVT', value='Sveriges Television')
    rebulk.string('SWER', value='SwearNet')
    rebulk.string('SYFY', value='Syfy')
    rebulk.string('TBS', value='TBS')
    rebulk.string('TFOU', value='TFou')
    rebulk.string('CW', value='The CW')
    rebulk.regex('The-?CW', value='The CW')
    rebulk.string('TLC', value='TLC')
    rebulk.string('TUBI', value='TubiTV')
    rebulk.string('TV3', value='TV3 Ireland')
    rebulk.string('TV4', value='TV4 Sweeden')
    rebulk.string('TVL', value='TV Land')
    rebulk.regex('TV-?Land', value='TV Land')
    rebulk.string('UFC', value='UFC')
    rebulk.string('UKTV', value='UKTV')
    rebulk.string('UNIV', value='Univision')
    rebulk.string('USAN', value='USA Network')
    rebulk.string('VLCT', value='Velocity')
    rebulk.string('VH1', value='VH1')
    rebulk.string('VICE', value='Viceland')
    rebulk.string('VMEO', value='Vimeo')
    rebulk.string('VRV', value='VRV')
    rebulk.string('WNET', value='W Network')
    rebulk.string('WME', value='WatchMe')
    rebulk.string('WWEN', value='WWE Network')
    rebulk.string('XBOX', value='Xbox Video')
    rebulk.string('YHOO', value='Yahoo')
    rebulk.string('RED', value='YouTube Red')
    rebulk.string('ZDF', value='ZDF')

    rebulk.rules(ValidateStreamingService)

    return rebulk


class ValidateStreamingService(Rule):
    """Validate streaming service matches."""

    priority = 32
    consequence = RemoveMatch

    def when(self, matches, context):
        """Streaming service is always before source.

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

            if not has_other:
                if (not next_match or
                        matches.holes(service.end, next_match.start,
                                      predicate=lambda match: match.value.strip(seps)) or
                        not seps_before(service)):
                    if (not previous_match or
                            matches.holes(previous_match.end, service.start,
                                          predicate=lambda match: match.value.strip(seps)) or
                            not seps_after(service)):
                        to_remove.append(service)
                        continue

            if service.value == 'Comedy Central':
                # Current match is a valid streaming service, removing invalid Criterion Collection (CC) matches
                to_remove.extend(matches.named('edition', predicate=lambda match: match.value == 'Criterion'))

        return to_remove

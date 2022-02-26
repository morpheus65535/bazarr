#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
video_bit_rate and audio_bit_rate properties
"""
from rebulk import Rebulk
from rebulk.remodule import re
from rebulk.rules import Rule, RemoveMatch, RenameMatch

from ..common import dash, seps
from ..common.pattern import is_disabled
from ..common.validators import seps_surround
from ...config import load_config_patterns


def bit_rate(config):  # pylint:disable=unused-argument
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: (is_disabled(context, 'audio_bit_rate')
                                              and is_disabled(context, 'video_bit_rate')))
    rebulk = rebulk.regex_defaults(flags=re.IGNORECASE, abbreviations=[dash])
    rebulk.defaults(name='audio_bit_rate', validator=seps_surround)

    load_config_patterns(rebulk, config.get('bit_rate'))

    rebulk.rules(BitRateTypeRule)

    return rebulk


class BitRateTypeRule(Rule):
    """
    Convert audio bit rate guess into video bit rate.
    """
    consequence = [RenameMatch('video_bit_rate'), RemoveMatch]

    def when(self, matches, context):
        to_rename = []
        to_remove = []

        if is_disabled(context, 'audio_bit_rate'):
            to_remove.extend(matches.named('audio_bit_rate'))
        else:
            video_bit_rate_disabled = is_disabled(context, 'video_bit_rate')
            for match in matches.named('audio_bit_rate'):
                previous = matches.previous(match, index=0,
                                            predicate=lambda m: m.name in ('source', 'screen_size', 'video_codec'))
                if previous and not matches.holes(previous.end, match.start, predicate=lambda m: m.value.strip(seps)):
                    after = matches.next(match, index=0, predicate=lambda m: m.name == 'audio_codec')
                    if after and not matches.holes(match.end, after.start, predicate=lambda m: m.value.strip(seps)):
                        bitrate = match.value
                        if bitrate.units == 'Kbps' or (bitrate.units == 'Mbps' and bitrate.magnitude < 10):
                            continue

                    if video_bit_rate_disabled:
                        to_remove.append(match)
                    else:
                        to_rename.append(match)

        if to_rename or to_remove:
            return to_rename, to_remove
        return False

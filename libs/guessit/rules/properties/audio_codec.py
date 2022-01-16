#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audio_codec, audio_profile and audio_channels property
"""
from rebulk import Rebulk, Rule, RemoveMatch
from rebulk.remodule import re

from ..common import dash
from ..common.pattern import is_disabled
from ..common.validators import seps_before, seps_after
from ...config import load_config_patterns

audio_properties = ['audio_codec', 'audio_profile', 'audio_channels']


def audio_codec(config):  # pylint:disable=unused-argument
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk() \
        .regex_defaults(flags=re.IGNORECASE, abbreviations=[dash]) \
        .string_defaults(ignore_case=True)

    def audio_codec_priority(match1, match2):
        """
        Gives priority to audio_codec
        :param match1:
        :type match1:
        :param match2:
        :type match2:
        :return:
        :rtype:
        """
        if match1.name == 'audio_codec' and match2.name in ['audio_profile', 'audio_channels']:
            return match2
        if match1.name in ['audio_profile', 'audio_channels'] and match2.name == 'audio_codec':
            return match1
        return '__default__'

    rebulk.defaults(name='audio_codec',
                    conflict_solver=audio_codec_priority,
                    disabled=lambda context: is_disabled(context, 'audio_codec'))

    load_config_patterns(rebulk, config.get('audio_codec'))

    rebulk.defaults(clear=True,
                    name='audio_profile',
                    disabled=lambda context: is_disabled(context, 'audio_profile'))

    load_config_patterns(rebulk, config.get('audio_profile'))

    rebulk.defaults(clear=True,
                    name="audio_channels",
                    disabled=lambda context: is_disabled(context, 'audio_channels'))

    load_config_patterns(rebulk, config.get('audio_channels'))

    rebulk.rules(DtsHDRule, DtsRule, AacRule, DolbyDigitalRule, AudioValidatorRule, HqConflictRule,
                 AudioChannelsValidatorRule)

    return rebulk


class AudioValidatorRule(Rule):
    """
    Remove audio properties if not surrounded by separators and not next each others
    """
    priority = 64
    consequence = RemoveMatch

    def when(self, matches, context):
        ret = []

        audio_list = matches.range(predicate=lambda match: match.name in audio_properties)
        for audio in audio_list:
            if not seps_before(audio):
                valid_before = matches.range(audio.start - 1, audio.start,
                                             lambda match: match.name in audio_properties)
                if not valid_before:
                    ret.append(audio)
                    continue
            if not seps_after(audio):
                valid_after = matches.range(audio.end, audio.end + 1,
                                            lambda match: match.name in audio_properties)
                if not valid_after:
                    ret.append(audio)
                    continue

        return ret


class AudioProfileRule(Rule):
    """
    Abstract rule to validate audio profiles
    """
    priority = 64
    dependency = AudioValidatorRule
    consequence = RemoveMatch

    def __init__(self, codec):
        super().__init__()
        self.codec = codec

    def enabled(self, context):
        return not is_disabled(context, 'audio_profile')

    def when(self, matches, context):
        profile_list = matches.named('audio_profile',
                                     lambda match: 'audio_profile.rule' in match.tags and
                                                   self.codec in match.tags)
        ret = []
        for profile in profile_list:
            codec = matches.at_span(profile.span,
                                    lambda match: match.name == 'audio_codec' and
                                                  match.value == self.codec, 0)
            if not codec:
                codec = matches.previous(profile,
                                         lambda match: match.name == 'audio_codec' and
                                                       match.value == self.codec)
            if not codec:
                codec = matches.next(profile,
                                     lambda match: match.name == 'audio_codec' and
                                                   match.value == self.codec)
            if not codec:
                ret.append(profile)
            if codec:
                ret.extend(matches.conflicting(profile))
        return ret


class DtsHDRule(AudioProfileRule):
    """
    Rule to validate DTS-HD profile
    """

    def __init__(self):
        super().__init__('DTS-HD')


class DtsRule(AudioProfileRule):
    """
    Rule to validate DTS profile
    """

    def __init__(self):
        super().__init__('DTS')


class AacRule(AudioProfileRule):
    """
    Rule to validate AAC profile
    """

    def __init__(self):
        super().__init__('AAC')


class DolbyDigitalRule(AudioProfileRule):
    """
    Rule to validate Dolby Digital profile
    """

    def __init__(self):
        super().__init__('Dolby Digital')


class HqConflictRule(Rule):
    """
    Solve conflict between HQ from other property and from audio_profile.
    """

    dependency = [DtsHDRule, DtsRule, AacRule, DolbyDigitalRule]
    consequence = RemoveMatch

    def enabled(self, context):
        return not is_disabled(context, 'audio_profile')

    def when(self, matches, context):
        hq_audio = matches.named('audio_profile', lambda m: m.value == 'High Quality')
        hq_audio_spans = [match.span for match in hq_audio]
        return matches.named('other', lambda m: m.span in hq_audio_spans)


class AudioChannelsValidatorRule(Rule):
    """
    Remove audio_channel if no audio codec as previous match.
    """
    priority = 128
    consequence = RemoveMatch

    def enabled(self, context):
        return not is_disabled(context, 'audio_channels')

    def when(self, matches, context):
        ret = []

        for audio_channel in matches.tagged('weak-audio_channels'):
            valid_before = matches.range(audio_channel.start - 1, audio_channel.start,
                                         lambda match: match.name == 'audio_codec')
            if not valid_before:
                ret.append(audio_channel)

        return ret

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

audio_properties = ['audio_codec', 'audio_profile', 'audio_channels']


def audio_codec(config):  # pylint:disable=unused-argument
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk()\
        .regex_defaults(flags=re.IGNORECASE, abbreviations=[dash])\
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

    rebulk.regex("MP3", "LAME", r"LAME(?:\d)+-?(?:\d)+", value="MP3")
    rebulk.string("MP2", value="MP2")
    rebulk.regex('Dolby', 'DolbyDigital', 'Dolby-Digital', 'DD', 'AC3D?', value='Dolby Digital')
    rebulk.regex('Dolby-?Atmos', 'Atmos', value='Dolby Atmos')
    rebulk.string("AAC", value="AAC")
    rebulk.string('EAC3', 'DDP', 'DD+', value='Dolby Digital Plus')
    rebulk.string("Flac", value="FLAC")
    rebulk.string("DTS", value="DTS")
    rebulk.regex('DTS-?HD', 'DTS(?=-?MA)', value='DTS-HD',
                 conflict_solver=lambda match, other: other if other.name == 'audio_codec' else '__default__')
    rebulk.regex('True-?HD', value='Dolby TrueHD')
    rebulk.string('Opus', value='Opus')
    rebulk.string('Vorbis', value='Vorbis')
    rebulk.string('PCM', value='PCM')
    rebulk.string('LPCM', value='LPCM')

    rebulk.defaults(clear=True,
                    name='audio_profile',
                    disabled=lambda context: is_disabled(context, 'audio_profile'))
    rebulk.string('MA', value='Master Audio', tags=['audio_profile.rule', 'DTS-HD'])
    rebulk.string('HR', 'HRA', value='High Resolution Audio', tags=['audio_profile.rule', 'DTS-HD'])
    rebulk.string('ES', value='Extended Surround', tags=['audio_profile.rule', 'DTS'])
    rebulk.string('HE', value='High Efficiency', tags=['audio_profile.rule', 'AAC'])
    rebulk.string('LC', value='Low Complexity', tags=['audio_profile.rule', 'AAC'])
    rebulk.string('HQ', value='High Quality', tags=['audio_profile.rule', 'Dolby Digital'])
    rebulk.string('EX', value='EX', tags=['audio_profile.rule', 'Dolby Digital'])

    rebulk.defaults(clear=True,
                    name="audio_channels",
                    disabled=lambda context: is_disabled(context, 'audio_channels'))
    rebulk.regex('7[01]', value='7.1', validator=seps_after, tags='weak-audio_channels')
    rebulk.regex('5[01]', value='5.1', validator=seps_after, tags='weak-audio_channels')
    rebulk.string('20', value='2.0', validator=seps_after, tags='weak-audio_channels')

    for value, items in config.get('audio_channels').items():
        for item in items:
            if item.startswith('re:'):
                rebulk.regex(item[3:], value=value, children=True)
            else:
                rebulk.string(item, value=value)

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
        super(AudioProfileRule, self).__init__()
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
        super(DtsHDRule, self).__init__('DTS-HD')


class DtsRule(AudioProfileRule):
    """
    Rule to validate DTS profile
    """

    def __init__(self):
        super(DtsRule, self).__init__('DTS')


class AacRule(AudioProfileRule):
    """
    Rule to validate AAC profile
    """

    def __init__(self):
        super(AacRule, self).__init__('AAC')


class DolbyDigitalRule(AudioProfileRule):
    """
    Rule to validate Dolby Digital profile
    """

    def __init__(self):
        super(DolbyDigitalRule, self).__init__('Dolby Digital')


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

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audio_codec, audio_profile and audio_channels property
"""
from rebulk.remodule import re

from rebulk import Rebulk, Rule, RemoveMatch
from ..common import dash
from ..common.validators import seps_before, seps_after

audio_properties = ['audio_codec', 'audio_profile', 'audio_channels']


def audio_codec():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash]).string_defaults(ignore_case=True)

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

    rebulk.defaults(name="audio_codec", conflict_solver=audio_codec_priority)

    rebulk.regex("MP3", "LAME", r"LAME(?:\d)+-?(?:\d)+", value="MP3")
    rebulk.regex('Dolby', 'DolbyDigital', 'Dolby-Digital', 'DD', 'AC3D?', value='AC3')
    rebulk.regex("DolbyAtmos", "Dolby-Atmos", "Atmos", value="DolbyAtmos")
    rebulk.string("AAC", value="AAC")
    rebulk.string('EAC3', 'DDP', 'DD+', value="EAC3")
    rebulk.string("Flac", value="FLAC")
    rebulk.string("DTS", value="DTS")
    rebulk.regex("True-?HD", value="TrueHD")

    rebulk.defaults(name="audio_profile")
    rebulk.string("HD", value="HD", tags="DTS")
    rebulk.regex("HD-?MA", value="HDMA", tags="DTS")
    rebulk.string("HE", value="HE", tags="AAC")
    rebulk.string("LC", value="LC", tags="AAC")
    rebulk.string("HQ", value="HQ", tags="AC3")

    rebulk.defaults(name="audio_channels")
    rebulk.regex(r'(7[\W_][01](?:ch)?)(?:[^\d]|$)', value='7.1', children=True)
    rebulk.regex(r'(5[\W_][01](?:ch)?)(?:[^\d]|$)', value='5.1', children=True)
    rebulk.regex(r'(2[\W_]0(?:ch)?)(?:[^\d]|$)', value='2.0', children=True)
    rebulk.regex('7[01]', value='7.1', validator=seps_after, tags='weak-audio_channels')
    rebulk.regex('5[01]', value='5.1', validator=seps_after, tags='weak-audio_channels')
    rebulk.string('20', value='2.0', validator=seps_after, tags='weak-audio_channels')
    rebulk.string('7ch', '8ch', value='7.1')
    rebulk.string('5ch', '6ch', value='5.1')
    rebulk.string('2ch', 'stereo', value='2.0')
    rebulk.string('1ch', 'mono', value='1.0')

    rebulk.rules(DtsRule, AacRule, Ac3Rule, AudioValidatorRule, HqConflictRule, AudioChannelsValidatorRule)

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

    def when(self, matches, context):
        profile_list = matches.named('audio_profile', lambda match: self.codec in match.tags)
        ret = []
        for profile in profile_list:
            codec = matches.previous(profile, lambda match: match.name == 'audio_codec' and match.value == self.codec)
            if not codec:
                codec = matches.next(profile, lambda match: match.name == 'audio_codec' and match.value == self.codec)
            if not codec:
                ret.append(profile)
        return ret


class DtsRule(AudioProfileRule):
    """
    Rule to validate DTS profile
    """

    def __init__(self):
        super(DtsRule, self).__init__("DTS")


class AacRule(AudioProfileRule):
    """
    Rule to validate AAC profile
    """

    def __init__(self):
        super(AacRule, self).__init__("AAC")


class Ac3Rule(AudioProfileRule):
    """
    Rule to validate AC3 profile
    """

    def __init__(self):
        super(Ac3Rule, self).__init__("AC3")


class HqConflictRule(Rule):
    """
    Solve conflict between HQ from other property and from audio_profile.
    """

    dependency = [DtsRule, AacRule, Ac3Rule]
    consequence = RemoveMatch

    def when(self, matches, context):
        hq_audio = matches.named('audio_profile', lambda match: match.value == 'HQ')
        hq_audio_spans = [match.span for match in hq_audio]
        hq_other = matches.named('other', lambda match: match.span in hq_audio_spans)

        if hq_other:
            return hq_other


class AudioChannelsValidatorRule(Rule):
    """
    Remove audio_channel if no audio codec as previous match.
    """
    priority = 128
    consequence = RemoveMatch

    def when(self, matches, context):
        ret = []

        for audio_channel in matches.tagged('weak-audio_channels'):
            valid_before = matches.range(audio_channel.start - 1, audio_channel.start,
                                         lambda match: match.name == 'audio_codec')
            if not valid_before:
                ret.append(audio_channel)

        return ret

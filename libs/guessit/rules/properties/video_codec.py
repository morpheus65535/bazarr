#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
video_codec and video_profile property
"""
from rebulk import Rebulk, Rule, RemoveMatch
from rebulk.remodule import re

from ..common import dash
from ..common.pattern import is_disabled
from ..common.validators import seps_after, seps_before, seps_surround


def video_codec(config):  # pylint:disable=unused-argument
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk()
    rebulk = rebulk.regex_defaults(flags=re.IGNORECASE, abbreviations=[dash]).string_defaults(ignore_case=True)
    rebulk.defaults(name="video_codec",
                    tags=['source-suffix', 'streaming_service.suffix'],
                    disabled=lambda context: is_disabled(context, 'video_codec'))

    rebulk.regex(r'Rv\d{2}', value='RealVideo')
    rebulk.regex('Mpe?g-?2', '[hx]-?262', value='MPEG-2')
    rebulk.string("DVDivX", "DivX", value="DivX")
    rebulk.string('XviD', value='Xvid')
    rebulk.regex('VC-?1', value='VC-1')
    rebulk.string('VP7', value='VP7')
    rebulk.string('VP8', 'VP80', value='VP8')
    rebulk.string('VP9', value='VP9')
    rebulk.regex('[hx]-?263', value='H.263')
    rebulk.regex('[hx]-?264', '(MPEG-?4)?AVC(?:HD)?', value='H.264')
    rebulk.regex('[hx]-?265', 'HEVC', value='H.265')
    rebulk.regex('(?P<video_codec>hevc)(?P<color_depth>10)', value={'video_codec': 'H.265', 'color_depth': '10-bit'},
                 tags=['video-codec-suffix'], children=True)

    # http://blog.mediacoderhq.com/h264-profiles-and-levels/
    # https://en.wikipedia.org/wiki/H.264/MPEG-4_AVC
    rebulk.defaults(clear=True,
                    name="video_profile",
                    validator=seps_surround,
                    disabled=lambda context: is_disabled(context, 'video_profile'))

    rebulk.string('BP', value='Baseline', tags='video_profile.rule')
    rebulk.string('XP', 'EP', value='Extended', tags='video_profile.rule')
    rebulk.string('MP', value='Main', tags='video_profile.rule')
    rebulk.string('HP', 'HiP', value='High', tags='video_profile.rule')

    # https://en.wikipedia.org/wiki/Scalable_Video_Coding
    rebulk.string('SC', 'SVC', value='Scalable Video Coding', tags='video_profile.rule')
    # https://en.wikipedia.org/wiki/AVCHD
    rebulk.regex('AVC(?:HD)?', value='Advanced Video Codec High Definition', tags='video_profile.rule')
    # https://en.wikipedia.org/wiki/H.265/HEVC
    rebulk.string('HEVC', value='High Efficiency Video Coding', tags='video_profile.rule')

    rebulk.regex('Hi422P', value='High 4:2:2')
    rebulk.regex('Hi444PP', value='High 4:4:4 Predictive')
    rebulk.regex('Hi10P?', value='High 10')  # no profile validation is required

    rebulk.string('DXVA', value='DXVA', name='video_api',
                  disabled=lambda context: is_disabled(context, 'video_api'))

    rebulk.defaults(clear=True,
                    name='color_depth',
                    validator=seps_surround,
                    disabled=lambda context: is_disabled(context, 'color_depth'))
    rebulk.regex('12.?bits?', value='12-bit')
    rebulk.regex('10.?bits?', 'YUV420P10', 'Hi10P?', value='10-bit')
    rebulk.regex('8.?bits?', value='8-bit')

    rebulk.rules(ValidateVideoCodec, VideoProfileRule)

    return rebulk


class ValidateVideoCodec(Rule):
    """
    Validate video_codec with source property or separated
    """
    priority = 64
    consequence = RemoveMatch

    def enabled(self, context):
        return not is_disabled(context, 'video_codec')

    def when(self, matches, context):
        ret = []
        for codec in matches.named('video_codec'):
            if not seps_before(codec) and \
                    not matches.at_index(codec.start - 1, lambda match: 'video-codec-prefix' in match.tags):
                ret.append(codec)
                continue
            if not seps_after(codec) and \
                    not matches.at_index(codec.end + 1, lambda match: 'video-codec-suffix' in match.tags):
                ret.append(codec)
                continue
        return ret


class VideoProfileRule(Rule):
    """
    Rule to validate video_profile
    """
    consequence = RemoveMatch

    def enabled(self, context):
        return not is_disabled(context, 'video_profile')

    def when(self, matches, context):
        profile_list = matches.named('video_profile', lambda match: 'video_profile.rule' in match.tags)
        ret = []
        for profile in profile_list:
            codec = matches.at_span(profile.span, lambda match: match.name == 'video_codec', 0)
            if not codec:
                codec = matches.previous(profile, lambda match: match.name == 'video_codec')
            if not codec:
                codec = matches.next(profile, lambda match: match.name == 'video_codec')
            if not codec:
                ret.append(profile)
        return ret

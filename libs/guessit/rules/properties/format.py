#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
format property
"""
from rebulk.remodule import re

from rebulk import Rebulk, RemoveMatch, Rule
from ..common import dash
from ..common.validators import seps_before, seps_after


def format_():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash])
    rebulk.defaults(name="format", tags=['video-codec-prefix', 'streaming_service.suffix'])

    rebulk.regex("VHS", "VHS-?Rip", value="VHS")
    rebulk.regex("CAM", "CAM-?Rip", "HD-?CAM", value="Cam")
    rebulk.regex("TELESYNC", "TS", "HD-?TS", value="Telesync")
    rebulk.regex("WORKPRINT", "WP", value="Workprint")
    rebulk.regex("TELECINE", "TC", value="Telecine")
    rebulk.regex("PPV", "PPV-?Rip", value="PPV")  # Pay Per View
    rebulk.regex("SD-?TV", "SD-?TV-?Rip", "Rip-?SD-?TV", "TV-?Rip",
                 "Rip-?TV", "TV-?(?=Dub)", value="TV")  # TV is too common to allow matching
    rebulk.regex("DVB-?Rip", "DVB", "PD-?TV", value="DVB")
    rebulk.regex("DVD", "DVD-?Rip", "VIDEO-?TS", "DVD-?R(?:$|(?!E))",  # "DVD-?R(?:$|^E)" => DVD-Real ...
                 "DVD-?9", "DVD-?5", value="DVD")

    rebulk.regex("HD-?TV", "TV-?RIP-?HD", "HD-?TV-?RIP", "HD-?RIP", value="HDTV",
                 conflict_solver=lambda match, other: other if other.name == 'other' else '__default__')
    rebulk.regex("VOD", "VOD-?Rip", value="VOD")
    rebulk.regex("WEB-?Rip", "WEB-?DL-?Rip", "WEB-?Cap", value="WEBRip")
    rebulk.regex("WEB-?DL", "WEB-?HD", "WEB", "DL-?WEB", "DL(?=-?Mux)", value="WEB-DL")
    rebulk.regex("HD-?DVD-?Rip", "HD-?DVD", value="HD-DVD")
    rebulk.regex("Blu-?ray(?:-?Rip)?", "B[DR]", "B[DR]-?Rip", "BD[59]", "BD25", "BD50", value="BluRay")
    rebulk.regex("AHDTV", value="AHDTV")
    rebulk.regex('UHD-?TV', 'UHD-?Rip', value='UHDTV',
                 conflict_solver=lambda match, other: other if other.name == 'other' else '__default__')
    rebulk.regex("HDTC", value="HDTC")
    rebulk.regex("DSR", "DSR?-?Rip", "SAT-?Rip", "DTH", "DTH-?Rip", value="SATRip")

    rebulk.rules(ValidateFormat)

    return rebulk


class ValidateFormat(Rule):
    """
    Validate format with screener property, with video_codec property or separated
    """
    priority = 64
    consequence = RemoveMatch

    def when(self, matches, context):
        ret = []
        for format_match in matches.named('format'):
            if not seps_before(format_match) and \
                    not matches.range(format_match.start - 1, format_match.start - 2,
                                      lambda match: 'format-prefix' in match.tags):
                ret.append(format_match)
                continue
            if not seps_after(format_match) and \
                    not matches.range(format_match.end, format_match.end + 1,
                                      lambda match: 'format-suffix' in match.tags):
                ret.append(format_match)
                continue
        return ret

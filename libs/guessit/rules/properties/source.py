#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
source property
"""
import copy

from rebulk.remodule import re

from rebulk import AppendMatch, Rebulk, RemoveMatch, Rule

from .audio_codec import HqConflictRule
from ..common import dash, seps
from ..common.pattern import is_disabled
from ..common.validators import seps_before, seps_after, or_


def source(config):  # pylint:disable=unused-argument
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, 'source'))
    rebulk = rebulk.regex_defaults(flags=re.IGNORECASE, abbreviations=[dash], private_parent=True, children=True)
    rebulk = rebulk.defaults(name='source',
                             tags=['video-codec-prefix', 'streaming_service.suffix'],
                             validate_all=True,
                             validator={'__parent__': or_(seps_before, seps_after)})

    rip_prefix = '(?P<other>Rip)-?'
    rip_suffix = '-?(?P<other>Rip)'
    rip_optional_suffix = '(?:' + rip_suffix + ')?'

    def build_source_pattern(*patterns, **kwargs):
        """Helper pattern to build source pattern."""
        prefix_format = kwargs.get('prefix') or ''
        suffix_format = kwargs.get('suffix') or ''

        string_format = prefix_format + '({0})' + suffix_format
        return [string_format.format(pattern) for pattern in patterns]

    def demote_other(match, other):  # pylint: disable=unused-argument
        """Default conflict solver with 'other' property."""
        return other if other.name == 'other' or other.name == 'release_group' else '__default__'

    rebulk.regex(*build_source_pattern('VHS', suffix=rip_optional_suffix),
                 value={'source': 'VHS', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('CAM', suffix=rip_optional_suffix),
                 value={'source': 'Camera', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('HD-?CAM', suffix=rip_optional_suffix),
                 value={'source': 'HD Camera', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('TELESYNC', 'TS', suffix=rip_optional_suffix),
                 value={'source': 'Telesync', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('HD-?TELESYNC', 'HD-?TS', suffix=rip_optional_suffix),
                 value={'source': 'HD Telesync', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('WORKPRINT', 'WP'), value='Workprint')
    rebulk.regex(*build_source_pattern('TELECINE', 'TC', suffix=rip_optional_suffix),
                 value={'source': 'Telecine', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('HD-?TELECINE', 'HD-?TC', suffix=rip_optional_suffix),
                 value={'source': 'HD Telecine', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('PPV', suffix=rip_optional_suffix),
                 value={'source': 'Pay-per-view', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('SD-?TV', suffix=rip_optional_suffix),
                 value={'source': 'TV', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('TV', suffix=rip_suffix),  # TV is too common to allow matching
                 value={'source': 'TV', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('TV', 'SD-?TV', prefix=rip_prefix),
                 value={'source': 'TV', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('TV-?(?=Dub)'), value='TV')
    rebulk.regex(*build_source_pattern('DVB', 'PD-?TV', suffix=rip_optional_suffix),
                 value={'source': 'Digital TV', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('DVD', suffix=rip_optional_suffix),
                 value={'source': 'DVD', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('DM', suffix=rip_optional_suffix),
                 value={'source': 'Digital Master', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('VIDEO-?TS', 'DVD-?R(?:$|(?!E))',  # 'DVD-?R(?:$|^E)' => DVD-Real ...
                                       'DVD-?9', 'DVD-?5'), value='DVD')

    rebulk.regex(*build_source_pattern('HD-?TV', suffix=rip_optional_suffix), conflict_solver=demote_other,
                 value={'source': 'HDTV', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('TV-?HD', suffix=rip_suffix), conflict_solver=demote_other,
                 value={'source': 'HDTV', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('TV', suffix='-?(?P<other>Rip-?HD)'), conflict_solver=demote_other,
                 value={'source': 'HDTV', 'other': 'Rip'})

    rebulk.regex(*build_source_pattern('VOD', suffix=rip_optional_suffix),
                 value={'source': 'Video on Demand', 'other': 'Rip'})

    rebulk.regex(*build_source_pattern('WEB', 'WEB-?DL', suffix=rip_suffix),
                 value={'source': 'Web', 'other': 'Rip'})
    # WEBCap is a synonym to WEBRip, mostly used by non english
    rebulk.regex(*build_source_pattern('WEB-?(?P<another>Cap)', suffix=rip_optional_suffix),
                 value={'source': 'Web', 'other': 'Rip', 'another': 'Rip'})
    rebulk.regex(*build_source_pattern('WEB-?DL', 'WEB-?U?HD', 'DL-?WEB', 'DL(?=-?Mux)'),
                 value={'source': 'Web'})
    rebulk.regex('(WEB)', value='Web', tags='weak.source')

    rebulk.regex(*build_source_pattern('HD-?DVD', suffix=rip_optional_suffix),
                 value={'source': 'HD-DVD', 'other': 'Rip'})

    rebulk.regex(*build_source_pattern('Blu-?ray', 'BD', 'BD[59]', 'BD25', 'BD50', suffix=rip_optional_suffix),
                 value={'source': 'Blu-ray', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('(?P<another>BR)-?(?=Scr(?:eener)?)', '(?P<another>BR)-?(?=Mux)'),  # BRRip
                 value={'source': 'Blu-ray', 'another': 'Reencoded'})
    rebulk.regex(*build_source_pattern('(?P<another>BR)', suffix=rip_suffix),  # BRRip
                 value={'source': 'Blu-ray', 'other': 'Rip', 'another': 'Reencoded'})

    rebulk.regex(*build_source_pattern('Ultra-?Blu-?ray', 'Blu-?ray-?Ultra'), value='Ultra HD Blu-ray')

    rebulk.regex(*build_source_pattern('AHDTV'), value='Analog HDTV')
    rebulk.regex(*build_source_pattern('UHD-?TV', suffix=rip_optional_suffix), conflict_solver=demote_other,
                 value={'source': 'Ultra HDTV', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('UHD', suffix=rip_suffix), conflict_solver=demote_other,
                 value={'source': 'Ultra HDTV', 'other': 'Rip'})

    rebulk.regex(*build_source_pattern('DSR', 'DTH', suffix=rip_optional_suffix),
                 value={'source': 'Satellite', 'other': 'Rip'})
    rebulk.regex(*build_source_pattern('DSR?', 'SAT', suffix=rip_suffix),
                 value={'source': 'Satellite', 'other': 'Rip'})

    rebulk.rules(ValidateSourcePrefixSuffix, ValidateWeakSource, UltraHdBlurayRule)

    return rebulk


class UltraHdBlurayRule(Rule):
    """
    Replace other:Ultra HD and source:Blu-ray with source:Ultra HD Blu-ray
    """
    dependency = HqConflictRule
    consequence = [RemoveMatch, AppendMatch]

    @classmethod
    def find_ultrahd(cls, matches, start, end, index):
        """Find Ultra HD match."""
        return matches.range(start, end, index=index, predicate=(
            lambda m: not m.private and m.name == 'other' and m.value == 'Ultra HD'
        ))

    @classmethod
    def validate_range(cls, matches, start, end):
        """Validate no holes or invalid matches exist in the specified range."""
        return (
            not matches.holes(start, end, predicate=lambda m: m.value.strip(seps)) and
            not matches.range(start, end, predicate=(
                lambda m: not m.private and (
                    m.name not in ('screen_size', 'color_depth') and (
                        m.name != 'other' or 'uhdbluray-neighbor' not in m.tags))))
        )

    def when(self, matches, context):
        to_remove = []
        to_append = []
        for filepart in matches.markers.named('path'):
            for match in matches.range(filepart.start, filepart.end, predicate=(
                    lambda m: not m.private and m.name == 'source' and m.value == 'Blu-ray')):
                other = self.find_ultrahd(matches, filepart.start, match.start, -1)
                if not other or not self.validate_range(matches, other.end, match.start):
                    other = self.find_ultrahd(matches, match.end, filepart.end, 0)
                    if not other or not self.validate_range(matches, match.end, other.start):
                        if not matches.range(filepart.start, filepart.end, predicate=(
                                lambda m: m.name == 'screen_size' and m.value == '2160p')):
                            continue

                if other:
                    other.private = True

                new_source = copy.copy(match)
                new_source.value = 'Ultra HD Blu-ray'
                to_remove.append(match)
                to_append.append(new_source)

        if to_remove or to_append:
            return to_remove, to_append
        return False


class ValidateSourcePrefixSuffix(Rule):
    """
    Validate source with source prefix, source suffix.
    """
    priority = 64
    consequence = RemoveMatch

    def when(self, matches, context):
        ret = []
        for filepart in matches.markers.named('path'):
            for match in matches.range(filepart.start, filepart.end, predicate=lambda m: m.name == 'source'):
                match = match.initiator
                if not seps_before(match) and \
                        not matches.range(match.start - 1, match.start - 2,
                                          lambda m: 'source-prefix' in m.tags):
                    if match.children:
                        ret.extend(match.children)
                    ret.append(match)
                    continue
                if not seps_after(match) and \
                        not matches.range(match.end, match.end + 1,
                                          lambda m: 'source-suffix' in m.tags):
                    if match.children:
                        ret.extend(match.children)
                    ret.append(match)
                    continue

        return ret


class ValidateWeakSource(Rule):
    """
    Validate weak source
    """
    dependency = [ValidateSourcePrefixSuffix]
    priority = 64
    consequence = RemoveMatch

    def when(self, matches, context):
        ret = []
        for filepart in matches.markers.named('path'):
            for match in matches.range(filepart.start, filepart.end, predicate=lambda m: m.name == 'source'):
                # if there are more than 1 source in this filepart, just before the year and with holes for the title
                # most likely the source is part of the title
                if 'weak.source' in match.tags \
                        and matches.range(match.end, filepart.end, predicate=lambda m: m.name == 'source') \
                        and matches.holes(filepart.start, match.start,
                                          predicate=lambda m: m.value.strip(seps), index=-1):
                    if match.children:
                        ret.extend(match.children)
                    ret.append(match)
                    continue

        return ret

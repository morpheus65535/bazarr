#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
other property
"""
import copy

from rebulk import Rebulk, Rule, RemoveMatch, POST_PROCESS, AppendMatch
from rebulk.remodule import re

from ..common import dash
from ..common import seps
from ..common.validators import seps_after, seps_before, seps_surround, compose
from ...reutils import build_or_pattern
from ...rules.common.formatters import raw_cleanup


def other():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash]).string_defaults(ignore_case=True)
    rebulk.defaults(name="other", validator=seps_surround)

    rebulk.regex('Audio-?Fix', 'Audio-?Fixed', value='AudioFix')
    rebulk.regex('Sync-?Fix', 'Sync-?Fixed', value='SyncFix')
    rebulk.regex('Dual', 'Dual-?Audio', value='DualAudio')
    rebulk.regex('ws', 'wide-?screen', value='WideScreen')
    rebulk.regex('Re-?Enc(?:oded)?', value='ReEncoded')

    rebulk.string('Real', 'Fix', 'Fixed', value='Proper', tags=['has-neighbor-before', 'has-neighbor-after'])
    rebulk.string('Proper', 'Repack', 'Rerip', 'Dirfix', 'Nfofix', 'Prooffix', value='Proper',
                  tags=['streaming_service.prefix', 'streaming_service.suffix'])
    rebulk.regex('(?:Proof-?)?Sample-?Fix', value='Proper',
                 tags=['streaming_service.prefix', 'streaming_service.suffix'])
    rebulk.string('Fansub', value='Fansub', tags='has-neighbor')
    rebulk.string('Fastsub', value='Fastsub', tags='has-neighbor')

    season_words = build_or_pattern(["seasons?", "series?"])
    complete_articles = build_or_pattern(["The"])

    def validate_complete(match):
        """
        Make sure season word is are defined.
        :param match:
        :type match:
        :return:
        :rtype:
        """
        children = match.children
        if not children.named('completeWordsBefore') and not children.named('completeWordsAfter'):
            return False
        return True

    rebulk.regex('(?P<completeArticle>' + complete_articles + '-)?' +
                 '(?P<completeWordsBefore>' + season_words + '-)?' +
                 'Complete' + '(?P<completeWordsAfter>-' + season_words + ')?',
                 private_names=['completeArticle', 'completeWordsBefore', 'completeWordsAfter'],
                 value={'other': 'Complete'},
                 tags=['release-group-prefix'],
                 validator={'__parent__': compose(seps_surround, validate_complete)})
    rebulk.string('R5', 'RC', value='R5')
    rebulk.regex('Pre-?Air', value='Preair')
    rebulk.regex('(?:PS-?)?Vita', value='PS Vita')

    for value in (
            'Screener', 'Remux', '3D', 'mHD', 'HDLight', 'HQ', 'DDC', 'HR', 'PAL', 'SECAM', 'NTSC',
            'CC', 'LD', 'MD', 'XXX'):
        rebulk.string(value, value=value)

    rebulk.string('LDTV', value='LD')
    rebulk.string('HD', value='HD', validator=None,
                  tags=['streaming_service.prefix', 'streaming_service.suffix'])
    rebulk.regex('Full-?HD', 'FHD', value='FullHD', validator=None,
                 tags=['streaming_service.prefix', 'streaming_service.suffix'])
    rebulk.regex('Ultra-?(?:HD)?', 'UHD', value='UltraHD', validator=None,
                 tags=['streaming_service.prefix', 'streaming_service.suffix'])

    for value in ('Complete', 'Classic', 'LiNE', 'Bonus', 'Trailer', 'FINAL', 'Retail',
                  'Colorized', 'Internal'):
        rebulk.string(value, value=value, tags=['has-neighbor', 'release-group-prefix'])
    rebulk.regex('Read-?NFO', value='Read NFO')
    rebulk.string('CONVERT', value='Converted', tags='has-neighbor')
    rebulk.string('DOCU', value='Documentary', tags='has-neighbor')
    rebulk.string('OM', value='Open Matte', tags='has-neighbor')
    rebulk.string('STV', value='Straight to Video', tags='has-neighbor')
    rebulk.string('OAR', value='Original Aspect Ratio', tags='has-neighbor')
    rebulk.string('Complet', value='Complete', tags=['has-neighbor', 'release-group-prefix'])

    for coast in ('East', 'West'):
        rebulk.regex(r'(?:Live-)?(?:Episode-)?' + coast + '-?(?:Coast-)?Feed', value=coast + ' Coast Feed')

    rebulk.string('VO', 'OV', value='OV', tags='has-neighbor')

    rebulk.regex('Scr(?:eener)?', value='Screener', validator=None,
                 tags=['other.validate.screener', 'format-prefix', 'format-suffix'])
    rebulk.string('Mux', value='Mux', validator=seps_after,
                  tags=['other.validate.mux', 'video-codec-prefix', 'format-suffix'])
    rebulk.string('HC', value='Hardcoded Subtitles')

    rebulk.rules(ValidateHasNeighbor, ValidateHasNeighborAfter, ValidateHasNeighborBefore, ValidateScreenerRule,
                 ValidateMuxRule, ValidateHardcodedSubs, ValidateStreamingServiceNeighbor, ProperCountRule)

    return rebulk


class ProperCountRule(Rule):
    """
    Add proper_count property
    """
    priority = POST_PROCESS

    consequence = AppendMatch

    properties = {'proper_count': [None]}

    def when(self, matches, context):
        propers = matches.named('other', lambda match: match.value == 'Proper')
        if propers:
            raws = {}  # Count distinct raw values
            for proper in propers:
                raws[raw_cleanup(proper.raw)] = proper
            proper_count_match = copy.copy(propers[-1])
            proper_count_match.name = 'proper_count'
            proper_count_match.value = len(raws)
            return proper_count_match


class ValidateHasNeighbor(Rule):
    """
    Validate tag has-neighbor
    """
    consequence = RemoveMatch

    def when(self, matches, context):
        ret = []
        for to_check in matches.range(predicate=lambda match: 'has-neighbor' in match.tags):
            previous_match = matches.previous(to_check, index=0)
            previous_group = matches.markers.previous(to_check, lambda marker: marker.name == 'group', 0)
            if previous_group and (not previous_match or previous_group.end > previous_match.end):
                previous_match = previous_group
            if previous_match and not matches.input_string[previous_match.end:to_check.start].strip(seps):
                break
            next_match = matches.next(to_check, index=0)
            next_group = matches.markers.next(to_check, lambda marker: marker.name == 'group', 0)
            if next_group and (not next_match or next_group.start < next_match.start):
                next_match = next_group
            if next_match and not matches.input_string[to_check.end:next_match.start].strip(seps):
                break
            ret.append(to_check)
        return ret


class ValidateHasNeighborBefore(Rule):
    """
    Validate tag has-neighbor-before that previous match exists.
    """
    consequence = RemoveMatch

    def when(self, matches, context):
        ret = []
        for to_check in matches.range(predicate=lambda match: 'has-neighbor-before' in match.tags):
            next_match = matches.next(to_check, index=0)
            next_group = matches.markers.next(to_check, lambda marker: marker.name == 'group', 0)
            if next_group and (not next_match or next_group.start < next_match.start):
                next_match = next_group
            if next_match and not matches.input_string[to_check.end:next_match.start].strip(seps):
                break
            ret.append(to_check)
        return ret


class ValidateHasNeighborAfter(Rule):
    """
    Validate tag has-neighbor-after that next match exists.
    """
    consequence = RemoveMatch

    def when(self, matches, context):
        ret = []
        for to_check in matches.range(predicate=lambda match: 'has-neighbor-after' in match.tags):
            previous_match = matches.previous(to_check, index=0)
            previous_group = matches.markers.previous(to_check, lambda marker: marker.name == 'group', 0)
            if previous_group and (not previous_match or previous_group.end > previous_match.end):
                previous_match = previous_group
            if previous_match and not matches.input_string[previous_match.end:to_check.start].strip(seps):
                break
            ret.append(to_check)
        return ret


class ValidateScreenerRule(Rule):
    """
    Validate tag other.validate.screener
    """
    consequence = RemoveMatch
    priority = 64

    def when(self, matches, context):
        ret = []
        for screener in matches.named('other', lambda match: 'other.validate.screener' in match.tags):
            format_match = matches.previous(screener, lambda match: match.name == 'format', 0)
            if not format_match or matches.input_string[format_match.end:screener.start].strip(seps):
                ret.append(screener)
        return ret


class ValidateMuxRule(Rule):
    """
    Validate tag other.validate.mux
    """
    consequence = RemoveMatch
    priority = 64

    def when(self, matches, context):
        ret = []
        for mux in matches.named('other', lambda match: 'other.validate.mux' in match.tags):
            format_match = matches.previous(mux, lambda match: match.name == 'format', 0)
            if not format_match:
                ret.append(mux)
        return ret


class ValidateHardcodedSubs(Rule):
    """Validate HC matches."""

    priority = 32
    consequence = RemoveMatch

    def when(self, matches, context):
        to_remove = []
        for hc_match in matches.named('other', predicate=lambda match: match.value == 'Hardcoded Subtitles'):
            next_match = matches.next(hc_match, predicate=lambda match: match.name == 'subtitle_language', index=0)
            if next_match and not matches.holes(hc_match.end, next_match.start,
                                                predicate=lambda match: match.value.strip(seps)):
                continue

            previous_match = matches.previous(hc_match,
                                              predicate=lambda match: match.name == 'subtitle_language', index=0)
            if previous_match and not matches.holes(previous_match.end, hc_match.start,
                                                    predicate=lambda match: match.value.strip(seps)):
                continue

            to_remove.append(hc_match)

        return to_remove


class ValidateStreamingServiceNeighbor(Rule):
    """Validate streaming service's neighbors."""

    priority = 32
    consequence = RemoveMatch

    def when(self, matches, context):
        to_remove = []
        for match in matches.named('other',
                                   predicate=lambda m: ('streaming_service.prefix' in m.tags or
                                                        'streaming_service.suffix' in m.tags)):

            if not seps_after(match):
                if 'streaming_service.prefix' in match.tags:
                    next_match = matches.next(match, lambda m: m.name == 'streaming_service', 0)
                    if next_match and not matches.holes(match.end, next_match.start,
                                                        predicate=lambda m: m.value.strip(seps)):
                        continue

                to_remove.append(match)

            elif not seps_before(match):
                if 'streaming_service.suffix' in match.tags:
                    previous_match = matches.previous(match, lambda m: m.name == 'streaming_service', 0)
                    if previous_match and not matches.holes(previous_match.end, match.start,
                                                            predicate=lambda m: m.value.strip(seps)):
                        continue

                to_remove.append(match)

        return to_remove

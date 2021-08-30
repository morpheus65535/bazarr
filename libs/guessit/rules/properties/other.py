#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
other property
"""
import copy

from rebulk import Rebulk, Rule, RemoveMatch, RenameMatch, POST_PROCESS, AppendMatch
from rebulk.remodule import re

from ..common import dash
from ..common import seps
from ..common.pattern import is_disabled
from ..common.validators import seps_after, seps_before, seps_surround, and_
from ...reutils import build_or_pattern
from ...rules.common.formatters import raw_cleanup


def other(config):  # pylint:disable=unused-argument,too-many-statements
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, 'other'))
    rebulk = rebulk.regex_defaults(flags=re.IGNORECASE, abbreviations=[dash]).string_defaults(ignore_case=True)
    rebulk.defaults(name="other", validator=seps_surround)

    rebulk.regex('Audio-?Fix', 'Audio-?Fixed', value='Audio Fixed')
    rebulk.regex('Sync-?Fix', 'Sync-?Fixed', value='Sync Fixed')
    rebulk.regex('Dual', 'Dual-?Audio', value='Dual Audio')
    rebulk.regex('ws', 'wide-?screen', value='Widescreen')
    rebulk.regex('Re-?Enc(?:oded)?', value='Reencoded')

    rebulk.string('Repack', 'Rerip', value='Proper',
                  tags=['streaming_service.prefix', 'streaming_service.suffix'])
    rebulk.string('Proper', value='Proper',
                  tags=['has-neighbor', 'streaming_service.prefix', 'streaming_service.suffix'])

    rebulk.regex('Real-Proper', 'Real-Repack', 'Real-Rerip', value='Proper',
                 tags=['streaming_service.prefix', 'streaming_service.suffix', 'real'])
    rebulk.regex('Real', value='Proper',
                 tags=['has-neighbor', 'streaming_service.prefix', 'streaming_service.suffix', 'real'])

    rebulk.string('Fix', 'Fixed', value='Fix', tags=['has-neighbor-before', 'has-neighbor-after',
                                                     'streaming_service.prefix', 'streaming_service.suffix'])
    rebulk.string('Dirfix', 'Nfofix', 'Prooffix', value='Fix',
                  tags=['streaming_service.prefix', 'streaming_service.suffix'])
    rebulk.regex('(?:Proof-?)?Sample-?Fix', value='Fix',
                 tags=['streaming_service.prefix', 'streaming_service.suffix'])

    rebulk.string('Fansub', value='Fan Subtitled', tags='has-neighbor')
    rebulk.string('Fastsub', value='Fast Subtitled', tags='has-neighbor')

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
                 validator={'__parent__': and_(seps_surround, validate_complete)})
    rebulk.string('R5', value='Region 5')
    rebulk.string('RC', value='Region C')
    rebulk.regex('Pre-?Air', value='Preair')
    rebulk.regex('(?:PS-?)Vita', value='PS Vita')
    rebulk.regex('Vita', value='PS Vita', tags='has-neighbor')
    rebulk.regex('(HD)(?P<another>Rip)', value={'other': 'HD', 'another': 'Rip'},
                 private_parent=True, children=True, validator={'__parent__': seps_surround}, validate_all=True)

    for value in ('Screener', 'Remux', 'Hybrid', 'PAL', 'SECAM', 'NTSC', 'XXX'):
        rebulk.string(value, value=value)
    rebulk.string('3D', value='3D', tags='has-neighbor')

    rebulk.string('HQ', value='High Quality', tags='uhdbluray-neighbor')
    rebulk.string('HR', value='High Resolution')
    rebulk.string('LD', value='Line Dubbed')
    rebulk.string('MD', value='Mic Dubbed')
    rebulk.string('mHD', 'HDLight', value='Micro HD')
    rebulk.string('LDTV', value='Low Definition')
    rebulk.string('HFR', value='High Frame Rate')
    rebulk.string('VFR', value='Variable Frame Rate')
    rebulk.string('HD', value='HD', validator=None,
                  tags=['streaming_service.prefix', 'streaming_service.suffix'])
    rebulk.regex('Full-?HD', 'FHD', value='Full HD', validator=None,
                 tags=['streaming_service.prefix', 'streaming_service.suffix'])
    rebulk.regex('Ultra-?(?:HD)?', 'UHD', value='Ultra HD', validator=None,
                 tags=['streaming_service.prefix', 'streaming_service.suffix'])
    rebulk.regex('Upscaled?', value='Upscaled')

    for value in ('Complete', 'Classic', 'Bonus', 'Trailer', 'Retail',
                  'Colorized', 'Internal'):
        rebulk.string(value, value=value, tags=['has-neighbor', 'release-group-prefix'])
    rebulk.regex('LiNE', value='Line Audio', tags=['has-neighbor-before', 'has-neighbor-after', 'release-group-prefix'])
    rebulk.regex('Read-?NFO', value='Read NFO')
    rebulk.string('CONVERT', value='Converted', tags='has-neighbor')
    rebulk.string('DOCU', 'DOKU', value='Documentary', tags='has-neighbor')
    rebulk.string('OM', value='Open Matte', tags='has-neighbor')
    rebulk.string('STV', value='Straight to Video', tags='has-neighbor')
    rebulk.string('OAR', value='Original Aspect Ratio', tags='has-neighbor')
    rebulk.string('Complet', value='Complete', tags=['has-neighbor', 'release-group-prefix'])

    for coast in ('East', 'West'):
        rebulk.regex(r'(?:Live-)?(?:Episode-)?' + coast + '-?(?:Coast-)?Feed', value=coast + ' Coast Feed')

    rebulk.string('VO', 'OV', value='Original Video', tags='has-neighbor')
    rebulk.string('Ova', 'Oav', value='Original Animated Video')

    rebulk.regex('Scr(?:eener)?', value='Screener', validator=None,
                 tags=['other.validate.screener', 'source-prefix', 'source-suffix'])
    rebulk.string('Mux', value='Mux', validator=seps_after,
                  tags=['other.validate.mux', 'video-codec-prefix', 'source-suffix'])
    rebulk.string('HC', 'vost', value='Hardcoded Subtitles')

    rebulk.string('SDR', value='Standard Dynamic Range', tags='uhdbluray-neighbor')
    rebulk.regex('HDR(?:10)?', value='HDR10', tags='uhdbluray-neighbor')
    rebulk.regex('Dolby-?Vision', value='Dolby Vision', tags='uhdbluray-neighbor')
    rebulk.regex('BT-?2020', value='BT.2020', tags='uhdbluray-neighbor')

    rebulk.string('Sample', value='Sample', tags=['at-end', 'not-a-release-group'])
    rebulk.string('Extras', value='Extras', tags='has-neighbor')
    rebulk.regex('Digital-?Extras?', value='Extras')
    rebulk.string('Proof', value='Proof', tags=['at-end', 'not-a-release-group'])
    rebulk.string('Obfuscated', 'Scrambled', value='Obfuscated', tags=['at-end', 'not-a-release-group'])
    rebulk.string('xpost', 'postbot', 'asrequested', value='Repost', tags='not-a-release-group')

    rebulk.rules(RenameAnotherToOther, ValidateHasNeighbor, ValidateHasNeighborAfter, ValidateHasNeighborBefore,
                 ValidateScreenerRule, ValidateMuxRule, ValidateHardcodedSubs, ValidateStreamingServiceNeighbor,
                 ValidateAtEnd, ValidateReal, ProperCountRule)

    return rebulk


class ProperCountRule(Rule):
    """
    Add proper_count property
    """
    priority = POST_PROCESS

    consequence = AppendMatch

    properties = {'proper_count': [None]}

    def when(self, matches, context):  # pylint:disable=inconsistent-return-statements
        propers = matches.named('other', lambda match: match.value == 'Proper')
        if propers:
            raws = {}  # Count distinct raw values
            for proper in propers:
                raws[raw_cleanup(proper.raw)] = proper
            proper_count_match = copy.copy(propers[-1])
            proper_count_match.name = 'proper_count'

            value = 0
            for raw in raws.values():
                value += 2 if 'real' in raw.tags else 1

            proper_count_match.value = value
            return proper_count_match


class RenameAnotherToOther(Rule):
    """
    Rename `another` properties to `other`
    """
    priority = 32
    consequence = RenameMatch('other')

    def when(self, matches, context):
        return matches.named('another')


class ValidateHasNeighbor(Rule):
    """
    Validate tag has-neighbor
    """
    consequence = RemoveMatch
    priority = 64

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
    priority = 64

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
    priority = 64

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
            source_match = matches.previous(screener, lambda match: match.initiator.name == 'source', 0)
            if not source_match or matches.input_string[source_match.end:screener.start].strip(seps):
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
            source_match = matches.previous(mux, lambda match: match.initiator.name == 'source', 0)
            if not source_match:
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
                                   predicate=lambda m: (m.initiator.name != 'source'
                                                        and ('streaming_service.prefix' in m.tags
                                                             or 'streaming_service.suffix' in m.tags))):
            match = match.initiator
            if not seps_after(match):
                if 'streaming_service.prefix' in match.tags:
                    next_match = matches.next(match, lambda m: m.name == 'streaming_service', 0)
                    if next_match and not matches.holes(match.end, next_match.start,
                                                        predicate=lambda m: m.value.strip(seps)):
                        continue
                if match.children:
                    to_remove.extend(match.children)
                to_remove.append(match)

            elif not seps_before(match):
                if 'streaming_service.suffix' in match.tags:
                    previous_match = matches.previous(match, lambda m: m.name == 'streaming_service', 0)
                    if previous_match and not matches.holes(previous_match.end, match.start,
                                                            predicate=lambda m: m.value.strip(seps)):
                        continue

                if match.children:
                    to_remove.extend(match.children)
                to_remove.append(match)

        return to_remove


class ValidateAtEnd(Rule):
    """Validate other which should occur at the end of a filepart."""

    priority = 32
    consequence = RemoveMatch

    def when(self, matches, context):
        to_remove = []
        for filepart in matches.markers.named('path'):
            for match in matches.range(filepart.start, filepart.end,
                                       predicate=lambda m: m.name == 'other' and 'at-end' in m.tags):
                if (matches.holes(match.end, filepart.end, predicate=lambda m: m.value.strip(seps)) or
                        matches.range(match.end, filepart.end, predicate=lambda m: m.name not in (
                            'other', 'container'))):
                    to_remove.append(match)

        return to_remove


class ValidateReal(Rule):
    """
    Validate Real
    """
    consequence = RemoveMatch
    priority = 64

    def when(self, matches, context):
        ret = []
        for filepart in matches.markers.named('path'):
            for match in matches.range(filepart.start, filepart.end, lambda m: m.name == 'other' and 'real' in m.tags):
                if not matches.range(filepart.start, match.start):
                    ret.append(match)

        return ret

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
streaming_service property
"""
from rebulk.remodule import re

from rebulk import Rebulk
from rebulk.rules import Rule, RemoveMatch

from ..common.pattern import is_disabled
from ...config import load_config_patterns
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

    load_config_patterns(rebulk, config)

    rebulk.rules(ValidateStreamingService)

    return rebulk


class ValidateStreamingService(Rule):
    """Validate streaming service matches."""

    priority = 128
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

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mimetype property
"""
import mimetypes

from rebulk import Rebulk, CustomRule, POST_PROCESS
from rebulk.match import Match

from ..common.pattern import is_disabled
from ...rules.processors import Processors


def mimetype(config):  # pylint:disable=unused-argument
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk(disabled=lambda context: is_disabled(context, 'mimetype'))
    rebulk.rules(Mimetype)

    return rebulk


class Mimetype(CustomRule):
    """
    Mimetype post processor
    :param matches:
    :type matches:
    :return:
    :rtype:
    """
    priority = POST_PROCESS

    dependency = Processors

    def when(self, matches, context):
        mime, _ = mimetypes.guess_type(matches.input_string, strict=False)
        return mime

    def then(self, matches, when_response, context):
        mime = when_response
        matches.append(Match(len(matches.input_string), len(matches.input_string), name='mimetype', value=mime))

    @property
    def properties(self):
        """
        Properties for this rule.
        """
        return {'mimetype': [None]}

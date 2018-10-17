#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mimetype property
"""
import mimetypes

from rebulk import Rebulk, CustomRule, POST_PROCESS
from rebulk.match import Match

from ...rules.processors import Processors


def mimetype():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    return Rebulk().rules(Mimetype)


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

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Expected property factory
"""
import re

from rebulk import Rebulk
from rebulk.utils import find_all

from . import dash, seps


def build_expected_function(context_key):
    """
    Creates a expected property function
    :param context_key:
    :type context_key:
    :param cleanup:
    :type cleanup:
    :return:
    :rtype:
    """

    def expected(input_string, context):
        """
        Expected property functional pattern.
        :param input_string:
        :type input_string:
        :param context:
        :type context:
        :return:
        :rtype:
        """
        ret = []
        for search in context.get(context_key):
            if search.startswith('re:'):
                search = search[3:]
                search = search.replace(' ', '-')
                matches = Rebulk().regex(search, abbreviations=[dash], flags=re.IGNORECASE) \
                    .matches(input_string, context)
                for match in matches:
                    ret.append(match.span)
            else:
                value = search
                for sep in seps:
                    input_string = input_string.replace(sep, ' ')
                    search = search.replace(sep, ' ')
                for start in find_all(input_string, search, ignore_case=True):
                    ret.append({'start': start, 'end': start + len(search), 'value': value})
        return ret

    return expected

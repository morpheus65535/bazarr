#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utils for re module
"""

from rebulk.remodule import re


def build_or_pattern(patterns, name=None, escape=False):
    """
    Build a or pattern string from a list of possible patterns

    :param patterns:
    :type patterns:
    :param name:
    :type name:
    :param escape:
    :type escape:
    :return:
    :rtype:
    """
    or_pattern = []
    for pattern in patterns:
        if not or_pattern:
            or_pattern.append('(?')
            if name:
                or_pattern.append('P<' + name + '>')
            else:
                or_pattern.append(':')
        else:
            or_pattern.append('|')
        or_pattern.append('(?:%s)' % re.escape(pattern) if escape else pattern)
    or_pattern.append(')')
    return ''.join(or_pattern)

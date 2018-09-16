#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pattern utility functions
"""


def is_disabled(context, name):
    """Whether a specific pattern is disabled.

    The context object might define an inclusion list (includes) or an exclusion list (excludes)
    A pattern is considered disabled if it's found in the exclusion list or
    it's not found in the inclusion list and the inclusion list is not empty or not defined.

    :param context:
    :param name:
    :return:
    """
    if not context:
        return False

    excludes = context.get('excludes')
    if excludes and name in excludes:
        return True

    includes = context.get('includes')
    return includes and name not in includes

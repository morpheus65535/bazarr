#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Formatter functions to use in patterns.

All those function have last argument as match.value (str).
"""


def formatters(*chained_formatters):
    """
    Chain formatter functions.
    :param chained_formatters:
    :type chained_formatters:
    :return:
    :rtype:
    """

    def formatters_chain(input_string):  # pylint:disable=missing-docstring
        for chained_formatter in chained_formatters:
            input_string = chained_formatter(input_string)
        return input_string

    return formatters_chain


def default_formatter(input_string):
    """
    Default formatter
    :param input_string:
    :return:
    """
    return input_string

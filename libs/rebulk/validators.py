#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Validator functions to use in patterns.

All those function have last argument as match, so it's possible to use functools.partial to bind previous arguments.
"""


def chars_before(chars, match):
    """
    Validate the match if left character is in a given sequence.

    :param chars:
    :type chars:
    :param match:
    :type match:
    :return:
    :rtype:
    """
    if match.start <= 0:
        return True
    return match.input_string[match.start - 1] in chars


def chars_after(chars, match):
    """
    Validate the match if right character is in a given sequence.

    :param chars:
    :type chars:
    :param match:
    :type match:
    :return:
    :rtype:
    """
    if match.end >= len(match.input_string):
        return True
    return match.input_string[match.end] in chars


def chars_surround(chars, match):
    """
    Validate the match if surrounding characters are in a given sequence.

    :param chars:
    :type chars:
    :param match:
    :type match:
    :return:
    :rtype:
    """
    return chars_before(chars, match) and chars_after(chars, match)


def validators(*chained_validators):
    """
    Creates a validator chain from several validator functions.

    :param chained_validators:
    :type chained_validators:
    :return:
    :rtype:
    """

    def validator_chain(match):  # pylint:disable=missing-docstring
        for chained_validator in chained_validators:
            if not chained_validator(match):
                return False
        return True

    return validator_chain


def allways_true(match):  # pylint:disable=unused-argument
    """
    A validator which is allways true
    :param match:
    :return:
    """
    return True

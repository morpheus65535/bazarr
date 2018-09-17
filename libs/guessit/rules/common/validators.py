#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Validators
"""
from functools import partial

from rebulk.validators import chars_before, chars_after, chars_surround
from . import seps

seps_before = partial(chars_before, seps)
seps_after = partial(chars_after, seps)
seps_surround = partial(chars_surround, seps)


def int_coercable(string):
    """
    Check if string can be coerced to int
    :param string:
    :type string:
    :return:
    :rtype:
    """
    try:
        int(string)
        return True
    except ValueError:
        return False


def compose(*validators):
    """
    Compose validators functions
    :param validators:
    :type validators:
    :return:
    :rtype:
    """
    def composed(string):
        """
        Composed validators function
        :param string:
        :type string:
        :return:
        :rtype:
        """
        for validator in validators:
            if not validator(string):
                return False
        return True
    return composed

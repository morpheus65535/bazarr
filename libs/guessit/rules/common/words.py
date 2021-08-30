#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Words utils
"""
from collections import namedtuple

from . import seps

_Word = namedtuple('_Word', ['span', 'value'])


def iter_words(string):
    """
    Iterate on all words in a string
    :param string:
    :type string:
    :return:
    :rtype: iterable[str]
    """
    i = 0
    last_sep_index = -1
    inside_word = False
    for char in string:
        if ord(char) < 128 and char in seps:  # Make sure we don't exclude unicode characters.
            if inside_word:
                yield _Word(span=(last_sep_index+1, i), value=string[last_sep_index+1:i])
            inside_word = False
            last_sep_index = i
        else:
            inside_word = True
        i += 1
    if inside_word:
        yield _Word(span=(last_sep_index+1, i), value=string[last_sep_index+1:i])

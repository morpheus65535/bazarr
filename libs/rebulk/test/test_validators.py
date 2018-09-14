#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, pointless-statement, missing-docstring, invalid-name,len-as-condition

from functools import partial

from rebulk.pattern import StringPattern

from ..validators import chars_before, chars_after, chars_surround, validators

chars = ' _.'
left = partial(chars_before, chars)
right = partial(chars_after, chars)
surrounding = partial(chars_surround, chars)


def test_left_chars():
    matches = list(StringPattern("word", validator=left).matches("xxxwordxxx"))
    assert len(matches) == 0

    matches = list(StringPattern("word", validator=left).matches("xxx_wordxxx"))
    assert len(matches) == 1

    matches = list(StringPattern("word", validator=left).matches("wordxxx"))
    assert len(matches) == 1


def test_right_chars():
    matches = list(StringPattern("word", validator=right).matches("xxxwordxxx"))
    assert len(matches) == 0

    matches = list(StringPattern("word", validator=right).matches("xxxword.xxx"))
    assert len(matches) == 1

    matches = list(StringPattern("word", validator=right).matches("xxxword"))
    assert len(matches) == 1


def test_surrounding_chars():
    matches = list(StringPattern("word", validator=surrounding).matches("xxxword xxx"))
    assert len(matches) == 0

    matches = list(StringPattern("word", validator=surrounding).matches("xxx.wordxxx"))
    assert len(matches) == 0

    matches = list(StringPattern("word", validator=surrounding).matches("xxx word_xxx"))
    assert len(matches) == 1

    matches = list(StringPattern("word", validator=surrounding).matches("word"))
    assert len(matches) == 1


def test_chain():
    matches = list(StringPattern("word", validator=validators(left, right)).matches("xxxword xxx"))
    assert len(matches) == 0

    matches = list(StringPattern("word", validator=validators(left, right)).matches("xxx.wordxxx"))
    assert len(matches) == 0

    matches = list(StringPattern("word", validator=validators(left, right)).matches("xxx word_xxx"))
    assert len(matches) == 1

    matches = list(StringPattern("word", validator=validators(left, right)).matches("word"))
    assert len(matches) == 1

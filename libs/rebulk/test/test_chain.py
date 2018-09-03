#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, pointless-statement, missing-docstring, no-member, len-as-condition
import re

from functools import partial

from ..validators import chars_surround
from ..rebulk import Rebulk, FunctionalPattern, RePattern, StringPattern


def test_chain_close():
    rebulk = Rebulk()
    ret = rebulk.chain().close()

    assert ret == rebulk
    assert len(rebulk.effective_patterns()) == 1


def test_build_chain():
    rebulk = Rebulk()

    def digit(input_string):
        i = input_string.find("1849")
        if i > -1:
            return i, i + len("1849")

    ret = rebulk.chain() \
        .functional(digit) \
        .string("test").repeater(2) \
        .string("x").repeater('{1,3}') \
        .string("optional").repeater('?') \
        .regex("f?x").repeater('+') \
        .close()

    assert ret == rebulk
    assert len(rebulk.effective_patterns()) == 1

    chain = rebulk.effective_patterns()[0]

    assert len(chain.parts) == 5

    assert isinstance(chain.parts[0].pattern, FunctionalPattern)
    assert chain.parts[0].repeater_start == 1
    assert chain.parts[0].repeater_end == 1

    assert isinstance(chain.parts[1].pattern, StringPattern)
    assert chain.parts[1].repeater_start == 2
    assert chain.parts[1].repeater_end == 2

    assert isinstance(chain.parts[2].pattern, StringPattern)
    assert chain.parts[2].repeater_start == 1
    assert chain.parts[2].repeater_end == 3

    assert isinstance(chain.parts[3].pattern, StringPattern)
    assert chain.parts[3].repeater_start == 0
    assert chain.parts[3].repeater_end == 1

    assert isinstance(chain.parts[4].pattern, RePattern)
    assert chain.parts[4].repeater_start == 1
    assert chain.parts[4].repeater_end is None


def test_chain_defaults():
    rebulk = Rebulk()
    rebulk.defaults(validator=lambda x: True, ignore_names=['testIgnore'], children=True)

    rebulk.chain()\
        .regex("(?P<test>test)") \
        .regex(" ").repeater("*") \
        .regex("(?P<testIgnore>testIgnore)")
    matches = rebulk.matches("test testIgnore")

    assert len(matches) == 1
    assert matches[0].name == "test"


def test_matches():
    rebulk = Rebulk()

    def digit(input_string):
        i = input_string.find("1849")
        if i > -1:
            return i, i + len("1849")

    input_string = "1849testtestxxfixfux_foxabc1849testtestxoptionalfoxabc"

    chain = rebulk.chain() \
        .functional(digit) \
        .string("test").hidden().repeater(2) \
        .string("x").hidden().repeater('{1,3}') \
        .string("optional").hidden().repeater('?') \
        .regex("f.?x", name='result').repeater('+') \
        .close()

    matches = chain.matches(input_string)

    assert len(matches) == 2
    children = matches[0].children

    assert children[0].value == '1849'
    assert children[1].value == 'fix'
    assert children[2].value == 'fux'

    children = matches[1].children
    assert children[0].value == '1849'
    assert children[1].value == 'fox'

    input_string = "_1850testtestxoptionalfoxabc"
    matches = chain.matches(input_string)

    assert len(matches) == 0

    input_string = "_1849testtesttesttestxoptionalfoxabc"
    matches = chain.matches(input_string)

    assert len(matches) == 0

    input_string = "_1849testtestxxxxoptionalfoxabc"
    matches = chain.matches(input_string)

    assert len(matches) == 0

    input_string = "_1849testtestoptionalfoxabc"
    matches = chain.matches(input_string)

    assert len(matches) == 0

    input_string = "_1849testtestxoptionalabc"
    matches = chain.matches(input_string)

    assert len(matches) == 0

    input_string = "_1849testtestxoptionalfaxabc"
    matches = chain.matches(input_string)

    assert len(matches) == 1
    children = matches[0].children

    assert children[0].value == '1849'
    assert children[1].value == 'fax'


def test_matches_2():
    rebulk = Rebulk() \
        .regex_defaults(flags=re.IGNORECASE) \
        .chain(children=True, formatter={'episode': int}) \
        .defaults(formatter={'version': int}) \
        .regex(r'e(?P<episode>\d{1,4})') \
        .regex(r'v(?P<version>\d+)').repeater('?') \
        .regex(r'[ex-](?P<episode>\d{1,4})').repeater('*') \
        .close()

    matches = rebulk.matches("This is E14v2-15E16x17")
    assert len(matches) == 5

    assert matches[0].name == 'episode'
    assert matches[0].value == 14

    assert matches[1].name == 'version'
    assert matches[1].value == 2

    assert matches[2].name == 'episode'
    assert matches[2].value == 15

    assert matches[3].name == 'episode'
    assert matches[3].value == 16

    assert matches[4].name == 'episode'
    assert matches[4].value == 17


def test_matches_3():
    alt_dash = (r'@', r'[\W_]')  # abbreviation

    rebulk = Rebulk()

    rebulk.chain(formatter={'season': int, 'episode': int},
                 tags=['SxxExx'],
                 abbreviations=[alt_dash],
                 private_names=['episodeSeparator', 'seasonSeparator'],
                 children=True,
                 private_parent=True,
                 conflict_solver=lambda match, other: match
                 if match.name in ['season', 'episode'] and other.name in
                 ['screen_size', 'video_codec', 'audio_codec',
                  'audio_channels', 'container', 'date']
                 else '__default__') \
        .regex(r'(?P<season>\d+)@?x@?(?P<episode>\d+)') \
        .regex(r'(?P<episodeSeparator>x|-|\+|&)(?P<episode>\d+)').repeater('*') \
        .chain() \
        .regex(r'S(?P<season>\d+)@?(?:xE|Ex|E|x)@?(?P<episode>\d+)') \
        .regex(r'(?:(?P<episodeSeparator>xE|Ex|E|x|-|\+|&)(?P<episode>\d+))').repeater('*') \
        .chain() \
        .regex(r'S(?P<season>\d+)') \
        .regex(r'(?P<seasonSeparator>S|-|\+|&)(?P<season>\d+)').repeater('*')

    matches = rebulk.matches("test-01x02-03")
    assert len(matches) == 3

    assert matches[0].name == 'season'
    assert matches[0].value == 1

    assert matches[1].name == 'episode'
    assert matches[1].value == 2

    assert matches[2].name == 'episode'
    assert matches[2].value == 3

    matches = rebulk.matches("test-S01E02-03")

    assert len(matches) == 3
    assert matches[0].name == 'season'
    assert matches[0].value == 1

    assert matches[1].name == 'episode'
    assert matches[1].value == 2

    assert matches[2].name == 'episode'
    assert matches[2].value == 3

    matches = rebulk.matches("test-S01-02-03-04")

    assert len(matches) == 4
    assert matches[0].name == 'season'
    assert matches[0].value == 1

    assert matches[1].name == 'season'
    assert matches[1].value == 2

    assert matches[2].name == 'season'
    assert matches[2].value == 3

    assert matches[3].name == 'season'
    assert matches[3].value == 4


def test_matches_4():
    seps_surround = partial(chars_surround, " ")

    rebulk = Rebulk()
    rebulk.regex_defaults(flags=re.IGNORECASE)
    rebulk.defaults(private_names=['episodeSeparator', 'seasonSeparator'], validate_all=True,
                    validator={'__parent__': seps_surround}, children=True, private_parent=True)

    rebulk.chain(formatter={'episode': int, 'version': int}) \
        .defaults(validator=None) \
        .regex(r'e(?P<episode>\d{1,4})') \
        .regex(r'v(?P<version>\d+)').repeater('?') \
        .regex(r'(?P<episodeSeparator>e|x|-)(?P<episode>\d{1,4})').repeater('*')

    matches = rebulk.matches("Some Series E01E02E03")
    assert len(matches) == 3

    assert matches[0].value == 1
    assert matches[1].value == 2
    assert matches[2].value == 3


def test_matches_5():
    seps_surround = partial(chars_surround, " ")

    rebulk = Rebulk()
    rebulk.regex_defaults(flags=re.IGNORECASE)
    rebulk.defaults(private_names=['episodeSeparator', 'seasonSeparator'], validate_all=True,
                    validator={'__parent__': seps_surround}, children=True, private_parent=True)

    rebulk.chain(formatter={'episode': int, 'version': int}) \
        .defaults(validator=None) \
        .regex(r'e(?P<episode>\d{1,4})') \
        .regex(r'v(?P<version>\d+)').repeater('?') \
        .regex(r'(?P<episodeSeparator>e|x|-)(?P<episode>\d{1,4})').repeater('{2,3}')

    matches = rebulk.matches("Some Series E01E02E03")
    assert len(matches) == 3

    matches = rebulk.matches("Some Series E01E02")
    assert len(matches) == 0

    matches = rebulk.matches("Some Series E01E02E03E04E05E06")  # Parent can't be validated, so no results at all
    assert len(matches) == 0


def test_matches_6():
    rebulk = Rebulk()
    rebulk.regex_defaults(flags=re.IGNORECASE)
    rebulk.defaults(private_names=['episodeSeparator', 'seasonSeparator'], validate_all=True,
                    validator=None, children=True, private_parent=True)

    rebulk.chain(formatter={'episode': int, 'version': int}) \
        .defaults(validator=None) \
        .regex(r'e(?P<episode>\d{1,4})') \
        .regex(r'v(?P<version>\d+)').repeater('?') \
        .regex(r'(?P<episodeSeparator>e|x|-)(?P<episode>\d{1,4})').repeater('{2,3}')

    matches = rebulk.matches("Some Series E01E02E03")
    assert len(matches) == 3

    matches = rebulk.matches("Some Series E01E02")
    assert len(matches) == 0

    matches = rebulk.matches("Some Series E01E02E03E04E05E06")  # No validator on parent, so it should give 4 episodes.
    assert len(matches) == 4


def test_matches_7():
    seps_surround = partial(chars_surround, ' .-/')
    rebulk = Rebulk()
    rebulk.regex_defaults(flags=re.IGNORECASE)
    rebulk.defaults(children=True, private_parent=True)

    rebulk.chain(). \
        regex(r'S(?P<season>\d+)', validate_all=True, validator={'__parent__': seps_surround}). \
        regex(r'[ -](?P<season>\d+)', validator=seps_surround).repeater('*')

    matches = rebulk.matches("Some S01")
    assert len(matches) == 1
    matches[0].value = 1

    matches = rebulk.matches("Some S01-02")
    assert len(matches) == 2
    matches[0].value = 1
    matches[1].value = 2

    matches = rebulk.matches("programs4/Some S01-02")
    assert len(matches) == 2
    matches[0].value = 1
    matches[1].value = 2

    matches = rebulk.matches("programs4/SomeS01middle.S02-03.andS04here")
    assert len(matches) == 2
    matches[0].value = 2
    matches[1].value = 3

    matches = rebulk.matches("Some 02.and.S04-05.here")
    assert len(matches) == 2
    matches[0].value = 4
    matches[1].value = 5


def test_chain_breaker():
    def chain_breaker(matches):
        seasons = matches.named('season')
        if len(seasons) > 1:
            if seasons[-1].value - seasons[-2].value > 10:
                return True
        return False

    seps_surround = partial(chars_surround, ' .-/')
    rebulk = Rebulk()
    rebulk.regex_defaults(flags=re.IGNORECASE)
    rebulk.defaults(children=True, private_parent=True, formatter={'season': int})

    rebulk.chain(chain_breaker=chain_breaker). \
        regex(r'S(?P<season>\d+)', validate_all=True, validator={'__parent__': seps_surround}). \
        regex(r'[ -](?P<season>\d+)', validator=seps_surround).repeater('*')

    matches = rebulk.matches("Some S01-02-03-50-51")
    assert len(matches) == 3
    matches[0].value = 1
    matches[1].value = 2
    matches[2].value = 3


def test_chain_breaker_defaults():
    def chain_breaker(matches):
        seasons = matches.named('season')
        if len(seasons) > 1:
            if seasons[-1].value - seasons[-2].value > 10:
                return True
        return False

    seps_surround = partial(chars_surround, ' .-/')
    rebulk = Rebulk()
    rebulk.regex_defaults(flags=re.IGNORECASE)
    rebulk.defaults(chain_breaker=chain_breaker, children=True, private_parent=True, formatter={'season': int})

    rebulk.chain(). \
        regex(r'S(?P<season>\d+)', validate_all=True, validator={'__parent__': seps_surround}). \
        regex(r'[ -](?P<season>\d+)', validator=seps_surround).repeater('*')

    matches = rebulk.matches("Some S01-02-03-50-51")
    assert len(matches) == 3
    matches[0].value = 1
    matches[1].value = 2
    matches[2].value = 3


def test_chain_breaker_defaults2():
    def chain_breaker(matches):
        seasons = matches.named('season')
        if len(seasons) > 1:
            if seasons[-1].value - seasons[-2].value > 10:
                return True
        return False

    seps_surround = partial(chars_surround, ' .-/')
    rebulk = Rebulk()
    rebulk.regex_defaults(flags=re.IGNORECASE)
    rebulk.chain_defaults(chain_breaker=chain_breaker)
    rebulk.defaults(children=True, private_parent=True, formatter={'season': int})

    rebulk.chain(). \
        regex(r'S(?P<season>\d+)', validate_all=True, validator={'__parent__': seps_surround}). \
        regex(r'[ -](?P<season>\d+)', validator=seps_surround).repeater('*')

    matches = rebulk.matches("Some S01-02-03-50-51")
    assert len(matches) == 3
    matches[0].value = 1
    matches[1].value = 2
    matches[2].value = 3

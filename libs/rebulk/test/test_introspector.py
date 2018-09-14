#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Introspector tests
"""
# pylint: disable=no-self-use,pointless-statement,missing-docstring,protected-access,invalid-name,len-as-condition
from ..rebulk import Rebulk
from .. import introspector
from .default_rules_module import RuleAppend2, RuleAppend3


def test_string_introspector():
    rebulk = Rebulk().string('One', 'Two', 'Three', name='first').string('1', '2', '3', name='second')

    introspected = introspector.introspect(rebulk, None)

    assert len(introspected.patterns) == 2

    first_properties = introspected.patterns[0].properties
    assert len(first_properties) == 1
    first_properties['first'] == ['One', 'Two', 'Three']

    second_properties = introspected.patterns[1].properties
    assert len(second_properties) == 1
    second_properties['second'] == ['1', '2', '3']

    properties = introspected.properties
    assert len(properties) == 2
    assert properties['first'] == first_properties['first']
    assert properties['second'] == second_properties['second']


def test_string_properties():
    rebulk = Rebulk()\
        .string('One', 'Two', 'Three', name='first', properties={'custom': ['One']})\
        .string('1', '2', '3', name='second', properties={'custom': [1]})

    introspected = introspector.introspect(rebulk, None)

    assert len(introspected.patterns) == 2
    assert len(introspected.rules) == 2

    first_properties = introspected.patterns[0].properties
    assert len(first_properties) == 1
    first_properties['custom'] == ['One']

    second_properties = introspected.patterns[1].properties
    assert len(second_properties) == 1
    second_properties['custom'] == [1]

    properties = introspected.properties
    assert len(properties) == 1
    assert properties['custom'] == ['One', 1]


def test_various_pattern():
    rebulk = Rebulk()\
        .regex('One', 'Two', 'Three', name='first', value="string") \
        .string('1', '2', '3', name='second', value="digit") \
        .string('4', '5', '6', name='third') \
        .string('private', private=True) \
        .functional(lambda string: (0, 5), name='func', value='test') \
        .regex('One', 'Two', 'Three', name='regex_name') \
        .regex('(?P<one>One)(?P<two>Two)(?P<three>Three)') \
        .functional(lambda string: (6, 10), name='func2') \
        .string('7', name='third')

    introspected = introspector.introspect(rebulk, None)

    assert len(introspected.patterns) == 8
    assert len(introspected.rules) == 2

    first_properties = introspected.patterns[0].properties
    assert len(first_properties) == 1
    first_properties['first'] == ['string']

    second_properties = introspected.patterns[1].properties
    assert len(second_properties) == 1
    second_properties['second'] == ['digit']

    third_properties = introspected.patterns[2].properties
    assert len(third_properties) == 1
    third_properties['third'] == ['4', '5', '6']

    func_properties = introspected.patterns[3].properties
    assert len(func_properties) == 1
    func_properties['func'] == ['test']

    regex_name_properties = introspected.patterns[4].properties
    assert len(regex_name_properties) == 1
    regex_name_properties['regex_name'] == [None]

    regex_groups_properties = introspected.patterns[5].properties
    assert len(regex_groups_properties) == 3
    regex_groups_properties['one'] == [None]
    regex_groups_properties['two'] == [None]
    regex_groups_properties['three'] == [None]

    func2_properties = introspected.patterns[6].properties
    assert len(func2_properties) == 1
    func2_properties['func2'] == [None]

    append_third_properties = introspected.patterns[7].properties
    assert len(append_third_properties) == 1
    append_third_properties['third'] == [None]

    properties = introspected.properties
    assert len(properties) == 9
    assert properties['first'] == first_properties['first']
    assert properties['second'] == second_properties['second']
    assert properties['third'] == third_properties['third'] + append_third_properties['third']
    assert properties['func'] == func_properties['func']
    assert properties['regex_name'] == regex_name_properties['regex_name']
    assert properties['one'] == regex_groups_properties['one']
    assert properties['two'] == regex_groups_properties['two']
    assert properties['three'] == regex_groups_properties['three']
    assert properties['func2'] == func2_properties['func2']


def test_rule_properties():
    rebulk = Rebulk(default_rules=False).rules(RuleAppend2, RuleAppend3)

    introspected = introspector.introspect(rebulk, None)

    assert len(introspected.rules) == 2
    assert len(introspected.patterns) == 0

    rule_properties = introspected.rules[0].properties
    assert len(rule_properties) == 1
    assert rule_properties['renamed'] == [None]

    rule_properties = introspected.rules[1].properties
    assert len(rule_properties) == 1
    assert rule_properties['renamed'] == [None]

    properties = introspected.properties
    assert len(properties) == 1
    assert properties['renamed'] == [None]

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, pointless-statement, missing-docstring, protected-access, invalid-name, len-as-condition

from ..pattern import StringPattern
from ..rebulk import Rebulk
from ..match import Match
from .. import debug
from .default_rules_module import RuleRemove0


class TestDebug(object):


    #request.addfinalizer(disable_debug)



    debug.DEBUG = True
    pattern = StringPattern(1, 3, value="es")

    match = Match(1, 3, value="es")
    rule = RuleRemove0()

    input_string = "This is a debug test"
    rebulk = Rebulk().string("debug") \
        .string("is")

    matches = rebulk.matches(input_string)
    debug.DEBUG = False

    @classmethod
    def setup_class(cls):
        debug.DEBUG = True

    @classmethod
    def teardown_class(cls):
        debug.DEBUG = False

    def test_pattern(self):
        assert self.pattern.defined_at.lineno == 20
        assert self.pattern.defined_at.name == 'rebulk.test.test_debug'
        assert self.pattern.defined_at.filename.endswith('test_debug.py')

        assert str(self.pattern.defined_at) == 'test_debug.py#L20'
        assert repr(self.pattern) == '<StringPattern@test_debug.py#L20:(1, 3)>'

    def test_match(self):
        assert self.match.defined_at.lineno == 22
        assert self.match.defined_at.name == 'rebulk.test.test_debug'
        assert self.match.defined_at.filename.endswith('test_debug.py')

        assert str(self.match.defined_at) == 'test_debug.py#L22'

    def test_rule(self):
        assert self.rule.defined_at.lineno == 23
        assert self.rule.defined_at.name == 'rebulk.test.test_debug'
        assert self.rule.defined_at.filename.endswith('test_debug.py')

        assert str(self.rule.defined_at) == 'test_debug.py#L23'
        assert repr(self.rule) == '<RuleRemove0@test_debug.py#L23>'

    def test_rebulk(self):
        """
        This test fails on travis CI, can't find out why there's 1 line offset ...
        """
        assert self.rebulk._patterns[0].defined_at.lineno in [26, 27]
        assert self.rebulk._patterns[0].defined_at.name == 'rebulk.test.test_debug'
        assert self.rebulk._patterns[0].defined_at.filename.endswith('test_debug.py')

        assert str(self.rebulk._patterns[0].defined_at) in ['test_debug.py#L26', 'test_debug.py#L27']

        assert self.rebulk._patterns[1].defined_at.lineno in [27, 28]
        assert self.rebulk._patterns[1].defined_at.name == 'rebulk.test.test_debug'
        assert self.rebulk._patterns[1].defined_at.filename.endswith('test_debug.py')

        assert str(self.rebulk._patterns[1].defined_at) in ['test_debug.py#L27', 'test_debug.py#L28']

        assert self.matches[0].defined_at == self.rebulk._patterns[0].defined_at
        assert self.matches[1].defined_at == self.rebulk._patterns[1].defined_at

    def test_repr(self):
        str(self.matches)

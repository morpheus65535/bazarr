#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, pointless-statement, missing-docstring, protected-access, invalid-name, len-as-condition

from .default_rules_module import RuleRemove0
from .. import debug
from ..match import Match
from ..pattern import StringPattern
from ..rebulk import Rebulk


class TestDebug(object):
    # request.addfinalizer(disable_debug)

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
        assert self.pattern.defined_at.lineno > 0
        assert self.pattern.defined_at.name == 'rebulk.test.test_debug'
        assert self.pattern.defined_at.filename.endswith('test_debug.py')

        assert str(self.pattern.defined_at).startswith('test_debug.py#L')
        assert repr(self.pattern).startswith('<StringPattern@test_debug.py#L')

    def test_match(self):
        assert self.match.defined_at.lineno > 0
        assert self.match.defined_at.name == 'rebulk.test.test_debug'
        assert self.match.defined_at.filename.endswith('test_debug.py')

        assert str(self.match.defined_at).startswith('test_debug.py#L')

    def test_rule(self):
        assert self.rule.defined_at.lineno > 0
        assert self.rule.defined_at.name == 'rebulk.test.test_debug'
        assert self.rule.defined_at.filename.endswith('test_debug.py')

        assert str(self.rule.defined_at).startswith('test_debug.py#L')
        assert repr(self.rule).startswith('<RuleRemove0@test_debug.py#L')

    def test_rebulk(self):
        """
        This test fails on travis CI, can't find out why there's 1 line offset ...
        """
        assert self.rebulk._patterns[0].defined_at.lineno > 0
        assert self.rebulk._patterns[0].defined_at.name == 'rebulk.test.test_debug'
        assert self.rebulk._patterns[0].defined_at.filename.endswith('test_debug.py')

        assert str(self.rebulk._patterns[0].defined_at).startswith('test_debug.py#L')

        assert self.rebulk._patterns[1].defined_at.lineno > 0
        assert self.rebulk._patterns[1].defined_at.name == 'rebulk.test.test_debug'
        assert self.rebulk._patterns[1].defined_at.filename.endswith('test_debug.py')

        assert str(self.rebulk._patterns[1].defined_at).startswith('test_debug.py#L')

        assert self.matches[0].defined_at == self.rebulk._patterns[0].defined_at
        assert self.matches[1].defined_at == self.rebulk._patterns[1].defined_at

    def test_repr(self):
        str(self.matches)

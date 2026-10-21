#!/usr/bin/env python

from .. import debug
from ..match import Match
from ..pattern import StringPattern
from ..rebulk import Rebulk
from .default_rules_module import RuleRemove0


class TestDebug:
    # request.addfinalizer(disable_debug)

    debug.DEBUG = True
    pattern = StringPattern(1, 3, value="es")

    match = Match(1, 3, value="es")
    rule = RuleRemove0()

    input_string = "This is a debug test"
    rebulk = Rebulk().string("debug").string("is")

    matches = rebulk.matches(input_string)
    debug.DEBUG = False

    @classmethod
    def setup_class(cls) -> None:
        debug.DEBUG = True

    @classmethod
    def teardown_class(cls) -> None:
        debug.DEBUG = False

    def test_pattern(self) -> None:
        defined = self.pattern.defined_at
        assert defined is not None
        assert defined.lineno > 0
        assert defined.name == "rebulk.test.test_debug"
        assert defined.filename.endswith("test_debug.py")

        assert str(self.pattern.defined_at).startswith("test_debug.py#L")
        assert repr(self.pattern).startswith("<StringPattern@test_debug.py#L")

    def test_match(self) -> None:
        defined = self.match.defined_at
        assert defined is not None
        assert defined.lineno > 0
        assert defined.name == "rebulk.test.test_debug"
        assert defined.filename.endswith("test_debug.py")

        assert str(self.match.defined_at).startswith("test_debug.py#L")

    def test_rule(self) -> None:
        defined = self.rule.defined_at
        assert defined is not None
        assert defined.lineno > 0
        assert defined.name == "rebulk.test.test_debug"
        assert defined.filename.endswith("test_debug.py")

        assert str(self.rule.defined_at).startswith("test_debug.py#L")
        assert repr(self.rule).startswith("<RuleRemove0@test_debug.py#L")

    def test_rebulk(self) -> None:
        defined0 = self.rebulk._patterns[0].defined_at
        assert defined0 is not None
        assert defined0.lineno > 0
        assert defined0.name == "rebulk.test.test_debug"
        assert defined0.filename.endswith("test_debug.py")

        assert str(self.rebulk._patterns[0].defined_at).startswith("test_debug.py#L")

        defined1 = self.rebulk._patterns[1].defined_at
        assert defined1 is not None
        assert defined1.lineno > 0
        assert defined1.name == "rebulk.test.test_debug"
        assert defined1.filename.endswith("test_debug.py")

        assert str(self.rebulk._patterns[1].defined_at).startswith("test_debug.py#L")

        assert self.matches[0].defined_at == self.rebulk._patterns[0].defined_at
        assert self.matches[1].defined_at == self.rebulk._patterns[1].defined_at

    def test_repr(self) -> None:
        str(self.matches)

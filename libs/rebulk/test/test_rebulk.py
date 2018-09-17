#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, pointless-statement, missing-docstring, no-member, len-as-condition

from ..rebulk import Rebulk
from ..rules import Rule
from . import rebulk_rules_module as rm


def test_rebulk_simple():
    rebulk = Rebulk()

    rebulk.string("quick")
    rebulk.regex("f.x")

    def func(input_string):
        i = input_string.find("over")
        if i > -1:
            return i, i + len("over")

    rebulk.functional(func)

    input_string = "The quick brown fox jumps over the lazy dog"

    matches = rebulk.matches(input_string)
    assert len(matches) == 3

    assert matches[0].value == "quick"
    assert matches[1].value == "fox"
    assert matches[2].value == "over"


def test_rebulk_composition():
    rebulk = Rebulk()

    rebulk.string("quick")
    rebulk.rebulk(Rebulk().regex("f.x"))

    rebulk.rebulk(Rebulk(disabled=lambda context: True).functional(lambda string: None))

    input_string = "The quick brown fox jumps over the lazy dog"

    matches = rebulk.matches(input_string)
    assert len(matches) == 2

    assert matches[0].value == "quick"
    assert matches[1].value == "fox"


def test_rebulk_context():
    rebulk = Rebulk()

    context = {'nostring': True, 'word': 'lazy'}

    rebulk.string("quick", disabled=lambda context: context.get('nostring', False))
    rebulk.regex("f.x", disabled=lambda context: context.get('noregex', False))

    def func(input_string, context):
        word = context.get('word', 'over')
        i = input_string.find(word)
        if i > -1:
            return i, i + len(word)

    rebulk.functional(func)

    input_string = "The quick brown fox jumps over the lazy dog"

    matches = rebulk.matches(input_string, context)
    assert len(matches) == 2

    assert matches[0].value == "fox"
    assert matches[1].value == "lazy"


def test_rebulk_prefer_longer():
    input_string = "The quick brown fox jumps over the lazy dog"

    matches = Rebulk().string("quick").string("own").regex("br.{2}n").matches(input_string)

    assert len(matches) == 2

    assert matches[0].value == "quick"
    assert matches[1].value == "brown"


def test_rebulk_defaults():
    input_string = "The quick brown fox jumps over the lazy dog"

    def func(input_string):
        i = input_string.find("fox")
        if i > -1:
            return i, i + len("fox")

    matches = Rebulk()\
        .string_defaults(name="string", tags=["a", "b"])\
        .regex_defaults(name="regex") \
        .functional_defaults(name="functional") \
        .string("quick", tags=["c"])\
        .functional(func)\
        .regex("br.{2}n") \
        .matches(input_string)
    assert matches[0].name == "string"
    assert matches[0].tags == ["a", "b", "c"]
    assert matches[1].name == "functional"
    assert matches[2].name == "regex"

    matches = Rebulk() \
        .defaults(name="default", tags=["0"])\
        .string_defaults(name="string", tags=["a", "b"]) \
        .functional_defaults(name="functional", tags=["1"]) \
        .string("quick", tags=["c"]) \
        .functional(func) \
        .regex("br.{2}n") \
        .matches(input_string)
    assert matches[0].name == "string"
    assert matches[0].tags == ["0", "a", "b", "c"]
    assert matches[1].name == "functional"
    assert matches[1].tags == ["0", "1"]
    assert matches[2].name == "default"
    assert matches[2].tags == ["0"]


def test_rebulk_rebulk():
    input_string = "The quick brown fox jumps over the lazy dog"

    base = Rebulk().string("quick")
    child = Rebulk().string("own").regex("br.{2}n")

    matches = base.rebulk(child).matches(input_string)

    assert len(matches) == 2

    assert matches[0].value == "quick"
    assert matches[1].value == "brown"


def test_rebulk_no_default():
    input_string = "The quick brown fox jumps over the lazy dog"

    matches = Rebulk(default_rules=False).string("quick").string("own").regex("br.{2}n").matches(input_string)

    assert len(matches) == 3

    assert matches[0].value == "quick"
    assert matches[1].value == "own"
    assert matches[2].value == "brown"


def test_rebulk_empty_match():
    input_string = "The quick brown fox jumps over the lazy dog"

    matches = Rebulk(default_rules=False).string("quick").string("own").regex("br(.*?)own", children=True)\
        .matches(input_string)

    assert len(matches) == 2

    assert matches[0].value == "quick"
    assert matches[1].value == "own"


def test_rebulk_tags_names():
    rebulk = Rebulk()

    rebulk.string("quick", name="str", tags=["first", "other"])
    rebulk.regex("f.x", tags="other")

    def func(input_string):
        i = input_string.find("over")
        if i > -1:
            return i, i + len("over"), {'tags': ['custom']}

    rebulk.functional(func, name="fn")

    def func2(input_string):
        i = input_string.find("lazy")
        if i > -1:
            return {'start': i, 'end': i + len("lazy"), 'tags': ['custom']}

    rebulk.functional(func2, name="fn")

    input_string = "The quick brown fox jumps over the lazy dog"

    matches = rebulk.matches(input_string)
    assert len(matches) == 4

    assert len(matches.named("str")) == 1
    assert len(matches.named("fn")) == 2
    assert len(matches.named("false")) == 0
    assert len(matches.tagged("false")) == 0
    assert len(matches.tagged("first")) == 1
    assert len(matches.tagged("other")) == 2
    assert len(matches.tagged("custom")) == 2


def test_rebulk_rules_1():
    rebulk = Rebulk()

    rebulk.regex(r'\d{4}', name="year")
    rebulk.rules(rm.RemoveAllButLastYear)

    matches = rebulk.matches("1984 keep only last 1968 entry 1982 case")
    assert len(matches) == 1
    assert matches[0].value == "1982"


def test_rebulk_rules_2():
    rebulk = Rebulk()

    rebulk.regex(r'\d{4}', name="year")
    rebulk.string(r'year', name="yearPrefix", private=True)
    rebulk.string(r'keep', name="yearSuffix", private=True)
    rebulk.rules(rm.PrefixedSuffixedYear)

    matches = rebulk.matches("Keep suffix 1984 keep prefixed year 1968 and remove the rest 1982")
    assert len(matches) == 2
    assert matches[0].value == "1984"
    assert matches[1].value == "1968"


def test_rebulk_rules_3():
    rebulk = Rebulk()

    rebulk.regex(r'\d{4}', name="year")
    rebulk.string(r'year', name="yearPrefix", private=True)
    rebulk.string(r'keep', name="yearSuffix", private=True)
    rebulk.rules(rm.PrefixedSuffixedYearNoLambda)

    matches = rebulk.matches("Keep suffix 1984 keep prefixed year 1968 and remove the rest 1982")
    assert len(matches) == 2
    assert matches[0].value == "1984"
    assert matches[1].value == "1968"


def test_rebulk_rules_4():
    class FirstOnlyRule(Rule):
        def when(self, matches, context):
            grabbed = matches.named("grabbed", 0)
            if grabbed and matches.previous(grabbed):
                return grabbed

        def then(self, matches, when_response, context):
            matches.remove(when_response)

    rebulk = Rebulk()

    rebulk.regex("This match (.*?)grabbed", name="grabbed")
    rebulk.regex("if it's (.*?)first match", private=True)

    rebulk.rules(FirstOnlyRule)

    matches = rebulk.matches("This match is grabbed only if it's the first match")
    assert len(matches) == 1
    assert matches[0].value == "This match is grabbed"

    matches = rebulk.matches("if it's NOT the first match, This match is NOT grabbed")
    assert len(matches) == 0


class TestMarkers(object):
    def test_one_marker(self):
        class MarkerRule(Rule):
            def when(self, matches, context):
                word_match = matches.named("word", 0)
                marker = matches.markers.at_match(word_match, lambda marker: marker.name == "mark1", 0)
                if not marker:
                    return word_match

            def then(self, matches, when_response, context):
                matches.remove(when_response)

        rebulk = Rebulk().regex(r'\(.*?\)', marker=True, name="mark1") \
            .regex(r'\[.*?\]', marker=True, name="mark2") \
            .string("word", name="word") \
            .rules(MarkerRule)

        matches = rebulk.matches("grab (word) only if it's in parenthesis")

        assert len(matches) == 1
        assert matches[0].value == "word"

        matches = rebulk.matches("don't grab [word] if it's in braket")
        assert len(matches) == 0

        matches = rebulk.matches("don't grab word at all")
        assert len(matches) == 0

    def test_multiple_marker(self):
        class MarkerRule(Rule):
            def when(self, matches, context):
                word_match = matches.named("word", 0)
                marker = matches.markers.at_match(word_match,
                                                  lambda marker: marker.name == "mark1" or marker.name == "mark2")
                if len(marker) < 2:
                    return word_match

            def then(self, matches, when_response, context):
                matches.remove(when_response)

        rebulk = Rebulk().regex(r'\(.*?\)', marker=True, name="mark1") \
            .regex(r'\[.*?\]', marker=True, name="mark2") \
            .regex("w.*?d", name="word") \
            .rules(MarkerRule)

        matches = rebulk.matches("[grab (word) only] if it's in parenthesis and brakets")

        assert len(matches) == 1
        assert matches[0].value == "word"

        matches = rebulk.matches("[don't grab](word)[if brakets are outside]")
        assert len(matches) == 0

        matches = rebulk.matches("(grab w[or)d even] if it's partially in parenthesis and brakets")
        assert len(matches) == 1
        assert matches[0].value == "w[or)d"

    def test_at_index_marker(self):
        class MarkerRule(Rule):
            def when(self, matches, context):
                word_match = matches.named("word", 0)
                marker = matches.markers.at_index(word_match.start,
                                                  lambda marker: marker.name == "mark1", 0)
                if not marker:
                    return word_match

            def then(self, matches, when_response, context):
                matches.remove(when_response)

        rebulk = Rebulk().regex(r'\(.*?\)', marker=True, name="mark1") \
            .regex("w.*?d", name="word") \
            .rules(MarkerRule)

        matches = rebulk.matches("gr(ab wo)rd only if starting of match is inside parenthesis")

        assert len(matches) == 1
        assert matches[0].value == "wo)rd"

        matches = rebulk.matches("don't grab wo(rd if starting of match is not inside parenthesis")

        assert len(matches) == 0

    def test_remove_marker(self):
        class MarkerRule(Rule):
            def when(self, matches, context):
                marker = matches.markers.named("mark1", 0)
                if marker:
                    return marker

            def then(self, matches, when_response, context):
                matches.markers.remove(when_response)

        rebulk = Rebulk().regex(r'\(.*?\)', marker=True, name="mark1") \
            .regex("w.*?d", name="word") \
            .rules(MarkerRule)

        matches = rebulk.matches("grab word event (if it's not) inside parenthesis")

        assert len(matches) == 1
        assert matches[0].value == "word"

        assert not matches.markers


class TestUnicode(object):
    def test_rebulk_simple(self):
        input_string = u"敏捷的棕色狐狸跳過懶狗"

        rebulk = Rebulk()

        rebulk.string(u"敏")
        rebulk.regex(u"捷")

        def func(input_string):
            i = input_string.find(u"的")
            if i > -1:
                return i, i + len(u"的")

        rebulk.functional(func)

        matches = rebulk.matches(input_string)
        assert len(matches) == 3

        assert matches[0].value == u"敏"
        assert matches[1].value == u"捷"
        assert matches[2].value == u"的"


class TestImmutable(object):
    def test_starting(self):
        input_string = "The quick brown fox jumps over the lazy dog"
        matches = Rebulk().string("quick").string("over").string("fox").matches(input_string)

        for i in range(0, len(input_string)):
            starting = matches.starting(i)
            for match in list(starting):
                starting.remove(match)

        assert len(matches) == 3

    def test_ending(self):
        input_string = "The quick brown fox jumps over the lazy dog"
        matches = Rebulk().string("quick").string("over").string("fox").matches(input_string)

        for i in range(0, len(input_string)):
            starting = matches.ending(i)
            for match in list(starting):
                starting.remove(match)

        assert len(matches) == 3

    def test_named(self):
        input_string = "The quick brown fox jumps over the lazy dog"
        matches = Rebulk().defaults(name='test').string("quick").string("over").string("fox").matches(input_string)

        named = matches.named('test')
        for match in list(named):
            named.remove(match)

        assert len(named) == 0
        assert len(matches) == 3

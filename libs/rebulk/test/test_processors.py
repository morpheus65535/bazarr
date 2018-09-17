#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, pointless-statement, missing-docstring, no-member, len-as-condition

from ..pattern import StringPattern, RePattern
from ..processors import ConflictSolver
from ..rules import execute_rule
from ..match import Matches


def test_conflict_1():
    input_string = "abcdefghijklmnopqrstuvwxyz"

    pattern = StringPattern("ijklmn", "kl", "abcdef", "ab", "ef", "yz")
    matches = Matches(pattern.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)

    values = [x.value for x in matches]

    assert values == ["ijklmn", "abcdef", "yz"]


def test_conflict_2():
    input_string = "abcdefghijklmnopqrstuvwxyz"

    pattern = StringPattern("ijklmn", "jklmnopqrst")
    matches = Matches(pattern.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)

    values = [x.value for x in matches]

    assert values == ["jklmnopqrst"]


def test_conflict_3():
    input_string = "abcdefghijklmnopqrstuvwxyz"

    pattern = StringPattern("ijklmnopqrst", "jklmnopqrst")
    matches = Matches(pattern.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)

    values = [x.value for x in matches]

    assert values == ["ijklmnopqrst"]


def test_conflict_4():
    input_string = "123456789"

    pattern = StringPattern("123", "456789")
    matches = Matches(pattern.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)

    values = [x.value for x in matches]
    assert values == ["123", "456789"]


def test_conflict_5():
    input_string = "123456789"

    pattern = StringPattern("123456", "789")
    matches = Matches(pattern.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)

    values = [x.value for x in matches]
    assert values == ["123456", "789"]


def test_prefer_longer_parent():
    input_string = "xxx.1x02.xxx"

    re1 = RePattern("([0-9]+)x([0-9]+)", name='prefer', children=True, formatter=int)
    re2 = RePattern("x([0-9]+)", name='skip', children=True)

    matches = Matches(re1.matches(input_string))
    matches.extend(re2.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)
    assert len(matches) == 2
    assert matches[0].value == 1
    assert matches[1].value == 2


def test_conflict_solver_1():
    input_string = "123456789"

    re1 = StringPattern("2345678", conflict_solver=lambda match, conflicting: '__default__')
    re2 = StringPattern("34567")

    matches = Matches(re1.matches(input_string))
    matches.extend(re2.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)
    assert len(matches) == 1
    assert matches[0].value == "2345678"


def test_conflict_solver_2():
    input_string = "123456789"

    re1 = StringPattern("2345678", conflict_solver=lambda match, conflicting: '__default__')
    re2 = StringPattern("34567", conflict_solver=lambda match, conflicting: conflicting)

    matches = Matches(re1.matches(input_string))
    matches.extend(re2.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)
    assert len(matches) == 1
    assert matches[0].value == "34567"


def test_conflict_solver_3():
    input_string = "123456789"

    re1 = StringPattern("2345678", conflict_solver=lambda match, conflicting: match)
    re2 = StringPattern("34567")

    matches = Matches(re1.matches(input_string))
    matches.extend(re2.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)
    assert len(matches) == 1
    assert matches[0].value == "34567"


def test_conflict_solver_4():
    input_string = "123456789"

    re1 = StringPattern("2345678")
    re2 = StringPattern("34567", conflict_solver=lambda match, conflicting: conflicting)

    matches = Matches(re1.matches(input_string))
    matches.extend(re2.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)
    assert len(matches) == 1
    assert matches[0].value == "34567"


def test_conflict_solver_5():
    input_string = "123456789"

    re1 = StringPattern("2345678", conflict_solver=lambda match, conflicting: conflicting)
    re2 = StringPattern("34567")

    matches = Matches(re1.matches(input_string))
    matches.extend(re2.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)
    assert len(matches) == 1
    assert matches[0].value == "2345678"


def test_conflict_solver_6():
    input_string = "123456789"

    re1 = StringPattern("2345678")
    re2 = StringPattern("34567", conflict_solver=lambda match, conflicting: conflicting)

    matches = Matches(re1.matches(input_string))
    matches.extend(re2.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)
    assert len(matches) == 1
    assert matches[0].value == "34567"


def test_conflict_solver_7():
    input_string = "102"

    re1 = StringPattern("102")
    re2 = StringPattern("02")

    matches = Matches(re2.matches(input_string))
    matches.extend(re1.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)
    assert len(matches) == 1
    assert matches[0].value == "102"


def test_unresolved():
    input_string = "123456789"

    re1 = StringPattern("23456")
    re2 = StringPattern("34567")

    matches = Matches(re1.matches(input_string))
    matches.extend(re2.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)
    assert len(matches) == 2

    re1 = StringPattern("34567")
    re2 = StringPattern("2345678", conflict_solver=lambda match, conflicting: None)

    matches = Matches(re1.matches(input_string))
    matches.extend(re2.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)
    assert len(matches) == 2

    re1 = StringPattern("34567", conflict_solver=lambda match, conflicting: None)
    re2 = StringPattern("2345678")

    matches = Matches(re1.matches(input_string))
    matches.extend(re2.matches(input_string))

    execute_rule(ConflictSolver(), matches, None)
    assert len(matches) == 2

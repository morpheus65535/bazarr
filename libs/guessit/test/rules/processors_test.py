#!/usr/bin/env python

from rebulk.match import Match, Matches

from ...rules.processors import StripSeparators


def test_strip_separators() -> None:
    strip_separators = StripSeparators()

    matches = Matches()

    m = Match(3, 11, input_string="pre.ABCDEF.post")

    assert m.raw == ".ABCDEF."
    matches.append(m)

    returned_matches = strip_separators.when(matches, None)
    assert returned_matches == matches

    strip_separators.then(matches, returned_matches, None)

    assert m.raw == "ABCDEF"


def test_strip_separators_keep_acronyms() -> None:
    strip_separators = StripSeparators()

    matches = Matches()

    m = Match(0, 13, input_string=".S.H.I.E.L.D.")
    m2 = Match(0, 22, input_string=".Agent.Of.S.H.I.E.L.D.")

    assert m.raw == ".S.H.I.E.L.D."
    matches.append(m)
    matches.append(m2)

    returned_matches = strip_separators.when(matches, None)
    assert returned_matches == matches

    strip_separators.then(matches, returned_matches, None)

    assert m.raw == ".S.H.I.E.L.D."
    assert m2.raw == "Agent.Of.S.H.I.E.L.D."

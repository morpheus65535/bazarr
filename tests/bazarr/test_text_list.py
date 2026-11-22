import logging

import pytest

from utilities.text_list import parse_text_list, parse_text_list_or_default


def test_parse_text_list_accepts_none_only_as_a_complete_token():
    assert parse_text_list("[None, 'en']") == [None, "en"]

    with pytest.raises(ValueError):
        parse_text_list("[Nonexistent]")


def test_parse_text_list_or_default_logs_invalid_legacy_values(caplog):
    caplog.set_level(logging.DEBUG, logger="utilities.text_list")

    assert parse_text_list_or_default("[True]", default=["en"]) == ["en"]
    assert "Could not parse text list '[True]'" in caplog.text
    assert "invalid text-list syntax" in caplog.text


def test_parse_text_list_round_trips_python_repr_escapes():
    values = ["line\nbreak", "tab\tvalue", "\x01", "separator\u2028", r"literal\backslash"]

    assert parse_text_list(repr(values)) == values
    assert parse_text_list(r"['\u2603', '\U0001f40d', '\x50']") == ["☃", "🐍", "P"]

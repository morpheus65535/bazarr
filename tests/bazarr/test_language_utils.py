# -*- coding: utf-8 -*-
"""
Tests for parse_language_token in subtitles/language_utils.py, used by adaptive searching.
"""
import pytest

from subtitles.language_utils import parse_language_token


# The request tuple is (language, hi, forced), matching download.generate_subtitles.
@pytest.mark.parametrize(
    "token, expected",
    [
        ("en", ("en", ("en", "False", "False"))),
        ("EN:HI", ("en:hi", ("en", "True", "False"))),
        ("en:forced:hi", ("en:forced:hi", ("en", "True", "True"))),
        ("hi:forced", ("hi:forced", ("hi", "False", "True"))),
        (" en : forced ", ("en:forced", ("en", "False", "True"))),
        ("en:hi:hi", ("en:hi", ("en", "True", "False"))),
        ("en:", ("en", ("en", "False", "False"))),
    ],
)
def test_parse_language_token_canonicalizes(token, expected):
    assert parse_language_token(token) == expected


@pytest.mark.parametrize("token", ["en:sdh", ":hi", "   ", None, 3])
def test_parse_language_token_rejects_invalid(token):
    assert parse_language_token(token) is None

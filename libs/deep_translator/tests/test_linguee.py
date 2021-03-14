#!/usr/bin/env python

"""Tests for `deep_translator` package."""

import pytest
from deep_translator import exceptions, LingueeTranslator


@pytest.fixture
def linguee():
    return LingueeTranslator(source="english", target='french')


def test_content(linguee):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string
    assert linguee.translate(word='good') is not None


def test_inputs():
    with pytest.raises(exceptions.LanguageNotSupportedException):
        LingueeTranslator(source="", target="")

    with pytest.raises(exceptions.LanguageNotSupportedException):
        LingueeTranslator(source="auto", target="nothing")

    l1 = LingueeTranslator("en", "fr")
    l2 = LingueeTranslator("english", "french")
    assert l1._source == l2._source
    assert l1._target == l2._target


def test_payload(linguee):

    with pytest.raises(exceptions.NotValidPayload):
        linguee.translate("")

    with pytest.raises(exceptions.NotValidPayload):
        linguee.translate(123)

    with pytest.raises(exceptions.NotValidPayload):
        linguee.translate({})

    with pytest.raises(exceptions.NotValidPayload):
        linguee.translate([])

    with pytest.raises(exceptions.NotValidLength):
        linguee.translate("a"*51)

#!/usr/bin/env python

"""Tests for `deep_translator` package."""

import pytest
from deep_translator import exceptions, MyMemoryTranslator


@pytest.fixture
def mymemory():
    return MyMemoryTranslator(source="en", target='fr')


def test_content(mymemory):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string
    assert mymemory.translate(text='good') is not None


def test_inputs():
    with pytest.raises(exceptions.LanguageNotSupportedException):
        MyMemoryTranslator(source="", target="")

    with pytest.raises(exceptions.LanguageNotSupportedException):
        MyMemoryTranslator(source="auto", target="nothing")
    m1 = MyMemoryTranslator("en", "fr")
    m2 = MyMemoryTranslator("english", "french")
    assert m1._source == m2._source
    assert m1._target == m2._target


def test_payload(mymemory):

    with pytest.raises(exceptions.NotValidPayload):
        mymemory.translate(text="")

    with pytest.raises(exceptions.NotValidPayload):
        mymemory.translate(text=123)

    with pytest.raises(exceptions.NotValidPayload):
        mymemory.translate(text={})

    with pytest.raises(exceptions.NotValidPayload):
        mymemory.translate(text=[])

    with pytest.raises(exceptions.NotValidLength):
        mymemory.translate(text="a"*501)

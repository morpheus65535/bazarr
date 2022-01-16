#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, pointless-statement, missing-docstring, invalid-name, pointless-string-statement
import json
import os
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from .. import api
from ..api import guessit, properties, suggested_expected, GuessitException, default_api

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def test_default():
    ret = guessit('Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv')
    assert ret and 'title' in ret


def test_forced_unicode():
    ret = guessit('Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv')
    assert ret and 'title' in ret and isinstance(ret['title'], str)


def test_forced_binary():
    ret = guessit(b'Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv')
    assert ret and 'title' in ret and isinstance(ret['title'], bytes)


def test_pathlike_object():
    path = Path('Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv')
    ret = guessit(path)
    assert ret and 'title' in ret


def test_unicode_japanese():
    ret = guessit('[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi')
    assert ret and 'title' in ret


def test_unicode_japanese_options():
    ret = guessit("[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi", options={"expected_title": ["阿维达"]})
    assert ret and 'title' in ret and ret['title'] == "阿维达"


def test_forced_unicode_japanese_options():
    ret = guessit("[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi", options={"expected_title": ["阿维达"]})
    assert ret and 'title' in ret and ret['title'] == "阿维达"


def test_properties():
    props = properties()
    assert 'video_codec' in props.keys()


def test_exception():
    with pytest.raises(GuessitException) as excinfo:
        guessit(object())
    assert "An internal error has occured in guessit" in str(excinfo.value)
    assert "Guessit Exception Report" in str(excinfo.value)
    assert "Please report at https://github.com/guessit-io/guessit/issues" in str(excinfo.value)


def test_suggested_expected():
    with open(os.path.join(__location__, 'suggested.json'), 'r', encoding='utf-8') as f:
        content = json.load(f)
    actual = suggested_expected(content['titles'])
    assert actual == content['suggested']


def test_should_rebuild_rebulk_on_advanced_config_change(mocker: MockerFixture):
    api.reset()
    rebulk_builder_spy = mocker.spy(api, 'rebulk_builder')

    string = "some.movie.trfr.mkv"

    result1 = default_api.guessit(string)

    assert result1.get('title') == 'some movie trfr'
    assert 'subtitle_language' not in result1

    rebulk_builder_spy.assert_called_once_with(mocker.ANY)
    rebulk_builder_spy.reset_mock()

    result2 = default_api.guessit(string, {'advanced_config': {'language': {'subtitle_prefixes': ['tr']}}})

    assert result2.get('title') == 'some movie'
    assert str(result2.get('subtitle_language')) == 'fr'

    rebulk_builder_spy.assert_called_once_with(mocker.ANY)
    rebulk_builder_spy.reset_mock()


def test_should_not_rebuild_rebulk_on_same_advanced_config(mocker: MockerFixture):
    api.reset()
    rebulk_builder_spy = mocker.spy(api, 'rebulk_builder')

    string = "some.movie.subfr.mkv"

    result1 = default_api.guessit(string)

    assert result1.get('title') == 'some movie'
    assert str(result1.get('subtitle_language')) == 'fr'

    rebulk_builder_spy.assert_called_once_with(mocker.ANY)
    rebulk_builder_spy.reset_mock()

    result2 = default_api.guessit(string)

    assert result2.get('title') == 'some movie'
    assert str(result2.get('subtitle_language')) == 'fr'

    assert rebulk_builder_spy.call_count == 0
    rebulk_builder_spy.reset_mock()

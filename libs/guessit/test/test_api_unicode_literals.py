#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, pointless-statement, missing-docstring, invalid-name, pointless-string-statement


import os

import pytest

from ..api import guessit, properties, GuessitException

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


def test_unicode_japanese():
    ret = guessit('[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi')
    assert ret and 'title' in ret


def test_unicode_japanese_options():
    ret = guessit("[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi", options={"expected_title": ["阿维达"]})
    assert ret and 'title' in ret and ret['title'] == "阿维达"


def test_forced_unicode_japanese_options():
    ret = guessit("[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi", options={"expected_title": ["阿维达"]})
    assert ret and 'title' in ret and ret['title'] == "阿维达"


def test_ensure_custom_string_class():
    class CustomStr(str):
        pass

    ret = guessit(CustomStr('some.title.1080p.mkv'), options={'advanced': True})
    assert ret and 'screen_size' in ret and isinstance(ret['screen_size'].input_string, CustomStr)
    assert ret and 'title' in ret and isinstance(ret['title'].input_string, CustomStr)
    assert ret and 'container' in ret and isinstance(ret['container'].input_string, CustomStr)


def test_properties():
    props = properties()
    assert 'video_codec' in props.keys()


def test_exception():
    with pytest.raises(GuessitException) as excinfo:
        guessit(object())
    assert "An internal error has occured in guessit" in str(excinfo.value)
    assert "Guessit Exception Report" in str(excinfo.value)
    assert "Please report at https://github.com/guessit-io/guessit/issues" in str(excinfo.value)

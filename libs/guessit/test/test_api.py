#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, pointless-statement, missing-docstring, invalid-name, pointless-string-statement
import json
import os
import sys

import pytest
import six

from ..api import guessit, properties, suggested_expected, GuessitException

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def test_default():
    ret = guessit('Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv')
    assert ret and 'title' in ret


def test_forced_unicode():
    ret = guessit(u'Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv')
    assert ret and 'title' in ret and isinstance(ret['title'], six.text_type)


def test_forced_binary():
    ret = guessit(b'Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv')
    assert ret and 'title' in ret and isinstance(ret['title'], six.binary_type)


@pytest.mark.skipif(sys.version_info < (3, 4), reason="Path is not available")
def test_pathlike_object():
    try:
        from pathlib import Path

        path = Path('Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv')
        ret = guessit(path)
        assert ret and 'title' in ret
    except ImportError:  # pragma: no-cover
        pass


def test_unicode_japanese():
    ret = guessit('[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi')
    assert ret and 'title' in ret


def test_unicode_japanese_options():
    ret = guessit("[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi", options={"expected_title": ["阿维达"]})
    assert ret and 'title' in ret and ret['title'] == "阿维达"


def test_forced_unicode_japanese_options():
    ret = guessit(u"[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi", options={"expected_title": [u"阿维达"]})
    assert ret and 'title' in ret and ret['title'] == u"阿维达"

# TODO: This doesn't compile on python 3, but should be tested on python 2.
"""
if six.PY2:
    def test_forced_binary_japanese_options():
        ret = guessit(b"[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi", options={"expected_title": [b"阿维达"]})
        assert ret and 'title' in ret and ret['title'] == b"阿维达"
"""


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
    with open(os.path.join(__location__, 'suggested.json'), 'r') as f:
        content = json.load(f)
    actual = suggested_expected(content['titles'])
    assert actual == content['suggested']

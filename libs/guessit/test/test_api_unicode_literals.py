#!/usr/bin/env python


import os

import pytest

from ..api import GuessitException, guessit, properties

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def test_default() -> None:
    ret = guessit("Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv")
    assert ret
    assert "title" in ret


def test_forced_unicode() -> None:
    ret = guessit("Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv")
    assert ret
    assert "title" in ret
    assert isinstance(ret["title"], str)


def test_forced_binary() -> None:
    ret = guessit(b"Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv")
    assert ret
    assert "title" in ret
    assert isinstance(ret["title"], bytes)


def test_unicode_japanese() -> None:
    ret = guessit("[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi")
    assert ret
    assert "title" in ret


def test_unicode_japanese_options() -> None:
    ret = guessit("[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi", options={"expected_title": ["阿维达"]})
    assert ret
    assert "title" in ret
    assert ret["title"] == "阿维达"


def test_forced_unicode_japanese_options() -> None:
    ret = guessit("[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi", options={"expected_title": ["阿维达"]})
    assert ret
    assert "title" in ret
    assert ret["title"] == "阿维达"


def test_ensure_custom_string_class() -> None:
    class CustomStr(str):
        pass

    ret = guessit(CustomStr("some.title.1080p.mkv"), options={"advanced": True})
    assert ret
    assert "screen_size" in ret
    assert isinstance(ret["screen_size"].input_string, CustomStr)
    assert ret
    assert "title" in ret
    assert isinstance(ret["title"].input_string, CustomStr)
    assert ret
    assert "container" in ret
    assert isinstance(ret["container"].input_string, CustomStr)


def test_properties() -> None:
    props = properties()
    assert "video_codec" in props


def test_exception() -> None:
    with pytest.raises(GuessitException) as excinfo:
        guessit(object())  # type: ignore[arg-type]
    assert "An internal error has occurred in guessit" in str(excinfo.value)
    assert "Guessit Exception Report" in str(excinfo.value)
    assert "Please report at https://github.com/guessit-io/guessit/issues" in str(excinfo.value)

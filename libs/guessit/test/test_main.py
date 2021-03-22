#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, pointless-statement, missing-docstring, invalid-name
import json
import os
import sys

import pytest
from _pytest.capture import CaptureFixture

from ..__main__ import main

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


# Prevent output from spamming the console
@pytest.fixture(scope="function", autouse=True)
def no_stdout(monkeypatch):
    with open(os.devnull, "w") as f:
        monkeypatch.setattr(sys, "stdout", f)
        yield

def test_main_no_args():
    main([])


def test_main():
    main(['Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv'])


def test_main_unicode():
    main(['[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi'])


def test_main_forced_unicode():
    main(['Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv'])


def test_main_verbose():
    main(['Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv', '--verbose'])


def test_main_yaml():
    main(['Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv', '--yaml'])


def test_main_json():
    main(['Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv', '--json'])


def test_main_show_property():
    main(['Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv', '-P', 'title'])


def test_main_advanced():
    main(['Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv', '-a'])


def test_main_input():
    main(['--input', os.path.join(__location__, 'test-input-file.txt')])


def test_main_properties():
    main(['-p'])
    main(['-p', '--json'])
    main(['-p', '--yaml'])


def test_main_values():
    main(['-V'])
    main(['-V', '--json'])
    main(['-V', '--yaml'])


def test_main_help():
    with pytest.raises(SystemExit):
        main(['--help'])


def test_main_version():
    main(['--version'])


def test_json_output_input_string(capsys: CaptureFixture):
    main(['--json', '--output-input-string', 'test.avi'])

    outerr = capsys.readouterr()
    data = json.loads(outerr.out)

    assert 'input_string' in data
    assert data['input_string'] == 'test.avi'


def test_json_no_output_input_string(capsys: CaptureFixture):
    main(['--json', 'test.avi'])

    outerr = capsys.readouterr()
    data = json.loads(outerr.out)

    assert 'input_string' not in data

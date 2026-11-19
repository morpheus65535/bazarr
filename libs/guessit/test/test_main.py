#!/usr/bin/env python
import json
import os
import sys
from collections.abc import Iterator

import pytest
from _pytest.capture import CaptureFixture

from ..__main__ import main

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


# Prevent output from spamming the console
@pytest.fixture(autouse=True)
def no_stdout(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    with open(os.devnull, "w") as f:
        monkeypatch.setattr(sys, "stdout", f)
        yield


def test_main_no_args() -> None:
    main([])


def test_main() -> None:
    main(["Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv"])


def test_main_unicode() -> None:
    main(["[阿维达].Avida.2006.FRENCH.DVDRiP.XViD-PROD.avi"])


def test_main_forced_unicode() -> None:
    main(["Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv"])


def test_main_verbose() -> None:
    main(["Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv", "--verbose"])


def test_main_yaml() -> None:
    main(["Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv", "--yaml"])


def test_main_json() -> None:
    main(["Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv", "--json"])


def test_main_show_property() -> None:
    main(["Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv", "-P", "title"])


def test_main_advanced() -> None:
    main(["Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv", "-a"])


def test_main_input() -> None:
    main(["--input", os.path.join(__location__, "test-input-file.txt")])


def test_main_properties() -> None:
    main(["-p"])
    main(["-p", "--json"])
    main(["-p", "--yaml"])


def test_main_values() -> None:
    main(["-V"])
    main(["-V", "--json"])
    main(["-V", "--yaml"])


def test_main_schema() -> None:
    main(["--schema"])
    main(["--schema", "--json"])
    main(["--schema", "--yaml"])


def test_main_json_schema() -> None:
    main(["--json-schema"])
    main(["--json-schema", "--json"])
    main(["--json-schema", "--yaml"])


def test_main_json_schema_output(capsys: CaptureFixture[str]) -> None:
    main(["--json-schema", "--json"])
    outerr = capsys.readouterr()
    data = json.loads(outerr.out)
    assert "draft-07" in data["$schema"]
    assert "title" in data["properties"]


def test_main_help() -> None:
    with pytest.raises(SystemExit):
        main(["--help"])


def test_main_version() -> None:
    main(["--version"])


def test_json_output_input_string(capsys: CaptureFixture[str]) -> None:
    main(["--json", "--output-input-string", "test.avi"])

    outerr = capsys.readouterr()
    data = json.loads(outerr.out)

    assert "input_string" in data
    assert data["input_string"] == "test.avi"


def test_json_no_output_input_string(capsys: CaptureFixture[str]) -> None:
    main(["--json", "test.avi"])

    outerr = capsys.readouterr()
    data = json.loads(outerr.out)

    assert "input_string" not in data

#!/usr/bin/env python
import time
from typing import Any

import pytest

from ..api import guessit


def case1() -> dict[str, Any]:
    return guessit("Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv")


def case2() -> dict[str, Any]:
    return guessit(
        "Movies/Fantastic Mr Fox/Fantastic.Mr.Fox.2009.DVDRip.{x264+LC-AAC.5.1}{Fr-Eng}{Sub.Fr-Eng}-™.[sharethefiles.com].mkv"  # noqa: E501
    )


def case3() -> dict[str, Any]:
    return guessit("Series/dexter/Dexter.5x02.Hello,.Bandit.ENG.-.sub.FR.HDTV.XviD-AlFleNi-TeaM.[tvu.org.ru].avi")


def case4() -> dict[str, Any]:
    return guessit(
        "Movies/The Doors (1991)/09.03.08.The.Doors.(1991).BDRip.720p.AC3.X264-HiS@SiLUHD-English.[sharethefiles.com].mkv"  # noqa: E501
    )


@pytest.mark.benchmark(
    group="Performance Tests", min_time=1, max_time=2, min_rounds=5, timer=time.time, disable_gc=True, warmup=False
)
@pytest.mark.skipif(True, reason="Disabled")
class TestBenchmark:
    def test_case1(self, benchmark: Any) -> None:
        ret = benchmark(case1)
        assert ret

    def test_case2(self, benchmark: Any) -> None:
        ret = benchmark(case2)
        assert ret

    def test_case3(self, benchmark: Any) -> None:
        ret = benchmark(case3)
        assert ret

    def test_case4(self, benchmark: Any) -> None:
        ret = benchmark(case4)
        assert ret

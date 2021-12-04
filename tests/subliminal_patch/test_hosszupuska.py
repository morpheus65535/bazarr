# -*- coding: utf-8 -*-
import pytest

from subliminal_patch.core import Episode
from subliminal_patch.providers.hosszupuska import HosszupuskaProvider


@pytest.fixture
def episode():
    return Episode(
        "American Horror Story s10e01 (amzn webrip-ntb).mkv",
        "American Horror Story",
        10,
        1,
        source="Web",
    )


@pytest.mark.vcr
def test_list_subtitles_episode(episode):
    with HosszupuskaProvider() as provider:
        subs = provider.list_subtitles(episode, [])

    for expected in (
        "http://hosszupuskasub.com/download.php?file=0124336.zip",
        "http://hosszupuskasub.com/download.php?file=0124335.zip",
        "http://hosszupuskasub.com/download.php?file=0124333.zip",
        "http://hosszupuskasub.com/download.php?file=0124253.zip",
    ):
        assert any([expected == sub.page_link for sub in subs])


@pytest.mark.vcr
def test_download_subtitle_episode(episode):
    with HosszupuskaProvider() as provider:
        sub = provider.list_subtitles(episode, [])[0]
        provider.download_subtitle(sub)
        assert sub.content is not None

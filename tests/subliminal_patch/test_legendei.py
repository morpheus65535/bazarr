# -*- coding: utf-8 -*-
"""Offline (VCR cassette) tests for the legendei provider.

Delete the files under ``tests/subliminal_patch/cassettes/test_legendei/`` and re-run on a
connected machine to refresh the recordings.
"""
import pytest

from subliminal.cache import region
# RetryingCFSession uses dogpile for Cloudflare token storage; an in-memory backend is enough.
if not region.is_configured:
    region.configure("dogpile.cache.memory")

from subliminal_patch.providers.legendei import LegendeiProvider


@pytest.fixture
def languages():
    from subzero.language import Language
    return [Language("por", "BR")]


@pytest.mark.vcr
def test_list_subtitles_episode(episodes, languages):
    # breaking_bad_s01e01 has per-episode subtitles on legendei
    with LegendeiProvider() as provider:
        subs = provider.list_subtitles(episodes["breaking_bad_s01e01"], languages)

    assert len(subs) > 0
    for sub in subs:
        assert "?download=" in sub.download_link
        assert sub.page_link.startswith("https://legendei.net/")
    # the site's full-text search can surface unrelated titles (e.g. "The Bad Guys Breaking In");
    # what matters is that real Breaking Bad S01E01 releases are among the results
    assert any("breaking bad" in sub.release_name.lower() for sub in subs)


@pytest.mark.vcr
def test_list_subtitles_movie(movies, languages):
    with LegendeiProvider() as provider:
        subs = provider.list_subtitles(movies["dune"], languages)

    assert len(subs) > 0
    for sub in subs:
        assert "?download=" in sub.download_link
        assert "dune" in sub.release_name.lower()


@pytest.mark.vcr
def test_download_subtitle_episode(episodes, languages):
    with LegendeiProvider() as provider:
        sub = provider.list_subtitles(episodes["breaking_bad_s01e01"], languages)[0]
        provider.download_subtitle(sub)

    assert sub.content is not None
    # a valid SRT starts with the index "1" (after optional BOM)
    head = sub.content.lstrip(b"\xef\xbb\xbf")
    assert head[:1] == b"1"


@pytest.mark.vcr
def test_list_subtitles_inexistent(episodes, languages):
    with LegendeiProvider() as provider:
        subs = provider.list_subtitles(episodes["inexistent"], languages)

    assert subs == []


def test_list_subtitles_rejects_non_pt_br(episodes):
    # legendei only serves pt-BR; requesting another language must yield nothing
    from subzero.language import Language
    with LegendeiProvider() as provider:
        subs = provider.list_subtitles(episodes["breaking_bad_s01e01"], [Language("eng")])

    assert subs == []

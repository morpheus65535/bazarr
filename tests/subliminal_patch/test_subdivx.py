# -*- coding: utf-8 -*-

import pytest
from subliminal_patch.providers.subdivx import SubdivxSubtitlesProvider
from subliminal_patch.providers.subdivx import SubdivxSubtitle
from subzero.language import Language


@pytest.mark.vcr
def test_list_subtitles_movie(movies):
    item = movies["dune"]
    with SubdivxSubtitlesProvider() as provider:
        subtitles = provider.list_subtitles(item, {Language("spa", "MX")})
        assert subtitles
        assert len(subtitles) == 9


@pytest.mark.vcr
def test_list_subtitles_episode(episodes):
    item = episodes["breaking_bad_s01e01"]
    with SubdivxSubtitlesProvider() as provider:
        subtitles = provider.list_subtitles(item, {Language("spa", "MX")})
        assert subtitles
        assert len(subtitles) == 15


@pytest.mark.vcr
def test_download_subtitle(movies):
    subtitle = SubdivxSubtitle(
        Language("spa", "MX"),
        movies["dune"],
        "https://www.subdivx.com/X66XNjMxMTAxX-dune--2021-aka-dune-part-one.html",
        "Dune",
        "",
        "",
    )
    with SubdivxSubtitlesProvider() as provider:
        provider.download_subtitle(subtitle)
        assert subtitle.content is not None

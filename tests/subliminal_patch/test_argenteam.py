# -*- coding: utf-8 -*-

import pytest
import os
from subliminal_patch.providers.argenteam import ArgenteamProvider
from subliminal_patch.providers.argenteam import ArgenteamSubtitle
from subzero.language import Language


def test_get_matches_episode(episodes):
    episode = episodes["breaking_bad_s01e01"]
    subtitle = ArgenteamSubtitle(
        Language.fromalpha2("es"),
        None,
        "https://argenteam.net/subtitles/24002/Breaking.Bad.%282008%29.S01E01-Pilot.BluRay.x264.720p-REWARD",
        "BluRay x264 720p",
        {"title", "season", "episode", "imdb_id"},
    )
    matches = subtitle.get_matches(episode)
    assert matches == {
        "title",
        "season",
        "episode",
        "imdb_id",
        "source",
        "video_codec",
        "resolution",
        "edition",
        "streaming_service",
        "release_group",
        "series",
        "year",
    }


def test_get_matches_movie(movies):
    movie = movies["dune"]
    subtitle = ArgenteamSubtitle(
        Language.fromalpha2("es"),
        None,
        "https://argenteam.net/subtitles/86024/Dune.Part.One.%282021%29.WEB.H264.1080p-NAISU",
        "WEB H264 1080p",
        {"title", "year", "imdb_id"},
    )
    matches = subtitle.get_matches(movie)
    assert matches == {
        "title",
        "year",
        "imdb_id",
        "source",
        "resolution",
        "edition",
        "video_codec",
    }


@pytest.mark.vcr
def test_list_subtitles_movie(movies):
    item = movies["dune"]
    with ArgenteamProvider() as provider:
        subtitles = provider.list_subtitles(item, {Language("spa", "MX")})

    for expected in (
        "https://argenteam.net/subtitles/86023/Dune.Part.One.%282021%29.WEB.H264.720p-NAISU",
        "https://argenteam.net/subtitles/86024/Dune.Part.One.%282021%29.WEB.H264.1080p-NAISU",
        "https://argenteam.net/subtitles/86025/Dune.Part.One.%282021%29.WEB.x265.2160p-NAISU",
    ):
        assert any(expected == sub.download_link for sub in subtitles)


@pytest.mark.vcr
def test_list_subtitles_episode(episodes):
    item = episodes["breaking_bad_s01e01"]
    with ArgenteamProvider() as provider:
        subtitles = provider.list_subtitles(item, {Language("spa", "MX")})

    for expected in (
        "https://argenteam.net/subtitles/24002/Breaking.Bad.%282008%29.S01E01-Pilot.BluRay.x264.720p-REWARD",
        "https://argenteam.net/subtitles/23940/Breaking.Bad.%282008%29.S01E01-Pilot.DVDRip.XviD-ORPHEUS",
    ):
        assert any(expected == sub.download_link for sub in subtitles)


@pytest.mark.vcr
def test_download_subtitle(episodes):
    item = episodes["breaking_bad_s01e01"]
    with ArgenteamProvider() as provider:
        subtitles = provider.list_subtitles(item, {Language("spa", "MX")})
        subtitle = subtitles[0]
        provider.download_subtitle(subtitle)
        assert subtitle.content is not None

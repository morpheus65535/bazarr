# -*- coding: utf-8 -*-

import pytest
import os
from subliminal_patch.providers.argenteam import ArgenteamProvider
from subliminal_patch.providers.argenteam import ArgenteamSubtitle
from subliminal_patch.core import Episode
from subzero.language import Language


@pytest.mark.parametrize(
    "imdb_id,expected_id", [("tt0028950", 62790), ("tt0054407", 102006)]
)
def test_search_ids_movie(imdb_id, expected_id):
    with ArgenteamProvider() as provider:
        ids = provider._search_ids(imdb_id)
        assert ids[0] == expected_id


def test_search_ids_tv_show():
    with ArgenteamProvider() as provider:
        ids = provider._search_ids("tt0306414", season=1, episode=1)
        assert ids[0] == 10075


def test_parse_subtitles_episode():
    with ArgenteamProvider() as provider:
        assert len(provider._parse_subtitles([10075])) > 1


def test_parse_subtitles_movie():
    with ArgenteamProvider() as provider:
        assert len(provider._parse_subtitles([61], is_episode=False)) > 3


def test_get_matches_episode(episodes):
    episode = episodes["breaking_bad_s01e01"]
    subtitle = ArgenteamSubtitle(
        Language.fromalpha2("es"),
        None,
        "https://argenteam.net/subtitles/24002/Breaking.Bad.%282008%29.S01E01-Pilot.BluRay.x264.720p-REWARD",
        "Breaking.Bad.(2008).S01E01-Pilot.BluRay.x264.720p-REWARD\nBluRay x264 720p",
        {"series", "title", "season", "episode", "imdb_id"},
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
        "streaming_service",
    }


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


def test_list_subtitles_movie_no_imdb(movies):
    item = movies["dune"]
    item.imdb_id = None
    with ArgenteamProvider() as provider:
        assert not provider.list_subtitles(item, {Language("spa", "MX")})


def test_list_subtitles_movie_not_found(movies):
    item = movies["dune"]
    item.imdb_id = "tt29318321832"
    with ArgenteamProvider() as provider:
        assert not provider.list_subtitles(item, {Language("spa", "MX")})


def test_list_subtitles_episode(episodes):
    item = episodes["breaking_bad_s01e01"]
    with ArgenteamProvider() as provider:
        subtitles = provider.list_subtitles(item, {Language("spa", "MX")})

    for expected in (
        "https://argenteam.net/subtitles/24002/Breaking.Bad.%282008%29.S01E01-Pilot.BluRay.x264.720p-REWARD",
        "https://argenteam.net/subtitles/23940/Breaking.Bad.%282008%29.S01E01-Pilot.DVDRip.XviD-ORPHEUS",
    ):
        assert any(expected == sub.download_link for sub in subtitles)


def test_list_subtitles_episode_no_imdb_id(episodes):
    item = episodes["breaking_bad_s01e01"]
    item.series_imdb_id = None
    with ArgenteamProvider() as provider:
        assert not provider.list_subtitles(item, {Language("spa", "MX")})


def test_list_subtitles_episode_not_found(episodes):
    item = episodes["breaking_bad_s01e01"]
    item.series_imdb_id = "tt29318321832"
    with ArgenteamProvider() as provider:
        assert not provider.list_subtitles(item, {Language("spa", "MX")})


def test_download_subtitle(episodes):
    item = episodes["breaking_bad_s01e01"]
    with ArgenteamProvider() as provider:
        subtitles = provider.list_subtitles(item, {Language("spa", "MX")})
        provider.download_subtitle(subtitles[0])
        assert subtitles[0].is_valid()

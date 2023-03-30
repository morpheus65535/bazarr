# -*- coding: utf-8 -*-

import pytest
from subliminal_patch.providers.supersubtitles import SuperSubtitlesProvider
from subliminal_patch.providers.supersubtitles import SuperSubtitlesSubtitle
from subliminal_patch.core import Episode
from subzero.language import Language


@pytest.fixture
def episode():
    episode = {
        "name": "/tv/All of Us Are Dead/Season 1/All of Us Are Dead - S01E11 - Episode 11 WEBDL-1080p.mp4",
        "source": "Web",
        "release_group": None,
        "resolution": "1080p",
        "video_codec": None,
        "audio_codec": None,
        "imdb_id": None,
        "subtitle_languages": set(),
        "streaming_service": None,
        "edition": None,
        "series": "All of Us Are Dead",
        "season": 1,
        "episode": 11,
        "title": "Episode 11",
        "year": None,
        "original_series": True,
        "tvdb_id": None,
        "series_tvdb_id": None,
        "series_imdb_id": None,
        "alternative_series": [],
    }
    return Episode(**episode)


def test_list_episode_subtitles(episode):
    language = Language.fromalpha2("en")

    with SuperSubtitlesProvider() as provider:
        assert provider.list_subtitles(episode, {language})


def test_download_episode_subtitle(episode):
    subtitle = SuperSubtitlesSubtitle(
        Language.fromalpha2("en"),
        "https://www.feliratok.eu/index.php?action=letolt&felirat=1643361676",
        1643361676,
        "All of us are dead",
        1,
        11,
        "",
        [
            "NF.WEB-DL.1080p-TEPES",
            "NF.WEBRip.1080p-TEPES",
            "WEBRip-ION10",
            "WEBRip-ION265",
            "WEBRip.1080p-RARBG",
        ],
        "",
        "",
        "",
        asked_for_episode=True,
    )
    assert subtitle.get_matches(episode)

    with SuperSubtitlesProvider() as provider:
        provider.download_subtitle(subtitle)
        assert subtitle.is_valid()


def test_list_and_download_movie_subtitles(movies):
    movie = movies["dune"]
    language = Language.fromalpha2("en")

    with SuperSubtitlesProvider() as provider:
        assert provider.list_subtitles(movie, {language})


def test_download_movie_subtitle(movies):
    movie = movies["dune"]

    subtitle = SuperSubtitlesSubtitle(
        Language.fromalpha2("en"),
        "https://www.feliratok.eu/index.php?action=letolt&felirat=1634579718",
        1634579718,
        "Dune",
        0,
        0,
        "",
        [
            "NF.WEB-DL.1080p-TEPES",
            "NF.WEBRip.1080p-TEPES",
            "WEBRip-ION10",
            "WEBRip-ION265",
            "WEBRip.1080p-RARBG",
        ],
        "",
        "",
        "",
        asked_for_episode=None,
    )
    assert subtitle.get_matches(movie)

    with SuperSubtitlesProvider() as provider:
        provider.download_subtitle(subtitle)
        assert subtitle.is_valid()


def test_subtitle_reprs(movies):
    subtitle = SuperSubtitlesSubtitle(
        Language.fromalpha2("en"),
        "https://www.feliratok.eu/index.php?action=letolt&felirat=1634579718",
        1634579718,
        "Dune",
        0,
        0,
        "",
        [
            "NF.WEB-DL.1080p-TEPES",
            "NF.WEBRip.1080p-TEPES",
            "WEBRip-ION10",
            "WEBRip-ION265",
            "WEBRip.1080p-RARBG",
        ],
        "",
        "",
        "",
        asked_for_episode=None,
    )
    assert isinstance(subtitle.__repr__(), str)
    assert isinstance(subtitle.__str__(), str)


@pytest.fixture
def video_2():
    return Episode(
        **{
            "name": "/tv/La.Brea/Season.02/La.Brea.S02E13.720p.WEB.H264-CAKES.mkv",
            "source": "Web",
            "release_group": "CAKES",
            "resolution": "720p",
            "video_codec": "H.264",
            "audio_codec": "Dolby Digital Plus",
            "imdb_id": None,
            "size": 1598748631,
            "original_name": "la.brea.s02e13.720p.web.h264-cakes.mkv",
            "hints": {"title": "La Brea", "type": "episode", "single_value": True},
            "streaming_service": None,
            "edition": None,
            "original_path": "/tv/La.Brea/Season.02/la.brea.s02e13.720p.web.h264-cakes.mkv",
            "other": None,
            "series": "La Brea",
            "season": 2,
            "episode": 13,
            "title": "The Journey (1)",
            "year": 2021,
            "tvdb_id": None,
            "series_tvdb_id": 395029,
            "series_imdb_id": "tt11640018",
            "alternative_series": [],
            "used_scene_name": True,
        }
    )


def test_list_video_2(video_2):
    lang = Language.fromalpha2("hu")

    with SuperSubtitlesProvider() as provider:
        subs = provider.list_subtitles(video_2, {lang})
        for sub in subs:
            matches = sub.get_matches(video_2)
            assert {"season", "episode", "series"}.issubset(matches)

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
        "https://www.feliratok.info/index.php?action=letolt&felirat=1643361676",
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
        "https://www.feliratok.info/index.php?action=letolt&felirat=1634579718",
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

#!/usr/bin/env python3

import os
import pytest

from subliminal_patch.core import Episode
from subliminal_patch.providers.animetosho import AnimeToshoProvider
from subzero.language import Language

@pytest.fixture(scope="session")
def anime_episodes():
    return {
        "frieren_s01e01": Episode(
            "Frieren - Beyond Journey's End S01E28 1080p WEB x264 AAC -Tsundere-Raws (CR) (Sousou no Frieren).mkv",
            "Frieren: Beyond Journey's End",
            1,
            28,
            source="Web",
            series_anidb_id=17617,
            series_anidb_episode_id=271418,
            series_tvdb_id=424536,
            series_imdb_id="tt22248376",
            release_group="Tsundere-Raws",
            resolution="1080p",
            video_codec="H.264",
        ),
        "solo_leveling_s01e10": Episode(
            "[New-raws] Ore Dake Level Up na Ken - 12 END [1080p] [AMZN].mkv",
            "Solo Leveling",
            1,
            12,
            source="Web",
            series_anidb_id=17495,
            series_anidb_episode_id=277518,
            series_tvdb_id=389597,
            series_imdb_id="tt21209876",
            release_group="New-raws",
            resolution="1080p",
            video_codec="H.264",
        ),
    }


def test_list_subtitles(anime_episodes, requests_mock, data):
    language = Language("eng")
    item = anime_episodes["solo_leveling_s01e10"]

    with open(os.path.join(data, 'animetosho_episode_response.json'), "rb") as f:
        requests_mock.get(' https://feed.animetosho.org/json?eid=277518', content=f.read())

    with open(os.path.join(data, 'animetosho_series_response.json'), "rb") as f:
        response = f.read()
        requests_mock.get('https://feed.animetosho.org/json?show=torrent&id=608516', content=response)
        requests_mock.get('https://feed.animetosho.org/json?show=torrent&id=608526', content=response)

    with AnimeToshoProvider(2) as provider:
        subtitles = provider.list_subtitles(item, languages={language})

        assert len(subtitles) == 2

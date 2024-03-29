#!/usr/bin/env python3

import datetime
import os
import pytest
import subliminal
import tempfile

from dogpile.cache.region import register_backend as register_cache_backend
from subliminal_patch.core import Episode
from subliminal_patch.providers.animetosho import AnimeToshoProvider
from subzero.language import Language


@pytest.fixture(scope="session")
def region():
    register_cache_backend(
        "subzero.cache.file", "subzero.cache_backends.file", "SZFileBackend"
    )
    subliminal.region.configure(
        "subzero.cache.file",
        expiration_time=datetime.timedelta(days=30),
        arguments={"appname": "sz_cache", "app_cache_dir": tempfile.gettempdir()},
    )
    subliminal.region.backend.sync()


@pytest.fixture(scope="session")
def anime_episodes():
    return {
        "frieren_s01e01": Episode(
            "Frieren - Beyond Journey's End S01E28 1080p WEB x264 AAC -Tsundere-Raws (CR) (Sousou no Frieren).mkv",
            "Frieren: Beyond Journey's End",
            1,
            28,
            source="Web",
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
            series_tvdb_id=389597,
            series_imdb_id="tt21209876",
            release_group="New-raws",
            resolution="1080p",
            video_codec="H.264",
        ),
    }


def test_list_subtitles(region, anime_episodes, requests_mock, data):
    language = Language("eng")
    item = anime_episodes["solo_leveling_s01e10"]

    with open(os.path.join(data, 'anidb_response.xml'), "rb") as f:
        requests_mock.get('http://api.anidb.net:9001/httpapi', content=f.read())

    with open(os.path.join(data, 'animetosho_episode_response.json'), "rb") as f:
        requests_mock.get(' https://feed.animetosho.org/json?eid=277518', content=f.read())

    with open(os.path.join(data, 'animetosho_series_response.json'), "rb") as f:
        response = f.read()
        requests_mock.get('https://feed.animetosho.org/json?show=torrent&id=608516', content=response)
        requests_mock.get('https://feed.animetosho.org/json?show=torrent&id=608526', content=response)

    with AnimeToshoProvider(2, 'mocked_client', 1) as provider:
        subtitles = provider.list_subtitles(item, languages={language})

        assert len(subtitles) == 2

    subliminal.region.backend.sync()

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


def _torrent_response(sub_info):
    return {
        "files": [
            {
                "filename": "[EMBER] Ore dake Level Up na Ken S01E12 [1080p] [HEVC WEBRip].mkv",
                "attachments": [
                    {"id": 1, "filename": "subs.ass", "type": "subtitle", "info": sub_info},
                ],
            }
        ]
    }


@pytest.mark.parametrize(
    "info,expected",
    [
        # AnimeTosho reports both Portuguese variants as "por"; the attachment name is the only
        # hint. The name is frequently absent altogether (the recorded API payload in
        # data/animetosho_series_response.json carries no "name" key), and an unnamed track must
        # stay plain Portuguese rather than be promoted to pt-BR.
        ({"lang": "por"}, Language("por")),
        ({"lang": "por", "name": "Portugues"}, Language("por")),
        # A name that starts with "brazil" is still Brazilian Portuguese.
        ({"lang": "por", "name": "Brazilian Portuguese"}, Language("por", "BR")),
        ({"lang": "por", "name": "Portuguese (Brazil)"}, Language("por", "BR")),
    ],
)
def test_portuguese_brazilian_detection(anime_episodes, requests_mock, info, expected):
    item = anime_episodes["solo_leveling_s01e10"]

    requests_mock.get(
        'https://feed.animetosho.org/json?eid=277518',
        json=[{"id": 608526, "timestamp": 1711853493, "status": "complete", "title": "Solo Leveling - 12"}],
    )
    requests_mock.get(
        'https://feed.animetosho.org/json?show=torrent&id=608526',
        json=_torrent_response(info),
    )

    with AnimeToshoProvider(1) as provider:
        # Ask for both variants so nothing is filtered out and the resolved language is asserted.
        subtitles = provider.list_subtitles(item, languages={Language("por"), Language("por", "BR")})

        assert len(subtitles) == 1
        assert subtitles[0].language == expected

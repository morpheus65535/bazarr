#!/usr/bin/env python3

import os
import pytest

from subliminal_patch.core import Episode
from subliminal_patch.providers.animetosho_xyz import AnimeToshoXYZProvider
from subzero.language import Language


@pytest.fixture(scope="session")
def anime_episodes():
    return {
        "crowned_s01e08": Episode(
            "[Erai-raws] Crowned in a Hundred Days - 08 (CA) [1080p CR WEB-DL AVC AAC][MultiSub][81FBD56D].mkv",
            "Crowned in a Hundred Days",
            1,
            8,
            source="Web",
            series_anidb_id=20151,
            series_anidb_episode_id=313249,
            series_tvdb_id=447504,
            series_imdb_id="tt32234060",
            release_group="Erai-raws",
            resolution="1080p",
            video_codec="H.264",
        ),
    }


def test_list_subtitles(anime_episodes, requests_mock, data):
    # Basic functionality test: verify that the provider can fetch subtitles for an anime episode
    # when given a valid AniDB episode ID. This is the happy path for the provider.
    language = Language("eng")
    item = anime_episodes["crowned_s01e08"]

    with open(os.path.join(data, 'animetosho_xyz_episode_response.json'), "rb") as f:
        requests_mock.get(
            'https://feed.animetosho.xyz/feed/json?eid=313249',
            content=f.read()
        )

    with open(os.path.join(data, 'animetosho_xyz_series_response.json'), "rb") as f:
        response = f.read()
        requests_mock.get(
            'https://feed.animetosho.xyz/json?show=torrent&id=622245',
            content=response
        )
        requests_mock.get(
            'https://feed.animetosho.xyz/json?show=torrent&id=622243',
            content=response
        )

    with AnimeToshoXYZProvider() as provider:
        subtitles = provider.list_subtitles(item, languages={language})
        assert len(subtitles) == 2
        assert all(s.language == language for s in subtitles)


def test_list_subtitles_with_portuguese_br(anime_episodes, requests_mock, data):
    # Brazilian Portuguese must be correctly identified when the language name contains "brazil".
    # This verifies the fix for the .find('brazil') bug that always returned truthy (-1).
    language = Language("por", "BR")
    item = anime_episodes["crowned_s01e08"]

    with open(os.path.join(data, 'animetosho_xyz_episode_response.json'), "rb") as f:
        requests_mock.get(
            'https://feed.animetosho.xyz/feed/json?eid=313249',
            content=f.read()
        )

    with open(os.path.join(data, 'animetosho_xyz_series_response.json'), "rb") as f:
        response = f.read()
        requests_mock.get(
            'https://feed.animetosho.xyz/json?show=torrent&id=622245',
            content=response
        )
        requests_mock.get(
            'https://feed.animetosho.xyz/json?show=torrent&id=622243',
            content=response
        )

    with AnimeToshoXYZProvider() as provider:
        subtitles = provider.list_subtitles(item, languages={language})
        assert len(subtitles) == 2
        assert all(s.language == language for s in subtitles)


def test_list_subtitles_no_anidb_episode_id():
    # When no AniDB episode ID is available, the provider should return an empty list
    # without making any API calls. This prevents unnecessary network requests.
    item = Episode(
        "Some.Show.S01E01.720p.WEB.x264.mkv",
        "Some Show",
        1,
        1,
        source="Web",
        resolution="720p",
        video_codec="H.264",
    )

    with AnimeToshoXYZProvider() as provider:
        subtitles = provider.list_subtitles(item, languages={Language("eng")})
        assert len(subtitles) == 0


def test_list_subtitles_with_episode_id_tuple(anime_episodes, requests_mock, data):
    # The AniDB refiner returns episode IDs as tuples (anime_id, episode_id), not lists.
    # This test ensures the provider correctly extracts the episode ID from a tuple,
    # preventing the bug where both IDs were sent to the API, returning empty results.
    language = Language("eng")
    item = anime_episodes["crowned_s01e08"]
    item.series_anidb_episode_id = (20151, 313249)

    with open(os.path.join(data, 'animetosho_xyz_episode_response.json'), "rb") as f:
        requests_mock.get(
            'https://feed.animetosho.xyz/feed/json?eid=313249',
            content=f.read()
        )

    with open(os.path.join(data, 'animetosho_xyz_series_response.json'), "rb") as f:
        response = f.read()
        requests_mock.get(
            'https://feed.animetosho.xyz/json?show=torrent&id=622245',
            content=response
        )
        requests_mock.get(
            'https://feed.animetosho.xyz/json?show=torrent&id=622243',
            content=response
        )

    with AnimeToshoXYZProvider() as provider:
        subtitles = provider.list_subtitles(item, languages={language})
        assert len(subtitles) == 2

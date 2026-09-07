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


def _torrent_response(*sub_infos):
    """Build an animetosho.org torrent payload carrying one subtitle attachment per info dict."""
    return {
        "files": [
            {
                "filename": "[EMBER] Ore dake Level Up na Ken S01E12 [1080p] [HEVC WEBRip].mkv",
                "attachments": [
                    {"id": idx, "filename": f"track{idx}.ass", "type": "subtitle", "info": info}
                    for idx, info in enumerate(sub_infos, start=1)
                ],
            }
        ]
    }


def _varyg_torrent_response():
    """The Brazilian Portuguese attachments of the VARYG release reported in #3579. AnimeTosho
    flags 2759029 as forced (a signs only track) and 2730010 as the normal full subtitle."""
    return {
        "files": [
            {
                "filename": "Frieren.Beyond.Journeys.End.S02E01.Shall.We.Go.Then.1080p.CR.WEB-DL."
                            "MULTi.AAC2.0.H.264-VARYG.mkv",
                "attachments": [
                    {
                        "id": 2759029,
                        "filename": "track24.ass",
                        "type": "subtitle",
                        "size": 3282,
                        "info": {"codec": "ASS", "lang": "por", "name": "Brazilian (Forced)",
                                 "default": 0, "enabled": 1, "forced": 1, "trackid": 24,
                                 "tracknum": 25},
                    },
                    {
                        "id": 2730010,
                        "filename": "track25.ass",
                        "type": "subtitle",
                        "size": 26993,
                        "info": {"codec": "ASS", "lang": "por", "name": "Brazilian",
                                 "default": 0, "enabled": 1, "forced": 0, "trackid": 25,
                                 "tracknum": 26},
                    },
                ],
            }
        ]
    }


def _mock_feed(requests_mock, torrent_response, entry_id=608526):
    requests_mock.get(
        'https://feed.animetosho.org/json?eid=277518',
        json=[{"id": entry_id, "timestamp": 1711853493, "status": "complete",
               "title": "Solo Leveling - 12"}],
    )
    requests_mock.get(
        f'https://feed.animetosho.org/json?show=torrent&id={entry_id}',
        json=torrent_response,
    )


# Every variant has to be requested when the test asserts on the resolved language, otherwise
# list_subtitles filters the subtitle out before it can be inspected.
_ALL_VARIANTS = {
    Language("eng"), Language("eng", forced=True),
    Language("por"), Language("por", forced=True),
    Language("por", "BR"), Language("por", "BR", forced=True),
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

    _mock_feed(requests_mock, _torrent_response(info))

    with AnimeToshoProvider(1) as provider:
        # Ask for both variants so nothing is filtered out and the resolved language is asserted.
        subtitles = provider.list_subtitles(item, languages={Language("por"), Language("por", "BR")})

        assert len(subtitles) == 1
        assert subtitles[0].language == expected


@pytest.mark.parametrize(
    "info,expected",
    [
        # AnimeTosho reports the forced disposition flag of the track as 0/1. It has to reach the
        # language, otherwise a signs only track is offered as a normal subtitle. #3579
        ({"lang": "eng", "forced": 1}, Language("eng", forced=True)),
        ({"lang": "eng", "forced": 0}, Language("eng")),
        ({"lang": "por", "name": "Brazilian (Forced)", "forced": 1}, Language("por", "BR", forced=True)),
        ({"lang": "por", "name": "Brazilian", "forced": 0}, Language("por", "BR")),
        # Payloads that predate the flag, or tracks that simply do not carry it.
        ({"lang": "eng"}, Language("eng")),
        ({"lang": "por", "name": "Brazilian"}, Language("por", "BR")),
    ],
)
def test_forced_flag_is_propagated(anime_episodes, requests_mock, info, expected):
    item = anime_episodes["solo_leveling_s01e10"]

    _mock_feed(requests_mock, _torrent_response(info))

    with AnimeToshoProvider(1) as provider:
        subtitles = provider.list_subtitles(item, languages=_ALL_VARIANTS)

        assert len(subtitles) == 1
        assert subtitles[0].language == expected
        assert subtitles[0].forced is bool(expected.forced)


def test_forced_track_is_not_offered_as_a_normal_subtitle(anime_episodes, requests_mock):
    """#3579: a profile asking for normal Brazilian Portuguese was served the forced track."""
    item = anime_episodes["solo_leveling_s01e10"]

    _mock_feed(requests_mock, _varyg_torrent_response())

    with AnimeToshoProvider(1) as provider:
        normal = provider.list_subtitles(item, languages={Language("por", "BR")})
        forced = provider.list_subtitles(item, languages={Language("por", "BR", forced=True)})

    # The normal request only gets the full subtitle, the forced one only the signs only track.
    assert [(s.language, s.forced) for s in normal] == [(Language("por", "BR"), False)]
    assert normal[0].download_link == "https://animetosho.org/storage/attach/0029a81a/2730010.xz"

    assert [(s.language, s.forced) for s in forced] == [(Language("por", "BR", forced=True), True)]
    assert forced[0].download_link == "https://animetosho.org/storage/attach/002a1975/2759029.xz"


def test_forced_languages_are_declared():
    # The provider pool intersects the requested languages with the ones declared by the provider
    # before calling list_subtitles, so without the forced variants a profile asking for forced
    # subtitles would never reach AnimeTosho at all.
    assert Language("eng", forced=True) in AnimeToshoProvider.languages
    assert Language("por", "BR", forced=True) in AnimeToshoProvider.languages


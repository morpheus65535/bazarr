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
        # The VARYG release reported in #3579. AnimeTosho.xyz nests its attachments under the file
        # for this one instead of exposing them at the top level of the release.
        "frieren_s02e01": Episode(
            "Frieren.Beyond.Journeys.End.S02E01.Shall.We.Go.Then.1080p.CR.WEB-DL.MULTi.AAC2.0.H.264-VARYG.mkv",
            "Frieren: Beyond Journey's End",
            2,
            1,
            source="Web",
            series_anidb_id=18886,
            series_anidb_episode_id=306529,
            series_tvdb_id=424536,
            series_imdb_id="tt22248376",
            release_group="VARYG",
            resolution="1080p",
            video_codec="H.264",
        ),
        # Exact Erai-raws release whose PT-BR attachment URL is reused across other releases on
        # AnimeTosho.xyz; used to assert release associations stay distinct until scoring.
        "black_torch_s01e10": Episode(
            "[Erai-raws] Black Torch - 10 [1080p CR WEB-DL AVC AAC][MultiSub][1595FA67].mkv",
            "BLACK TORCH",
            1,
            10,
            source="Web",
            series_anidb_id=19001,
            series_anidb_episode_id=315278,
            release_group="Erai-raws",
            resolution="1080p",
            video_codec="H.264",
        ),
        # The AnoZu release reported in #3612. AnimeTosho appends the Japanese title to the torrent
        # name after a pipe, which guessit parses as the release group instead of the real "AnoZu".
        "anozu_s04e16": Episode(
            "Re.ZERO.Starting.Life.in.Another.World.2016.S04E16.1080p.CR.WEB-DL.DUAL.DDP2.0.H.264-AnoZu.mkv",
            "Re: ZERO -Starting Life in Another World-",
            4,
            16,
            year=2016,
            original_series=False,
            source="Web",
            series_anidb_id=19242,
            series_anidb_episode_id=315621,
            series_tvdb_id=305089,
            release_group="AnoZu",
            resolution="1080p",
            video_codec="H.264",
        ),
    }


_RELEASE_NAME = "[Erai-raws] Crowned in a Hundred Days - 08 (CA) [1080p CR WEB-DL AVC AAC][MultiSub][81FBD56D]"


def _top_level_response(*sub_infos):
    """Release payload exposing its subtitle attachments at the top level."""
    return {
        "id": 622245,
        "torrent_name": _RELEASE_NAME,
        "attachments": [
            {
                "id": idx,
                "type": "subtitle",
                "url": f"https://storage.animetosho.xyz/releases/622245/subtitles/track{idx}.ass.xz",
                "info": info,
            }
            for idx, info in enumerate(sub_infos, start=1)
        ],
        "files": [{"id": 1, "filename": f"{_RELEASE_NAME}.mkv"}],
    }


def _nested_response(*sub_infos):
    """Release payload nesting its subtitle attachments under its file, which is what
    AnimeTosho.xyz does for most releases."""
    return {
        "id": 592301,
        "torrent_name": "Frieren Beyond Journeys End S02E01 Shall We Go Then 1080p CR WEB-DL MULTi "
                        "AAC2.0 H 264-VARYG (Sousou no Frieren, Multi-Audio, Multi-Subs)",
        "attachments": None,
        "files": [
            {
                "id": 1,
                "filename": "Frieren.Beyond.Journeys.End.S02E01.Shall.We.Go.Then.1080p.CR.WEB-DL."
                            "MULTi.AAC2.0.H.264-VARYG.mkv",
                "attachments": [
                    {
                        "id": idx,
                        "type": "subtitle",
                        "url": f"https://storage.animetosho.xyz/attachments/0029a/{idx}.xz",
                        "info": info,
                    }
                    for idx, info in enumerate(sub_infos, start=1)
                ],
            }
        ],
    }


def _anozu_s04e16_response(*sub_infos):
    """The release reported in #3612: its torrent name carries the Japanese title after a pipe,
    which guessit parses as the release group, while the file name holds the real "AnoZu"."""
    return {
        "id": 691630,
        "torrent_name": "[AnoZu] Re: ZERO, Starting Life in Another World S04E16 1080p CR WEB-DL "
                        "Dual-Audio DDP 2.0 H.264 | Re:Zero kara Hajimeru Isekai Seikatsu 4th Season",
        "attachments": [
            {
                "id": idx,
                "type": "subtitle",
                "url": f"https://storage.animetosho.xyz/releases/691630/subtitles/track{idx}.ass.xz",
                "info": info,
            }
            for idx, info in enumerate(sub_infos, start=1)
        ],
        "files": [
            {
                "id": 1404449,
                "filename": "Re.ZERO.Starting.Life.in.Another.World.2016.S04E16.1080p.CR.WEB-DL."
                            "DUAL.DDP2.0.H.264-AnoZu.mkv",
            }
        ],
    }


def _subsplease_batch_response(*sub_infos):
    """A batch whose torrent name ("... (01-10) [Batch]") parses "Batch" as the release group while
    the primary file name carries the real "[SubsPlease]" group."""
    return {
        "id": 612661,
        "torrent_name": "[SubsPlease] Sousou no Frieren S2 (01-10) (1080p) [Batch]",
        "primary_file_id": 4338,
        "attachments": [
            {
                "id": idx,
                "type": "subtitle",
                "url": f"https://storage.animetosho.xyz/releases/612661/subtitles/track{idx}.ass.xz",
                "info": info,
            }
            for idx, info in enumerate(sub_infos, start=1)
        ],
        "files": [
            {"id": 4338, "filename": "[SubsPlease] Sousou no Frieren S2 - 01v2 (1080p) [4149A222].mkv"},
            {"id": 4339, "filename": "[SubsPlease] Sousou no Frieren S2 - 02v2 (1080p) [B1C1DECE].mkv"},
        ],
    }


def _mock_feed(requests_mock, torrent_response, eid, entry_id, title):
    """Mock the feed endpoint and, when a payload is given, the release detail endpoint. Leave
    torrent_response as None to register the detail endpoint from a recorded file instead."""
    requests_mock.get(
        f'https://feed.animetosho.xyz/feed/json?eid={eid}',
        json=[{"id": entry_id, "timestamp": 1784290258, "status": "complete", "title": title}],
    )

    if torrent_response is not None:
        requests_mock.get(
            f'https://feed.animetosho.xyz/json?show=torrent&id={entry_id}',
            json=torrent_response,
        )


# Every variant has to be requested when the test asserts on the resolved language, otherwise
# list_subtitles filters the subtitle out before it can be inspected.
_ALL_VARIANTS = {
    Language("eng"), Language("eng", forced=True),
    Language("por"), Language("por", forced=True),
    Language("por", "BR"), Language("por", "BR", forced=True),
}

_VARYG_TITLE = ("Frieren Beyond Journeys End S02E01 Shall We Go Then 1080p CR WEB-DL MULTi AAC2.0 "
                "H 264-VARYG (Sousou no Frieren, Multi-Audio, Multi-Subs)")


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


@pytest.mark.parametrize(
    "info,expected",
    [
        # AnimeTosho reports the forced disposition flag of the track as a boolean. It has to
        # reach the language, otherwise a signs only track is offered as a normal subtitle. #3579
        ({"language": "English", "language_code": "eng", "forced": True}, Language("eng", forced=True)),
        ({"language": "English", "language_code": "eng", "forced": False}, Language("eng")),
        ({"language": "Portuguese[BR]", "language_code": "por", "forced": True},
         Language("por", "BR", forced=True)),
        ({"language": "Portuguese[BR]", "language_code": "por", "forced": False}, Language("por", "BR")),
        # Payloads that predate the flag, or tracks that simply do not carry it.
        ({"language": "English", "language_code": "eng"}, Language("eng")),
        ({"language": "Portuguese[BR]", "language_code": "por"}, Language("por", "BR")),
    ],
)
def test_forced_flag_is_propagated(anime_episodes, requests_mock, info, expected):
    item = anime_episodes["crowned_s01e08"]

    _mock_feed(
        requests_mock,
        _top_level_response(info),
        eid=313249,
        entry_id=622245,
        title=_RELEASE_NAME,
    )

    with AnimeToshoXYZProvider() as provider:
        subtitles = provider.list_subtitles(item, languages=_ALL_VARIANTS)

        assert len(subtitles) == 1
        assert subtitles[0].language == expected
        assert subtitles[0].forced is bool(expected.forced)


def test_nested_attachments_are_found(anime_episodes, requests_mock, data):
    """Most releases nest their attachments under "files[].attachments" and carry no top level
    "attachments" at all. Those used to be missed entirely, so nothing was ever listed for them."""
    item = anime_episodes["frieren_s02e01"]

    _mock_feed(requests_mock, None, eid=306529, entry_id=592301, title=_VARYG_TITLE)
    with open(os.path.join(data, 'animetosho_xyz_series_nested_attachments_response.json'), "rb") as f:
        requests_mock.get('https://feed.animetosho.xyz/json?show=torrent&id=592301', content=f.read())

    with AnimeToshoXYZProvider() as provider:
        subtitles = provider.list_subtitles(item, languages=_ALL_VARIANTS)

    assert {(s.language, s.forced) for s in subtitles} == {
        (Language("eng"), False),
        (Language("eng", forced=True), True),
        # Nested attachments only carry "language_code" and no "language" name, so there is nothing
        # telling Brazilian Portuguese apart from Portuguese and it stays plain Portuguese.
        (Language("por"), False),
        (Language("por", forced=True), True),
    }

    by_language = {(s.language, s.forced): s for s in subtitles}
    assert by_language[(Language("por"), False)].download_link \
        == "https://storage.animetosho.xyz/attachments/0029a/81a.xz"
    assert by_language[(Language("por", forced=True), True)].download_link \
        == "https://storage.animetosho.xyz/attachments/002a1/975.xz"


def test_file_name_is_used_to_match_release_metadata(anime_episodes, requests_mock):
    """#3612: guessit parsed the Japanese title appended to the torrent name as the release group,
    so the exact AnoZu match only scored 250/360 and was never downloaded."""
    item = anime_episodes["anozu_s04e16"]

    _mock_feed(
        requests_mock,
        _anozu_s04e16_response({"language": "English", "language_code": "eng", "forced": False}),
        eid=315621,
        entry_id=691630,
        title="[AnoZu] Re: ZERO, Starting Life in Another World S04E16 1080p CR WEB-DL Dual-Audio "
              "DDP 2.0 H.264 | Re:Zero kara Hajimeru Isekai Seikatsu 4th Season",
    )

    with AnimeToshoXYZProvider() as provider:
        subtitles = provider.list_subtitles(item, languages={Language("eng")})

    assert len(subtitles) == 1
    assert {"release_group", "year"}.issubset(subtitles[0].get_matches(item))


def test_batch_primary_file_name_is_used_to_match_the_release_group(requests_mock):
    """A batch torrent name parses "Batch" as the release group; the real group only exists in its
    primary file name."""
    item = Episode(
        "[SubsPlease] Sousou no Frieren S2 - 01v2 (1080p) [4149A222].mkv",
        "Frieren: Beyond Journey's End",
        2,
        1,
        source="Web",
        series_anidb_episode_id=306529,
        release_group="SubsPlease",
        resolution="1080p",
        video_codec="H.264",
    )

    _mock_feed(
        requests_mock,
        _subsplease_batch_response({"language": "English", "language_code": "eng", "forced": False}),
        eid=306529,
        entry_id=612661,
        title="[SubsPlease] Sousou no Frieren S2 (01-10) (1080p) [Batch]",
    )

    with AnimeToshoXYZProvider() as provider:
        subtitles = provider.list_subtitles(item, languages={Language("eng")})

    assert len(subtitles) == 1
    assert "release_group" in subtitles[0].get_matches(item)


def test_torrent_name_is_used_to_match_when_no_file_is_listed(anime_episodes, requests_mock):
    """Releases with no file entry have to keep being matched through the torrent name."""
    item = anime_episodes["crowned_s01e08"]

    response = _top_level_response({"language": "English", "language_code": "eng", "forced": False})
    response["files"] = []

    _mock_feed(requests_mock, response, eid=313249, entry_id=622245, title=_RELEASE_NAME)

    with AnimeToshoXYZProvider() as provider:
        subtitles = provider.list_subtitles(item, languages={Language("eng")})

    assert len(subtitles) == 1
    assert "release_group" in subtitles[0].get_matches(item)


def test_forced_track_is_not_offered_as_a_normal_subtitle(anime_episodes, requests_mock, data):
    """#3579 on animetosho.xyz: the forced Portuguese attachment of the VARYG release must not be
    served to a profile asking for normal Portuguese, and vice versa."""
    item = anime_episodes["frieren_s02e01"]

    _mock_feed(requests_mock, None, eid=306529, entry_id=592301, title=_VARYG_TITLE)
    with open(os.path.join(data, 'animetosho_xyz_series_nested_attachments_response.json'), "rb") as f:
        requests_mock.get('https://feed.animetosho.xyz/json?show=torrent&id=592301', content=f.read())

    with AnimeToshoXYZProvider() as provider:
        normal = provider.list_subtitles(item, languages={Language("por")})
        forced = provider.list_subtitles(item, languages={Language("por", forced=True)})

    assert [(s.language, s.forced) for s in normal] == [(Language("por"), False)]
    assert [(s.language, s.forced) for s in forced] == [(Language("por", forced=True), True)]


def test_attachments_are_not_listed_twice(anime_episodes, requests_mock):
    # A release only ever uses one of the two shapes, but a release carrying both must still not
    # produce a duplicate subtitle for the same attachment.
    item = anime_episodes["crowned_s01e08"]

    info = {"language": "English", "language_code": "eng", "forced": False}
    url = "https://storage.animetosho.xyz/releases/622245/subtitles/track1.eng.ass.xz"
    attachment = {"id": 127399, "type": "subtitle", "url": url, "info": info}

    response = {
        "id": 622245,
        "torrent_name": _RELEASE_NAME,
        "attachments": [dict(attachment)],
        "files": [
            {"id": 1, "filename": f"{_RELEASE_NAME}.mkv", "attachments": [dict(attachment)]},
        ],
    }

    _mock_feed(
        requests_mock,
        response,
        eid=313249,
        entry_id=622245,
        title=_RELEASE_NAME,
    )

    with AnimeToshoXYZProvider() as provider:
        subtitles = provider.list_subtitles(item, languages={Language("eng")})

        assert len(subtitles) == 1
        assert subtitles[0].download_link == url


def test_reused_attachment_across_releases_keeps_distinct_candidates(anime_episodes, requests_mock):
    # AnimeTosho.xyz may point multiple releases at the same attachment URL. Each release
    # association must stay distinct until scoring, otherwise the pool drops later ones by id
    # and the exact local release can be lost (BLACK TORCH S01E10 / Erai-raws 1080p).
    item = anime_episodes["black_torch_s01e10"]

    shared_url = "https://storage.animetosho.xyz/attachments/10002/3f70.xz"
    pt_br_info = {"language": "Portuguese[BR]", "language_code": "por", "forced": False}

    onalrie_title = "[Onalrie] Black Torch - S01E10 [1080p WEBRip AV1]"
    erai_title = "[Erai-raws] Black Torch - 10 [1080p CR WEB-DL AVC AAC][MultiSub][1595FA67]"

    requests_mock.get(
        'https://feed.animetosho.xyz/feed/json?eid=315278',
        json=[
            {"id": 685592, "timestamp": 200, "status": "complete", "title": onalrie_title},
            {"id": 685550, "timestamp": 100, "status": "complete", "title": erai_title},
        ],
    )
    requests_mock.get(
        'https://feed.animetosho.xyz/json?show=torrent&id=685592',
        json={
            "id": 685592,
            "torrent_name": onalrie_title,
            "attachments": [
                {"id": 3, "type": "subtitle", "url": shared_url, "info": pt_br_info},
            ],
            "files": [],
        },
    )
    requests_mock.get(
        'https://feed.animetosho.xyz/json?show=torrent&id=685550',
        json={
            "id": 685550,
            "torrent_name": erai_title,
            "attachments": [
                {"id": 3, "type": "subtitle", "url": shared_url, "info": pt_br_info},
            ],
            "files": [],
        },
    )

    with AnimeToshoXYZProvider() as provider:
        subtitles = provider.list_subtitles(item, languages={Language("por", "BR")})

    assert len(subtitles) == 2
    assert {s.download_link for s in subtitles} == {shared_url}
    assert {s.release_id for s in subtitles} == {685592, 685550}
    assert {s.id for s in subtitles} == {
        f"685592:{shared_url}",
        f"685550:{shared_url}",
    }


def test_forced_languages_are_declared():
    # The provider pool intersects the requested languages with the ones declared by the provider
    # before calling list_subtitles, so without the forced variants a profile asking for forced
    # subtitles would never reach AnimeTosho at all.
    assert Language("eng", forced=True) in AnimeToshoXYZProvider.languages
    assert Language("por", "BR", forced=True) in AnimeToshoXYZProvider.languages

# -*- coding: utf-8 -*-
import lzma

import pytest

from subliminal.exceptions import ProviderError
from subliminal_patch.core import Episode, Movie
from subliminal_patch.providers import tsukihime
from subliminal_patch.providers.tsukihime import TsukiHimeProvider, TsukiHimeSubtitle
from subzero.language import Language

API = "https://api.tsukihime.org/v1"
STORE = "https://storage.tsukihime.org"


@pytest.fixture
def episode():
    video = Episode(
        "One.Piece.S01E1171.1080p.NF.WEB-DL.AAC2.0.H.264-VARYG.mkv",
        "One Piece",
        1,
        1171,
        year=1999,
        series_anidb_id=69,
    )
    video.series_anidb_episode_no = 1171
    return video


@pytest.fixture
def movie():
    video = Movie(
        "Summer.Pockets.Season.1.Omnibus.1080p.BluRay.mkv",
        "Summer Pockets Season 1: Omnibus",
        year=2025,
    )
    video.anilist_id = 195230
    return video


def _attachment(attachment_id, lang, codec, name="English", forced=0, cached=1):
    return {
        "id": attachment_id,
        "type": 1,
        "info": {
            "cached": cached,
            "codec": codec,
            "lang": lang,
            "name": name,
            "forced": forced,
        },
    }


def _mock_anime(requests_mock, anime):
    requests_mock.get(f"{API}/animes/anidb/69", json={"id": 2086, "release_year": 1999})
    requests_mock.get(f"{API}/animes/anilist/195230", json={"id": 400, "release_year": 2025})
    return anime


def test_list_episode_subtitles_uses_native_storage(episode, requests_mock):
    _mock_anime(requests_mock, episode)
    requests_mock.get(
        f"{API}/animes/2086/episodes/1171",
        json={
            "results": [
                {
                    "id": 301,
                    "name": "One.Piece.S01E1171.1080p.NF.WEB-DL.AAC2.0.H.264-VARYG",
                    "state": "completed",
                    "sublangs": ["ar"],
                    "source_date": 1234,
                },
            ],
        },
    )
    requests_mock.get(
        f"{API}/torrents/301",
        json={
            "files": [
                {
                    "filename": "One.Piece.S01E1171.1080p.NF.WEB-DL.AAC2.0.H.264-VARYG.mkv",
                    "attachments": [
                        _attachment(133226, "ar", "srt", name="Arabic"),
                    ],
                },
            ],
        },
    )

    with TsukiHimeProvider() as provider:
        subtitles = provider.list_subtitles(episode, {Language("ara")})

    assert len(subtitles) == 1
    subtitle = subtitles[0]
    assert subtitle.language == Language("ara")
    assert subtitle.format == "srt"
    assert subtitle.download_url == f"{STORE}/attach/0002086A/133226.xz"
    assert {"series", "season", "episode", "year"} <= subtitle.get_matches(episode)


def test_list_movie_subtitles_uses_animetosho_storage_and_best_file(movie, requests_mock):
    _mock_anime(requests_mock, movie)
    requests_mock.get(
        f"{API}/animes/400",
        json={
            "results": [
                {
                    "id": 401,
                    "name": "Summer.Pockets.Season.1.Omnibus.1080p.BluRay",
                    "state": "completed",
                    "sublangs": ["en"],
                    "source_date": 4321,
                    "animetosho": True,
                },
            ],
        },
    )
    requests_mock.get(
        f"{API}/torrents/401",
        json={
            "files": [
                {
                    "filename": "Summer.Pockets.Season.1.Omnibus.1080p.BluRay.mkv",
                    "attachments": [_attachment(65537, "en", "ass")],
                },
                {
                    "filename": "Random.Extra.Track.1080p.mkv",
                    "attachments": [_attachment(65538, "en", "srt")],
                },
            ],
        },
    )

    with TsukiHimeProvider() as provider:
        subtitles = provider.list_subtitles(movie, {Language("eng")})

    assert len(subtitles) == 1
    subtitle = subtitles[0]
    assert subtitle.format == "ass"
    assert subtitle.download_url == f"{STORE}/tosho/attach/00010001/65537.xz"
    assert {"title", "year"} <= subtitle.get_matches(movie)


def test_reused_attachment_across_releases_keeps_distinct_candidates(movie, requests_mock):
    # TsukiHime reuses the same attachment across release associations, so the same download URL
    # must stay as distinct candidates, otherwise the pool drops later ones by id (#3582).
    _mock_anime(requests_mock, movie)
    shared_url = f"{STORE}/attach/0000000A/10.xz"
    requests_mock.get(
        f"{API}/animes/400",
        json={
            "results": [
                {"id": 1, "name": "Summer.Pockets", "state": "completed",
                 "sublangs": ["en"], "source_date": 1},
                {"id": 2, "name": "Summer.Pockets", "state": "completed",
                 "sublangs": ["en"], "source_date": 2},
            ],
        },
    )
    for entry_id in (1, 2):
        requests_mock.get(
            f"{API}/torrents/{entry_id}",
            json={
                "files": [
                    {
                        "filename": "Summer.Pockets.mkv",
                        "attachments": [_attachment(10, "en", "srt")],
                    },
                ],
            },
        )

    with TsukiHimeProvider() as provider:
        subtitles = provider.list_subtitles(movie, {Language("eng")})

    assert len(subtitles) == 2
    assert {s.download_url for s in subtitles} == {shared_url}
    assert {s.release_id for s in subtitles} == {1, 2}
    assert {s.id for s in subtitles} == {f"1:{shared_url}", f"2:{shared_url}"}


@pytest.mark.parametrize(
    "code,expected",
    [
        ("en", Language("eng")),
        # Alphabetically ordered: the simpler ISO-639 codes are returned as-is.
        ("zh-Hans", Language("zho", "CN")),
        ("zh-Hant", Language("zho", "TW")),
        ("pt-BR", Language("por", "BR")),
        ("es-419", Language("spa", "MX")),
        ("por", Language("por")),
        # Unknown codes fall back to the alpha3 conversion or are dropped.
        ("eng", Language("eng")),
        ("xx-not-real", None),
    ],
)
def test_language_from_code(code, expected):
    assert tsukihime._language_from_code(code) == expected


def test_forced_track_is_propagated_to_the_language(episode, requests_mock):
    _mock_anime(requests_mock, episode)
    requests_mock.get(
        f"{API}/animes/2086/episodes/1171",
        json={
            "results": [
                {"id": 301, "name": "One.Piece.S01E1171", "state": "completed",
                 "sublangs": ["en"], "source_date": 1},
            ],
        },
    )
    requests_mock.get(
        f"{API}/torrents/301",
        json={
            "files": [
                {
                    "filename": "One.Piece.S01E1171.mkv",
                    "attachments": [
                        _attachment(1, "en", "srt", name="Signs", forced=1),
                        _attachment(2, "en", "srt", name="English (CC)"),
                        _attachment(3, "en", "srt", name="English", forced=0),
                    ],
                },
            ],
        },
    )

    with TsukiHimeProvider() as provider:
        normal = provider.list_subtitles(episode, {Language("eng")})
        forced = provider.list_subtitles(episode, {Language("eng", forced=True)})
        hi = provider.list_subtitles(episode, {Language("eng", hi=True)})

    # Only the plain track answers a normal request, the signs one answers forced, and the CC one
    # answers hearing-impaired.
    assert [s.language for s in normal] == [Language("eng")]
    assert [s.language for s in forced] == [Language("eng", forced=True)]
    assert [s.language for s in hi] == [Language("eng", hi=True)]
    assert normal[0].download_url == f"{STORE}/attach/00000003/3.xz"
    assert forced[0].download_url == f"{STORE}/attach/00000001/1.xz"
    assert hi[0].download_url == f"{STORE}/attach/00000002/2.xz"


def test_track_name_drives_forced_and_hi_classification(episode, requests_mock):
    # Signs tracks are often muxed without the forced disposition flag; the name is the only hint,
    # so an unflagged "Signs" track must not be offered as a full subtitle (nor should a CC one).
    _mock_anime(requests_mock, episode)
    requests_mock.get(
        f"{API}/animes/2086/episodes/1171",
        json={
            "results": [
                {"id": 301, "name": "One.Piece.S01E1171", "state": "completed",
                 "sublangs": ["en"], "source_date": 1},
            ],
        },
    )
    requests_mock.get(
        f"{API}/torrents/301",
        json={
            "files": [
                {
                    "filename": "One.Piece.S01E1171.mkv",
                    "attachments": [
                        _attachment(1, "en", "ass", name="English [Signs]"),
                        _attachment(2, "en", "ass", name="English (Signs & Songs)"),
                        _attachment(3, "en", "ass", name="English"),
                        _attachment(4, "en", "ass", name="English [CC]"),
                    ],
                },
            ],
        },
    )

    with TsukiHimeProvider() as provider:
        normal = provider.list_subtitles(episode, {Language("eng")})
        forced = provider.list_subtitles(episode, {Language("eng", forced=True)})
        hi = provider.list_subtitles(episode, {Language("eng", hi=True)})

    assert [s.download_url for s in normal] == [f"{STORE}/attach/00000003/3.xz"]
    assert {s.download_url for s in forced} == {
        f"{STORE}/attach/00000001/1.xz",
        f"{STORE}/attach/00000002/2.xz",
    }
    assert [s.download_url for s in hi] == [f"{STORE}/attach/00000004/4.xz"]


@pytest.mark.parametrize(
    "release_name,expected_suffix",
    [
        # The streaming source belongs in the release info so alike releases stay distinguishable
        # without repurposing the Uploader column.
        ("[ToonsHub] Mushoku Tensei Jobless Reincarnation S03E03 1080p CR WEB-DL AAC2.0 H.264", "Crunchy Roll"),
        ("[ToonsHub] Mushoku Tensei Jobless Reincarnation S03E03 1080p NF WEB-DL AAC2.0 H.264", "Netflix"),
        ("[SubsPlease] Mushoku Tensei S3 - 03 (1080p) [8488B15C].mkv", None),
    ],
)
def test_streaming_service_is_exposed_in_release_info(episode, requests_mock, release_name, expected_suffix):
    _mock_anime(requests_mock, episode)
    requests_mock.get(
        f"{API}/animes/2086/episodes/1171",
        json={
            "results": [
                {"id": 301, "name": release_name, "state": "completed",
                 "sublangs": ["en"], "source_date": 1},
            ],
        },
    )
    requests_mock.get(
        f"{API}/torrents/301",
        json={
            "files": [
                {
                    "filename": "One.Piece.S01E1171.mkv",
                    "attachments": [_attachment(1, "en", "srt")],
                },
            ],
        },
    )

    with TsukiHimeProvider() as provider:
        subtitles = provider.list_subtitles(episode, {Language("eng")})

    assert len(subtitles) == 1
    subtitle = subtitles[0]
    assert subtitle.uploader is None
    if expected_suffix:
        assert subtitle.release_info == f"[{expected_suffix}] {release_name}"
    else:
        assert subtitle.release_info == release_name


def test_same_release_tracks_are_distinguished_in_release_info(episode, requests_mock):
    # [Sonomama]-style releases bundle several full tracks for the same language under one release
    # name; the track name is appended to the release info so the rows are not identical.
    _mock_anime(requests_mock, episode)
    requests_mock.get(
        f"{API}/animes/2086/episodes/1171",
        json={
            "results": [
                {"id": 301, "name": "[Sonomama] One Piece - S01E1171", "state": "completed",
                 "sublangs": ["en"], "source_date": 1},
            ],
        },
    )
    requests_mock.get(
        f"{API}/torrents/301",
        json={
            "files": [
                {
                    "filename": "One.Piece.S01E1171.mkv",
                    "attachments": [
                        _attachment(1, "en", "ass", name="[Sonomama]"),
                        _attachment(2, "en", "ass", name="Crunchyroll"),
                        _attachment(3, "en", "ass", name="English"),
                    ],
                },
            ],
        },
    )

    with TsukiHimeProvider() as provider:
        subtitles = provider.list_subtitles(episode, {Language("eng")})

    assert {s.release_info for s in subtitles} == {
        "[[Sonomama]] [Sonomama] One Piece - S01E1171",
        "[Crunchyroll] [Sonomama] One Piece - S01E1171",
        "[Sonomama] One Piece - S01E1171",
    }
    assert all(s.uploader is None for s in subtitles)


def test_uncached_native_subtitle_is_skipped(episode, requests_mock):
    _mock_anime(requests_mock, episode)
    requests_mock.get(
        f"{API}/animes/2086/episodes/1171",
        json={
            "results": [
                {"id": 301, "name": "One.Piece.S01E1171", "state": "completed",
                 "sublangs": ["en"], "source_date": 1},
            ],
        },
    )
    requests_mock.get(
        f"{API}/torrents/301",
        json={
            "files": [
                {
                    "filename": "One.Piece.S01E1171.mkv",
                    "attachments": [
                        _attachment(1, "en", "srt", cached=0),
                        _attachment(2, "en", "srt", cached=1),
                    ],
                },
            ],
        },
    )

    with TsukiHimeProvider() as provider:
        subtitles = provider.list_subtitles(episode, {Language("eng")})

    assert [s.download_url for s in subtitles] == [f"{STORE}/attach/00000002/2.xz"]


def test_download_subtitle_decompresses_xz(requests_mock):
    subtitle = TsukiHimeSubtitle(
        Language("eng"),
        f"{STORE}/attach/00000001/1.xz",
        release_info="Example",
        release_id=1,
        codec="srt",
        verified_matches={"title"},
    )
    content = b"1\n00:00:01,000 --> 00:00:02,000\nExample\n"
    requests_mock.get(subtitle.download_url, content=lzma.compress(content))

    with TsukiHimeProvider() as provider:
        result = provider.download_subtitle(subtitle)

    assert result is subtitle
    assert subtitle.content == content


def test_download_subtitle_rejects_non_xz_response(requests_mock):
    subtitle = TsukiHimeSubtitle(
        Language("eng"),
        f"{STORE}/attach/00000001/1.xz",
        release_info="Example",
        release_id=1,
        codec="srt",
        verified_matches={"title"},
    )
    requests_mock.get(subtitle.download_url, content=b"<html>not a subtitle</html>")

    with TsukiHimeProvider() as provider:
        with pytest.raises(ProviderError, match="unidentified archive type"):
            provider.download_subtitle(subtitle)


def test_list_subtitles_without_anime_id_returns_empty(movie, requests_mock):
    movie.anilist_id = None

    with TsukiHimeProvider() as provider:
        assert provider.list_subtitles(movie, {Language("eng")}) == []


def test_list_subtitles_missing_anime_404_returns_empty(movie, requests_mock):
    requests_mock.get(f"{API}/animes/anilist/195230", status_code=404)

    with TsukiHimeProvider() as provider:
        assert provider.list_subtitles(movie, {Language("eng")}) == []


def test_forced_and_hi_variants_are_declared():
    # The pool intersects the requested languages with the declared ones before calling
    # list_subtitles, so regional, forced and hearing-impaired variants have to be present.
    assert Language("eng", forced=True) in TsukiHimeProvider.languages
    assert Language("eng", hi=True) in TsukiHimeProvider.languages
    assert Language("por", "BR") in TsukiHimeProvider.languages
    assert Language("zho", "CN") in TsukiHimeProvider.languages
    assert Language("spa", "MX") in TsukiHimeProvider.languages

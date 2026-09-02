# -*- coding: utf-8 -*-
import lzma

import pytest

from subliminal.exceptions import ProviderError
from subliminal_patch.core import Episode, Movie
from subliminal_patch.providers.tsukihime import TsukiHimeProvider, TsukiHimeSubtitle
from subzero.language import Language


@pytest.fixture
def episode():
    video = Episode(
        'One.Piece.S01E1171.1080p.NF.WEB-DL.AAC2.0.H.264-VARYG.mkv',
        'One Piece',
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
        'Summer.Pockets.Season.1.Omnibus.1080p.BluRay.mkv',
        'Summer Pockets Season 1: Omnibus',
        year=2025,
    )
    video.anilist_id = 195230
    return video


def test_list_episode_subtitles_uses_native_storage(episode, requests_mock):
    requests_mock.get(
        'https://api.tsukihime.org/v1/animes/anidb/69',
        json={'id': 2086, 'release_year': 1999},
    )
    requests_mock.get(
        'https://api.tsukihime.org/v1/animes/2086/episodes/1171',
        json={
            'results': [
                {
                    'id': 301,
                    'name': 'One.Piece.S01E1171.1080p.NF.WEB-DL.AAC2.0.H.264-VARYG',
                    'state': 'completed',
                    'sublangs': ['ar'],
                    'source_date': 2,
                },
                {
                    'id': 302,
                    'name': 'One.Piece.S01E1171.1080p.WEB-DL',
                    'state': 'completed',
                    'sublangs': ['en'],
                    'source_date': 3,
                },
            ],
        },
    )
    requests_mock.get(
        'https://api.tsukihime.org/v1/torrents/301',
        json={
            'files': [
                {
                    'filename': 'One.Piece.S01E1171.1080p.NF.WEB-DL.AAC2.0.H.264-VARYG.mkv',
                    'attachments': [
                        {
                            'id': 133226,
                            'type': 1,
                            'info': {
                                'cached': 1,
                                'codec': 'srt',
                                'lang': 'ar',
                                'name': 'Arabic',
                                'tracknum': 4,
                            },
                        },
                    ],
                },
            ],
        },
    )

    with TsukiHimeProvider() as provider:
        subtitles = provider.list_subtitles(episode, {Language('ara')})

    assert len(subtitles) == 1
    subtitle = subtitles[0]
    assert subtitle.language == Language('ara')
    assert subtitle.format == 'srt'
    assert subtitle.download_url == (
        'https://storage.tsukihime.org/attach/0002086A/'
        'One.Piece.S01E1171.1080p.NF.WEB-DL.AAC2.0.H.264-VARYG_track4.ar.srt.xz'
    )
    assert {'series', 'season', 'episode', 'year'} <= subtitle.get_matches(episode)


def test_list_movie_subtitles_uses_animetosho_storage_and_best_file(movie, requests_mock):
    requests_mock.get(
        'https://api.tsukihime.org/v1/animes/anilist/195230',
        json={'id': 400, 'release_year': 2025},
    )
    requests_mock.get(
        'https://api.tsukihime.org/v1/animes/400',
        json={
            'results': [
                {
                    'id': 401,
                    'name': 'Summer.Pockets.Season.1.Omnibus.1080p.BluRay',
                    'state': 'completed',
                    'sublangs': ['en'],
                    'source_date': '4',
                    'animetosho': True,
                },
            ],
        },
    )
    requests_mock.get(
        'https://api.tsukihime.org/v1/torrents/401',
        json={
            'files': [
                {
                    'filename': 'Unrelated.Movie.1080p.BluRay.mkv',
                    'attachments': [],
                },
                {
                    'filename': 'Summer.Pockets.Season.1.Omnibus.1080p.BluRay.mkv',
                    'attachments': [
                        {
                            'id': 65537,
                            'type': 1,
                            'info': {
                                'cached': 1,
                                'codec': 'ass',
                                'lang': 'en',
                                'name': 'English',
                                'tracknum': 2,
                            },
                        },
                    ],
                },
            ],
        },
    )

    with TsukiHimeProvider() as provider:
        subtitles = provider.list_subtitles(movie, {Language('eng')})

    assert len(subtitles) == 1
    subtitle = subtitles[0]
    assert subtitle.download_url == (
        'https://storage.tsukihime.org/tosho/attach/00010001/'
        'Summer.Pockets.Season.1.Omnibus.1080p.BluRay_track2.en.ass.xz'
    )
    assert {'title', 'year'} <= subtitle.get_matches(movie)


def test_download_subtitle_decompresses_xz(requests_mock):
    subtitle = TsukiHimeSubtitle(
        Language('eng'),
        'https://storage.tsukihime.org/attach/00000001/subtitle.en.srt.xz',
        release_info='Example',
        filename='Example.mkv',
        codec='srt',
        verified_matches={'title'},
    )
    content = b'1\n00:00:01,000 --> 00:00:02,000\nExample\n'
    requests_mock.get(subtitle.download_url, content=lzma.compress(content))

    with TsukiHimeProvider() as provider:
        result = provider.download_subtitle(subtitle)

    assert result is subtitle
    assert subtitle.content == content


def test_download_subtitle_rejects_non_xz_response(requests_mock):
    subtitle = TsukiHimeSubtitle(
        Language('eng'),
        'https://storage.tsukihime.org/attach/00000001/subtitle.en.srt.xz',
        release_info='Example',
        filename='Example.mkv',
        codec='srt',
        verified_matches={'title'},
    )
    requests_mock.get(subtitle.download_url, content=b'<html>not a subtitle</html>')

    with TsukiHimeProvider() as provider:
        with pytest.raises(ProviderError, match='unidentified archive type'):
            provider.download_subtitle(subtitle)


def test_list_subtitles_without_anime_id_returns_empty(movie):
    movie.anilist_id = None

    with TsukiHimeProvider() as provider:
        assert provider.list_subtitles(movie, {Language('eng')}) == []

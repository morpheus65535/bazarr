# -*- coding: utf-8 -*-
import pytest

from subliminal_patch.core import Episode, Movie
from subliminal_patch.providers.napiprojekt import NapiProjektProvider
from babelfish import Language


@pytest.fixture
def episode():
    return Episode(
        name='Attack on Titan - S02E01 - Beast Titan Bluray-1080p.mkv',
        series='Attack on Titan',
        season=2,
        episode=1,
        source='Web',
        series_imdb_id='tt2560140',
        hashes={
            'napiprojekt': 'fe93bb3a7743c39e12c8d7c4a864dff1'
        }
    )

@pytest.fixture
def movie():
    return Movie(
        name='Shrek.mkv',
        title='Shrek',
        year=2001,
        imdb_id='tt0126029',
        hashes={
            'napiprojekt': '444563eef63f83d47cabb888f7a45113'
        }
    )


@pytest.mark.vcr
def test_list_subtitles_episode(episode):
    with NapiProjektProvider() as provider:
        subs = provider.list_subtitles(episode, [Language.fromalpha2('pl')])
        assert len(subs) == 3


@pytest.mark.vcr
def test_list_subtitles_movie(movie):
    with NapiProjektProvider() as provider:
        subs = provider.list_subtitles(movie, [Language.fromalpha2('pl')])
        assert len(subs) == 28


import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import TableMissingSubtitles, TableMovies
from radarr.movie_snapshot import IncompleteMovie
from radarr.sync import movies
from radarr.sync.utils import MOVIE_DECODER
from tests.helpers.arr_fixtures import movie_payload


@pytest.mark.parametrize('incomplete', ['images', 'title', 'quality'])
def test_single_movie_sync_preserves_usable_incomplete_response(incomplete: str, memory_session: Session,
                                                               monkeypatch: pytest.MonkeyPatch) -> None:
    memory_session.add(TableMovies(radarrId=7, tmdbId='7', title='Existing movie', path='/movie.mkv', movie_file_id=10))
    memory_session.add(TableMissingSubtitles(media_type='movie', media_id=7, language='en'))
    memory_session.commit()
    payload = movie_payload(movie_id=7, file_id=10, path='/movie.mkv')
    if incomplete == 'images':
        payload['images'] = [{}]
    elif incomplete == 'title':
        del payload['title']
    else:
        file = payload['movieFile']
        assert isinstance(file, dict)
        del file['quality']
    record = MOVIE_DECODER.from_value(payload)
    assert isinstance(record, IncompleteMovie)
    assert record.hasFile is True and record.movieFile is not None
    monkeypatch.setattr(movies, 'database', memory_session)
    monkeypatch.setattr(movies.settings.general, 'movie_default_enabled', False)
    monkeypatch.setattr(movies, 'get_profile_list', lambda: [])
    monkeypatch.setattr(movies, 'get_tags', lambda: [])
    monkeypatch.setattr(movies, 'get_language_profiles', lambda: [])
    monkeypatch.setattr(movies, 'get_movies_from_radarr_api', lambda **kwargs: record)
    monkeypatch.setattr(movies, 'delete_media_and_wanted_search_state',
                        lambda *args: pytest.fail('Incomplete metadata must not delete a usable movie'))
    monkeypatch.setattr(movies, 'event_stream', lambda **kwargs: pytest.fail('The movie must be left unchanged'))

    movies.update_one_movie(7, 'updated')

    assert memory_session.execute(select(TableMovies.title)).scalar_one() == 'Existing movie'
    assert memory_session.execute(select(TableMissingSubtitles.language)).scalars().all() == ['en']

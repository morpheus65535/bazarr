"""Exercise the runtime ORM and autocommit engine, rather than table proxies."""
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from sqlalchemy import create_engine, event, insert, select
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from app import database as db
from constants import MINIMUM_VIDEO_SIZE
from languages import get_languages
import radarr.sync.movies as radarr
import sonarr.sync.series as sonarr
import subtitles.indexer.movies as movie_indexer
import subtitles.indexer.series as episode_indexer
import subtitles.wanted_state as state


@pytest.fixture
def runtime_database(monkeypatch, tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / "runtime.sqlite"}', isolation_level='AUTOCOMMIT')
    db.metadata.create_all(engine)
    with Session(engine) as session:
        for module in [db, state, movie_indexer, episode_indexer, radarr, sonarr]:
            monkeypatch.setattr(module, 'database', session)
        monkeypatch.setattr(get_languages, 'languages_dict', [
            {'code2': 'en', 'code3': 'eng', 'code3b': None, 'name': 'English'},
        ])
        yield engine, session
    engine.dispose()


def seed_media(session, media_type, missing='[]'):
    session.execute(insert(db.TableLanguagesProfiles).values(profileId=1, name='English', items='[]'))
    if media_type == 'movie':
        table, id_column = db.TableMovies, 'radarrId'
        session.execute(insert(table).values(
            radarrId=7, profileId=1, missing_subtitles=missing, audio_language='[]',
            path='/movie.mkv', title='Movie', tmdbId='7',
        ))
    else:
        table, id_column = db.TableEpisodes, 'sonarrEpisodeId'
        session.execute(insert(db.TableShows).values(sonarrSeriesId=7, path='/series', title='Series', profileId=1))
        session.execute(insert(table).values(
            sonarrEpisodeId=7, sonarrSeriesId=7, path='/series/episode.mkv', title='Episode',
            season=1, episode=1,
            missing_subtitles=missing, audio_language='[]',
        ))
    return table, id_column


def configure_indexer(monkeypatch, media_type):
    module = movie_indexer if media_type == 'movie' else episode_indexer
    monkeypatch.setattr(module, 'get_profiles_list', lambda **kwargs: {
        'items': [{'language': 'en', 'forced': 'False', 'hi': 'False'}],
    })
    monkeypatch.setattr(module, 'get_profile_cutoff', lambda **kwargs: None)
    monkeypatch.setattr(module, 'get_subtitles', lambda **kwargs: [])
    monkeypatch.setattr(module.settings.general, 'use_embedded_subs', False)
    events = []
    monkeypatch.setattr(module, 'event_stream', lambda **kwargs: events.append(kwargs))
    recalculate = (
        lambda: module.list_missing_subtitles_movies(no=7)
        if media_type == 'movie' else module.list_missing_subtitles(epno=7)
    )
    return recalculate, events


@pytest.mark.parametrize('media_type', ['movie', 'series'])
def test_bulk_subtitles_match_single_media_with_embedded_ids(runtime_database, media_type):
    _, session = runtime_database
    seed_media(session, media_type)
    table = db.TableMoviesSubtitles if media_type == 'movie' else db.TableEpisodesSubtitles
    values = {'radarrId': 7} if media_type == 'movie' else {'sonarrEpisodeId': 7, 'sonarrSeriesId': 7}
    session.execute(insert(table), [
        dict(values, id=71, language='en', forced=False, hi=False, embedded_track_id=0, path=None, size=0),
        dict(values, id=72, language='en', forced=True, hi=False, embedded_track_id=None, path='/movie.en.srt', size=123),
    ])
    single = db.get_subtitles(**({'radarr_id': 7} if media_type == 'movie' else {'sonarr_episode_id': 7}))
    assert db.get_subtitles_map(media_type, [7, 8])[7] == single
    assert {subtitle['id'] for subtitle in single} == {71, 72}


@pytest.mark.parametrize('media_type', ['movie', 'series'])
def test_missing_state_failure_rolls_back_both_representations(runtime_database, monkeypatch, media_type):
    engine, session = runtime_database
    table, _ = seed_media(session, media_type, "['fr']")
    state.refresh_wanted_search_state(media_type, 7, "['fr']", failed_attempts="[['fr', 10]]")
    recalculate, events = configure_indexer(monkeypatch, media_type)

    def fail_insert(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith('INSERT INTO table_missing_subtitles'):
            raise sqlite3.OperationalError('interrupted normalized insert')

    event.listen(engine, 'before_cursor_execute', fail_insert)
    try:
        with pytest.raises(sqlite3.OperationalError):
            recalculate()
    finally:
        event.remove(engine, 'before_cursor_execute', fail_insert)
    assert session.execute(select(table.missing_subtitles)).scalar_one() == "['fr']"
    assert state.get_missing_languages(media_type, 7) == ['fr']
    assert events == []
    recalculate()
    assert session.execute(select(table.missing_subtitles)).scalar_one() == "['en']"
    assert state.get_missing_languages(media_type, 7) == ['en']
    assert state.get_failed_attempt_pairs(media_type, 7) == [['fr', 10.0]]


@pytest.mark.parametrize('media_type', ['movie', 'series'])
@pytest.mark.parametrize('stale_languages', [[], ['fr']])
def test_unchanged_legacy_value_repairs_normalized_state(runtime_database, monkeypatch, media_type, stale_languages):
    _, session = runtime_database
    seed_media(session, media_type, "['en']")
    state.refresh_wanted_search_state(media_type, 7, stale_languages)
    recalculate, _ = configure_indexer(monkeypatch, media_type)
    recalculate()
    assert state.get_missing_languages(media_type, 7) == ['en']


def test_concurrent_missing_refreshes_keep_representations_consistent(runtime_database, monkeypatch):
    engine, session = runtime_database
    seed_media(session, 'movie')
    thread_sessions = scoped_session(sessionmaker(bind=engine))
    monkeypatch.setattr(state, 'database', thread_sessions)
    first_insert = Event()
    second_begin = Event()

    def interleave(connection, cursor, statement, parameters, context, executemany):
        if statement == 'BEGIN IMMEDIATE' and first_insert.is_set():
            second_begin.set()
        elif statement.startswith('INSERT INTO table_missing_subtitles') and not first_insert.is_set():
            first_insert.set()
            assert second_begin.wait(5), 'second writer did not reach its transaction'

    def refresh(value):
        try:
            state.store_missing_subtitles(db.TableMovies.__table__, 'radarrId', 'movie', 7, value)
        finally:
            thread_sessions.remove()

    event.listen(engine, 'before_cursor_execute', interleave)
    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            first = workers.submit(refresh, "['en']")
            assert first_insert.wait(5), 'first writer did not reach its insert'
            second = workers.submit(refresh, "['fr']")
            first.result(timeout=10)
            second.result(timeout=10)
    finally:
        event.remove(engine, 'before_cursor_execute', interleave)
    assert session.execute(select(db.TableMovies.missing_subtitles)).scalar_one() == "['fr']"
    assert state.get_missing_languages('movie', 7) == ['fr']


@pytest.mark.parametrize('media_type', ['movie', 'series'])
def test_failed_attempt_mirror_rolls_back_with_normalized_rows(runtime_database, monkeypatch, media_type):
    engine, session = runtime_database
    media_table, id_column = seed_media(session, media_type)

    def fail_legacy_update(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith(f'UPDATE {media_table.__tablename__}'):
            raise sqlite3.OperationalError('interrupted legacy mirror update')

    event.listen(engine, 'before_cursor_execute', fail_legacy_update)
    try:
        with pytest.raises(sqlite3.OperationalError):
            state.record_failed_subtitle_attempts_map(media_type, {7: ['en']})
    finally:
        event.remove(engine, 'before_cursor_execute', fail_legacy_update)

    assert state.get_failed_attempt_pairs(media_type, 7) == []
    assert session.execute(select(getattr(media_table, 'failedAttempts'))
                           .where(getattr(media_table, id_column) == 7)).scalar_one() is None

    state.record_failed_subtitle_attempts_map(media_type, {7: ['en']})
    normalized = state.get_failed_attempt_pairs(media_type, 7)
    legacy = session.execute(select(getattr(media_table, 'failedAttempts'))
                             .where(getattr(media_table, id_column) == 7)).scalar_one()
    assert state.get_attempt_windows(legacy) == {'en': (normalized[0][1], normalized[-1][1])}


def test_concurrent_failed_attempts_keep_latest_timestamp_and_legacy_mirror(runtime_database, monkeypatch):
    engine, session = runtime_database
    seed_media(session, 'movie')
    thread_sessions = scoped_session(sessionmaker(bind=engine))
    monkeypatch.setattr(state, 'database', thread_sessions)
    first_insert = Event()
    second_begin = Event()
    first_begin = Event()

    def interleave(connection, cursor, statement, parameters, context, executemany):
        if statement == 'BEGIN IMMEDIATE':
            if first_begin.is_set():
                second_begin.set()
            else:
                first_begin.set()
        elif statement.startswith('INSERT INTO table_failed_subtitle_attempts') and first_begin.is_set():
            first_insert.set()
            assert second_begin.wait(5), 'second writer did not reach its transaction'

    def record():
        try:
            return state.record_failed_subtitle_attempts_map('movie', {7: ['en']})
        finally:
            thread_sessions.remove()

    event.listen(engine, 'before_cursor_execute', interleave)
    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            first = workers.submit(record)
            assert first_insert.wait(5), 'first writer did not reach its upsert'
            second = workers.submit(record)
            first.result(timeout=10)
            second.result(timeout=10)
    finally:
        event.remove(engine, 'before_cursor_execute', interleave)

    normalized = state.get_failed_attempt_pairs('movie', 7)
    legacy = session.execute(select(db.TableMovies.failedAttempts)
                             .where(db.TableMovies.radarrId == 7)).scalar_one()
    windows = state.get_attempt_windows(legacy)
    assert len(normalized) == 2
    assert normalized[0][1] <= normalized[-1][1]
    assert windows == {'en': (normalized[0][1], normalized[-1][1])}


@pytest.mark.parametrize('media_type, event_type', [('movie', 'movie'), ('series', 'episode')])
def test_unchanged_missing_state_notifies_rescan_without_rewriting(runtime_database, monkeypatch, media_type, event_type):
    engine, session = runtime_database
    seed_media(session, media_type, "['en']")
    state.refresh_wanted_search_state(media_type, 7, "['en']")
    recalculate, events = configure_indexer(monkeypatch, media_type)
    writes = []

    def collect_writes(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith(('UPDATE ', 'INSERT ', 'DELETE ')):
            writes.append(statement)

    event.listen(engine, 'before_cursor_execute', collect_writes)
    try:
        recalculate()
    finally:
        event.remove(engine, 'before_cursor_execute', collect_writes)
    assert writes == []
    assert {'type': event_type, 'payload': 7} in events
    assert {'type': event_type + '-wanted', 'action': 'update', 'payload': 7} in events


def configure_sync(monkeypatch, module, payload):
    movie_sync = module is radarr
    service = 'radarr' if movie_sync else 'sonarr'
    monkeypatch.setattr(module, f'check_{service}_rootfolder', lambda: None)
    monkeypatch.setattr(module, 'get_movies_from_radarr_api' if movie_sync else 'get_series_from_sonarr_api',
                        lambda **kwargs: payload)
    for name in ['get_profile_list', 'get_tags', 'get_language_profiles']:
        monkeypatch.setattr(module, name, lambda: [])
    monkeypatch.setattr(module, 'event_stream', lambda **kwargs: None)
    monkeypatch.setattr(module.jobs_queue, 'update_job_progress', lambda **kwargs: None)
    monkeypatch.setattr(module.jobs_queue, 'update_job_name', lambda **kwargs: None)
    if movie_sync:
        monkeypatch.setattr(module.settings.general, 'movie_default_enabled', False)
        monkeypatch.setattr(module.settings.radarr, 'apikey', 'test')
        monkeypatch.setattr(module.settings.radarr, 'sync_only_monitored_movies', False)
    else:
        monkeypatch.setattr(module.settings.sonarr, 'sync_only_monitored_series', False)


@pytest.mark.parametrize('movie_file', [None, {}, {'id': 1}, {'path': '/movie.mkv'},
                                      {'id': 1, 'path': '/movie.mkv', 'size': 'bad'}])
def test_malformed_movie_file_preserves_library_and_history(runtime_database, monkeypatch, movie_file):
    _, session = runtime_database
    seed_media(session, 'movie')
    session.execute(insert(db.TableHistoryMovie).values(radarrId=7, action=1, description='Saved history'))
    configure_sync(monkeypatch, radarr, [{'id': 7, 'hasFile': True, 'movieFile': movie_file}])
    radarr.update_movies(job_id='test')
    assert session.execute(select(db.TableMovies.radarrId)).scalars().all() == [7]
    assert session.execute(select(db.TableHistoryMovie.description)).scalars().all() == ['Saved history']


@pytest.mark.parametrize('media_type', ['movie', 'series'])
@pytest.mark.parametrize('bad_entry', [None, {}, {'id': [7]}, {'id': 'invalid'}, {'id': True}, {'id': 0}])
def test_unidentified_entries_disable_deletion_sweep(runtime_database, monkeypatch, media_type, bad_entry):
    _, session = runtime_database
    table, id_column = seed_media(session, media_type)
    module = radarr if media_type == 'movie' else sonarr
    configure_sync(monkeypatch, module, [bad_entry])
    (module.update_movies if media_type == 'movie' else module.update_series)(job_id='test')
    assert session.execute(select(getattr(table, id_column))).scalars().all() == [7]


@pytest.mark.parametrize('media_type', ['movie', 'series'])
def test_incomplete_sync_still_processes_identifiable_entries(runtime_database, monkeypatch, media_type):
    _, session = runtime_database
    table, id_column = seed_media(session, media_type)
    good = {'id': 8, 'title': 'New media', 'hasFile': True,
            'movieFile': {'id': 8, 'path': '/new.mkv', 'size': MINIMUM_VIDEO_SIZE + 1}}
    module = radarr if media_type == 'movie' else sonarr
    configure_sync(monkeypatch, module, [None, good])
    processed = []
    if media_type == 'movie':
        monkeypatch.setattr(radarr, 'movieParser', lambda movie, **kwargs: {'radarrId': movie['id'], 'title': movie['title']})
        monkeypatch.setattr(radarr, 'add_movie', lambda movie: processed.append(movie['radarrId']))
        radarr.update_movies(job_id='test')
    else:
        monkeypatch.setattr(sonarr, 'update_one_series', lambda series_id, **kwargs: processed.append(series_id))
        monkeypatch.setattr(sonarr, 'sync_episodes', lambda **kwargs: None)
        sonarr.update_series(job_id='test')
    assert processed == [8]
    assert session.execute(select(getattr(table, id_column))).scalars().all() == [7]


@pytest.mark.parametrize('payload', [
    {'id': 7, 'hasFile': False},
    {'id': 7, 'hasFile': True, 'movieFile': {'id': 1, 'path': '/movie.mkv', 'size': 1}},
])
def test_explicit_unusable_movie_removes_history_and_wanted_state(runtime_database, monkeypatch, payload):
    _, session = runtime_database
    seed_media(session, 'movie')
    session.execute(insert(db.TableHistoryMovie).values(radarrId=7, action=1, description='Saved history'))
    state.refresh_wanted_search_state('movie', 7, "['en']", "[['en', 10]]")
    configure_sync(monkeypatch, radarr, [payload])
    monkeypatch.setattr(radarr, 'get_movie_file_size_from_db', lambda path: 0)
    monkeypatch.setattr(radarr.settings.general, 'enable_strm_support', False)
    radarr.update_movies(job_id='test')
    assert session.execute(select(db.TableMovies.radarrId)).scalars().all() == []
    assert session.execute(select(db.TableHistoryMovie.id)).scalars().all() == []
    assert state.get_missing_languages('movie', 7) == []
    assert state.get_failed_attempt_pairs('movie', 7) == []


@pytest.mark.parametrize('media_type', ['movie', 'series'])
def test_valid_empty_response_removes_media_and_normalized_state(runtime_database, monkeypatch, media_type):
    _, session = runtime_database
    table, id_column = seed_media(session, media_type)
    state.refresh_wanted_search_state(media_type, 7, "['en']", "[['en', 10]]")
    module = radarr if media_type == 'movie' else sonarr
    configure_sync(monkeypatch, module, [])
    (module.update_movies if media_type == 'movie' else module.update_series)(job_id='test')
    assert session.execute(select(getattr(table, id_column))).scalars().all() == []
    assert state.get_missing_languages(media_type, 7) == []
    assert state.get_failed_attempt_pairs(media_type, 7) == []


def test_due_iterator_bounds_orm_fetches_and_handles_deleted_batches(monkeypatch):
    fetched = []

    class Cursor(sqlite3.Cursor):
        def execute(self, sql, parameters=()):
            self.sql = sql
            return super().execute(sql, parameters)

        def fetchall(self):
            rows = super().fetchall()
            if self.sql.startswith('SELECT') and 'table_missing_subtitles' in self.sql:
                fetched.append(len(rows))
            return rows

    class Connection(sqlite3.Connection):
        def cursor(self, *args, **kwargs):
            kwargs['factory'] = Cursor
            return super().cursor(*args, **kwargs)

    engine = create_engine('sqlite://', creator=lambda: sqlite3.connect(':memory:', factory=Connection),
                          isolation_level='AUTOCOMMIT')
    db.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            monkeypatch.setattr(state, 'database', session)
            monkeypatch.setattr(state, 'get_adaptive_search_policy', lambda: None)
            session.execute(insert(db.TableMissingSubtitles), [
                {'media_type': 'series', 'media_id': media_id, 'language': language}
                for media_id in range(1, 1002) for language in ['en', 'fr:hi', 'de:forced']
            ])
            iterator = state.iter_due_missing_languages_maps('series', batch_size=2)
            first = next(iterator)
            assert first == {1: ['en', 'fr:hi', 'de:forced'], 2: ['en', 'fr:hi', 'de:forced']}
            assert max(fetched) <= 6
            state.delete_wanted_search_state('series', list(first))
            remaining = [media_id for batch in iterator for media_id in batch]
            assert remaining == list(range(3, 1002))
            assert max(fetched) <= 6
    finally:
        engine.dispose()

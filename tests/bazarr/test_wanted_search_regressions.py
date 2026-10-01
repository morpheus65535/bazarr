"""Exercise the runtime ORM and autocommit engine, rather than table proxies."""
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from types import SimpleNamespace

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


@pytest.mark.skipif(not hasattr(sqlite3.Connection, 'setlimit'), reason='requires SQLite connection limits')
def test_bulk_database_queries_and_retry_upserts_respect_legacy_sqlite_limit(
    runtime_database,
    monkeypatch,
):
    engine, session = runtime_database
    connection = session.connection()
    raw_connection = connection.connection.driver_connection
    previous_limit = raw_connection.getlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER)
    session.execute(insert(db.TableMissingSubtitles), [
        {'media_type': 'movie', 'media_id': media_id, 'language': 'en'}
        for media_id in range(1, 1001)
    ])
    monkeypatch.setattr(state, 'get_adaptive_search_policy', lambda: None)
    raw_connection.setlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER, 999)

    try:
        assert len(state.get_missing_languages_map('movie', list(range(1, 1000)))) == 999
        assert db.get_subtitles_map('movie', list(range(1, 1001))) == {}
        due_batches = list(state.iter_due_missing_languages_maps('movie', batch_size=1000))
        assert len(due_batches) == 1
        assert len(due_batches[0]) == 1000

        connection.execute(insert(db.TableMovies), [
            {'radarrId': media_id, 'title': 'Movie', 'tmdbId': str(media_id), 'path': f'/movie-{media_id}.mkv'}
            for media_id in range(1, 1001)
        ])
        state.record_failed_subtitle_attempts_map(
            'movie', {media_id: ['en'] for media_id in range(1, 1001)},
        )
        assert len(connection.execute(select(db.TableFailedSubtitleAttempts)).all()) == 1000
    finally:
        raw_connection.setlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER, previous_limit)


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
def test_failed_attempt_upserts_roll_back_without_changing_legacy_snapshot(runtime_database, monkeypatch, media_type):
    engine, session = runtime_database
    media_table, id_column = seed_media(session, media_type)

    monkeypatch.setattr(state, 'FAILED_ATTEMPT_UPSERT_BATCH_SIZE', 1)
    inserts = []

    def fail_second_insert(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith('INSERT INTO table_failed_subtitle_attempts'):
            inserts.append(statement)
            if len(inserts) == 2:
                raise sqlite3.OperationalError('interrupted retry upsert')

    event.listen(engine, 'before_cursor_execute', fail_second_insert)
    try:
        with pytest.raises(sqlite3.OperationalError):
            state.record_failed_subtitle_attempts_map(media_type, {7: ['en', 'fr']})
    finally:
        event.remove(engine, 'before_cursor_execute', fail_second_insert)

    assert state.get_failed_attempt_pairs(media_type, 7) == []
    assert session.execute(select(getattr(media_table, 'failedAttempts'))
                           .where(getattr(media_table, id_column) == 7)).scalar_one() is None

    state.record_failed_subtitle_attempts_map(media_type, {7: ['en', 'fr']})
    assert {language for language, _ in state.get_failed_attempt_pairs(media_type, 7)} == {'en', 'fr'}
    assert session.execute(select(getattr(media_table, 'failedAttempts'))
                           .where(getattr(media_table, id_column) == 7)).scalar_one() is None


@pytest.mark.parametrize('media_type', ['movie', 'series'])
def test_record_failed_attempts_ignores_media_deleted_before_write(runtime_database, media_type):
    _, _session = runtime_database

    assert state.record_failed_subtitle_attempts(media_type, 7, ['en']) is None
    assert state.get_failed_attempt_pairs(media_type, 7) == []


def test_concurrent_failed_attempts_keep_timestamp_bounds_and_legacy_snapshot(runtime_database, monkeypatch):
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

    def record(timestamp):
        try:
            return state.record_failed_subtitle_attempts_map('movie', {7: ['en']}, {7: timestamp})
        finally:
            thread_sessions.remove()

    event.listen(engine, 'before_cursor_execute', interleave)
    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            first = workers.submit(record, 200)
            assert first_insert.wait(5), 'first writer did not reach its upsert'
            second = workers.submit(record, 100)
            first.result(timeout=10)
            second.result(timeout=10)
    finally:
        event.remove(engine, 'before_cursor_execute', interleave)

    normalized = state.get_failed_attempt_pairs('movie', 7)
    legacy = session.execute(select(db.TableMovies.failedAttempts)
                             .where(db.TableMovies.radarrId == 7)).scalar_one()
    assert normalized == [['en', 100.0], ['en', 200.0]]
    assert legacy is None


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
    job = SimpleNamespace(cancel_event=Event())
    monkeypatch.setattr(module.jobs_queue, 'get_job', lambda **kwargs: job)
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


@pytest.fixture
def series_deletion_state(runtime_database):
    engine, session = runtime_database

    def enable_foreign_keys(connection, _record):
        connection.execute('PRAGMA foreign_keys=ON')

    event.listen(engine, 'connect', enable_foreign_keys)
    session.connection().exec_driver_sql('PRAGMA foreign_keys=ON')
    seed_media(session, 'series', "['en']")
    state.refresh_wanted_search_state('series', 7, "['en']", failed_attempts="[['en', 10]]")
    try:
        yield engine, session
    finally:
        event.remove(engine, 'connect', enable_foreign_keys)


@pytest.mark.parametrize('failed_table', [
    'table_shows', 'table_missing_subtitles', 'table_failed_subtitle_attempts',
])
def test_series_deletion_failure_preserves_media_and_search_state(series_deletion_state, monkeypatch, failed_table):
    engine, session = series_deletion_state
    events = []
    monkeypatch.setattr(sonarr, 'event_stream', lambda **kwargs: events.append(kwargs))

    def fail_delete(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith(f'DELETE FROM {failed_table}'):
            raise sqlite3.OperationalError('injected deletion failure')

    event.listen(engine, 'before_cursor_execute', fail_delete)
    try:
        with pytest.raises(sqlite3.OperationalError, match='injected deletion failure'):
            sonarr.update_one_series(7, 'deleted')
    finally:
        event.remove(engine, 'before_cursor_execute', fail_delete)

    assert session.execute(select(db.TableShows.sonarrSeriesId)).scalars().all() == [7]
    assert session.execute(select(db.TableEpisodes.missing_subtitles)).scalars().all() == ["['en']"]
    assert state.get_missing_languages('series', 7) == ['en']
    assert session.execute(select(db.TableFailedSubtitleAttempts.language)).scalars().all() == ['en']
    assert events == []


@pytest.mark.parametrize('writer_kind', ['missing', 'attempts'])
def test_series_deletion_blocks_state_recreation(series_deletion_state, monkeypatch, writer_kind):
    engine, session = series_deletion_state
    thread_sessions = scoped_session(sessionmaker(bind=engine))
    monkeypatch.setattr(state, 'database', thread_sessions)
    monkeypatch.setattr(sonarr, 'database', thread_sessions)
    deletion_started = Event()
    writer_started = Event()
    notifications = []

    def notify(**kwargs):
        # Notifications are sent only after the deletion transaction commits.
        with engine.connect() as connection:
            assert connection.execute(select(db.TableShows.sonarrSeriesId)).first() is None
            assert connection.execute(select(db.TableMissingSubtitles.id)).first() is None
        notifications.append(kwargs)

    monkeypatch.setattr(sonarr, 'event_stream', notify)

    def interleave(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith('DELETE FROM table_shows'):
            deletion_started.set()
            assert writer_started.wait(5), 'state writer did not reach its transaction'
        elif statement == 'BEGIN IMMEDIATE' and deletion_started.is_set():
            writer_started.set()

    def delete_series():
        try:
            sonarr.update_one_series(7, 'deleted')
        finally:
            thread_sessions.remove()

    def refresh_state():
        try:
            if writer_kind == 'missing':
                state.store_missing_subtitles(db.TableEpisodes.__table__, 'sonarrEpisodeId', 'series', 7, "['fr']")
            else:
                state.record_failed_subtitle_attempts('series', 7, ['fr'])
        finally:
            thread_sessions.remove()

    event.listen(engine, 'before_cursor_execute', interleave)
    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            deletion = workers.submit(delete_series)
            assert deletion_started.wait(5), 'series deletion did not start'
            writer = workers.submit(refresh_state)
            deletion.result(timeout=10)
            writer.result(timeout=10)
    finally:
        event.remove(engine, 'before_cursor_execute', interleave)

    for table in [db.TableShows, db.TableEpisodes, db.TableMissingSubtitles, db.TableFailedSubtitleAttempts]:
        assert session.execute(select(table)).first() is None
    assert notifications == [{'type': 'series', 'action': 'delete', 'payload': 7}]


@pytest.fixture(params=['movie', 'series'])
def deletable_media(runtime_database, request):
    engine, session = runtime_database

    def enable_foreign_keys(connection, _record):
        connection.execute('PRAGMA foreign_keys=ON')

    event.listen(engine, 'connect', enable_foreign_keys)
    session.connection().exec_driver_sql('PRAGMA foreign_keys=ON')
    table, id_column = seed_media(session, request.param, "['en']")
    state.refresh_wanted_search_state(request.param, 7, "['en']", failed_attempts="[['en', 10]]")
    try:
        yield engine, session, request.param, table, id_column
    finally:
        event.remove(engine, 'connect', enable_foreign_keys)


@pytest.mark.parametrize('failed_delete', ['table_missing_subtitles', 'table_failed_subtitle_attempts'])
def test_media_deletion_rolls_back_parent_and_search_state(deletable_media, failed_delete):
    engine, session, media_type, table, id_column = deletable_media
    media_table = table.__table__

    def fail_state_delete(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith(f'DELETE FROM {failed_delete}'):
            raise sqlite3.OperationalError('injected search-state deletion failure')

    event.listen(engine, 'before_cursor_execute', fail_state_delete)
    try:
        with pytest.raises(sqlite3.OperationalError, match='injected search-state deletion failure'):
            state.delete_media_and_wanted_search_state(media_type, table, id_column, [7])
    finally:
        event.remove(engine, 'before_cursor_execute', fail_state_delete)

    assert session.execute(select(media_table.c[id_column])).scalars().all() == [7]
    assert state.get_missing_languages(media_type, 7) == ['en']
    assert session.execute(select(db.TableFailedSubtitleAttempts.language)).scalars().all() == ['en']


@pytest.mark.parametrize('writer_kind', ['missing', 'attempts'])
def test_media_deletion_waits_for_concurrent_state_writer(deletable_media, monkeypatch, writer_kind):
    engine, session, media_type, table, id_column = deletable_media
    media_table = table.__table__
    thread_sessions = scoped_session(sessionmaker(bind=engine))
    monkeypatch.setattr(state, 'database', thread_sessions)
    deletion_started = Event()
    writer_started = Event()

    def interleave(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith(f'DELETE FROM {media_table.name}'):
            deletion_started.set()
            assert writer_started.wait(5), 'state writer did not reach its transaction'
        elif statement == 'BEGIN IMMEDIATE' and deletion_started.is_set():
            writer_started.set()

    def delete_media():
        try:
            state.delete_media_and_wanted_search_state(media_type, table, id_column, [7])
        finally:
            thread_sessions.remove()

    def write_state():
        try:
            if writer_kind == 'missing':
                state.store_missing_subtitles(media_table, id_column, media_type, 7, "['fr']")
            else:
                state.record_failed_subtitle_attempts(media_type, 7, ['fr'])
        finally:
            thread_sessions.remove()

    event.listen(engine, 'before_cursor_execute', interleave)
    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            deletion = workers.submit(delete_media)
            assert deletion_started.wait(5), 'media deletion did not start'
            writer = workers.submit(write_state)
            deletion.result(timeout=10)
            writer.result(timeout=10)
    finally:
        event.remove(engine, 'before_cursor_execute', interleave)

    assert session.execute(select(media_table.c[id_column])).first() is None
    assert session.execute(select(db.TableMissingSubtitles.id)).first() is None
    assert session.execute(select(db.TableFailedSubtitleAttempts.id)).first() is None

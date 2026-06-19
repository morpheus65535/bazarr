import importlib
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import delete, event, insert, select, update

from subtitles import adaptive_searching, wanted_state


@pytest.mark.parametrize('kind', ['movies', 'series'])
def test_wanted_search_uses_normalized_retries_with_legacy_missing_languages(
    kind, row_factory, wanted_module, transactional_session, wanted_search_tables, monkeypatch,
):
    now = datetime.now()
    row = row_factory(
        missing_languages=['en', 'fr:hi:forced'],
        failed_attempts=[['en', (now - timedelta(days=30)).timestamp()], ['en', now.timestamp()]],
    )
    media_type, media_id, table, id_column, search = (
        ('movie', row.radarrId, wanted_search_tables.movie, 'radarrId', wanted_module._wanted_movie)
        if kind == 'movies' else
        ('series', row.sonarrEpisodeId, wanted_search_tables.episode, 'sonarrEpisodeId', wanted_module._wanted_episode)
    )
    # Retry columns and the missing-language mirror deliberately disagree with
    # their counterparts. This PR must use only the normalized retry history.
    transactional_session.execute(update(table).values(failedAttempts='malformed legacy value'))
    transactional_session.execute(delete(wanted_search_tables.missing_subtitles))
    del row.failedAttempts
    monkeypatch.setattr(adaptive_searching, 'get_adaptive_search_policy', lambda: {
        'delay': timedelta(days=21), 'delta': timedelta(days=7),
        'initial_search_cutoff': (now - timedelta(days=21)).timestamp(),
        'latest_search_cutoff': (now - timedelta(days=7)).timestamp(),
    })
    requested = []
    monkeypatch.setattr(wanted_module, 'generate_subtitles', lambda path, languages, *args, **kwargs:
                        requested.extend(languages) or iter([]))
    search(row, ['provider'])

    assert requested == [('fr', 'True', 'True')]
    attempts = wanted_state.get_failed_attempt_pairs(media_type, media_id)
    assert ['en', now.timestamp()] in attempts
    assert any(language == 'fr:forced:hi' for language, _ in attempts)
    assert transactional_session.execute(select(table.c.failedAttempts).where(
        table.c[id_column] == media_id)).scalar_one() == 'malformed legacy value'


@pytest.mark.parametrize('kind', ['movies', 'series'])
@pytest.mark.parametrize('outcome', ['failed', 'success', 'no_providers', 'exception'])
def test_wanted_search_records_all_failed_languages_only_after_a_completed_failed_search(
    kind, outcome, row_factory, wanted_module, monkeypatch,
):
    row = row_factory(missing_languages=['en', 'fr'], failed_attempts=[])
    media_type, media_id, search = (
        ('movie', row.radarrId, wanted_module._wanted_movie) if kind == 'movies' else
        ('series', row.sonarrEpisodeId, wanted_module._wanted_episode)
    )
    monkeypatch.setattr(adaptive_searching, 'get_adaptive_search_policy', lambda: None)
    for name in ('store_subtitles_movie', 'store_subtitles', 'history_log_movie', 'history_log',
                 'send_notifications_movie', 'send_notifications', 'event_stream'):
        if hasattr(wanted_module, name):
            monkeypatch.setattr(wanted_module, name, lambda *args, **kwargs: None)

    def generate(*args, **kwargs):
        if outcome == 'exception':
            raise RuntimeError('search interrupted')
        if outcome == 'success':
            yield SimpleNamespace(message='downloaded')

    monkeypatch.setattr(wanted_module, 'generate_subtitles', generate)
    if outcome == 'exception':
        with pytest.raises(RuntimeError, match='interrupted'):
            search(row, ['provider'])
    else:
        search(row, [] if outcome == 'no_providers' else ['provider'])
    attempts = wanted_state.get_failed_attempt_pairs(media_type, media_id)
    assert {language for language, _ in attempts} == ({'en', 'fr'} if outcome == 'failed' else set())


@pytest.mark.parametrize('kind', ['movies', 'series'])
def test_sync_checks_normalized_retry_windows(kind, row_factory, bind_wanted_database, monkeypatch):
    now = datetime.now()
    row = row_factory(missing_languages=['en'], failed_attempts=[
        ['en', (now - timedelta(days=30)).timestamp()], ['en', now.timestamp()],
    ])
    module = importlib.import_module('radarr.sync.movies' if kind == 'movies' else 'sonarr.sync.episodes')
    bind_wanted_database(module, kind)
    monkeypatch.setattr(module, 'get_exclusion_clause', lambda *args: [])
    monkeypatch.setattr(adaptive_searching, 'get_adaptive_search_policy', lambda: {
        'delay': timedelta(days=21), 'delta': timedelta(days=7),
        'initial_search_cutoff': (now - timedelta(days=21)).timestamp(),
        'latest_search_cutoff': (now - timedelta(days=7)).timestamp(),
    })
    kwargs = {'radarr_id': row.radarrId} if kind == 'movies' else {'episode_id': row.sonarrEpisodeId}
    assert module._is_there_missing_subtitles(**kwargs) is False
    media_type = 'movie' if kind == 'movies' else 'series'
    media_id = row.radarrId if kind == 'movies' else row.sonarrEpisodeId
    wanted_state.refresh_failed_subtitle_attempts(media_type, media_id, [])
    assert module._is_there_missing_subtitles(**kwargs) is True


@pytest.mark.parametrize('kind', ['movies', 'series'])
def test_indexer_updates_normalized_missing_languages_before_sync_checks(
    kind, row_factory, bind_wanted_database, monkeypatch,
):
    now = datetime.now()
    row = row_factory(missing_languages=['fr'], failed_attempts=[
        ['en', (now - timedelta(days=30)).timestamp()], ['en', now.timestamp()],
    ])
    indexer = importlib.import_module('subtitles.indexer.movies' if kind == 'movies' else 'subtitles.indexer.series')
    bind_wanted_database(indexer, kind)
    monkeypatch.setattr(indexer, 'get_profiles_list', lambda **kwargs: {'items': [{
        'language': 'en', 'hi': 'False', 'forced': 'False', 'audio_exclude': 'False', 'audio_only_include': 'False',
    }]})
    monkeypatch.setattr(indexer, 'get_profile_cutoff', lambda **kwargs: None)
    monkeypatch.setattr(indexer, 'event_stream', lambda **kwargs: None)
    if kind == 'movies':
        indexer.list_missing_subtitles_movies(no=row.radarrId)
        media_type, media_id = 'movie', row.radarrId
    else:
        indexer.list_missing_subtitles(epno=row.sonarrEpisodeId)
        media_type, media_id = 'series', row.sonarrEpisodeId
    assert wanted_state.get_missing_languages(media_type, media_id) == ['en']
    sync = importlib.import_module('radarr.sync.movies' if kind == 'movies' else 'sonarr.sync.episodes')
    bind_wanted_database(sync, kind)
    monkeypatch.setattr(sync, 'get_exclusion_clause', lambda *args: [])
    monkeypatch.setattr(adaptive_searching, 'get_adaptive_search_policy', lambda: {
        'delay': timedelta(days=21), 'delta': timedelta(days=7),
        'initial_search_cutoff': (now - timedelta(days=21)).timestamp(),
        'latest_search_cutoff': (now - timedelta(days=7)).timestamp(),
    })
    kwargs = {'radarr_id': media_id} if kind == 'movies' else {'episode_id': media_id}
    assert sync._is_there_missing_subtitles(**kwargs) is False


def test_retry_upsert_canonicalizes_languages_and_preserves_timestamp_bounds(
    movie_row_factory, monkeypatch,
):
    movie = movie_row_factory(failed_attempts=[['en', 10], ['en', 20]])
    for timestamp in (100, 200, 150):
        monkeypatch.setattr(wanted_state, 'datetime', SimpleNamespace(
            now=lambda: datetime.fromtimestamp(timestamp), timestamp=datetime.timestamp,
        ))
        assert wanted_state.record_failed_subtitle_attempts(
            'movie', movie.radarrId, [' EN ', 'fr:hi:forced', 'FR:FORCED:HI', '', None],
        ) is None
    assert sorted(wanted_state.get_failed_attempt_pairs('movie', movie.radarrId)) == [
        ['en', 10.0], ['en', 200.0], ['fr:forced:hi', 100.0], ['fr:forced:hi', 200.0],
    ]


def test_retry_upsert_rolls_back_all_chunks_on_failure(
    movie_row_factory, transactional_connection, monkeypatch,
):
    movie = movie_row_factory(failed_attempts=[])
    monkeypatch.setattr(wanted_state, 'FAILED_ATTEMPT_UPSERT_BATCH_SIZE', 1)
    calls = []

    def reject_second_insert(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith('INSERT INTO table_failed_subtitle_attempts'):
            calls.append(statement)
            if len(calls) == 2:
                raise RuntimeError('write failed')

    event.listen(transactional_connection, 'before_cursor_execute', reject_second_insert)
    try:
        with pytest.raises(RuntimeError, match='write failed'):
            wanted_state.record_failed_subtitle_attempts('movie', movie.radarrId, ['en', 'fr'])
    finally:
        event.remove(transactional_connection, 'before_cursor_execute', reject_second_insert)
    assert wanted_state.get_failed_attempt_pairs('movie', movie.radarrId) == []


@pytest.mark.parametrize('kind', ['movies', 'series'])
def test_deleting_media_cleans_up_retries_and_skips_late_writes(
    kind, row_factory, wanted_search_tables, transactional_session,
):
    row = row_factory()
    media_type, media_id, table, id_column = (
        ('movie', row.radarrId, wanted_search_tables.movie, 'radarrId') if kind == 'movies' else
        ('series', row.sonarrEpisodeId, wanted_search_tables.episode, 'sonarrEpisodeId')
    )
    assert wanted_state.delete_media_and_wanted_search_state(media_type, table, id_column, media_id) == [media_id]
    wanted_state.record_failed_subtitle_attempts(media_type, media_id, ['en'])
    assert wanted_state.get_failed_attempt_pairs(media_type, media_id) == []
    assert wanted_state.get_missing_languages(media_type, media_id) == []
    assert transactional_session.execute(select(table.c[id_column])).all() == []


def test_bulk_retry_writes_and_deletion_respect_older_sqlite_bind_limits(
    movie_row_factory, wanted_search_tables, transactional_session, transactional_connection,
):
    movie = movie_row_factory(missing_languages=[], failed_attempts=[])
    table = wanted_search_tables.movie
    media_ids = list(range(1000, 2005))
    transactional_session.execute(insert(table), [
        dict(vars(movie), id=media_id, radarrId=media_id) for media_id in media_ids
    ])

    def check_bind_count(connection, cursor, statement, parameters, context, executemany):
        if not executemany:
            assert len(parameters) <= 999

    event.listen(transactional_connection, 'before_cursor_execute', check_bind_count)
    try:
        wanted_state.record_failed_subtitle_attempts_map('movie', {media_id: ['en'] for media_id in media_ids})
        assert len(transactional_session.execute(select(wanted_search_tables.failed_subtitle_attempts)).all()) == 1005
        assert wanted_state.delete_media_and_wanted_search_state('movie', table, 'radarrId', media_ids) == media_ids
        assert transactional_session.execute(select(wanted_search_tables.failed_subtitle_attempts)).all() == []
    finally:
        event.remove(transactional_connection, 'before_cursor_execute', check_bind_count)

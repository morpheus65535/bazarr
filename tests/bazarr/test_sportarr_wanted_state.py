"""
Sports events keep missing languages and failed attempts in the shared tables, keyed by the event row id.

These tests run the sports code against the real models on SQLite, so the queries, the shared-table writers and
the cleanup paths run as they do in the application.
"""
from datetime import datetime, timedelta
from threading import Event
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import database as db
from sportarr.sync import events as sync_events_module
from sportarr.sync import leagues as sync_leagues_module
from subtitles import wanted_state
from subtitles.wanted import sports as wanted_sports


@pytest.fixture
def sports_session(tmp_path, monkeypatch):
    engine = create_engine(f'sqlite:///{tmp_path / "sports.sqlite"}')
    db.metadata.create_all(engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode='create_savepoint')
    for module in (wanted_state, wanted_sports, sync_events_module, sync_leagues_module):
        monkeypatch.setattr(module, 'database', session)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


def _add_league(session, league_id=1, tags='[]'):
    session.execute(db.insert(db.TableSportsLeagues).values(
        sportarrLeagueId=league_id, title=f'League {league_id}', path=f'/sports/{league_id}', profileId=None,
        tags=tags, monitored='True',
    ))


def _add_event(session, row_id, league_id=1, sportarr_event_id=None, part_number=0, missing=(), failed=()):
    session.execute(db.insert(db.TableSportsEvents).values(
        id=row_id, sportarrLeagueId=league_id, sportarrEventId=sportarr_event_id or row_id, partNumber=part_number,
        path=f'/sports/{league_id}/{row_id}.mkv', title=f'Event {row_id}', season=2026, episode=row_id,
        monitored='True', file_id=row_id, missing_subtitles_calculated=True,
    ))
    # An indexed external subtitle keeps the search from reindexing the event.
    session.execute(db.insert(db.TableSportsEventsSubtitles).values(
        sportsEventId=row_id, sportarrLeagueId=league_id, language='xx', forced=False, hi=False,
        path=f'/sports/{league_id}/{row_id}.xx.srt',
    ))
    if missing:
        session.execute(db.insert(db.TableMissingSubtitles), [
            {'media_type': 'sports', 'media_id': row_id, 'language': language} for language in missing
        ])
    for language, initial, latest in failed:
        session.execute(db.insert(db.TableFailedSubtitleAttempts).values(
            media_type='sports', media_id=row_id, language=language, initial_attempt_at=initial,
            latest_attempt_at=latest,
        ))


def _shared_rows(session, model):
    return sorted(session.execute(
        db.select(model.media_id, model.language).where(model.media_type == 'sports')
    ).all())


def _failed_languages(session, row_id):
    return sorted(session.execute(
        db.select(db.TableFailedSubtitleAttempts.language)
        .where(db.TableFailedSubtitleAttempts.media_type == 'sports')
        .where(db.TableFailedSubtitleAttempts.media_id == row_id)
    ).scalars().all())


class _FakeJobsQueue:
    def __init__(self):
        self.job = SimpleNamespace(cancel_event=Event())
        self.progress = []
        self.names = []

    def get_job(self, job_id):
        return self.job

    def add_job_from_function(self, *args, **kwargs):
        return None

    def update_job_progress(self, **kwargs):
        self.progress.append(kwargs)

    def update_job_name(self, **kwargs):
        self.names.append(kwargs['new_job_name'])


@pytest.fixture
def search(monkeypatch):
    calls = []
    results = {}

    def generate_subtitles(path, languages, audio_language, scene_name, title, media_type, profile_id,
                           attempted_languages=None, **kwargs):
        calls.append({'path': path, 'languages': list(languages), 'scene_name': scene_name,
                      'media_type': media_type})
        if attempted_languages is not None:
            attempted_languages.update(languages)
        yield from results.get(path, [])

    monkeypatch.setattr(wanted_sports, 'generate_subtitles', generate_subtitles)
    monkeypatch.setattr(wanted_sports, 'get_providers', lambda: ['provider'])
    monkeypatch.setattr(wanted_sports, 'get_adaptive_search_policy', lambda: None)
    monkeypatch.setattr(wanted_sports, 'get_audio_profile_languages', lambda value: [])
    monkeypatch.setattr(wanted_sports, 'store_subtitles_sports', lambda event_id: None)
    monkeypatch.setattr(wanted_sports, 'get_sports_subtitles', lambda sports_event_id: [
        {'path': f'/sports/{sports_event_id}.xx.srt', 'embedded_track_id': None},
    ])
    monkeypatch.setattr(wanted_sports, 'history_log_sports', lambda *args, **kwargs: None)
    monkeypatch.setattr(wanted_sports, 'event_stream', lambda **kwargs: None)
    monkeypatch.setattr(wanted_sports.path_mappings, 'path_replace_sports', lambda path: path)
    monkeypatch.setattr(wanted_sports.settings.sportarr, 'excluded_tags', [])
    monkeypatch.setattr(wanted_sports.settings.sportarr, 'excluded_sports', [])
    monkeypatch.setattr(wanted_sports.settings.sportarr, 'only_monitored', False)
    return SimpleNamespace(calls=calls, results=results)


def test_failed_search_records_every_searched_language(sports_session, search):
    _add_league(sports_session)
    _add_event(sports_session, 1, missing=['en', 'fr:hi', 'de:forced'])

    wanted_sports.wanted_download_subtitles_sports(1)

    assert search.calls[0]['languages'] == [('en', 'False', 'False'), ('fr', 'True', 'False'),
                                            ('de', 'False', 'True')]
    assert search.calls[0]['scene_name'] is None
    # The old column stamped only the last language. Every searched language is recorded now.
    assert _failed_languages(sports_session, 1) == ['de:forced', 'en', 'fr:hi']


def test_failed_search_keeps_parts_of_one_event_apart(sports_session, search):
    _add_league(sports_session)
    _add_event(sports_session, 1, sportarr_event_id=318, part_number=1, missing=['en'])
    _add_event(sports_session, 2, sportarr_event_id=318, part_number=2, missing=['es'])

    wanted_sports.wanted_download_subtitles_sports(2)

    assert search.calls[0]['languages'] == [('es', 'False', 'False')]
    assert _failed_languages(sports_session, 1) == []
    assert _failed_languages(sports_session, 2) == ['es']


def test_search_skips_languages_throttled_by_adaptive_search(sports_session, search, monkeypatch):
    now = datetime.now()
    policy = {
        'delay': timedelta(weeks=3), 'delta': timedelta(weeks=1), 'delay_label': '3w', 'delta_label': '1w',
        'now': now,
        'initial_search_cutoff': (now - timedelta(weeks=3)).timestamp(),
        'latest_search_cutoff': (now - timedelta(weeks=1)).timestamp(),
    }
    monkeypatch.setattr(wanted_sports, 'get_adaptive_search_policy', lambda: policy)
    old_attempt = (now - timedelta(weeks=4)).timestamp()
    recent_attempt = (now - timedelta(days=1)).timestamp()
    _add_league(sports_session)
    _add_event(sports_session, 1, missing=['en', 'fr'], failed=[('en', old_attempt, recent_attempt)])

    wanted_sports.wanted_download_subtitles_sports(1)

    assert search.calls[0]['languages'] == [('fr', 'False', 'False')]


def test_scheduled_search_reads_due_rows_and_records_attempts(sports_session, search, monkeypatch):
    jobs_queue = _FakeJobsQueue()
    monkeypatch.setattr(wanted_sports, 'jobs_queue', jobs_queue)
    monkeypatch.setattr(wanted_sports, '_DUE_SPORTS_EVENT_DETAILS_BATCH_SIZE', 1)
    monkeypatch.setattr(wanted_sports.settings.sportarr, 'excluded_tags', ['skip'])
    _add_league(sports_session, 1)
    _add_league(sports_session, 2, tags="['skip']")
    _add_event(sports_session, 1, league_id=1, missing=['en', 'fr'])
    _add_event(sports_session, 2, league_id=1)
    _add_event(sports_session, 3, league_id=2, missing=['en'])
    _add_event(sports_session, 4, league_id=1, missing=['de'])
    search.results['/sports/1/4.mkv'] = [SimpleNamespace(message='found')]

    def store_subtitles_sports(event_id):
        # The download satisfied the language, as the indexer would record.
        wanted_state.store_missing_subtitles(db.TableSportsEvents.__table__, 'id', 'sports', event_id, '[]')

    monkeypatch.setattr(wanted_sports, 'store_subtitles_sports', store_subtitles_sports)

    wanted_sports.wanted_search_missing_subtitles_sports(job_id=1)

    assert [call['path'] for call in search.calls] == ['/sports/1/1.mkv', '/sports/1/4.mkv']
    assert jobs_queue.progress[0] == {'job_id': 1, 'progress_max': 2}
    assert _failed_languages(sports_session, 1) == ['en', 'fr']
    assert _failed_languages(sports_session, 3) == []
    assert _failed_languages(sports_session, 4) == []
    assert jobs_queue.names == ['Searched for missing sports events subtitles']


def test_scheduled_search_marks_empty_run_complete(sports_session, search, monkeypatch):
    jobs_queue = _FakeJobsQueue()
    monkeypatch.setattr(wanted_sports, 'jobs_queue', jobs_queue)
    _add_league(sports_session)
    _add_event(sports_session, 1)

    wanted_sports.wanted_search_missing_subtitles_sports(job_id=1)

    assert search.calls == []
    assert {'job_id': 1, 'progress_value': 'max'} in jobs_queue.progress


def test_wanted_download_recalculates_when_calculation_is_incomplete(sports_session, search, monkeypatch):
    _add_league(sports_session)
    _add_event(sports_session, 1)
    sports_session.execute(db.update(db.TableSportsEvents).values(missing_subtitles_calculated=False))
    recalculated = []

    def list_missing_subtitles_sports(evno=None):
        recalculated.append(evno)
        wanted_state.store_missing_subtitles(db.TableSportsEvents.__table__, 'id', 'sports', evno, "['en']")

    monkeypatch.setattr(wanted_sports, 'list_missing_subtitles_sports', list_missing_subtitles_sports)

    wanted_sports.wanted_download_subtitles_sports(1)

    assert recalculated == [1]
    assert search.calls[0]['languages'] == [('en', 'False', 'False')]


@pytest.fixture
def sync(monkeypatch):
    deleted = []
    monkeypatch.setattr(sync_events_module, 'store_subtitles_sports', lambda event_id: None)
    monkeypatch.setattr(sync_events_module, 'event_stream',
                        lambda **kwargs: deleted.append(kwargs['payload']) if kwargs.get('action') == 'delete'
                        else None)
    monkeypatch.setattr(sync_events_module.settings.sportarr, 'sync_only_monitored_leagues', False)
    monkeypatch.setattr(sync_events_module.settings.sportarr, 'sync_only_monitored_events', False)
    return deleted


def _sportarr_event(event_id, parts, league_id=1):
    return {
        'id': event_id, 'leagueId': league_id, 'title': f'Event {event_id}', 'monitored': True, 'hasFile': True,
        'files': [{'id': event_id * 10 + part, 'partNumber': part, 'filePath': f'/sports/{league_id}/{event_id}.mkv',
                   'size': 500 * 1024 * 1024} for part in parts],
    }


def _seed_sync_rows(session):
    _add_league(session)
    _add_event(session, 1, sportarr_event_id=10, missing=['en'], failed=[('en', 1, 2)])
    _add_event(session, 2, sportarr_event_id=11, part_number=1, missing=['en'], failed=[('en', 1, 2)])
    _add_event(session, 3, sportarr_event_id=11, part_number=2, missing=['fr'], failed=[('fr', 1, 2)])


def test_event_sync_removal_deletes_shared_rows(sports_session, sync, monkeypatch):
    _seed_sync_rows(sports_session)
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: [_sportarr_event(11, [1])])

    sync_events_module.sync_events(league_id=1)

    assert sports_session.execute(db.select(db.TableSportsEvents.id)).scalars().all() == [2]
    assert _shared_rows(sports_session, db.TableMissingSubtitles) == [(2, 'en')]
    assert _shared_rows(sports_session, db.TableFailedSubtitleAttempts) == [(2, 'en')]
    # Deletion notifications carry the Sportarr event id, once per removed row.
    assert sorted(sync) == [10, 11]


@pytest.mark.parametrize('events', [
    [_sportarr_event(11, [1]), 'not an event'],
    [_sportarr_event(11, [1]), {'id': None, 'hasFile': True}],
], ids=['not-a-dict', 'no-id'])
def test_event_sync_keeps_rows_when_sportarr_returns_unidentified_events(sports_session, sync, monkeypatch, events):
    _seed_sync_rows(sports_session)
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api', lambda **kwargs: events)

    sync_events_module.sync_events(league_id=1)

    assert sports_session.execute(db.select(db.TableSportsEvents.id)).scalars().all() == [1, 2, 3]
    assert len(_shared_rows(sports_session, db.TableMissingSubtitles)) == 3
    assert sync == []


@pytest.mark.parametrize('payload', [None, {'records': []}, 'error'], ids=['failed', 'dict', 'text'])
def test_event_sync_stops_on_an_invalid_top_level_response(sports_session, sync, monkeypatch, payload):
    _seed_sync_rows(sports_session)
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api', lambda **kwargs: payload)

    sync_events_module.sync_events(league_id=1)

    assert sports_session.execute(db.select(db.TableSportsEvents.id)).scalars().all() == [1, 2, 3]
    assert sync == []


@pytest.mark.parametrize('file_change', [
    {'size': 'unknown'}, {'size': None}, {'filePath': ''}, {'filePath': None}, {'id': None}, {'partNumber': 'two'},
], ids=['size', 'no-size', 'path', 'no-path', 'file-id', 'part-number'])
def test_event_sync_keeps_a_part_when_its_file_data_is_incomplete(sports_session, sync, monkeypatch, file_change):
    _seed_sync_rows(sports_session)
    event = _sportarr_event(11, [1, 2])
    event['files'][1].update(file_change)
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api', lambda **kwargs: [event])

    sync_events_module.sync_events(league_id=1)

    assert sports_session.execute(db.select(db.TableSportsEvents.id)).scalars().all() == [2, 3]
    assert _shared_rows(sports_session, db.TableMissingSubtitles) == [(2, 'en'), (3, 'fr')]
    assert sync == [10]


def _add_history(session, row_id, league_id=1):
    session.execute(db.insert(db.TableHistorySports).values(
        action=1, description=f'Downloaded for {row_id}', sportsEventId=row_id, sportarrLeagueId=league_id,
    ))


def _event_rows(session):
    return session.execute(
        db.select(db.TableSportsEvents.id, db.TableSportsEvents.sportarrEventId, db.TableSportsEvents.partNumber,
                  db.TableSportsEvents.file_id)
        .order_by(db.TableSportsEvents.id)
    ).all()


def _row_ids(session, column):
    return sorted(session.execute(db.select(column)).scalars().all())


def _seed_fight_card(session):
    # Event 11 is a card with two parts, and each part has history.
    _seed_sync_rows(session)
    _add_history(session, 2)
    _add_history(session, 3)


def _partly_downloaded_event(parts):
    # Sportarr reports hasFile false until every monitored part has a file.
    event = _sportarr_event(11, parts)
    event['hasFile'] = False
    return event


def test_event_sync_adds_the_present_part_of_a_partly_downloaded_event(sports_session, sync, monkeypatch):
    _add_league(sports_session)
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: [_partly_downloaded_event([2])])

    sync_events_module.sync_events(league_id=1)

    assert [(row.sportarrEventId, row.partNumber, row.file_id) for row in _event_rows(sports_session)] == \
        [(11, 2, 112)]


def test_event_sync_keeps_the_other_part_when_one_part_loses_its_file(sports_session, sync, monkeypatch):
    _seed_fight_card(sports_session)
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: [_sportarr_event(10, [0]), _partly_downloaded_event([1])])

    sync_events_module.sync_events(league_id=1)

    assert [row.id for row in _event_rows(sports_session)] == [1, 2]
    assert _row_ids(sports_session, db.TableSportsEventsSubtitles.sportsEventId) == [1, 2]
    assert _row_ids(sports_session, db.TableHistorySports.sportsEventId) == [2]
    assert _shared_rows(sports_session, db.TableMissingSubtitles) == [(1, 'en'), (2, 'en')]
    assert _shared_rows(sports_session, db.TableFailedSubtitleAttempts) == [(1, 'en'), (2, 'en')]
    assert sync == [11]


def test_event_sync_removes_every_part_when_no_file_remains(sports_session, sync, monkeypatch):
    _seed_fight_card(sports_session)
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: [_sportarr_event(10, [0]), _partly_downloaded_event([])])

    sync_events_module.sync_events(league_id=1)

    assert [row.id for row in _event_rows(sports_session)] == [1]
    assert _row_ids(sports_session, db.TableSportsEventsSubtitles.sportsEventId) == [1]
    assert _row_ids(sports_session, db.TableHistorySports.sportsEventId) == []
    assert _shared_rows(sports_session, db.TableMissingSubtitles) == [(1, 'en')]
    assert _shared_rows(sports_session, db.TableFailedSubtitleAttempts) == [(1, 'en')]
    assert sorted(sync) == [11, 11]


@pytest.mark.parametrize('files', [None, 'error'], ids=['no-files', 'text'])
def test_event_sync_keeps_parts_when_the_file_list_is_invalid(sports_session, sync, monkeypatch, files):
    _seed_fight_card(sports_session)
    event = _partly_downloaded_event([1])
    event['files'] = files
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: [_sportarr_event(10, [0]), event])

    sync_events_module.sync_events(league_id=1)

    assert [row.id for row in _event_rows(sports_session)] == [1, 2, 3]
    assert _row_ids(sports_session, db.TableHistorySports.sportsEventId) == [2, 3]
    assert sync == []


def test_event_sync_updates_an_upgraded_part_in_place(sports_session, sync, monkeypatch):
    _seed_fight_card(sports_session)
    # Only part 2 differs from Sportarr, so only part 2 is reindexed.
    for row_id, event_id, file_id in ((1, 10, 100), (2, 11, 111), (3, 11, 112)):
        sports_session.execute(db.update(db.TableSportsEvents)
                               .values(file_id=file_id, path=f'/sports/1/{event_id}.mkv')
                               .where(db.TableSportsEvents.id == row_id))
    reindexed = []
    monkeypatch.setattr(sync_events_module, 'store_subtitles_sports', reindexed.append)
    event = _partly_downloaded_event([1, 2])
    event['files'][1]['id'] = 999
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: [_sportarr_event(10, [0]), event])

    sync_events_module.sync_events(league_id=1)

    assert [(row.id, row.partNumber, row.file_id) for row in _event_rows(sports_session)
            if row.sportarrEventId == 11] == [(2, 1, 111), (3, 2, 999)]
    assert _row_ids(sports_session, db.TableHistorySports.sportsEventId) == [2, 3]
    assert reindexed == [3]
    assert sync == []


def test_league_removal_deletes_shared_rows_of_its_events(sports_session, monkeypatch):
    _add_league(sports_session, 1)
    _add_league(sports_session, 2)
    _add_event(sports_session, 1, league_id=1, missing=['en'], failed=[('en', 1, 2)])
    _add_event(sports_session, 2, league_id=1, sportarr_event_id=1, part_number=1, missing=['fr'])
    _add_event(sports_session, 3, league_id=2, missing=['de'], failed=[('de', 1, 2)])
    removed = []
    monkeypatch.setattr(sync_leagues_module, 'event_stream', lambda **kwargs: removed.append(kwargs))

    sync_leagues_module.update_one_league(1, action='deleted')

    assert sports_session.execute(db.select(db.TableSportsLeagues.sportarrLeagueId)).scalars().all() == [2]
    assert sports_session.execute(db.select(db.TableSportsEvents.id)).scalars().all() == [3]
    assert _shared_rows(sports_session, db.TableMissingSubtitles) == [(3, 'de')]
    assert _shared_rows(sports_session, db.TableFailedSubtitleAttempts) == [(3, 'de')]
    assert removed == [{'type': 'sports-league', 'action': 'delete', 'payload': 1}]


def test_league_sync_skips_removal_when_sportarr_returns_unidentified_leagues(sports_session, monkeypatch):
    _add_league(sports_session, 1)
    _add_league(sports_session, 2)
    _add_event(sports_session, 1, league_id=2, missing=['en'])
    monkeypatch.setattr(sync_leagues_module, 'check_sportarr_rootfolder', lambda: None)
    monkeypatch.setattr(sync_leagues_module, 'get_tags', lambda: [])
    monkeypatch.setattr(sync_leagues_module, 'get_language_profiles', lambda: [])
    actions = []
    monkeypatch.setattr(sync_leagues_module, 'update_one_league',
                        lambda league_id, action, **kwargs: actions.append((league_id, action)))
    monkeypatch.setattr(sync_leagues_module, 'sync_events', lambda league_id: None)
    monkeypatch.setattr(sync_leagues_module, 'jobs_queue', _FakeJobsQueue())
    monkeypatch.setattr(sync_leagues_module.settings.sportarr, 'sync_only_monitored_leagues', False)
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api', lambda **kwargs: [
        {'id': 1, 'name': 'League 1', 'path': '/sports/1', 'monitored': True}, {'name': 'No id'},
    ])

    sync_leagues_module.update_leagues(job_id=1)

    assert actions == [(1, 'updated')]
    assert _shared_rows(sports_session, db.TableMissingSubtitles) == [(1, 'en')]


def test_league_sync_stops_on_an_invalid_top_level_response(sports_session, monkeypatch):
    jobs_queue = _FakeJobsQueue()
    monkeypatch.setattr(sync_leagues_module, 'check_sportarr_rootfolder', lambda: None)
    monkeypatch.setattr(sync_leagues_module, 'jobs_queue', jobs_queue)
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api', lambda **kwargs: 'Unauthorized')
    monkeypatch.setattr(sync_leagues_module, 'update_one_league',
                        lambda *args, **kwargs: pytest.fail('a league was synced from an invalid response'))

    sync_leagues_module.update_leagues(job_id=1)

    assert jobs_queue.names == ['Synced leagues with Sportarr']


@pytest.fixture
def mass_download(monkeypatch, tmp_path, sports_session):
    from subtitles.mass_download import sports as mass_download_sports

    calls = []

    def generate_subtitles(path, languages, *args, **kwargs):
        calls.append((path, list(languages)))
        yield from []

    for name, value in [
        ('generate_subtitles', generate_subtitles),
        ('get_providers', lambda: ['provider']),
        ('get_audio_profile_languages', lambda value: []),
        ('store_subtitles_sports', lambda event_id: None),
        ('history_log_sports', lambda *args, **kwargs: None),
        ('get_sports_subtitles', lambda sports_event_id: [{'path': '/x.srt', 'embedded_track_id': None}]),
        ('jobs_queue', _FakeJobsQueue()),
    ]:
        monkeypatch.setattr(mass_download_sports, name, value)
    # Every event path exists under tmp_path, so the file check passes.
    monkeypatch.setattr(mass_download_sports.path_mappings, 'path_replace_sports',
                        lambda path: str(tmp_path) + path)
    (tmp_path / 'sports' / '1').mkdir(parents=True)
    for row_id in range(1, 4):
        (tmp_path / 'sports' / '1' / f'{row_id}.mkv').touch()
    monkeypatch.setattr(mass_download_sports.settings.sportarr, 'excluded_tags', [])
    monkeypatch.setattr(mass_download_sports.settings.sportarr, 'excluded_sports', [])
    monkeypatch.setattr(mass_download_sports.settings.sportarr, 'only_monitored', False)
    monkeypatch.setattr(mass_download_sports, 'database', sports_session)
    return SimpleNamespace(module=mass_download_sports, calls=calls, root=str(tmp_path))


def test_league_download_searches_each_part_with_its_own_languages(sports_session, mass_download):
    _add_league(sports_session)
    _add_event(sports_session, 1, sportarr_event_id=318, part_number=1, missing=['en', 'fr:hi'])
    _add_event(sports_session, 2, sportarr_event_id=318, part_number=2, missing=['de'])
    _add_event(sports_session, 3)

    mass_download.module.league_download_subtitles(1, job_id=1)

    assert mass_download.calls == [
        (mass_download.root + '/sports/1/1.mkv', [('en', 'False', 'False'), ('fr', 'True', 'False')]),
        (mass_download.root + '/sports/1/2.mkv', [('de', 'False', 'False')]),
    ]


def test_league_download_reports_an_unknown_league(sports_session, mass_download):
    mass_download.module.league_download_subtitles(99, job_id=1)

    assert mass_download.calls == []
    assert mass_download.module.jobs_queue.progress == [
        {'job_id': 1, 'progress_message': 'League not found in database.'},
    ]


def test_league_download_stops_when_the_job_is_cancelled(sports_session, mass_download):
    _add_league(sports_session)
    _add_event(sports_session, 1, missing=['en'])
    mass_download.module.jobs_queue.job.cancel_event.set()

    with pytest.raises(mass_download.module.JobCanceled):
        mass_download.module.league_download_subtitles(1, job_id=1)

    assert mass_download.calls == []


def test_event_download_recalculates_when_calculation_is_incomplete(sports_session, mass_download, monkeypatch):
    _add_league(sports_session)
    _add_event(sports_session, 1)
    sports_session.execute(db.update(db.TableSportsEvents).values(missing_subtitles_calculated=False))
    recalculated = []

    def list_missing_subtitles_sports(evno=None):
        recalculated.append(evno)
        wanted_state.store_missing_subtitles(db.TableSportsEvents.__table__, 'id', 'sports', evno, "['en']")

    monkeypatch.setattr(mass_download.module, 'list_missing_subtitles_sports', list_missing_subtitles_sports)

    # Preloaded languages are dropped once the calculation reruns.
    mass_download.module.sports_event_download_subtitles(1, job_id=1, job_sub_function=True,
                                                         missing_languages=['stale'])

    assert recalculated == [1]
    assert mass_download.calls == [(mass_download.root + '/sports/1/1.mkv', [('en', 'False', 'False')])]

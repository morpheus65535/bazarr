"""
A league or event sync deletes Bazarr rows only when Sportarr proves the media is gone.

These tests run the sync against the real models on SQLite with foreign keys on, as Bazarr runs them, so a
deleted league or event also takes its subtitles, history and blacklist rows.
"""
import logging
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from requests.exceptions import ConnectionError as RequestsConnectionError
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app import database as db
from sportarr.sync import events as sync_events_module
from sportarr.sync import leagues as sync_leagues_module
from sportarr.sync import state as sync_state
from sportarr.sync import utils as sync_utils
from subtitles import wanted_state


@pytest.fixture
def sports_db(tmp_path, monkeypatch):
    engine = create_engine(f'sqlite:///{tmp_path / "sports.sqlite"}')

    @event.listens_for(engine, 'connect')
    def enable_foreign_keys(dbapi_connection, connection_record):
        # Bazarr turns this on, and the cascades are what delete the history.
        dbapi_connection.execute('PRAGMA foreign_keys=ON')

    db.metadata.create_all(engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode='create_savepoint')
    for module in (wanted_state, sync_events_module, sync_leagues_module):
        monkeypatch.setattr(module, 'database', session)
    monkeypatch.setattr(sync_events_module, 'store_subtitles_sports', lambda row_id: None)
    monkeypatch.setattr(sync_events_module, 'list_missing_subtitles_sports', lambda evno: None)
    monkeypatch.setattr(sync_events_module, 'event_stream', lambda **kwargs: None)
    # An event that a league read leaves out is gone from Sportarr, unless a test moves it.
    monkeypatch.setattr(sync_events_module, 'get_event_from_sportarr_api', lambda **kwargs: None)
    monkeypatch.setattr(sync_events_module, 'get_league_from_sportarr_api', lambda **kwargs: None)
    monkeypatch.setattr(sync_leagues_module, 'event_stream', lambda **kwargs: None)
    monkeypatch.setattr(sync_leagues_module, 'check_sportarr_rootfolder', lambda: None)
    monkeypatch.setattr(sync_leagues_module, 'get_tags', lambda: [])
    monkeypatch.setattr(sync_leagues_module, 'get_language_profiles', lambda: [])
    monkeypatch.setattr(sync_leagues_module, 'jobs_queue', SimpleNamespace(
        add_job_from_function=lambda *args, **kwargs: None, update_job_progress=lambda **kwargs: None,
        update_job_name=lambda **kwargs: None))
    monkeypatch.setattr(sync_leagues_module.settings.general, 'league_default_enabled', False)
    # A full sync here sets module state. The monkeypatch undoes it after the test.
    monkeypatch.setattr(sync_state, 'last_complete_sync_started_at', 0.0)
    monkeypatch.setattr(sync_state, 'last_incomplete_sync_reason', None)
    monkeypatch.setattr(sync_state, 'last_sync_started_at', 0.0)
    monkeypatch.setattr(sync_leagues_module.settings.sportarr, 'sync_only_monitored_leagues', False)
    monkeypatch.setattr(sync_leagues_module.settings.sportarr, 'sync_only_monitored_events', False)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


def add_league(session, league_id, external_id=None, path=None, profile_id=None):
    session.execute(db.insert(db.TableSportsLeagues).values(
        sportarrLeagueId=league_id, title=f'League {league_id}', path=path or f'/sports/{league_id}',
        externalId=external_id, profileId=profile_id, tags='[]', monitored='True',
    ))


def add_event(session, row_id, league_id, sportarr_event_id, part_number=0, external_id=None):
    session.execute(db.insert(db.TableSportsEvents).values(
        id=row_id, sportarrLeagueId=league_id, sportarrEventId=sportarr_event_id, partNumber=part_number,
        externalId=external_id, path=f'/sports/{league_id}/{sportarr_event_id}-{part_number}.mkv',
        title=f'Event {sportarr_event_id}', season=2026, episode=1, monitored='True',
        file_id=sportarr_event_id * 10 + part_number,
    ))
    session.execute(db.insert(db.TableSportsEventsSubtitles).values(
        sportsEventId=row_id, sportarrLeagueId=league_id, language='en', forced=False, hi=False,
        path=f'/sports/{league_id}/{sportarr_event_id}-{part_number}.en.srt',
    ))
    session.execute(db.insert(db.TableHistorySports).values(
        action=1, description='Downloaded', sportsEventId=row_id, sportarrLeagueId=league_id,
    ))
    session.execute(db.insert(db.TableBlacklistSports).values(
        language='en', provider='provider', sports_event_id=row_id, sportarr_league_id=league_id, subs_id='bad',
    ))


def sportarr_league(league_id, path='default', external_id=None):
    return {'id': league_id, 'name': f'League {league_id}', 'monitored': True, 'tags': [],
            'path': f'/sports/{league_id}' if path == 'default' else path, 'externalId': external_id}


def sportarr_event(event_id, league_id, parts=(0,), external_id=None, monitored=True):
    return {
        'id': event_id, 'leagueId': league_id, 'title': f'Event {event_id}', 'monitored': monitored,
        'externalId': external_id, 'hasFile': True,
        'files': [{'id': event_id * 10 + part, 'partNumber': part,
                   'filePath': f'/sports/{league_id}/{event_id}-{part}.mkv', 'size': 500 * 1024 * 1024}
                  for part in parts],
    }


def counts(session):
    return {
        'leagues': sorted(session.execute(db.select(db.TableSportsLeagues.sportarrLeagueId)).scalars().all()),
        'events': sorted(session.execute(db.select(db.TableSportsEvents.id)).scalars().all()),
        'subtitles': session.execute(db.select(db.func.count()).select_from(db.TableSportsEventsSubtitles)).scalar(),
        'history': session.execute(db.select(db.func.count()).select_from(db.TableHistorySports)).scalar(),
        'blacklist': session.execute(db.select(db.func.count()).select_from(db.TableBlacklistSports)).scalar(),
    }


def test_league_without_a_folder_keeps_its_rows(sports_db, monkeypatch, caplog):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 10)
    add_event(sports_db, 2, 1, 11)
    before = counts(sports_db)
    synced = []
    monkeypatch.setattr(sync_leagues_module, 'sync_events', lambda league_id: synced.append(league_id))
    # Create League Folders is off in Sportarr, so both leagues report a null path.
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api',
                        lambda **kwargs: [sportarr_league(1, path=None), sportarr_league(2, path=None)])

    with caplog.at_level(logging.INFO):
        sync_leagues_module.update_leagues(job_id=1)

    assert counts(sports_db) == before
    assert synced == []
    assert 'Skipped 2 leagues that have no league folder in Sportarr' in caplog.text


def test_league_folder_turned_back_on_resumes_the_sync(sports_db, monkeypatch):
    add_league(sports_db, 1)
    synced = []
    monkeypatch.setattr(sync_leagues_module, 'sync_events', lambda league_id: synced.append(league_id))
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api',
                        lambda **kwargs: [sportarr_league(1), sportarr_league(2)])

    sync_leagues_module.update_leagues(job_id=1)

    assert counts(sports_db)['leagues'] == [1, 2]
    assert synced == [1, 2]


def test_single_league_sync_without_a_folder_keeps_the_row(sports_db, monkeypatch):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 10)
    synced = []
    monkeypatch.setattr(sync_leagues_module, 'sync_events', lambda league_id: synced.append(league_id))

    sync_leagues_module.update_one_league(1, action='updated', league_data=[sportarr_league(1, path=None)])

    assert sports_db.execute(db.select(db.TableSportsLeagues.path)).scalar_one() == '/sports/1'
    assert synced == []


def fake_sportarr(monkeypatch, pages):
    """Serve the event pages of a league. A callable page receives the query string."""
    requested = []

    def get(url, **kwargs):
        query = parse_qs(urlparse(url).query)
        requested.append(query)
        page = pages[int(query['page'][0]) - 1]
        body = page(query) if callable(page) else page
        return SimpleNamespace(json=lambda: body, raise_for_status=lambda: None)

    monkeypatch.setattr(sync_utils.requests, 'get', get)
    monkeypatch.setattr(sync_utils, 'url_api_sportarr', lambda: 'http://sportarr/api/')
    return requested


@pytest.mark.parametrize('page', [
    {'page': 1, 'pageSize': 1000, 'totalPages': 1},
    {'page': 1, 'pageSize': 1000, 'totalPages': 1, 'totalRecords': 1, 'records': None},
    {'page': 1, 'pageSize': 1000, 'totalPages': 1, 'totalRecords': 3, 'records': [{'id': 1}]},
    {'page': 1, 'pageSize': 1000, 'totalRecords': 1, 'records': [{'id': 1}]},
], ids=['no-records', 'null-records', 'short-walk', 'no-page-count'])
def test_malformed_event_page_reads_as_incomplete(monkeypatch, page):
    fake_sportarr(monkeypatch, [page])

    assert sync_utils.get_events_from_sportarr_api(apikey_sportarr='key', league_id=1) is None


def test_event_walk_reads_every_event_of_the_league(monkeypatch):
    requested = fake_sportarr(monkeypatch, [
        {'page': 1, 'totalPages': 2, 'totalRecords': 2, 'records': [{'id': 1}]},
        {'page': 2, 'totalPages': 2, 'totalRecords': 2, 'records': [{'id': 2}]},
    ])

    assert sync_utils.get_events_from_sportarr_api(apikey_sportarr='key', league_id=1) == [{'id': 1}, {'id': 2}]
    # showAll bypasses the monitoring filters, so a filtered event is not read as removed.
    assert [query.get('showAll') for query in requested] == [['true'], ['true']]


def test_event_hidden_by_a_monitoring_filter_keeps_its_rows(sports_db, monkeypatch):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 10)
    add_event(sports_db, 2, 1, 11)
    before = counts(sports_db)
    practice, race = sportarr_event(10, 1), sportarr_event(11, 1)

    def league_events(query):
        # Sportarr drops the practice session from the filtered list, as when its monitoring is off.
        records = [practice, race] if query.get('showAll') == ['true'] else [race]
        return {'page': 1, 'pageSize': 1000, 'totalPages': 1, 'totalRecords': len(records), 'records': records}

    fake_sportarr(monkeypatch, [league_events])

    sync_events_module.sync_events(league_id=1)

    assert counts(sports_db) == before


def test_event_without_a_league_is_skipped_and_kept(sports_db, monkeypatch, caplog):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 10)
    before = counts(sports_db)
    orphan = sportarr_event(10, None)
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api', lambda **kwargs: [orphan])

    with caplog.at_level(logging.INFO):
        sync_events_module.sync_events(league_id=1)

    assert counts(sports_db) == before
    assert 'has no league' in caplog.text


def test_event_sync_does_nothing_for_a_league_bazarr_does_not_hold(sports_db, monkeypatch):
    called = []
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: called.append(kwargs) or [sportarr_event(10, 5)])

    sync_events_module.sync_events(league_id=5)

    assert called == []
    assert counts(sports_db)['events'] == []


def seed_readded_league(session):
    # Bazarr holds league 1. Sportarr removed it and added it again as league 7.
    add_league(session, 1, external_id='lg-4387', profile_id=None)
    session.execute(db.insert(db.TableLanguagesProfiles).values(
        profileId=3, name='English', cutoff=None, items='[]', mustContain='[]', mustNotContain='[]',
        originalFormat=False, tag=None))
    session.execute(db.update(db.TableSportsLeagues).values(profileId=3))
    add_event(session, 1, 1, 10, external_id='ev-100')
    add_event(session, 2, 1, 11, part_number=1, external_id='ev-101')
    add_event(session, 3, 1, 11, part_number=2, external_id='ev-101')


def readded_events(league_id):
    return [sportarr_event(70, league_id, external_id='ev-100'),
            sportarr_event(71, league_id, parts=(1, 2), external_id='ev-101')]


def test_readded_league_keeps_its_subtitle_history(sports_db, monkeypatch):
    seed_readded_league(sports_db)
    before = counts(sports_db)
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api',
                        lambda **kwargs: [sportarr_league(7, path='/sports/1', external_id='lg-4387')])
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: readded_events(kwargs['league_id']))

    sync_leagues_module.update_leagues(job_id=1)

    after = counts(sports_db)
    assert after['leagues'] == [7]
    assert after['events'] == before['events']
    assert (after['subtitles'], after['history'], after['blacklist']) == \
        (before['subtitles'], before['history'], before['blacklist'])
    assert sports_db.execute(db.select(db.TableSportsLeagues.profileId)).scalar_one() == 3
    assert sports_db.execute(
        db.select(db.TableSportsEvents.id, db.TableSportsEvents.sportarrEventId, db.TableSportsEvents.partNumber,
                  db.TableSportsEvents.sportarrLeagueId).order_by(db.TableSportsEvents.id)).all() == [
        (1, 70, 0, 7), (2, 71, 1, 7), (3, 71, 2, 7)]
    assert set(sports_db.execute(db.select(db.TableHistorySports.sportarrLeagueId)).scalars().all()) == {7}
    assert set(sports_db.execute(db.select(db.TableBlacklistSports.sportarr_league_id)).scalars().all()) == {7}


def test_league_still_in_sportarr_is_not_moved(sports_db, monkeypatch):
    seed_readded_league(sports_db)
    # Both ids are in Sportarr, so league 1 is not proven gone.
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api', lambda **kwargs: [
        sportarr_league(1, external_id='lg-4387'), sportarr_league(7, path='/sports/7', external_id='lg-4387')])
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api', lambda **kwargs: [])

    sync_leagues_module.update_leagues(job_id=1)

    assert counts(sports_db)['leagues'] == [1, 7]


def test_single_readded_league_asks_for_a_full_sync(sports_db, monkeypatch):
    seed_readded_league(sports_db)
    full_syncs = []
    monkeypatch.setattr(sync_leagues_module, 'queue_full_sync', lambda: full_syncs.append(True))

    sync_leagues_module.update_one_league(7, action='updated',
                                          league_data=[sportarr_league(7, path='/sports/1', external_id='lg-4387')])

    assert full_syncs == [True]
    assert counts(sports_db)['leagues'] == [1]


def test_stream_event_with_a_known_external_id_waits_for_the_league_sync(sports_db, monkeypatch):
    seed_readded_league(sports_db)

    result = sync_events_module.sync_one_event(sportarr_event(70, 1, external_id='ev-100'))

    assert result == sync_events_module.EVENT_NEEDS_LEAGUE_SYNC
    assert counts(sports_db)['events'] == [1, 2, 3]


def test_readded_league_waits_for_a_complete_list(sports_db, monkeypatch):
    seed_readded_league(sports_db)
    before = counts(sports_db)
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: readded_events(kwargs['league_id']))
    # One unidentified league makes the list incomplete, so league 1 is not proven gone.
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api', lambda **kwargs: [
        sportarr_league(7, path='/sports/7', external_id='lg-4387'), {'name': 'No id'}])

    sync_leagues_module.update_leagues(job_id=1)

    assert counts(sports_db) == before

    # The next complete list moves the league with its history.
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api',
                        lambda **kwargs: [sportarr_league(7, path='/sports/7', external_id='lg-4387')])

    sync_leagues_module.update_leagues(job_id=1)

    after = counts(sports_db)
    assert after['leagues'] == [7]
    assert after['history'] == before['history']


def test_queued_league_sync_returns_the_job_id(monkeypatch):
    monkeypatch.setattr(sync_leagues_module, 'jobs_queue', SimpleNamespace(
        add_job_from_function=lambda *args, **kwargs: False))

    # False means a matching job is queued or running, so the caller knows the request was dropped.
    assert sync_leagues_module.update_leagues() is False


@pytest.mark.parametrize('events_read, recorded', [(True, True), (False, False)], ids=['complete', 'failed-read'])
def test_full_sync_records_its_start_only_when_it_read_everything(sports_db, monkeypatch, events_read, recorded):
    add_league(sports_db, 1)
    monkeypatch.setattr(sync_state, 'last_complete_sync_started_at', 0.0)
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api', lambda **kwargs: [sportarr_league(1)])
    monkeypatch.setattr(sync_leagues_module, 'sync_events', lambda league_id: events_read)

    sync_leagues_module.update_leagues(job_id=1)

    assert (sync_state.last_complete_sync_started_at > 0) is recorded


@pytest.fixture
def media_on_disk(tmp_path, monkeypatch):
    """Map Sportarr paths under tmp_path, and create the media files of the given rows."""
    monkeypatch.setattr(sync_events_module.path_mappings, 'path_replace_sports', lambda path: str(tmp_path) + path)

    def create(session):
        for path in session.execute(db.select(db.TableSportsEvents.path)).scalars().all():
            media = tmp_path / path.lstrip('/')
            media.parent.mkdir(parents=True, exist_ok=True)
            media.write_bytes(b'video')
        return tmp_path

    return create


def fileless(events):
    for sportarr_event_data in events:
        sportarr_event_data['files'] = []
    return events


def test_league_readded_while_bazarr_runs_keeps_its_events_until_the_files_return(sports_db, monkeypatch,
                                                                                  media_on_disk):
    seed_readded_league(sports_db)
    root = media_on_disk(sports_db)
    before = counts(sports_db)
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api',
                        lambda **kwargs: [sportarr_league(7, path='/sports/1', external_id='lg-4387')])
    # Sportarr re-adds the events before it imports the kept files again.
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: fileless(readded_events(kwargs['league_id'])))

    sync_leagues_module.update_leagues(job_id=1)

    assert counts(sports_db) == {**before, 'leagues': [7]}
    assert sports_db.execute(
        db.select(db.TableSportsEvents.id, db.TableSportsEvents.sportarrEventId, db.TableSportsEvents.partNumber)
        .order_by(db.TableSportsEvents.id)).all() == [(1, 70, 0), (2, 71, 1), (3, 71, 2)]

    # The files come back. Each row picks up its new file and keeps its history.
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: readded_events(kwargs['league_id']))
    sync_events_module.sync_events(league_id=7)

    assert counts(sports_db) == {**before, 'leagues': [7]}
    assert sports_db.execute(db.select(db.TableSportsEvents.file_id).order_by(db.TableSportsEvents.id)) \
        .scalars().all() == [700, 711, 712]

    # Sportarr deletes a file from disk before it reports it, so a part whose file is gone loses its row.
    (root / 'sports' / '7' / '70-0.mkv').unlink(missing_ok=True)
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: [fileless([sportarr_event(70, 7, external_id='ev-100')])[0],
                                          sportarr_event(71, 7, parts=(1, 2), external_id='ev-101')])
    sync_events_module.sync_events(league_id=7)

    assert counts(sports_db)['events'] == [2, 3]


def test_fileless_part_whose_file_left_the_disk_is_deleted(sports_db, monkeypatch, media_on_disk):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 10)
    add_event(sports_db, 2, 1, 11)
    media_on_disk(sports_db)
    monkeypatch.setattr(sync_events_module.path_mappings, 'path_replace_sports', lambda path: '/nowhere' + path)
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: fileless([sportarr_event(10, 1)]) + [sportarr_event(11, 1)])

    sync_events_module.sync_events(league_id=1)

    assert counts(sports_db)['events'] == [2]


def test_row_of_an_event_gone_from_sportarr_is_deleted_with_its_file_on_disk(sports_db, monkeypatch, media_on_disk):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 10, external_id='ev-100')
    add_event(sports_db, 2, 1, 11)
    media_on_disk(sports_db)
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: [sportarr_event(11, 1)])

    sync_events_module.sync_events(league_id=1)

    assert counts(sports_db)['events'] == [2]


def part_rows(session):
    return session.execute(
        db.select(db.TableSportsEvents.sportarrEventId, db.TableSportsEvents.partNumber)
        .order_by(db.TableSportsEvents.sportarrEventId, db.TableSportsEvents.partNumber)).all()


def test_renumbered_part_leaves_one_row(sports_db, monkeypatch, media_on_disk):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 10, part_number=1)
    media_on_disk(sports_db)
    # The user cleared the part name. Sportarr keeps the file id and the path, and changes the part number.
    renumbered = sportarr_event(10, 1, parts=(0,))
    renumbered['files'][0].update(id=101, filePath='/sports/1/10-1.mkv')
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api', lambda **kwargs: [renumbered])

    sync_events_module.sync_events(league_id=1)

    assert part_rows(sports_db) == [(10, 0)]


def test_whole_file_replacing_parts_leaves_only_the_listed_row(sports_db, monkeypatch, media_on_disk):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 11, part_number=1)
    add_event(sports_db, 2, 1, 11, part_number=2)
    # The old part files stay on disk because Sportarr could not delete them.
    media_on_disk(sports_db)
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: [sportarr_event(11, 1, parts=(0,))])

    sync_events_module.sync_events(league_id=1)

    assert part_rows(sports_db) == [(11, 0)]


def test_fileless_event_loses_a_row_whose_file_another_event_lists(sports_db, monkeypatch, media_on_disk):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 10)
    media_on_disk(sports_db)
    other = sportarr_event(12, 1)
    other['files'][0]['filePath'] = '/sports/1/10-0.mkv'
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: fileless([sportarr_event(10, 1)]) + [other])

    sync_events_module.sync_events(league_id=1)

    assert part_rows(sports_db) == [(12, 0)]


def test_unmonitored_fileless_event_keeps_its_rows_like_a_monitored_one(sports_db, monkeypatch, media_on_disk):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 10)
    sports_db.execute(db.update(db.TableSportsEvents).values(monitored='False'))
    media_on_disk(sports_db)
    monkeypatch.setattr(sync_events_module.settings.sportarr, 'sync_only_monitored_leagues', True)
    monkeypatch.setattr(sync_events_module.settings.sportarr, 'sync_only_monitored_events', True)
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: fileless([sportarr_event(10, 1, monitored=False)]))

    sync_events_module.sync_events(league_id=1)

    assert part_rows(sports_db) == [(10, 0)]


def test_waiting_move_does_not_follow_an_event_of_another_league(sports_db, monkeypatch, media_on_disk):
    add_league(sports_db, 1)
    add_league(sports_db, 2)
    add_event(sports_db, 1, 1, 10, external_id='ev-100')
    media_on_disk(sports_db)
    # Sportarr lists an event of league 2 under league 1, with the same external id.
    stray = fileless([sportarr_event(70, 2, external_id='ev-100')])
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api', lambda **kwargs: stray)

    sync_events_module.sync_events(league_id=1)

    assert part_rows(sports_db) == []


def test_stream_leaves_a_fileless_event_with_files_on_disk_to_the_league_sync(sports_db, media_on_disk):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 10)
    media_on_disk(sports_db)

    result = sync_events_module.sync_one_event(fileless([sportarr_event(10, 1)])[0])

    assert result == sync_events_module.EVENT_NEEDS_LEAGUE_SYNC
    assert part_rows(sports_db) == [(10, 0)]


def test_incomplete_full_sync_names_the_league_it_could_not_read(sports_db, monkeypatch):
    add_league(sports_db, 1)
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api', lambda **kwargs: [sportarr_league(1)])
    monkeypatch.setattr(sync_leagues_module, 'sync_events', lambda league_id: False)

    sync_leagues_module.update_leagues(job_id=1)

    assert sync_state.last_incomplete_sync_reason == 'Sportarr did not return the events of League 1.'


def row_parts(session):
    return session.execute(
        db.select(db.TableSportsEvents.id, db.TableSportsEvents.partNumber, db.TableSportsEvents.file_id)
        .order_by(db.TableSportsEvents.id)).all()


@pytest.mark.parametrize('sync', ['league', 'stream'])
def test_renumbered_part_keeps_its_row_and_history(sports_db, monkeypatch, sync):
    add_league(sports_db, 1)
    add_event(sports_db, 8, 1, 10, part_number=1)
    before = counts(sports_db)
    # The user cleared the part name. Sportarr keeps the file id and the path, and changes the part number.
    renumbered = sportarr_event(10, 1, parts=(0,))
    renumbered['files'][0].update(id=101, filePath='/sports/1/10-1.mkv')
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api', lambda **kwargs: [renumbered])

    if sync == 'league':
        sync_events_module.sync_events(league_id=1)
    else:
        sync_events_module.sync_one_event(renumbered)

    assert row_parts(sports_db) == [(8, 0, 101)]
    assert counts(sports_db) == before


def test_parts_that_swap_numbers_both_keep_their_rows(sports_db, monkeypatch):
    add_league(sports_db, 1)
    add_event(sports_db, 8, 1, 11, part_number=1)
    add_event(sports_db, 9, 1, 11, part_number=2)
    before = counts(sports_db)
    swapped = sportarr_event(11, 1, parts=(1, 2))
    # The file of part 1 is part 2 now, and the other way round.
    swapped['files'][0].update(id=112, filePath='/sports/1/11-2.mkv')
    swapped['files'][1].update(id=111, filePath='/sports/1/11-1.mkv')
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api', lambda **kwargs: [swapped])

    sync_events_module.sync_events(league_id=1)

    assert row_parts(sports_db) == [(8, 2, 111), (9, 1, 112)]
    assert counts(sports_db) == before


def test_league_added_again_without_a_folder_keeps_the_held_league(sports_db, monkeypatch):
    seed_readded_league(sports_db)
    before = counts(sports_db)
    # Create League Folders is off, so the re-added league has no path.
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api',
                        lambda **kwargs: [sportarr_league(7, path=None, external_id='lg-4387')])
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api', lambda **kwargs: [])

    sync_leagues_module.update_leagues(job_id=1)

    assert counts(sports_db) == before


def test_stream_leaves_the_events_of_an_unmonitored_league_alone(sports_db, monkeypatch):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 10)
    sports_db.execute(db.update(db.TableSportsLeagues).values(monitored='False'))
    before = counts(sports_db)
    monkeypatch.setattr(sync_events_module.settings.sportarr, 'sync_only_monitored_leagues', True)

    # Only a league read tells whether Sportarr monitors the league now.
    result = sync_events_module.sync_one_event(sportarr_event(10, 1, parts=()))

    assert result == sync_events_module.EVENT_NEEDS_LEAGUE_SYNC
    assert counts(sports_db) == before


def test_renumbered_part_replaces_a_part_whose_file_is_gone(sports_db, monkeypatch):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 11, part_number=1)
    add_event(sports_db, 2, 1, 11, part_number=2)
    # Sportarr lists only the file of part 1, now as part 2. The file of part 2 is gone.
    renumbered = sportarr_event(11, 1, parts=(2,))
    renumbered['files'][0].update(id=111, filePath='/sports/1/11-1.mkv')
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api', lambda **kwargs: [renumbered])

    sync_events_module.sync_events(league_id=1)

    assert row_parts(sports_db) == [(1, 2, 111)]


def test_new_file_at_the_old_number_of_a_renumbered_part_gets_its_own_row(sports_db, monkeypatch):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 11, part_number=1)
    add_event(sports_db, 2, 1, 11, part_number=2)
    renumbered = sportarr_event(11, 1, parts=(1, 2))
    # A new file takes part 1, and the file of part 1 moves to part 2.
    renumbered['files'][0].update(id=999, filePath='/sports/1/11-new.mkv')
    renumbered['files'][1].update(id=111, filePath='/sports/1/11-1.mkv')
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api', lambda **kwargs: [renumbered])

    sync_events_module.sync_events(league_id=1)

    rows = row_parts(sports_db)
    # The history of the moved file stays on its row.
    assert rows[0] == (1, 2, 111)
    assert [(part, file_id) for _, part, file_id in rows[1:]] == [(1, 999)]
    assert sports_db.execute(db.select(db.TableHistorySports.sportsEventId)).scalars().all() == [1]


def test_single_league_sync_queues_the_same_full_sync_as_the_scheduler(sports_db, monkeypatch):
    seed_readded_league(sports_db)
    queued = []
    monkeypatch.setattr(sync_leagues_module, 'queue_full_sync', lambda: queued.append(True), raising=False)
    monkeypatch.setattr(sync_leagues_module, 'update_leagues', lambda **kwargs: pytest.fail(
        'the full sync must be queued with the arguments the scheduler uses'))

    sync_leagues_module.update_one_league(7, action='updated',
                                          league_data=[sportarr_league(7, path='/sports/1', external_id='lg-4387')])

    assert queued == [True]


def test_renumbered_part_of_an_unmonitored_event_keeps_its_row(sports_db, monkeypatch):
    add_league(sports_db, 1)
    add_event(sports_db, 8, 1, 10, part_number=1)
    sports_db.execute(db.update(db.TableSportsEvents).values(monitored='False'))
    before = counts(sports_db)
    monkeypatch.setattr(sync_events_module.settings.sportarr, 'sync_only_monitored_leagues', True)
    monkeypatch.setattr(sync_events_module.settings.sportarr, 'sync_only_monitored_events', True)
    renumbered = sportarr_event(10, 1, parts=(0,), monitored=False)
    renumbered['files'][0].update(id=101, filePath='/sports/1/10-1.mkv')
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api', lambda **kwargs: [renumbered])

    sync_events_module.sync_events(league_id=1)

    assert row_parts(sports_db) == [(8, 0, 101)]
    assert counts(sports_db) == before


def test_renumber_waits_while_an_incomplete_read_keeps_the_row_at_its_new_number(sports_db, monkeypatch, caplog):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 11, part_number=1)
    add_event(sports_db, 2, 1, 11, part_number=2)
    renumbered = sportarr_event(11, 1, parts=(2,))
    renumbered['files'][0].update(id=111, filePath='/sports/1/11-1.mkv')
    # An unidentified event makes the read incomplete, so nothing is deleted.
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: [renumbered, {'id': None}])

    sync_events_module.sync_events(league_id=1)

    assert 'cannot change the part numbers' not in caplog.text
    assert row_parts(sports_db) == [(1, 1, 111), (2, 2, 112)]


def league_ids_of_children(session):
    return {
        'subtitles': set(session.execute(db.select(db.TableSportsEventsSubtitles.sportarrLeagueId)).scalars()),
        'history': set(session.execute(db.select(db.TableHistorySports.sportarrLeagueId)).scalars()),
        'blacklist': set(session.execute(db.select(db.TableBlacklistSports.sportarr_league_id)).scalars()),
    }


def moved_event_setup(session, monkeypatch):
    """Event 10 sits in league 1 in Bazarr. Sportarr moved it to league 2, and its file stayed where it was."""
    add_league(session, 1)
    add_league(session, 2)
    add_event(session, 1, 1, 10)
    moved = sportarr_event(10, 2)
    moved['files'][0]['filePath'] = '/sports/1/10-0.mkv'
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: {1: [], 2: [moved]}[kwargs['league_id']])
    monkeypatch.setattr(sync_events_module, 'get_event_from_sportarr_api',
                        lambda **kwargs: moved if kwargs['event_id'] == 10 else None)
    return moved


@pytest.mark.parametrize('league_order', [(1, 2), (2, 1)], ids=['old league first', 'new league first'])
def test_full_sync_keeps_the_history_of_an_event_that_moved_league(sports_db, monkeypatch, league_order):
    moved_event_setup(sports_db, monkeypatch)
    before = counts(sports_db)
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api',
                        lambda **kwargs: [sportarr_league(league_id) for league_id in league_order])

    sync_leagues_module.update_leagues(job_id=1)

    assert counts(sports_db) == before
    assert sports_db.execute(
        db.select(db.TableSportsEvents.id, db.TableSportsEvents.sportarrLeagueId)).all() == [(1, 2)]
    assert league_ids_of_children(sports_db) == {'subtitles': {2}, 'history': {2}, 'blacklist': {2}}


def test_sync_of_the_old_league_alone_keeps_an_event_that_moved(sports_db, monkeypatch):
    moved_event_setup(sports_db, monkeypatch)
    before = counts(sports_db)

    sync_events_module.sync_events(league_id=1)

    # The sync of league 2 takes the rows over later.
    assert counts(sports_db) == before


@pytest.mark.parametrize('sportarr_league', [None, {'id': 3, 'path': None}],
                         ids=['league gone from Sportarr', 'league without a folder'])
def test_event_that_moved_to_a_league_bazarr_cannot_hold_is_deleted(sports_db, monkeypatch, sportarr_league):
    moved = moved_event_setup(sports_db, monkeypatch)
    moved['leagueId'] = 3
    monkeypatch.setattr(sync_events_module, 'get_league_from_sportarr_api', lambda **kwargs: sportarr_league)

    sync_events_module.sync_events(league_id=1)

    assert counts(sports_db)['events'] == []


def test_full_sync_keeps_the_history_of_an_event_that_moved_to_a_new_league(sports_db, monkeypatch):
    # League 2 is new in Sportarr, and the full sync reads league 1 before it adds league 2.
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 10)
    before = counts(sports_db)
    moved = sportarr_event(10, 2)
    moved['files'][0]['filePath'] = '/sports/1/10-0.mkv'
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api',
                        lambda **kwargs: [sportarr_league(1), sportarr_league(2)])
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: {1: [], 2: [moved]}[kwargs['league_id']])
    monkeypatch.setattr(sync_events_module, 'get_event_from_sportarr_api', lambda **kwargs: moved)
    monkeypatch.setattr(sync_events_module, 'get_league_from_sportarr_api', lambda **kwargs: sportarr_league(2))

    sync_leagues_module.update_leagues(job_id=1)

    after = counts(sports_db)
    assert after['leagues'] == [1, 2]
    assert (after['events'], after['subtitles'], after['history'], after['blacklist']) == \
        (before['events'], before['subtitles'], before['history'], before['blacklist'])
    assert league_ids_of_children(sports_db) == {'subtitles': {2}, 'history': {2}, 'blacklist': {2}}


def subtitle_rows(session):
    return sorted(session.execute(
        db.select(db.TableSportsEventsSubtitles.sportarrLeagueId, db.TableSportsEventsSubtitles.language,
                  db.TableSportsEventsSubtitles.path)).all())


def test_move_drops_an_index_row_that_the_new_league_already_holds(sports_db, monkeypatch):
    moved = moved_event_setup(sports_db, monkeypatch)
    # The indexer already stored the same file under league 2. The French file is not a copy, so it moves.
    sports_db.execute(db.insert(db.TableSportsEventsSubtitles), [
        {'sportsEventId': 1, 'sportarrLeagueId': 2, 'language': 'en', 'forced': False, 'hi': False,
         'path': '/sports/1/10-0.en.srt'},
        {'sportsEventId': 1, 'sportarrLeagueId': 1, 'language': 'fr', 'forced': False, 'hi': False,
         'path': '/sports/1/10-0.fr.srt'},
    ])
    history = counts(sports_db)['history']

    sync_events_module.sync_one_event(moved)

    assert sports_db.execute(db.select(db.TableSportsEvents.sportarrLeagueId)).scalar_one() == 2
    assert subtitle_rows(sports_db) == [(2, 'en', '/sports/1/10-0.en.srt'), (2, 'fr', '/sports/1/10-0.fr.srt')]
    assert counts(sports_db)['history'] == history


def test_move_keeps_one_copy_when_two_old_leagues_hold_the_file(sports_db, monkeypatch):
    moved = moved_event_setup(sports_db, monkeypatch)
    add_league(sports_db, 3)
    # An earlier build moved the event row to league 2 alone, and the indexer then stored the file again there.
    sports_db.execute(db.update(db.TableSportsEvents).values(sportarrLeagueId=2))
    sports_db.execute(db.insert(db.TableSportsEventsSubtitles).values(
        sportsEventId=1, sportarrLeagueId=2, language='en', forced=False, hi=False, path='/sports/1/10-0.en.srt'))
    moved['leagueId'] = 3

    sync_events_module.sync_one_event(moved)

    assert sports_db.execute(db.select(db.TableSportsEvents.sportarrLeagueId)).scalar_one() == 3
    assert subtitle_rows(sports_db) == [(3, 'en', '/sports/1/10-0.en.srt')]


def test_failed_move_leaves_the_event_and_its_rows_in_the_old_league(sports_db, monkeypatch, caplog):
    from sqlalchemy.exc import IntegrityError

    moved = moved_event_setup(sports_db, monkeypatch)

    def fail(connection, row_id, league_id):
        raise IntegrityError('UPDATE table_sports_events_subtitles', {}, Exception('unique'))

    monkeypatch.setattr(sync_events_module, '_move_child_rows', fail)

    sync_events_module.sync_one_event(moved)

    assert 'cannot update events' in caplog.text
    assert sports_db.execute(db.select(db.TableSportsEvents.sportarrLeagueId)).scalar_one() == 1
    assert league_ids_of_children(sports_db) == {'subtitles': {1}, 'history': {1}, 'blacklist': {1}}


def test_rows_stay_when_sportarr_cannot_say_whether_the_new_league_has_a_folder(sports_db, monkeypatch):
    moved = moved_event_setup(sports_db, monkeypatch)
    moved['leagueId'] = 3
    before = counts(sports_db)

    def unreachable(**kwargs):
        raise RequestsConnectionError('Sportarr is down')

    monkeypatch.setattr(sync_events_module, 'get_league_from_sportarr_api', unreachable)

    sync_events_module.sync_events(league_id=1)

    assert counts(sports_db) == before


def test_full_sync_moves_child_rows_left_in_the_old_league_before_it_deletes_that_league(sports_db, monkeypatch):
    moved_event_setup(sports_db, monkeypatch)
    # An earlier build moved the event row to league 2 and left its child rows in league 1.
    sports_db.execute(db.update(db.TableSportsEvents).values(sportarrLeagueId=2))
    # The indexer then stored the English file again under league 2.
    sports_db.execute(db.insert(db.TableSportsEventsSubtitles).values(
        sportsEventId=1, sportarrLeagueId=2, language='en', forced=False, hi=False, path='/sports/1/10-0.en.srt'))
    recalculated = []
    monkeypatch.setattr(sync_events_module, 'list_missing_subtitles_sports', lambda evno: recalculated.append(evno))
    before = counts(sports_db)
    # League 1 left Sportarr, and the read of league 2 fails.
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api', lambda **kwargs: [sportarr_league(2)])
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api', lambda **kwargs: None)

    sync_leagues_module.update_leagues(job_id=1)

    after = counts(sports_db)
    assert after['leagues'] == [2]
    assert (after['history'], after['blacklist']) == (before['history'], before['blacklist'])
    assert subtitle_rows(sports_db) == [(2, 'en', '/sports/1/10-0.en.srt')]
    assert league_ids_of_children(sports_db) == {'subtitles': {2}, 'history': {2}, 'blacklist': {2}}
    assert recalculated == [1]


def test_lost_part_of_an_event_still_listed_is_deleted_without_asking_sportarr(sports_db, monkeypatch):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 10, part_number=1)
    add_event(sports_db, 2, 1, 10, part_number=2)
    reads = []
    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api',
                        lambda **kwargs: [sportarr_event(10, 1, parts=(2,))])
    monkeypatch.setattr(sync_events_module, 'get_event_from_sportarr_api',
                        lambda **kwargs: reads.append(kwargs['event_id']))

    sync_events_module.sync_events(league_id=1)

    assert counts(sports_db)['events'] == [2]
    assert reads == []


def test_league_move_works_out_the_missing_subtitles_again(sports_db, monkeypatch):
    moved = moved_event_setup(sports_db, monkeypatch)
    indexed = []
    monkeypatch.setattr(sync_events_module, 'store_subtitles_sports', lambda row_id: indexed.append(row_id))

    sync_events_module.sync_one_event(moved)

    # The new league can have another profile, and the file did not change.
    assert indexed == [1]


def test_event_stays_when_sportarr_cannot_say_where_it_went(sports_db, monkeypatch):
    moved_event_setup(sports_db, monkeypatch)
    before = counts(sports_db)

    def unreachable(**kwargs):
        raise RequestsConnectionError('Sportarr is down')

    monkeypatch.setattr(sync_events_module, 'get_event_from_sportarr_api', unreachable)

    sync_events_module.sync_events(league_id=1)

    assert counts(sports_db) == before


def test_stream_move_takes_the_subtitles_and_history_to_the_new_league(sports_db, monkeypatch):
    moved = moved_event_setup(sports_db, monkeypatch)
    before = counts(sports_db)

    sync_events_module.sync_one_event(moved)

    assert counts(sports_db) == before
    assert league_ids_of_children(sports_db) == {'subtitles': {2}, 'history': {2}, 'blacklist': {2}}
    # The old league can now leave Bazarr without taking the event's history with it.
    sports_db.execute(db.delete(db.TableSportsLeagues).where(db.TableSportsLeagues.sportarrLeagueId == 1))
    assert counts(sports_db)['history'] == before['history']


def test_first_failed_sportarr_read_keeps_every_remaining_event_without_more_reads(sports_db, monkeypatch):
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 10)
    add_event(sports_db, 2, 1, 11)
    before = counts(sports_db)
    reads = []

    def unreachable(**kwargs):
        reads.append(kwargs['event_id'])
        raise RequestsConnectionError('Sportarr is down')

    monkeypatch.setattr(sync_events_module, 'get_events_from_sportarr_api', lambda **kwargs: [])
    monkeypatch.setattr(sync_events_module, 'get_event_from_sportarr_api', unreachable)

    sync_events_module.sync_events(league_id=1)

    # Each read could wait the whole timeout, so the sync stops asking after one failure.
    assert reads == [10]
    assert counts(sports_db) == before


def test_rows_stay_when_sportarr_does_not_say_which_league_the_event_is_in(sports_db, monkeypatch):
    moved = moved_event_setup(sports_db, monkeypatch)
    del moved['leagueId']
    before = counts(sports_db)

    sync_events_module.sync_events(league_id=1)

    assert counts(sports_db) == before


def test_full_sync_on_a_clean_database_works_out_nothing_again(sports_db, monkeypatch):
    moved_event_setup(sports_db, monkeypatch)
    recalculated = []
    monkeypatch.setattr(sync_events_module, 'list_missing_subtitles_sports', lambda evno: recalculated.append(evno))
    monkeypatch.setattr(sync_leagues_module, 'get_leagues_from_sportarr_api',
                        lambda **kwargs: [sportarr_league(1), sportarr_league(2)])

    sync_leagues_module.update_leagues(job_id=1)

    assert recalculated == []


def test_repair_moves_child_rows_to_the_league_the_event_is_in_when_it_runs(sports_db, monkeypatch):
    moved_event_setup(sports_db, monkeypatch)
    add_league(sports_db, 3)
    sports_db.execute(db.update(db.TableSportsEvents).values(sportarrLeagueId=2))
    read_stranded = sync_events_module._stranded_child_rows

    def stranded_then_moved():
        rows = read_stranded()
        # The stream moves the event to league 3 after the repair read where it was.
        sports_db.execute(db.update(db.TableSportsEvents).values(sportarrLeagueId=3))
        return rows

    monkeypatch.setattr(sync_events_module, '_stranded_child_rows', stranded_then_moved)

    sync_events_module.repair_stranded_child_rows()

    assert league_ids_of_children(sports_db) == {'subtitles': {3}, 'history': {3}, 'blacklist': {3}}

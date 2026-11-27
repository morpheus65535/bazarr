"""
The Sportarr event stream client syncs only the event a frame names, and keeps its cursor across restarts.
Every change the stream skips leaves a saved full sync debt.
"""
import json
import logging
import time
from threading import Event

import pytest
from requests.exceptions import ConnectionError as RequestsConnectionError

from app import database as db
from sportarr import sse_client
from sportarr.sync import leagues as sync_leagues
from sportarr.sync import events as sync_events_module
from tests.bazarr.test_sportarr_sync_safety import (  # noqa: F401
    add_event, add_league, counts, sports_db, sportarr_event, sportarr_league)


class FakeResponse:
    def __init__(self, lines):
        self.lines = lines

    def raise_for_status(self):
        pass

    def iter_lines(self, decode_unicode=True):
        yield from self.lines

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeSession:
    """Answer each stream request with the next script entry: a list of lines or an exception."""
    scripts = []
    urls = []
    on_empty = None

    def __init__(self):
        self.verify = True
        self.headers = {}

    def get(self, url, **kwargs):
        FakeSession.urls.append(url)
        if not FakeSession.scripts and FakeSession.on_empty:
            FakeSession.on_empty()
        script = FakeSession.scripts.pop(0)
        if isinstance(script, Exception):
            raise script
        return FakeResponse(script)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def frame(frame_id, payload, name=None):
    lines = [f'id: {frame_id}'] if frame_id is not None else []
    if name:
        lines.append(f'event: {name}')
    return lines + [f'data: {json.dumps(payload)}', '']


def file_frame(frame_id, event_id, action='imported', **extra):
    return frame(frame_id, {'resourceType': 'file', 'action': action, 'eventId': event_id, **extra})


def saved(cursor_file):
    return json.loads(cursor_file.read_text())


@pytest.fixture
def stream(tmp_path, monkeypatch):
    """A client with its cursor file in tmp_path and no real Sportarr behind it."""
    calls = []
    cursor_file = tmp_path / 'sportarr_stream.json'
    monkeypatch.setattr(sse_client, 'cursor_file_path', lambda: str(cursor_file))
    monkeypatch.setattr(sse_client, 'url_sportarr', lambda: 'http://sportarr:1867')
    monkeypatch.setattr(sse_client.settings.general, 'use_sportarr', True)
    monkeypatch.setattr(sse_client.settings.sportarr, 'apikey', 'key-1')
    monkeypatch.setattr(sse_client.args, 'no_signalr', False)
    monkeypatch.setattr(sse_client, 'Session', FakeSession)
    # A full sync in an earlier test must not cover a debt in this one.
    monkeypatch.setattr(sse_client.sync_state, 'last_complete_sync_started_at', 0.0)
    monkeypatch.setattr(sse_client.sync_state, 'last_sync_started_at', 0.0)
    monkeypatch.setattr(sse_client.sync_state, 'last_incomplete_sync_reason', None)
    monkeypatch.setattr(sse_client, 'event_stream', lambda **kwargs: calls.append(('badge', kwargs['type'])))
    monkeypatch.setattr(sse_client, 'queue_full_sync', lambda: calls.append(('full sync',)))
    monkeypatch.setattr(sse_client, 'full_sync_queued_or_running', lambda: False)
    monkeypatch.setattr(sse_client, 'sync_events', lambda league_id: calls.append(('league sync', league_id)))
    monkeypatch.setattr(sse_client, 'update_one_league',
                        lambda league_id, action, **kwargs: calls.append(('league insert', league_id)))
    monkeypatch.setattr(sse_client, 'league_in_bazarr', lambda league_id: True)
    monkeypatch.setattr(sse_client, 'league_left_unmonitored', lambda league_id: False)
    monkeypatch.setattr(sse_client, 'get_league_from_sportarr_api',
                        lambda **kwargs: calls.append(('read league', kwargs['league_id'])) or
                        {'id': kwargs['league_id'], 'path': f"/sports/{kwargs['league_id']}"})
    monkeypatch.setattr(sse_client, 'get_event_from_sportarr_api',
                        lambda **kwargs: calls.append(('read event', kwargs['event_id'])) or
                        sportarr_event(kwargs['event_id'], 1))
    monkeypatch.setattr(sse_client, 'sync_one_event', lambda event: calls.append(('event sync', event['id'])))
    monkeypatch.setattr(sse_client, 'delete_event_rows', lambda event_id: calls.append(('delete event', event_id)))
    FakeSession.scripts = []
    FakeSession.urls = []
    FakeSession.on_empty = None
    client = sse_client.SportarrSSEClient()
    return client, calls, cursor_file


def begin(client, cursor=None):
    """Make a current run, as start() does, without its reconnect loop."""
    run = sse_client._Run()
    client.load_cursor(run)
    if cursor is not None:
        run.last_event_id = cursor
        run.current_at = time.time()
    client._run = run
    return run


def calls_of(calls, *kinds):
    return [call for call in calls if call[0] in kinds]


class InstantEvent(Event):
    """Record each reconnect delay instead of waiting it out."""
    waits = []

    def wait(self, timeout=None):
        InstantEvent.waits.append(timeout)
        return self.is_set()


def run_cycles(client, monkeypatch, scripts):
    """Run start() through the given connections, then stop."""
    InstantEvent.waits = []
    monkeypatch.setattr(sse_client, 'Event', InstantEvent)
    FakeSession.scripts = list(scripts)

    def stop():
        client._run.stop.set()
        FakeSession.scripts.append(RequestsConnectionError('script ended'))

    FakeSession.on_empty = stop
    client.start()


def test_frame_syncs_only_the_event_it_names(stream):
    client, calls, _ = stream
    run = begin(client, cursor=40)
    FakeSession.scripts = [file_frame(41, 17)]

    client.connect(run)

    assert calls_of(calls, 'read event', 'read league', 'event sync', 'league sync') == [
        ('read event', 17), ('event sync', 17)]
    assert run.last_event_id == 41


def test_cursor_survives_a_restart(stream):
    client, calls, cursor_file = stream
    run = begin(client)
    FakeSession.scripts = [file_frame(41, 17)]
    client.connect(run)
    # The first connection had no cursor, and no full sync has completed since.
    assert (saved(cursor_file)['lastEventId'], saved(cursor_file)['fullSyncOwed']) == (41, True)
    calls.clear()

    restarted = begin(client)
    FakeSession.scripts = [[]]
    client.connect(restarted)

    assert FakeSession.urls[-1].endswith('&since=41')
    # The restart resumes from the cursor and still asks for the owed sync.
    assert calls.count(('full sync',)) == 1


def test_settings_save_keeps_the_cursor_of_the_same_sportarr(stream, monkeypatch):
    client, calls, _ = stream
    started = []
    monkeypatch.setattr(sse_client, 'Thread', lambda target, daemon: type('T', (), {
        'start': lambda self: started.append(target)})())
    run = begin(client, cursor=41)
    client.save_cursor(run)

    client.restart()

    assert len(started) == 1
    assert client.load_cursor(sse_client._Run())


def test_new_api_key_drops_the_cursor(stream, monkeypatch):
    client, calls, _ = stream
    client.save_cursor(begin(client, cursor=41))
    monkeypatch.setattr(sse_client.settings.sportarr, 'apikey', 'key-2')

    run = sse_client._Run()

    assert not client.load_cursor(run)
    assert run.last_event_id is None


def test_each_connection_without_a_cursor_syncs_every_league(stream):
    client, calls, _ = stream
    run = begin(client)
    FakeSession.scripts = [[], []]

    client.connect(run)
    client.connect(run)

    # Sportarr replays nothing without a cursor, so each connection owes a full sync.
    assert calls.count(('full sync',)) == 2
    assert '&since=' not in FakeSession.urls[0]


def test_cursor_older_than_the_stream_window_syncs_every_league(stream):
    client, calls, cursor_file = stream
    client.save_cursor(begin(client, cursor=41))
    stale = saved(cursor_file)
    stale['savedAt'] = time.time() - 8 * 24 * 60 * 60
    cursor_file.write_text(json.dumps(stale))
    run = begin(client)
    FakeSession.scripts = [[]]

    client.connect(run)

    assert ('full sync',) in calls
    assert '&since=' not in FakeSession.urls[0]


def test_resync_takes_its_last_id_as_the_cursor(stream):
    client, calls, cursor_file = stream
    run = begin(client, cursor=41)
    client.queue_league_sync(run, 3)
    FakeSession.scripts = [frame(None, {'reason': 'too far behind', 'lastId': 90}, name='stream.resync'), []]

    client.connect(run)

    # The owed full sync covers what Sportarr did not replay, and the waiting league with it.
    assert ('full sync',) in calls
    assert run.pending == {}
    assert (saved(cursor_file)['lastEventId'], saved(cursor_file)['fullSyncOwed']) == (90, True)
    client.connect(run)
    assert FakeSession.urls[-1].endswith('&since=90')


def test_unreachable_sportarr_does_not_advance_the_cursor(stream, monkeypatch):
    client, calls, _ = stream
    run = begin(client, cursor=40)

    def unreachable(**kwargs):
        raise RequestsConnectionError('Sportarr is down')

    monkeypatch.setattr(sse_client, 'get_event_from_sportarr_api', unreachable)
    FakeSession.scripts = [file_frame(41, 17)]

    with pytest.raises(RequestsConnectionError):
        client.connect(run)

    assert run.last_event_id == 40


def test_frame_that_cannot_be_applied_is_skipped_with_a_debt(stream, monkeypatch, caplog):
    client, calls, cursor_file = stream
    run = begin(client, cursor=40)

    def locked(event):
        raise RuntimeError('database is locked')

    monkeypatch.setattr(sse_client, 'sync_one_event', locked)
    FakeSession.scripts = [file_frame(41, 17) + file_frame(42, 18)]

    client.connect(run)

    assert run.last_event_id == 42
    assert 'could not apply Sportarr stream frame 41' in caplog.text
    # The skipped change is owed to a full sync, and the debt is saved with the cursor.
    assert ('full sync',) in calls
    assert saved(cursor_file)['fullSyncOwed'] is True


def test_league_sync_that_fails_unexpectedly_leaves_a_debt(stream, monkeypatch):
    client, calls, cursor_file = stream
    run = begin(client, cursor=40)

    def locked(league_id):
        raise RuntimeError('database is locked')

    monkeypatch.setattr(sse_client, 'sync_events', locked)
    client.queue_league_sync(run, 1)

    client.flush_league_syncs(run)

    assert run.pending == {}
    assert ('full sync',) in calls
    assert saved(cursor_file)['fullSyncOwed'] is True


def test_removed_event_is_deleted_without_a_league_sync(stream, monkeypatch):
    client, calls, _ = stream
    run = begin(client, cursor=40)
    monkeypatch.setattr(sse_client, 'get_event_from_sportarr_api',
                        lambda **kwargs: calls.append(('read event', kwargs['event_id'])))
    FakeSession.scripts = [file_frame(41, 17, action='removed', leagueId=1)]

    client.connect(run)

    assert calls_of(calls, 'read event', 'read league', 'delete event', 'league sync') == [
        ('read event', 17), ('read league', 1), ('delete event', 17)]


def test_league_delete_reads_the_league_once(stream, monkeypatch):
    client, calls, _ = stream
    run = begin(client, cursor=40)
    monkeypatch.setattr(sse_client, 'get_event_from_sportarr_api', lambda **kwargs: None)
    monkeypatch.setattr(sse_client, 'get_league_from_sportarr_api',
                        lambda **kwargs: calls.append(('read league', kwargs['league_id'])))
    removals = []
    for frame_id, event_id in ((41, 17), (42, 18), (43, 19)):
        removals += frame(frame_id, {'resourceType': 'event', 'action': 'removed', 'eventId': event_id,
                                     'leagueId': 1})
    FakeSession.scripts = [removals]

    client.connect(run)

    # The rows wait for the league sync, which keeps them when Sportarr adds the league again.
    assert calls_of(calls, 'read league', 'delete event') == [('read league', 1)]


def test_burst_for_a_new_league_syncs_it_once(stream, monkeypatch):
    client, calls, cursor_file = stream
    run = begin(client, cursor=40)
    monkeypatch.setattr(sse_client, 'league_in_bazarr', lambda league_id: False)
    monkeypatch.setattr(sse_client, 'get_event_from_sportarr_api',
                        lambda **kwargs: calls.append(('read event', kwargs['event_id'])) or
                        sportarr_event(kwargs['event_id'], 5))
    monkeypatch.setattr(sse_client, 'sync_one_event', lambda event: sync_events_module.EVENT_NEEDS_LEAGUE_SYNC)
    saved_cursors = []
    save_cursor = client.save_cursor

    def record_save(this_run, final=False):
        save_cursor(this_run, final)
        if cursor_file.exists():
            saved_cursors.append(saved(cursor_file)['lastEventId'])

    monkeypatch.setattr(client, 'save_cursor', record_save)
    burst = []
    for frame_id, event_id in ((41, 17), (42, 18), (43, 19)):
        burst += frame(frame_id, {'resourceType': 'event', 'action': 'added', 'eventId': event_id, 'leagueId': 5})
    # The keepalive comment marks the end of the burst.
    FakeSession.scripts = [burst + [': keepalive']]

    client.connect(run)

    assert calls_of(calls, 'read event', 'read league', 'league insert') == [
        ('read event', 17), ('read league', 5), ('league insert', 5)]
    # Until the league sync runs, the saved cursor stays before the first frame that waits for it.
    assert saved_cursors[0] == 40
    assert saved_cursors[-1] == 43


def test_repeated_frames_of_a_fileless_event_wait_for_one_league_sync(stream, monkeypatch):
    client, calls, _ = stream
    run = begin(client, cursor=40)
    monkeypatch.setattr(sse_client, 'sync_one_event',
                        lambda event: calls.append(('event sync', event['id'])) or
                        sync_events_module.EVENT_NEEDS_LEAGUE_SYNC)
    FakeSession.scripts = [file_frame(41, 17) + file_frame(42, 17) + [': keepalive']]

    client.connect(run)

    assert calls_of(calls, 'event sync', 'league sync') == [('event sync', 17), ('league sync', 1)]


def test_frame_after_league_folders_are_turned_on_is_applied(stream, monkeypatch):
    client, calls, _ = stream
    run = begin(client, cursor=40)
    folders = {'path': None}
    monkeypatch.setattr(sse_client, 'get_league_from_sportarr_api', lambda **kwargs: {'id': 1, **folders})
    FakeSession.scripts = [file_frame(41, 17)]
    client.connect(run)
    folders['path'] = '/sports/1'
    FakeSession.scripts = [file_frame(42, 18)]

    client.connect(run)

    assert calls_of(calls, 'event sync') == [('event sync', 17), ('event sync', 18)]


def test_replayed_frame_dates_the_cursor_by_its_change(stream):
    client, calls, _ = stream
    run = begin(client, cursor=40)
    FakeSession.scripts = [file_frame(41, 17, timestamp='2026-08-10T23:30:45.1234567Z')]

    client.connect(run)

    assert run.current_at == 1786404645


def test_reconnects_back_off_and_log_once(stream, caplog):
    client, calls, _ = stream

    assert [sse_client.reconnect_delay(failures) for failures in range(1, 10)] == [
        5, 10, 20, 40, 80, 160, 300, 300, 300]


def test_frame_that_keeps_failing_is_owed_to_a_full_sync(stream, monkeypatch, caplog):
    client, calls, cursor_file = stream
    client.save_cursor(begin(client, cursor=40))
    client._run = None

    def get_event(**kwargs):
        if kwargs['event_id'] == 17:
            raise RequestsConnectionError('Sportarr returns 500 for this event')
        calls.append(('read event', kwargs['event_id']))
        return sportarr_event(kwargs['event_id'], 1)

    monkeypatch.setattr(sse_client, 'get_event_from_sportarr_api', get_event)
    replay = file_frame(41, 17, leagueId=3) + file_frame(42, 18)

    with caplog.at_level(logging.INFO):
        run_cycles(client, monkeypatch, [replay] * 3 + [[]])

    # The later frame is applied once the failing frame is given up.
    assert ('event sync', 18) in calls
    assert (saved(cursor_file)['lastEventId'], saved(cursor_file)['fullSyncOwed']) == (42, True)
    # The retries back off instead of reconnecting every 5 seconds.
    assert InstantEvent.waits[:2] == [5, 10]
    assert len([record for record in caplog.records
                if record.levelno == logging.INFO and 'cannot reach' in record.getMessage()]) == 1


def test_failing_frame_does_not_refresh_the_cursor_age(stream, monkeypatch):
    client, calls, cursor_file = stream
    client.save_cursor(begin(client, cursor=40))
    old = saved(cursor_file)
    old['savedAt'] -= 1000
    cursor_file.write_text(json.dumps(old))
    client._run = None

    def get_event(**kwargs):
        raise RequestsConnectionError('Sportarr returns 500 for this event')

    monkeypatch.setattr(sse_client, 'get_event_from_sportarr_api', get_event)

    run_cycles(client, monkeypatch, [file_frame(41, 17)])

    assert saved(cursor_file)['savedAt'] == old['savedAt']


@pytest.mark.parametrize('league_known', [True, False], ids=['known-league', 'new-league'])
def test_failed_league_sync_keeps_the_league_waiting(stream, monkeypatch, league_known):
    client, calls, cursor_file = stream
    run = begin(client, cursor=40)
    inserted = []
    monkeypatch.setattr(sse_client, 'league_in_bazarr', lambda league_id: league_known or bool(inserted))
    monkeypatch.setattr(sse_client, 'update_one_league', lambda league_id, action, **kwargs: inserted.append(1))
    monkeypatch.setattr(sse_client, 'sync_one_event', lambda event: sync_events_module.EVENT_NEEDS_LEAGUE_SYNC)
    # Sportarr does not answer the event pages of the league.
    monkeypatch.setattr(sse_client, 'sync_events', lambda league_id: False)
    FakeSession.scripts = [frame(41, {'resourceType': 'event', 'action': 'added', 'eventId': 17}) + [': keepalive']]

    client.connect(run)

    assert 1 in run.pending
    assert saved(cursor_file)['lastEventId'] == 40


def test_league_sync_that_keeps_failing_is_owed_to_a_full_sync(stream, monkeypatch):
    client, calls, cursor_file = stream
    run = begin(client, cursor=40)
    synced = []
    monkeypatch.setattr(sse_client, 'sync_events', lambda league_id: synced.append(league_id) and False)
    client.queue_league_sync(run, 1)
    run.last_event_id = 45

    for _ in range(sse_client.MAX_ATTEMPTS):
        run.flush_due_at = 0
        client.flush_league_syncs(run)

    assert synced == [1, 1, 1]
    assert run.pending == {}
    client.save_cursor(run)
    # The cursor moves past the league only because the debt is saved with it.
    assert (saved(cursor_file)['lastEventId'], saved(cursor_file)['fullSyncOwed']) == (45, True)


def test_failed_league_sync_waits_before_it_runs_again(stream, monkeypatch):
    client, calls, _ = stream
    run = begin(client, cursor=40)
    now = [1000.0]
    monkeypatch.setattr(sse_client.time, 'time', lambda: now[0])
    synced = []
    monkeypatch.setattr(sse_client, 'sync_events', lambda league_id: synced.append(league_id) and False)
    client.queue_league_sync(run, 1)

    client.flush_league_syncs(run)
    client.flush_league_syncs(run)
    assert synced == [1]

    now[0] += sse_client.LEAGUE_RETRY_DELAY + 1
    client.flush_league_syncs(run)
    assert synced == [1, 1]


@pytest.mark.parametrize('league', [{'id': 1, 'path': None}, {'id': 1, 'path': '/sports/1', 'unmonitored': 1}],
                         ids=['no-folder', 'unmonitored'])
def test_league_sync_from_the_stream_leaves_a_league_the_full_sync_skips(stream, monkeypatch, league):
    client, calls, _ = stream
    run = begin(client, cursor=40)
    monkeypatch.setattr(sse_client, 'get_league_from_sportarr_api', lambda **kwargs: league)
    monkeypatch.setattr(sse_client, 'league_left_unmonitored', lambda league_id: 'unmonitored' in league)
    client.queue_league_sync(run, 1)

    client.flush_league_syncs(run)

    assert ('league sync', 1) not in calls
    assert run.pending == {}


def test_full_sync_request_matches_the_scheduled_one(monkeypatch):
    started = []
    monkeypatch.setattr(sync_leagues, 'Thread', lambda target, kwargs, daemon: type('T', (), {
        'start': lambda self: started.append((target, kwargs))})())

    sync_leagues.queue_full_sync()

    # The jobs queue drops a request whose arguments match a queued or running job.
    assert started == [(sync_leagues.update_leagues, {'wait_for_completion': True})]


def test_keepalive_queues_nothing_while_a_full_sync_runs(stream, monkeypatch):
    client, calls, _ = stream
    run = begin(client, cursor=40)
    run.owed_at = time.monotonic()
    monkeypatch.setattr(sse_client, 'full_sync_queued_or_running', lambda: True)
    FakeSession.scripts = [[': keepalive'] * 5]

    client.connect(run)

    assert ('full sync',) not in calls


def test_full_sync_that_cannot_complete_is_left_to_the_scheduler(stream, monkeypatch, caplog):
    client, calls, _ = stream
    run = begin(client, cursor=40)
    monkeypatch.setattr(sse_client.sync_state, 'last_incomplete_sync_reason',
                        'Sportarr did not return the events of UFC.')
    with caplog.at_level(logging.INFO):
        client.owe_full_sync(run)
        # The queued sync ran after the debt and could not read every league.
        monkeypatch.setattr(sse_client.sync_state, 'last_sync_started_at', time.monotonic())
        for _ in range(3):
            client.settle_full_sync(run)

    assert calls.count(('full sync',)) == 1
    assert run.owed_at is not None
    assert [record.getMessage() for record in caplog.records if 'cannot finish' in record.getMessage()] == [
        'BAZARR cannot finish a full league sync. Sportarr did not return the events of UFC. '
        'The scheduled sync tries again.']


def test_full_sync_debt_survives_a_restart_until_a_later_sync_completes(stream, monkeypatch):
    client, calls, cursor_file = stream
    client.owe_full_sync(begin(client, cursor=40))
    assert saved(cursor_file)['fullSyncOwed'] is True

    run = begin(client)
    debt = run.owed_at
    assert debt is not None
    # A sync that started before the debt does not cover it.
    monkeypatch.setattr(sse_client.sync_state, 'last_complete_sync_started_at', debt - 1)
    client.settle_full_sync(run)
    assert saved(cursor_file)['fullSyncOwed'] is True

    monkeypatch.setattr(sse_client.sync_state, 'last_complete_sync_started_at', debt + 1)
    client.settle_full_sync(run)
    assert saved(cursor_file)['fullSyncOwed'] is False


def test_saved_debt_starts_on_the_clock_of_the_new_run(stream, monkeypatch):
    client, calls, _ = stream
    client.owe_full_sync(begin(client, cursor=41))
    monkeypatch.setattr(sse_client.time, 'monotonic', lambda: 50.0)

    assert begin(client).owed_at == 50.0


def test_settled_debt_is_written_even_without_a_cursor(stream, monkeypatch):
    client, calls, cursor_file = stream
    run = begin(client)
    client.owe_full_sync(run)
    monkeypatch.setattr(sse_client.sync_state, 'last_complete_sync_started_at', time.monotonic() + 1)

    client.settle_full_sync(run)

    assert saved(cursor_file)['fullSyncOwed'] is False


def test_newer_need_moves_the_debt_forward(stream, monkeypatch):
    client, calls, _ = stream
    run = begin(client, cursor=40)
    clock = [100.0]
    monkeypatch.setattr(sse_client.time, 'monotonic', lambda: clock[0])
    client.owe_full_sync(run)
    clock[0] = 200.0
    monkeypatch.setattr(sse_client, 'league_in_bazarr', lambda league_id: False)
    monkeypatch.setattr(sse_client, 'update_one_league',
                        lambda league_id, action, **kwargs: kwargs['request_full_sync']())

    client.sync_league(run, 7)

    # A sync that started at 150 read the league list before the new league existed.
    assert run.owed_at == 200.0


def test_cursor_writes_use_their_own_temporary_file(stream, monkeypatch):
    client, calls, _ = stream
    run = begin(client, cursor=41)
    sources = []
    replace = sse_client.os.replace
    monkeypatch.setattr(sse_client.os, 'replace', lambda source, target: sources.append(source) or
                        replace(source, target))

    client.save_cursor(run)
    client.save_cursor(run)

    assert len(set(sources)) == 2


def test_old_reader_cannot_write_the_cursor_after_a_restart(stream, monkeypatch):
    client, calls, cursor_file = stream
    old = begin(client, cursor=40)
    client.save_cursor(old)

    def restart_during_dispatch(event):
        # A settings save restarts the client while this frame is applied.
        begin(client, cursor=40)

    monkeypatch.setattr(sse_client, 'sync_one_event', restart_during_dispatch)
    FakeSession.scripts = [file_frame(41, 17) + [': keepalive']]

    client.connect(old)

    assert saved(cursor_file)['lastEventId'] == 40
    assert client._run.last_event_id == 40


def test_stop_after_a_new_api_key_saves_under_the_old_connection(stream, monkeypatch):
    client, calls, _ = stream
    begin(client, cursor=41)
    client.connected = True
    # The settings save writes the new key before it restarts the client.
    monkeypatch.setattr(sse_client.settings.sportarr, 'apikey', 'key-2')

    client.stop()

    assert not client.load_cursor(sse_client._Run())


def test_connect_and_disconnect_update_the_badge(stream):
    client, calls, _ = stream
    run = begin(client, cursor=40)
    FakeSession.scripts = [[]]

    client.connect(run)

    assert calls_of(calls, 'badge') == [('badge', 'badges'), ('badge', 'badges')]
    assert not client.connected


def test_no_signalr_keeps_the_stream_off(stream, monkeypatch):
    client, calls, _ = stream
    started = []
    monkeypatch.setattr(sse_client.args, 'no_signalr', True)
    monkeypatch.setattr(sse_client, 'Thread', lambda target, daemon: type('T', (), {
        'start': lambda self: started.append(target)})())

    client.start()
    client.restart()

    assert FakeSession.urls == []
    assert started == []


def test_badge_reports_off_under_no_signalr(api_client, api_key, monkeypatch):
    from api.badges import badges

    monkeypatch.setattr(badges.args, 'no_signalr', True)

    response = api_client.get('/api/badges', headers={'X-API-KEY': api_key})

    assert response.json['sportarr_sse'] == response.json['sonarr_signalr'] == 'OFF'


def test_stream_frame_writes_the_event_rows(sports_db, stream, monkeypatch):  # noqa: F811
    client, calls, _ = stream
    monkeypatch.setattr(sse_client, 'sync_one_event', sync_events_module.sync_one_event)
    add_league(sports_db, 1)
    monkeypatch.setattr(sse_client, 'get_event_from_sportarr_api', lambda **kwargs: sportarr_event(17, 1, (1, 2)))
    run = begin(client, cursor=40)
    FakeSession.scripts = [file_frame(41, 17)]

    client.connect(run)

    assert sports_db.execute(db.select(db.TableSportsEvents.sportarrEventId, db.TableSportsEvents.partNumber)
                             .order_by(db.TableSportsEvents.partNumber)).all() == [(17, 1), (17, 2)]
    assert not calls_of(calls, 'league sync')


def test_stream_frame_removes_a_part_that_lost_its_file(sports_db, stream, monkeypatch):  # noqa: F811
    client, calls, _ = stream
    monkeypatch.setattr(sse_client, 'sync_one_event', sync_events_module.sync_one_event)
    monkeypatch.setattr(sse_client, 'delete_event_rows', sync_events_module.delete_event_rows)
    monkeypatch.setattr(sse_client, 'database', sports_db)
    add_league(sports_db, 1)
    add_event(sports_db, 1, 1, 17, part_number=1)
    add_event(sports_db, 2, 1, 17, part_number=2)
    add_event(sports_db, 3, 1, 18)
    monkeypatch.setattr(sse_client, 'get_event_from_sportarr_api',
                        lambda **kwargs: sportarr_event(17, 1, (1,)) if kwargs['event_id'] == 17 else None)
    run = begin(client, cursor=40)
    FakeSession.scripts = [file_frame(41, 17, action='removed')
                           + frame(42, {'resourceType': 'event', 'action': 'removed', 'eventId': 18})]

    client.connect(run)

    assert counts(sports_db)['events'] == [1]
    assert not calls_of(calls, 'league sync')


def test_league_monitored_again_in_sportarr_is_synced_from_the_stream(stream, monkeypatch):
    client, calls, _ = stream
    run = begin(client, cursor=40)
    # Bazarr still holds the league as unmonitored, and Sportarr monitors it now.
    monkeypatch.setattr(sse_client, 'league_left_unmonitored', lambda league_id: True)
    monkeypatch.setattr(sse_client, 'get_league_from_sportarr_api',
                        lambda **kwargs: {'id': 1, 'path': '/sports/1', 'monitored': True})
    client.queue_league_sync(run, 1)

    client.flush_league_syncs(run)

    assert ('league sync', 1) in calls


def test_burst_of_skipped_frames_writes_and_logs_the_debt_once(stream, monkeypatch, caplog):
    client, calls, cursor_file = stream
    run = begin(client, cursor=40)
    writes = []
    replace = sse_client.os.replace
    monkeypatch.setattr(sse_client.os, 'replace', lambda source, target: writes.append(target) or
                        replace(source, target))

    def locked(event):
        raise RuntimeError('database is locked')

    monkeypatch.setattr(sse_client, 'sync_one_event', locked)
    FakeSession.scripts = [file_frame(41, 17) + file_frame(42, 18) + file_frame(43, 19)]

    with caplog.at_level(logging.INFO):
        client.connect(run)

    assert len([record for record in caplog.records if record.levelno == logging.INFO and
                'keeps a full league sync owed' in record.getMessage()]) == 1
    # One traceback for the burst, not one for each frame.
    assert len([record for record in caplog.records if record.levelno >= logging.ERROR and record.exc_info]) == 1
    # The debt is written once, and the cursor once more as the connection ends.
    assert len(writes) == 2
    assert saved(cursor_file)['fullSyncOwed'] is True
    assert run.last_event_id == 43


def test_failure_after_a_good_frame_shows_its_traceback_while_a_debt_is_owed(stream, monkeypatch, caplog):
    client, calls, _ = stream
    run = begin(client, cursor=40)
    # A debt from an earlier run must not hide new failures.
    run.owed_at = sse_client.time.monotonic()

    def apply(event):
        if event['id'] in (17, 19):
            raise RuntimeError('database is locked')
        return sync_events_module.EVENT_SYNCED

    monkeypatch.setattr(sse_client, 'sync_one_event', apply)
    FakeSession.scripts = [file_frame(41, 17) + file_frame(42, 18) + file_frame(43, 19)]

    with caplog.at_level(logging.INFO):
        client.connect(run)

    # Frame 42 applies, so the failure of frame 43 is new and shows its traceback.
    assert len([record for record in caplog.records if record.levelno >= logging.ERROR and record.exc_info]) == 2
    assert run.last_event_id == 43


def test_stream_league_sync_stores_the_monitored_flag_from_sportarr(sports_db, stream, monkeypatch):  # noqa: F811
    client, calls, _ = stream
    add_league(sports_db, 1)
    sports_db.execute(db.update(db.TableSportsLeagues).values(monitored='False'))
    monkeypatch.setattr(sse_client.settings.sportarr, 'sync_only_monitored_leagues', True)
    monkeypatch.setattr(sse_client, 'league_in_bazarr', sync_events_module.league_in_bazarr)
    monkeypatch.setattr(sse_client, 'league_left_unmonitored', sync_events_module.league_left_unmonitored)
    monkeypatch.setattr(sse_client, 'update_one_league', sync_leagues.update_one_league)
    # The user monitors the league again in Sportarr.
    monkeypatch.setattr(sse_client, 'get_league_from_sportarr_api',
                        lambda **kwargs: sportarr_league(1, external_id=None))
    run = begin(client, cursor=40)
    client.queue_league_sync(run, 1)

    client.flush_league_syncs(run)

    # The row follows Sportarr, so later frames are not handed to a league sync again.
    assert sports_db.execute(db.select(db.TableSportsLeagues.monitored)).scalar_one() == 'True'
    assert ('league sync', 1) in calls

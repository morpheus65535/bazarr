# coding=utf-8

import calendar
import hashlib
import json
import logging
import os
import tempfile
import time
from threading import Event, RLock, Thread

from requests import Response, Session
from requests.exceptions import RequestException

from app.config import settings
from app.database import database, select, TableSportsEvents
from app.event_handler import event_stream
from app.get_args import args
from constants import HEADERS
from sportarr.info import url_sportarr
from sportarr.sync import state as sync_state
from sportarr.sync.events import (EVENT_NEEDS_LEAGUE_SYNC, delete_event_rows, league_in_bazarr,
                                  league_left_unmonitored, sync_events, sync_one_event)
from sportarr.sync.utils import get_event_from_sportarr_api, get_league_from_sportarr_api
from sportarr.sync.leagues import full_sync_queued_or_running, queue_full_sync, update_one_league

# Sportarr keeps stream events for 7 days. A cursor older than that can miss
# changes, so a margin of one day triggers a full sync before that happens.
CURSOR_MAX_AGE = 6 * 24 * 60 * 60
# How often a quiet stream refreshes the age of the saved cursor.
CURSOR_REFRESH_INTERVAL = 60 * 60
# How often a busy stream writes the cursor to disk.
CURSOR_SAVE_INTERVAL = 5
# League syncs that frames ask for wait this long, so a burst syncs a league once.
LEAGUE_SYNC_DELAY = 10
# A failed league sync waits this long, times its attempts, before it runs again.
LEAGUE_RETRY_DELAY = 30
# After this many attempts, a frame or a league sync is handed to a full sync,
# so one item that Sportarr cannot serve does not stop the stream.
MAX_ATTEMPTS = 3
# A league delete sends one frame for each event. One read answers them all.
LEAGUE_GONE_TTL = 60
RECONNECT_DELAYS = (5, 10, 20, 40, 80, 160, 300)


class UnreadableFrame(ValueError):
    """A stream frame that does not say what changed."""


def cursor_file_path() -> str:
    """The file that holds the saved cursor and debt."""
    return os.path.join(args.config_dir, 'config', 'sportarr_stream.json')


def reconnect_delay(failures: int) -> int:
    """Seconds to wait before the next connection, longer after each failure."""
    return RECONNECT_DELAYS[min(max(failures, 1), len(RECONNECT_DELAYS)) - 1]


def connection_fingerprint() -> str:
    """Identify the Sportarr address and API key that a saved cursor belongs to."""
    # The file does not hold the key in clear text. The hash has no salt, so
    # anyone who reads the file can test a guessed key against it. That is
    # safe for a random key, which Sportarr makes unless the user sets one.
    return hashlib.sha256(f'{url_sportarr()}|{settings.sportarr.apikey}'.encode('utf-8')).hexdigest()


def frame_time(raw: str) -> int | None:
    """The time of a frame, in seconds, or None. Sportarr writes UTC, for example 2026-08-10T23:30:45Z."""
    try:
        stamp = json.loads(raw).get('timestamp')
        return calendar.timegm(time.strptime(stamp[:19], '%Y-%m-%dT%H:%M:%S'))
    except (ValueError, TypeError, AttributeError):
        return None


class _Run:
    """The state of one run of the client. A restart builds a new one, so an old reader cannot change it."""

    def __init__(self) -> None:
        self.stop = Event()
        self.fingerprint = None
        self.last_event_id = None
        # When Bazarr last had every change up to last_event_id.
        self.current_at = 0
        self.saved_at = 0
        self.dirty = False
        # When Bazarr last skipped a change that only a full sync covers, on the monotonic clock.
        self.owed_at = None
        self.incomplete_logged = False
        self.pending: dict[int, dict[str, float]] = {}
        self.pending_cursor = None
        self.flush_due_at = 0
        self.failing_frame = (None, 0)
        self.gone_leagues: dict[int, float] = {}
        self.failures = 0
        self.failure_logged = False
        # True after a frame failed to apply, until a frame applies again.
        self.apply_failing = False
        # True after a cursor save failed, until a save works again.
        self.save_failing = False


class SportarrSSEClient:
    """Reads Sportarr's event stream so changes arrive without waiting for a sync.

    Sportarr sends Server-Sent Events rather than SignalR. Each frame carries a
    monotonic id, so a reconnect asks for everything after the last id handled
    and resumes exactly where it stopped. The id is saved to disk, so a
    restart of Bazarr resumes too.

    When the stream cannot cover a change, Bazarr owes a full league sync. The
    debt is saved with the cursor and stays until a full sync that started
    after it reads every league.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._run = None
        self._response = None
        # stop() counts up, so a start() that began before a stop() can tell.
        self._generation = 0
        self.connected = False

    def start(self) -> None:
        """Read the stream until stop() runs, and reconnect after each drop."""
        with self._lock:
            generation = self._generation
        if args.no_signalr or not settings.general.use_sportarr:
            self.connected = False
            return

        run = _Run()
        self.load_cursor(run)
        with self._lock:
            if self._generation != generation or not settings.general.use_sportarr:
                # stop() ran while the cursor was read. That stop applies to this start too.
                return
            previous, previous_response = self._run, self._response
            if previous:
                previous.stop.set()
            self._run = run
            self._response = None
            self.connected = False
        if previous_response:
            self._close_response(previous_response)

        while not run.stop.is_set():
            try:
                self.connect(run)
            except RequestException:
                if not run.stop.is_set():
                    run.failures += 1
                    if not run.failure_logged:
                        run.failure_logged = True
                        logging.info('BAZARR cannot reach the Sportarr event stream. It keeps trying to reconnect.')
                    else:
                        logging.debug('BAZARR cannot reach the Sportarr event stream.')
            except Exception:
                if not run.stop.is_set():
                    logging.exception('BAZARR unexpected error reading the Sportarr event stream.')
                    run.failures += 1

            if run.stop.is_set():
                break
            self._set_connected(run, False)
            # Sportarr keeps a window of past events, so reconnecting after a
            # pause still returns what was missed.
            run.stop.wait(reconnect_delay(run.failures))

    @staticmethod
    def _stream_works(run: _Run) -> None:
        """Reset the reconnect backoff, because the stream delivered."""
        # The stream counts as working only once it delivers, not when it
        # answers. A frame that fails on every connection keeps the backoff.
        if run.failure_logged:
            logging.info('BAZARR reconnected to the Sportarr event stream.')
        run.failures = 0
        run.failure_logged = False

    def _set_connected(self, run: _Run, connected: bool) -> None:
        """Set the connected state of the current run, and refresh the badge when it changes."""
        with self._lock:
            if self._run is not run or self.connected == connected:
                return
            self.connected = connected
        event_stream(type='badges')

    def stop(self) -> None:
        """End the current run, and any start() that has not made its run yet."""
        with self._lock:
            run, response, was_connected = self._run, self._response, self.connected
            self._run = None
            self._response = None
            self._generation += 1
            self.connected = False
            if run:
                run.stop.set()
        if response:
            self._close_response(response)
        if run and was_connected:
            self.save_cursor(run, final=True)
            event_stream(type='badges')
        logging.info('BAZARR SSE client for Sportarr is now disconnected.')

    def restart(self) -> None:
        """Stop the client, then start it again in a new thread when Sportarr is enabled."""
        self.stop()
        # The saved cursor stays. start() drops it when the Sportarr address
        # or the API key changed.
        if settings.general.use_sportarr and not args.no_signalr:
            Thread(target=self.start, daemon=True).start()

    @staticmethod
    def _close_response(response: Response) -> None:
        """Close a stream response, and wake a reader that waits on it."""
        # Shutdown wakes a reader blocked while waiting for the next frame.
        try:
            response.raw.shutdown()
        except (AttributeError, ValueError, RuntimeError, OSError):
            pass
        response.close()

    @staticmethod
    def load_cursor(run: _Run) -> bool:
        """Read the saved cursor and debt into run. Returns False when there is no cursor."""
        run.fingerprint = connection_fingerprint()
        try:
            with open(cursor_file_path(), 'r', encoding='utf-8') as handle:
                saved = json.load(handle)
        except FileNotFoundError:
            return False
        except (OSError, ValueError):
            logging.debug('BAZARR could not read the saved Sportarr event stream cursor.')
            return False

        if not isinstance(saved, dict) or saved.get('connection') != run.fingerprint:
            return False
        if saved.get('fullSyncOwed') is True:
            # The clock of the run that saved it means nothing now, so the debt starts now.
            run.owed_at = time.monotonic()
        if type(saved.get('lastEventId')) is not int or saved['lastEventId'] <= 0 or \
                not isinstance(saved.get('savedAt'), (int, float)):
            return False
        run.last_event_id = saved['lastEventId']
        run.current_at = saved['savedAt']
        return True

    def save_cursor(self, run: _Run, final: bool = False) -> None:
        """Write the cursor of run, while run is the current one, or as stop() ends it."""
        with self._lock:
            if self._run is not run and not final:
                return
            # Frames that wait for a league sync are not handled yet. The saved
            # cursor stays before them until that sync runs.
            cursor = run.pending_cursor if run.pending else run.last_event_id
            if cursor is None and run.owed_at is None and not run.dirty:
                return
            path = cursor_file_path()
            run.saved_at = time.time()
            run.dirty = False
            # savedAt is when Bazarr last had every change up to the cursor,
            # not when the file was written.
            saved = {'connection': run.fingerprint, 'lastEventId': cursor, 'savedAt': run.current_at,
                     'fullSyncOwed': run.owed_at is not None}
            temp_path = None
            try:
                handle, temp_path = tempfile.mkstemp(dir=os.path.dirname(path), prefix='sportarr_stream.',
                                                     suffix='.tmp')
                with os.fdopen(handle, 'w', encoding='utf-8') as temp_file:
                    json.dump(saved, temp_file)
                # A crash during the write leaves the previous file whole.
                os.replace(temp_path, path)
            except OSError as e:
                # The next keepalive tries again.
                run.dirty = True
                if not run.save_failing:
                    run.save_failing = True
                    logging.warning(f'BAZARR could not save the Sportarr event stream cursor: {e}. It keeps '
                                    f'trying. Until a save works, a restart replays changes and can lose a '
                                    f'full league sync that is owed.')
                else:
                    logging.debug(f'BAZARR could not save the Sportarr event stream cursor: {e}')
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
            else:
                if run.save_failing:
                    run.save_failing = False
                    logging.info('BAZARR saved the Sportarr event stream cursor again.')

    def owe_full_sync(self, run: _Run, reason: str | None = None) -> None:
        """Record that only a full league sync covers a change, and queue one."""
        owed_before = run.owed_at is not None
        # The newest need counts, so a sync that read the league list before it does not cover it.
        run.owed_at = time.monotonic()
        if owed_before:
            # The saved file already holds the debt, so a burst writes and logs it once.
            if reason:
                logging.debug(f'BAZARR {reason}')
        else:
            run.incomplete_logged = False
            run.dirty = True
            if reason:
                logging.info(f'BAZARR {reason} It keeps a full league sync owed until one completes.')
            self.save_cursor(run)
        self.settle_full_sync(run)

    def settle_full_sync(self, run: _Run) -> None:
        """Clear the debt when a full sync covered it, or queue one when none ran since the debt."""
        if run.owed_at is None:
            return
        if sync_state.last_complete_sync_started_at >= run.owed_at:
            run.owed_at = None
            run.dirty = True
            self.save_cursor(run)
            return
        if full_sync_queued_or_running():
            return
        if sync_state.last_sync_started_at >= run.owed_at:
            # A sync ran after the debt and could not read everything. The
            # scheduled sync tries again, and the debt stays until one completes.
            if not run.incomplete_logged:
                run.incomplete_logged = True
                logging.info(f'BAZARR cannot finish a full league sync. {sync_state.last_incomplete_sync_reason} '
                             f'The scheduled sync tries again.')
            return
        queue_full_sync()

    def connect(self, run: _Run) -> None:
        """Open one stream connection and read it until it ends."""
        if run.last_event_id and time.time() - run.current_at > CURSOR_MAX_AGE:
            # Sportarr may have pruned changes after the cursor.
            run.last_event_id = None
            self.owe_full_sync(run, 'was away from the Sportarr event stream for too long.')

        url = f"{url_sportarr()}/api/stream?apikey={settings.sportarr.apikey}"
        if run.last_event_id:
            url += f"&since={run.last_event_id}"

        logging.debug('BAZARR trying to connect to Sportarr event stream...')
        with Session() as session:
            session.verify = False
            session.headers = HEADERS
            with session.get(url, stream=True, timeout=(10, 60)) as response:
                response.raise_for_status()
                with self._lock:
                    if run.stop.is_set() or self._run is not run:
                        return
                    self._response = response
                self._set_connected(run, True)
                if not run.failure_logged:
                    logging.info('BAZARR SSE client for Sportarr is connected and waiting for events.')

                if not run.last_event_id:
                    # Sportarr replays nothing without a cursor, so the stream
                    # alone cannot tell what changed while Bazarr was away.
                    self.owe_full_sync(run)
                else:
                    self.settle_full_sync(run)

                try:
                    self.read_frames(response, run)
                finally:
                    with self._lock:
                        if self._response is response:
                            self._response = None
                    self._set_connected(run, False)
                    self.save_cursor(run)

    def read_frames(self, response: Response, run: _Run) -> None:
        """Parse the stream lines into frames and keepalives, and handle each one."""
        frame_id = None
        frame_name = None
        data = []
        for line in response.iter_lines(decode_unicode=True):
            if run.stop.is_set():
                break
            if line.startswith(':'):
                # A keepalive comment. Sportarr sends it only when it has
                # nothing else to send, so Bazarr is up to date.
                run.current_at = time.time()
                self._stream_works(run)
                self.flush_league_syncs(run)
                self.settle_full_sync(run)
                if run.dirty or time.time() - run.saved_at > CURSOR_REFRESH_INTERVAL:
                    self.save_cursor(run)
                continue
            if line:
                field, _, value = line.partition(':')
                value = value[1:] if value.startswith(' ') else value
                if field == 'id':
                    frame_id = value
                elif field == 'event':
                    frame_name = value
                elif field == 'data':
                    data.append(value)
                continue

            # A blank line ends the frame.
            if data:
                self.handle_frame(run, frame_id, frame_name, '\n'.join(data))
            frame_id = None
            frame_name = None
            data = []

    def handle_resync(self, run: _Run, raw: str) -> None:
        """Take the cursor that Sportarr gives, and owe a full sync for what it could not replay."""
        # Sportarr goes live after lastId, so that id is the cursor now. It is
        # lower than the cursor when Sportarr's ids went back, for example
        # after a restore from backup. Sportarr says 0 when it holds no events.
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = None
        if not isinstance(payload, dict):
            payload = {}
        last_id = payload.get('lastId')
        if type(last_id) is int and last_id >= 0:
            run.last_event_id = last_id or None
            run.dirty = True
        run.pending = {}
        run.pending_cursor = None
        run.current_at = time.time()
        reason = payload.get('reason')
        if isinstance(reason, str) and reason.startswith('cursor ahead'):
            self.owe_full_sync(run, 'held a cursor past the newest Sportarr change, for example after a Sportarr '
                                    'restore.')
        else:
            self.owe_full_sync(run, 'missed too many Sportarr changes to replay them.')

    def handle_frame(self, run: _Run, frame_id: str | None, frame_name: str | None, raw: str) -> None:
        """Apply one frame, then move the cursor past it or record a debt for it."""
        if frame_name == 'stream.resync':
            self.handle_resync(run, raw)
            return

        league_to_sync = None
        try:
            league_to_sync = self.dispatch(raw, run)
        except RequestException:
            attempts = run.failing_frame[1] + 1 if run.failing_frame[0] == frame_id else 1
            run.failing_frame = (frame_id, attempts)
            if attempts < MAX_ATTEMPTS:
                # Sportarr did not answer. The cursor stays before this frame,
                # so the reconnect replays it.
                raise
            self.owe_full_sync(run, f'could not read the change in Sportarr stream frame {frame_id} after '
                                    f'{attempts} attempts.')
        except UnreadableFrame as e:
            # The stream cannot send the change again, so only a full sync covers it.
            self.owe_full_sync(run, f'could not read Sportarr stream frame {frame_id}, because {e}.')
        except Exception:
            # For example a locked database. The frame is skipped, so a full sync covers it.
            if not run.apply_failing:
                logging.exception(f'BAZARR could not apply Sportarr stream frame {frame_id}.')
            else:
                # A burst of failures shows its traceback once.
                logging.debug(f'BAZARR could not apply Sportarr stream frame {frame_id}.', exc_info=True)
            run.apply_failing = True
            self.owe_full_sync(run, f'skipped Sportarr stream frame {frame_id}.')
        else:
            run.apply_failing = False

        run.failing_frame = (None, 0)
        if league_to_sync is not None:
            self.queue_league_sync(run, league_to_sync)
        try:
            event_id = int(frame_id)
        except (TypeError, ValueError):
            event_id = None
        if event_id is not None and (run.last_event_id is None or event_id > run.last_event_id):
            run.last_event_id = event_id
            # A replayed frame is as old as its change, not as old as now.
            run.current_at = min(frame_time(raw) or time.time(), time.time())
            run.dirty = True
        self._stream_works(run)

        if run.pending and time.time() - min(entry['queued'] for entry in run.pending.values()) > LEAGUE_SYNC_DELAY:
            self.flush_league_syncs(run)
        if time.time() - run.saved_at > CURSOR_SAVE_INTERVAL:
            self.save_cursor(run)

    @staticmethod
    def queue_league_sync(run: _Run, league_id: int) -> None:
        """Ask for a league sync, and keep the saved cursor before the frames that wait for it."""
        if not run.pending:
            run.pending_cursor = run.last_event_id
        run.pending.setdefault(league_id, {'queued': time.time(), 'attempts': 0})

    def flush_league_syncs(self, run: _Run) -> None:
        """Run the league syncs that frames asked for, unless a retry must wait."""
        if not run.pending or time.time() < run.flush_due_at:
            return
        for league_id in list(run.pending):
            if run.stop.is_set():
                return
            if not self.sync_league(run, league_id):
                entry = run.pending[league_id]
                entry['attempts'] += 1
                if entry['attempts'] < MAX_ATTEMPTS:
                    # The league keeps waiting, and the saved cursor stays before it.
                    run.flush_due_at = time.time() + LEAGUE_RETRY_DELAY * entry['attempts']
                    return
                # The debt is saved before the cursor can move past the league.
                self.owe_full_sync(run, f'could not sync Sportarr league {league_id} from the event stream.')
            del run.pending[league_id]
        run.pending_cursor = None
        run.dirty = True

    def sync_league(self, run: _Run, league_id: int) -> bool:
        """Sync one league the way the full sync does. Returns False when Sportarr did not answer."""
        try:
            league = get_league_from_sportarr_api(apikey_sportarr=settings.sportarr.apikey, league_id=league_id)
            if league is None:
                # The league left Sportarr. The next full league sync removes
                # it, or moves it to a new add with the same external id.
                return True
            if not league.get('path') or (league_left_unmonitored(league_id) and not league.get('monitored')):
                # The full sync leaves this league as it is, so the stream does too.
                return True
            # As in the full sync, the league row follows Sportarr first, for
            # example its monitored flag. An unchanged row is not written.
            update_one_league(league_id, action='updated', league_data=[league], sync_events_after_update=False,
                              request_full_sync=lambda: self.owe_full_sync(run))
            if not league_in_bazarr(league_id):
                # update_one_league logged why it did not store the league.
                return True
            return sync_events(league_id=league_id)
        except RequestException:
            return False
        except Exception:
            logging.exception(f'BAZARR could not sync Sportarr league {league_id}.')
            self.owe_full_sync(run, f'skipped the stream sync of Sportarr league {league_id}.')
            return True

    def dispatch(self, raw: str, run: _Run | None = None) -> int | None:
        """Apply one frame. Returns a league that needs a league sync, or None.

        Raises UnreadableFrame when the frame does not say what changed.
        """
        try:
            payload = json.loads(raw)
        except ValueError:
            raise UnreadableFrame('it is not valid JSON') from None
        if not isinstance(payload, dict):
            raise UnreadableFrame('it holds no object')

        resource = payload.get('resourceType')
        event_id = payload.get('eventId')
        league_id = payload.get('leagueId')
        pending = run.pending if run else {}

        if resource not in ('event', 'file'):
            # Sportarr sends event and file frames only. Another kind has nothing to sync.
            return None
        if type(event_id) is not int:
            raise UnreadableFrame('it names no event')
        if type(league_id) is int and league_id in pending:
            # The league sync that waits already covers this event.
            return None

        # Every frame names its event, so only that event is read again.
        event = get_event_from_sportarr_api(apikey_sportarr=settings.sportarr.apikey, event_id=event_id)
        if event is None:
            self.event_gone(run, event_id, league_id)
            return None
        if isinstance(event, dict) and event.get('leagueId') in pending:
            return None

        if sync_one_event(event) == EVENT_NEEDS_LEAGUE_SYNC:
            return event['leagueId']
        return None

    def event_gone(self, run: _Run | None, event_id: int, league_id: int | None) -> None:
        """Delete the rows of an event that left Sportarr, unless its whole league left."""
        if type(league_id) is not int:
            league_id = self.league_id_for_event(event_id)
        if league_id is None:
            return
        gone_leagues = run.gone_leagues if run else {}
        if time.time() - gone_leagues.get(league_id, 0) > LEAGUE_GONE_TTL:
            if get_league_from_sportarr_api(apikey_sportarr=settings.sportarr.apikey, league_id=league_id):
                delete_event_rows(event_id)
                return
            gone_leagues[league_id] = time.time()
        # The whole league left Sportarr. The rows stay until the next full
        # league sync, which the stream does not hurry. If Sportarr adds the
        # league again with the same external id before then, that sync moves
        # the rows to the new league and keeps their subtitles and history.
        # Otherwise it removes them.

    @staticmethod
    def league_id_for_event(event_id: int) -> int | None:
        """The league that Bazarr holds an event in, or None."""
        row = database.execute(
            select(TableSportsEvents.sportarrLeagueId)
            .where(TableSportsEvents.sportarrEventId == event_id)).first()
        return row[0] if row else None


sportarr_sse_client = SportarrSSEClient()

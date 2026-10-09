# coding=utf-8

import json
import logging
from threading import Event, Lock, Thread

from requests import Session
from requests.exceptions import RequestException

from app.config import settings
from app.database import database, select, TableSportsEvents
from constants import HEADERS
from sportarr.info import url_sportarr
from sportarr.sync.events import sync_events
from sportarr.sync.utils import get_event_from_sportarr_api
from sportarr.sync.leagues import update_one_league


class SportarrSSEClient:
    """Reads Sportarr's event stream so changes arrive without waiting for a sync.

    Sportarr sends Server-Sent Events rather than SignalR. Each frame carries a
    monotonic id, so a reconnect asks for everything after the last id seen and
    resumes exactly where it stopped. There is no full resync after a drop.
    """

    def __init__(self):
        self._lock = Lock()
        self._run_stop = None
        self._response = None
        self.connected = False
        self.stopped = False
        self.last_event_id = None

    def start(self):
        if not settings.general.use_sportarr:
            return

        run_stop = Event()
        with self._lock:
            previous_stop = self._run_stop
            previous_response = self._response
            if previous_stop:
                previous_stop.set()
            self._run_stop = run_stop
            self._response = None
            self.stopped = False
            self.connected = False
        if previous_response:
            self._close_response(previous_response)

        while not run_stop.is_set():
            try:
                self.connect(run_stop)
            except RequestException:
                if not run_stop.is_set():
                    logging.debug('BAZARR connection to Sportarr event stream was lost.')
            except Exception:
                if not run_stop.is_set():
                    logging.exception('BAZARR unexpected error reading the Sportarr event stream.')

            if run_stop.is_set():
                break

            with self._lock:
                if self._run_stop is run_stop:
                    self.connected = False
            # Sportarr keeps a window of past events, so reconnecting after a
            # pause still returns what was missed.
            run_stop.wait(5)

    def stop(self):
        with self._lock:
            run_stop = self._run_stop
            response = self._response
            self._run_stop = None
            self._response = None
            self.stopped = True
            self.connected = False
            if run_stop:
                run_stop.set()
        if response:
            self._close_response(response)
        logging.info('BAZARR SSE client for Sportarr is now disconnected.')

    def restart(self):
        self.stop()
        self.last_event_id = None
        if settings.general.use_sportarr:
            Thread(target=self.start, daemon=True).start()

    @staticmethod
    def _close_response(response):
        # Shutdown wakes a reader blocked while waiting for the next frame.
        try:
            response.raw.shutdown()
        except (AttributeError, ValueError, RuntimeError, OSError):
            pass
        response.close()

    def connect(self, run_stop):
        url = f"{url_sportarr()}/api/stream?apikey={settings.sportarr.apikey}"
        if self.last_event_id:
            url += f"&since={self.last_event_id}"

        logging.info('BAZARR trying to connect to Sportarr event stream...')
        with Session() as session:
            session.verify = False
            session.headers = HEADERS
            with session.get(url, stream=True, timeout=(10, 60)) as response:
                response.raise_for_status()
                with self._lock:
                    if run_stop.is_set() or self._run_stop is not run_stop:
                        return
                    self._response = response
                    self.connected = True
                logging.info('BAZARR SSE client for Sportarr is connected and waiting for events.')

                try:
                    event_id = None
                    for line in response.iter_lines(decode_unicode=True):
                        if run_stop.is_set():
                            break
                        if not line:
                            continue
                        # Lines opening with a colon are keepalive comments.
                        if line.startswith(':'):
                            continue

                        if line.startswith('id:'):
                            event_id = line[3:].strip()
                        elif line.startswith('data:'):
                            if event_id:
                                with self._lock:
                                    if run_stop.is_set() or self._run_stop is not run_stop:
                                        break
                                    self.last_event_id = event_id
                            self.dispatch(line[5:].strip())
                finally:
                    with self._lock:
                        if self._response is response:
                            self._response = None
                        if self._run_stop is run_stop:
                            self.connected = False

    def dispatch(self, raw):
        try:
            payload = json.loads(raw)
        except ValueError:
            logging.debug('BAZARR could not read a frame from the Sportarr event stream.')
            return

        resource = payload.get('resourceType')
        action = payload.get('action')
        event_id = payload.get('eventId')
        league_id = payload.get('leagueId')

        if resource == 'league':
            if league_id:
                update_one_league(league_id, action='deleted' if action == 'removed' else 'updated')
            return

        if resource not in ('event', 'file'):
            return

        # Every frame names its event, so only that event's league is resynced
        # rather than the whole catalogue.
        if not league_id and event_id:
            league_id = self.league_id_for_event(event_id)

        if not league_id:
            logging.debug('BAZARR received a Sportarr event with no league to sync.')
            return

        sync_events(league_id=league_id)

    @staticmethod
    def league_id_for_event(event_id):
        """Find the league for an event a frame did not name.

        A file frame carries only the event, so the league comes from a row we
        already hold. On a first run there are no rows yet, so Sportarr is
        asked directly rather than dropping the frame.
        """
        row = database.execute(
            select(TableSportsEvents.sportarrLeagueId)
            .where(TableSportsEvents.sportarrEventId == event_id)).first()
        if row:
            return row[0]

        event = get_event_from_sportarr_api(apikey_sportarr=settings.sportarr.apikey, event_id=event_id)
        return event.get('leagueId') if event else None


sportarr_sse_client = SportarrSSEClient()

# coding=utf-8

import json
import logging
import time

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
        self.session = Session()
        self.session.verify = False
        self.session.headers = HEADERS
        self.connected = False
        self.stopped = False
        self.last_event_id = None

    def start(self):
        if not settings.general.use_sportarr:
            return

        self.stopped = False
        while not self.stopped:
            try:
                self.connect()
            except RequestException:
                logging.debug('BAZARR connection to Sportarr event stream was lost.')
            except Exception:
                logging.exception('BAZARR unexpected error reading the Sportarr event stream.')

            if self.stopped:
                break

            self.connected = False
            # Sportarr keeps a window of past events, so reconnecting after a
            # pause still returns what was missed.
            time.sleep(5)

    def stop(self):
        self.stopped = True
        self.connected = False
        logging.info('BAZARR SSE client for Sportarr is now disconnected.')

    def restart(self):
        if self.connected:
            self.stop()
        if settings.general.use_sportarr:
            self.start()

    def connect(self):
        url = f"{url_sportarr()}/api/stream?apikey={settings.sportarr.apikey}"
        if self.last_event_id:
            url += f"&since={self.last_event_id}"

        logging.info('BAZARR trying to connect to Sportarr event stream...')
        with self.session.get(url, stream=True, timeout=(10, None)) as response:
            response.raise_for_status()
            self.connected = True
            logging.info('BAZARR SSE client for Sportarr is connected and waiting for events.')

            event_id = None
            for line in response.iter_lines(decode_unicode=True):
                if self.stopped:
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
                        self.last_event_id = event_id
                    self.dispatch(line[5:].strip())

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

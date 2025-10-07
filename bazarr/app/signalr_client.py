# coding=utf-8

import logging
import json
import time
import threading

from requests import Session
from signalr import Connection
from requests.exceptions import ConnectionError
from signalrcore.hub_connection_builder import HubConnectionBuilder
from collections import deque
from time import sleep

from constants import HEADERS
from app.event_handler import event_stream
from sonarr.sync.episodes import sync_episodes, sync_one_episode
from sonarr.sync.series import update_series, update_one_series
from radarr.sync.movies import update_movies, update_one_movie
from sonarr.info import get_sonarr_info, url_sonarr
from radarr.info import url_radarr
from app.database import TableShows, TableMovies, database, select
from app.jobs_queue import jobs_queue

from .config import settings
from .scheduler import scheduler
from .get_args import args

sonarr_queue = deque()
radarr_queue = deque()

last_event_data = None


class SonarrSignalrClientLegacy:
    def __init__(self):
        super(SonarrSignalrClientLegacy, self).__init__()
        self.apikey_sonarr = None
        self.session = Session()
        self.session.timeout = 60
        self.session.verify = False
        self.session.headers = HEADERS
        self.connection = None
        self.connected = False

    def start(self):
        if get_sonarr_info.is_legacy():
            logging.warning(
                f'BAZARR can only sync from Sonarr v3 SignalR feed to get real-time update. You should consider '
                f'upgrading your version({get_sonarr_info.version()}).')
        else:
            self.connected = False
            event_stream(type='badges')
            logging.info('BAZARR trying to connect to Sonarr SignalR feed...')
            self.configure()
            while not self.connection.started:
                try:
                    self.connection.start()
                except ConnectionError:
                    time.sleep(5)
                except json.decoder.JSONDecodeError:
                    logging.error("BAZARR cannot parse JSON returned by SignalR feed. This is caused by a permissions "
                                  "issue when Sonarr try to access its /config/.config directory."
                                  "Typically permissions are too permissive - only the user and group Sonarr runs as "
                                  "should have Read/Write permissions (e.g. files 664 / folders 775). You should fix "
                                  "permissions on that directory and restart Sonarr. Also, if you're a Docker image "
                                  "user, you should make sure you properly defined PUID/PGID environment variables. "
                                  "Otherwise, please contact Sonarr support.")
                    self.stop()
                    break
                else:
                    self.connected = True
                    event_stream(type='badges')
                    logging.info('BAZARR SignalR client for Sonarr is connected and waiting for events.')
                    if not args.dev:
                        scheduler.add_job(update_series, kwargs={'send_event': True}, max_instances=1)

    def stop(self, log=True):
        try:
            self.connection.close()
        except Exception:
            self.connection.started = False
        if log:
            logging.info('BAZARR SignalR client for Sonarr is now disconnected.')

    def restart(self):
        if self.connection:
            if self.connection.started:
                self.stop(log=False)
        if settings.general.use_sonarr:
            self.start()

    def exception_handler(self):
        sonarr_queue.clear()
        self.connected = False
        event_stream(type='badges')
        logging.error('BAZARR connection to Sonarr SignalR feed has been lost.')
        self.restart()

    def configure(self):
        self.apikey_sonarr = settings.sonarr.apikey
        self.connection = Connection(f"{url_sonarr()}/signalr", self.session)
        self.connection.qs = {'apikey': self.apikey_sonarr}
        sonarr_hub = self.connection.register_hub('')  # Sonarr doesn't use named hub

        sonarr_method = ['series', 'episode']
        for item in sonarr_method:
            sonarr_hub.client.on(item, feed_queue)

        self.connection.exception += self.exception_handler


class SonarrSignalrClient:
    def __init__(self):
        super(SonarrSignalrClient, self).__init__()
        self.apikey_sonarr = None
        self.connection = None
        self.connected = False

    def start(self):
        self.configure()
        logging.info('BAZARR trying to connect to Sonarr SignalR feed...')
        while self.connection.transport.state.value not in [0, 1, 2]:
            try:
                self.connection.start()
            except ConnectionError:
                time.sleep(5)

    def stop(self):
        logging.info('BAZARR SignalR client for Sonarr is now disconnected.')
        self.connection.stop()

    def restart(self):
        if self.connection:
            if self.connection.transport.state.value in [0, 1, 2]:
                self.stop()
        if settings.general.use_sonarr:
            self.start()

    def exception_handler(self):
        sonarr_queue.clear()
        self.connected = False
        event_stream(type='badges')
        logging.error("BAZARR connection to Sonarr SignalR feed has failed. We'll try to reconnect.")
        self.restart()

    def on_connect_handler(self):
        self.connected = True
        event_stream(type='badges')
        logging.info('BAZARR SignalR client for Sonarr is connected and waiting for events.')
        if not args.dev:
            scheduler.add_job(update_series, kwargs={'send_event': True}, max_instances=1)

    def on_reconnect_handler(self):
        self.connected = False
        event_stream(type='badges')
        logging.error('BAZARR SignalR client for Sonarr connection as been lost. Trying to reconnect...')

    def configure(self):
        self.apikey_sonarr = settings.sonarr.apikey
        self.connection = HubConnectionBuilder() \
            .with_url(f"{url_sonarr()}/signalr/messages?access_token={self.apikey_sonarr}",
                      options={
                          "verify_ssl": False,
                          "headers": HEADERS
                      }) \
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 5,
                "reconnect_interval": 180,
                "max_attempts": None
            }).build()
        self.connection.on_open(self.on_connect_handler)
        self.connection.on_reconnect(self.on_reconnect_handler)
        self.connection.on_close(lambda: logging.debug('BAZARR SignalR client for Sonarr is disconnected.'))
        self.connection.on_error(self.exception_handler)
        self.connection.on("receiveMessage", feed_queue)


class RadarrSignalrClient:
    def __init__(self):
        super(RadarrSignalrClient, self).__init__()
        self.apikey_radarr = None
        self.connection = None
        self.connected = False

    def start(self):
        self.configure()
        logging.info('BAZARR trying to connect to Radarr SignalR feed...')
        while self.connection.transport.state.value not in [0, 1, 2]:
            try:
                self.connection.start()
            except ConnectionError:
                time.sleep(5)

    def stop(self):
        logging.info('BAZARR SignalR client for Radarr is now disconnected.')
        self.connection.stop()

    def restart(self):
        if self.connection:
            if self.connection.transport.state.value in [0, 1, 2]:
                self.stop()
        if settings.general.use_radarr:
            self.start()

    def exception_handler(self):
        radarr_queue.clear()
        self.connected = False
        event_stream(type='badges')
        logging.error("BAZARR connection to Radarr SignalR feed has failed. We'll try to reconnect.")
        self.restart()

    def on_connect_handler(self):
        self.connected = True
        event_stream(type='badges')
        logging.info('BAZARR SignalR client for Radarr is connected and waiting for events.')
        if not args.dev:
            scheduler.add_job(update_movies, kwargs={'send_event': True}, max_instances=1)

    def on_reconnect_handler(self):
        self.connected = False
        event_stream(type='badges')
        logging.error('BAZARR SignalR client for Radarr connection as been lost. Trying to reconnect...')

    def configure(self):
        self.apikey_radarr = settings.radarr.apikey
        self.connection = HubConnectionBuilder() \
            .with_url(f"{url_radarr()}/signalr/messages?access_token={self.apikey_radarr}",
                      options={
                          "verify_ssl": False,
                          "headers": HEADERS
                      }) \
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 5,
                "reconnect_interval": 180,
                "max_attempts": None
            }).build()
        self.connection.on_open(self.on_connect_handler)
        self.connection.on_reconnect(self.on_reconnect_handler)
        self.connection.on_close(lambda: logging.debug('BAZARR SignalR client for Radarr is disconnected.'))
        self.connection.on_error(self.exception_handler)
        self.connection.on("receiveMessage", feed_queue)


def dispatcher(data):
    try:
        series_title = series_year = episode_title = season_number = episode_number = movie_title = movie_year = None

        #
        try:
            episodesChanged = False
            topic = data['name']

            media_id = data['body']['resource']['id']
            action = data['body']['action']
            if topic == 'series':
                if 'episodesChanged' in data['body']['resource']:
                    episodesChanged = data['body']['resource']['episodesChanged']
                series_title = data['body']['resource']['title']
                series_year = data['body']['resource']['year']
            elif topic == 'episode':
                if 'series' in data['body']['resource']:
                    series_title = data['body']['resource']['series']['title']
                    series_year = data['body']['resource']['series']['year']
                else:
                    series_metadata = database.execute(
                        select(TableShows.title, TableShows.year)
                        .where(TableShows.sonarrSeriesId == data['body']['resource']['seriesId'])) \
                        .first()
                    if series_metadata:
                        series_title = series_metadata.title
                        series_year = series_metadata.year
                episode_title = data['body']['resource']['title']
                season_number = data['body']['resource']['seasonNumber']
                episode_number = data['body']['resource']['episodeNumber']
            elif topic == 'movie':
                if action == 'deleted':
                    existing_movie_details = database.execute(
                        select(TableMovies.title, TableMovies.year)
                        .where(TableMovies.radarrId == media_id)) \
                        .first()
                    if existing_movie_details:
                        movie_title = existing_movie_details.title
                        movie_year = existing_movie_details.year
                    else:
                        return
                else:
                    movie_title = data['body']['resource']['title']
                    movie_year = data['body']['resource']['year']
        except KeyError:
            return

        if topic == 'series':
            logging.debug(f'Event received from Sonarr for series: {series_title} ({series_year})')
            jobs_queue.feed_jobs_pending_queue(f'Update series {series_title} ({series_year})',
                                               'sonarr.sync.series',
                                               'update_one_series',
                                               [],
                                               {'series_id': media_id, 'action': action,
                                                'defer_search': settings.sonarr.defer_search_signalr})
            if episodesChanged:
                # this will happen if a season's monitored status is changed.
                jobs_queue.feed_jobs_pending_queue(f'Sync episodes for series {series_title} ({series_year})',
                                                   'sonarr.sync.episodes',
                                                   'sync_episodes',
                                                   [],
                                                   {'series_id': media_id, 'send_event': True,
                                                    'defer_search': settings.sonarr.defer_search_signalr})
        elif topic == 'episode':
            logging.debug(f'Event received from Sonarr for episode: {series_title} ({series_year}) - '
                          f'S{season_number:0>2}E{episode_number:0>2} - {episode_title}')
            jobs_queue.feed_jobs_pending_queue(f'Sync episode {series_title} ({series_year}) - S{season_number:0>2}E'
                                               f'{episode_number:0>2} - {episode_title}',
                                               'sonarr.sync.episodes',
                                               'sync_one_episode',
                                               [],
                                               {'episode_id': media_id,
                                                'defer_search': settings.sonarr.defer_search_signalr})
        elif topic == 'movie':
            logging.debug(f'Event received from Radarr for movie: {movie_title} ({movie_year})')
            jobs_queue.feed_jobs_pending_queue(f'Update movie {movie_title} ({movie_year})',
                                               'radarr.sync.movies',
                                               'update_one_movie',
                                               [],
                                               {'movie_id': media_id, 'action': action,
                                                'defer_search': settings.radarr.defer_search_signalr})
    except Exception as e:
        logging.debug(f'BAZARR an exception occurred while parsing SignalR feed: {repr(e)}')
    finally:
        event_stream(type='badges')
        return


def feed_queue(data):
    # check if event is duplicate from the previous one
    global last_event_data
    if data == last_event_data:
        return
    else:
        last_event_data = data

    # some sonarr version sends events as a list of a single dict, we make it a dict
    if isinstance(data, list) and len(data):
        data = data[0]

    # if data is a dict and contain an event for series, episode or movie, we add it to the event queue
    if isinstance(data, dict) and 'name' in data:
        if data['name'] in ['series', 'episode']:
            sonarr_queue.append(data)
        elif data['name'] == 'movie':
            radarr_queue.append(data)


def consume_queue(queue):
    # get events data from queues one at a time and dispatch it
    while True:
        try:
            data = queue.popleft()
        except IndexError:
            pass
        except (KeyboardInterrupt, SystemExit):
            break
        else:
            dispatcher(data)
        sleep(0.1)


# start both queues consuming threads
sonarr_queue_thread = threading.Thread(target=consume_queue, args=(sonarr_queue,))
sonarr_queue_thread.daemon = True
sonarr_queue_thread.start()
radarr_queue_thread = threading.Thread(target=consume_queue, args=(radarr_queue,))
radarr_queue_thread.daemon = True
radarr_queue_thread.start()

# instantiate proper SignalR client
sonarr_signalr_client = SonarrSignalrClientLegacy() if get_sonarr_info.version().startswith(('0.', '2.', '3.')) else \
    SonarrSignalrClient()
radarr_signalr_client = RadarrSignalrClient()

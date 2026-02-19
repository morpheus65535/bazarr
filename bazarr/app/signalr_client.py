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
from radarr.info import url_radarr, url_radarr_from_instance
from app.database import TableShows, TableMovies, TableRadarrInstances, database, select
from app.jobs_queue import jobs_queue

from .config import settings
from .scheduler import scheduler
from .get_args import args

sonarr_queue = deque()
radarr_queue = deque()

last_series_event_data = None
last_episode_event_data = None
last_movie_event_data = None


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
                    if settings.sonarr.series_sync_on_live:
                        scheduler.execute_job_now(taskid="update_series")

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
        if settings.sonarr.series_sync_on_live:
            scheduler.execute_job_now(taskid="update_series")

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
    """SignalR client for a single Radarr instance."""

    def __init__(self, instance=None):
        """
        Args:
            instance: dict from TableRadarrInstances.to_dict(). If None, uses primary settings.
        """
        super(RadarrSignalrClient, self).__init__()
        self.instance = instance
        self.instance_id = instance['id'] if instance else 1
        self.apikey_radarr = None
        self.connection = None
        self.connected = False

    def _get_base_url(self):
        if self.instance:
            return url_radarr_from_instance(self.instance)
        return url_radarr()

    def _get_apikey(self):
        if self.instance:
            return self.instance.get('apikey', settings.radarr.apikey)
        return settings.radarr.apikey

    def _get_movies_sync_on_live(self):
        if self.instance:
            return bool(self.instance.get('movies_sync_on_live', 1))
        return settings.radarr.movies_sync_on_live

    def start(self):
        self.configure()
        logging.info(f'BAZARR trying to connect to Radarr SignalR feed (instance {self.instance_id})...')
        while self.connection.transport.state.value not in [0, 1, 2]:
            try:
                self.connection.start()
            except ConnectionError:
                time.sleep(5)

    def stop(self):
        logging.info(f'BAZARR SignalR client for Radarr instance {self.instance_id} is now disconnected.')
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
        logging.error(f"BAZARR connection to Radarr SignalR feed (instance {self.instance_id}) has failed. "
                      f"We'll try to reconnect.")
        self.restart()

    def on_connect_handler(self):
        self.connected = True
        event_stream(type='badges')
        logging.info(f'BAZARR SignalR client for Radarr instance {self.instance_id} is connected and waiting for events.')
        if self._get_movies_sync_on_live():
            scheduler.execute_job_now(taskid="update_movies")

    def on_reconnect_handler(self):
        self.connected = False
        event_stream(type='badges')
        logging.error(f'BAZARR SignalR client for Radarr instance {self.instance_id} connection has been lost. '
                      f'Trying to reconnect...')

    def configure(self):
        self.apikey_radarr = self._get_apikey()
        base_url = self._get_base_url()
        instance_id = self.instance_id

        def _feed_queue_with_instance(data):
            feed_queue(data, radarr_instance_id=instance_id)

        self.connection = HubConnectionBuilder() \
            .with_url(f"{base_url}/signalr/messages?access_token={self.apikey_radarr}",
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
        self.connection.on_close(lambda: logging.debug(
            f'BAZARR SignalR client for Radarr instance {self.instance_id} is disconnected.'))
        self.connection.on_error(self.exception_handler)
        self.connection.on("receiveMessage", _feed_queue_with_instance)


class RadarrSignalrManager:
    """Manages multiple RadarrSignalrClient instances (one per Radarr instance).

    Provides a backward-compatible interface with a single .connected property
    and .start()/.restart() methods.
    """

    def __init__(self):
        # dict mapping instance_id -> RadarrSignalrClient
        self._clients: dict = {}

    @property
    def connected(self):
        """True if any Radarr instance is connected."""
        return any(client.connected for client in self._clients.values())

    def _load_instances(self):
        """Load all enabled Radarr instances from the database."""
        try:
            from app.database import get_radarr_instances
            return get_radarr_instances()
        except Exception as e:
            logging.warning(f"BAZARR Could not load Radarr instances from DB: {e}. "
                            f"Using primary instance from settings.")
            return []

    def start(self):
        """Start SignalR clients for all enabled Radarr instances."""
        instances = self._load_instances()

        if not instances:
            # Fallback: start single client using settings
            client = RadarrSignalrClient(instance=None)
            self._clients[1] = client
            client.start()
            return

        for instance in instances:
            instance_id = instance['id']
            if instance_id not in self._clients:
                client = RadarrSignalrClient(instance=instance)
                self._clients[instance_id] = client
                t = threading.Thread(target=client.start, daemon=True)
                t.start()

    def restart(self):
        """Restart the primary Radarr SignalR client (called when settings change)."""
        if settings.general.use_radarr:
            # Stop and remove existing primary client
            if 1 in self._clients:
                try:
                    self._clients[1].stop()
                except Exception:
                    pass
                del self._clients[1]

            # Reload all instances and restart
            instances = self._load_instances()
            if instances:
                for instance in instances:
                    instance_id = instance['id']
                    if instance_id not in self._clients:
                        client = RadarrSignalrClient(instance=instance)
                        self._clients[instance_id] = client
                        t = threading.Thread(target=client.start, daemon=True)
                        t.start()
            else:
                client = RadarrSignalrClient(instance=None)
                self._clients[1] = client
                t = threading.Thread(target=client.start, daemon=True)
                t.start()

    def add_instance(self, instance):
        """Start a SignalR client for a newly added Radarr instance."""
        instance_id = instance['id']
        if instance_id in self._clients:
            try:
                self._clients[instance_id].stop()
            except Exception:
                pass
        client = RadarrSignalrClient(instance=instance)
        self._clients[instance_id] = client
        t = threading.Thread(target=client.start, daemon=True)
        t.start()

    def remove_instance(self, instance_id):
        """Stop the SignalR client for a removed Radarr instance."""
        if instance_id in self._clients:
            try:
                self._clients[instance_id].stop()
            except Exception:
                pass
            del self._clients[instance_id]


def dispatcher(data):
    try:
        series_title = series_year = episode_title = season_number = episode_number = movie_title = movie_year = None

        # Extract the radarr instance id (injected by feed_queue)
        radarr_instance_id = data.pop('_radarr_instance_id', 1)

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
                        .where(TableMovies.radarrId == media_id)
                        .where(TableMovies.radarr_instance_id == radarr_instance_id)) \
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
            if episodesChanged:
                sync_episodes(series_id=media_id, defer_search=settings.sonarr.defer_search_signalr, is_signalr=True)
            else:
                update_one_series(series_id=media_id, action=action, is_signalr=True)
        elif topic == 'episode':
            logging.debug(f'Event received from Sonarr for episode: {series_title} ({series_year}) - '
                          f'S{season_number:0>2}E{episode_number:0>2} - {episode_title}')
            sync_one_episode(episode_id=media_id, defer_search=settings.sonarr.defer_search_signalr, is_signalr=True)
        elif topic == 'movie':
            logging.debug(f'Event received from Radarr instance {radarr_instance_id} for movie: '
                          f'{movie_title} ({movie_year})')
            update_one_movie(movie_id=media_id, action=action,
                             defer_search=settings.radarr.defer_search_signalr,
                             is_signalr=True,
                             radarr_instance_id=radarr_instance_id)
    except Exception as e:
        logging.debug(f'BAZARR an exception occurred while parsing SignalR feed: {repr(e)}')
    finally:
        event_stream(type='badges')
        return


def filter_nested_dict(data: dict) -> dict:
    """
    Filters out specific keys from a nested dictionary structure.
    """
    keys_to_remove = ['statistics']

    filtered_data = {}

    for key, value in data.items():
        if key not in keys_to_remove:
            if isinstance(value, dict):
                filtered_data[key] = filter_nested_dict(value)
            elif isinstance(value, list):
                filtered_data[key] = [
                    filter_nested_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                filtered_data[key] = value

    return filtered_data


def feed_queue(data, radarr_instance_id=1):
    # some sonarr version sends events as a list of a single dict, we make it a dict
    if isinstance(data, list) and len(data):
        data = data[0]

    if isinstance(data, dict) and 'name' in data and data['name'] in ['series', 'episode', 'movie']:
        data = filter_nested_dict(data)

        # check if event is duplicate from the previous one
        if data['name'] == 'series':
            global last_series_event_data
            if data == last_series_event_data:
                return
            else:
                last_series_event_data = data
        elif data['name'] == 'episode':
            global last_episode_event_data
            if data == last_episode_event_data:
                return
            else:
                last_episode_event_data = data
        elif data['name'] == 'movie':
            global last_movie_event_data
            if data == last_movie_event_data:
                return
            else:
                last_movie_event_data = data

        if isinstance(data, dict) and 'name' in data:
            if data['name'] in ['series', 'episode']:
                sonarr_queue.append(data)
            elif data['name'] == 'movie':
                # Embed the instance_id so dispatcher knows which Radarr sent this
                data['_radarr_instance_id'] = radarr_instance_id
                radarr_queue.append(data)


def consume_queue(queue):
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
radarr_signalr_client = RadarrSignalrManager()

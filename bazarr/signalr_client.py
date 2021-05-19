# coding=utf-8

import logging

import gevent
import json
from requests import Session
from signalr import Connection
from requests.exceptions import ConnectionError
from signalrcore.hub_connection_builder import HubConnectionBuilder

from config import settings, url_sonarr, url_radarr
from get_episodes import sync_episodes, sync_one_episode
from get_series import update_series, update_one_series
from get_movies import update_movies, update_one_movie
from scheduler import scheduler
from utils import get_sonarr_version
from get_args import args


class SonarrSignalrClient:
    def __init__(self):
        super(SonarrSignalrClient, self).__init__()
        self.apikey_sonarr = None
        self.session = Session()
        self.connection = None

    def start(self):
        if get_sonarr_version().startswith('2.'):
            logging.warning('BAZARR can only sync from Sonarr v3 SignalR feed to get real-time update. You should '
                            'consider upgrading.')
            return

        logging.debug('BAZARR connecting to Sonarr SignalR feed...')
        self.configure()
        while not self.connection.is_open:
            try:
                self.connection.start()
            except ConnectionError:
                gevent.sleep(5)
            except json.decoder.JSONDecodeError:
                logging.error('BAZARR cannot parse JSON returned by SignalR feed. Take a look at: '
                              'https://forums.sonarr.tv/t/signalr-problem/5785/3')
                self.stop()
        logging.info('BAZARR SignalR client for Sonarr is connected and waiting for events.')
        if not args.dev:
            scheduler.add_job(update_series, kwargs={'send_event': False}, max_instances=1)
            scheduler.add_job(sync_episodes, kwargs={'send_event': False}, max_instances=1)

    def stop(self, log=True):
        try:
            self.connection.close()
        except Exception as e:
            pass
        if log:
            logging.info('BAZARR SignalR client for Sonarr is now disconnected.')

    def restart(self):
        if self.connection.is_open:
            self.stop(log=False)
        if settings.general.getboolean('use_sonarr'):
            self.start()

    def exception_handler(self, type, exception, traceback):
        logging.error('BAZARR connection to Sonarr SignalR feed has been lost. Reconnecting...')
        self.restart()

    def configure(self):
        self.apikey_sonarr = settings.sonarr.apikey
        self.connection = Connection(url_sonarr() + "/signalr", self.session)
        self.connection.qs = {'apikey': self.apikey_sonarr}
        sonarr_hub = self.connection.register_hub('')  # Sonarr doesn't use named hub

        sonarr_method = ['series', 'episode']
        for item in sonarr_method:
            sonarr_hub.client.on(item, dispatcher)

        self.connection.exception += self.exception_handler


class RadarrSignalrClient:
    def __init__(self):
        super(RadarrSignalrClient, self).__init__()
        self.apikey_radarr = None
        self.connection = None

    def start(self):
        self.configure()
        logging.debug('BAZARR connecting to Radarr SignalR feed...')
        self.connection.start()

    def stop(self):
        logging.info('BAZARR SignalR client for Radarr is now disconnected.')
        self.connection.stop()

    def restart(self):
        if self.connection.transport.state.value in [0, 1, 2]:
            self.stop()
        if settings.general.getboolean('use_radarr'):
            self.start()

    def exception_handler(self):
        logging.error("BAZARR connection to Radarr SignalR feed has failed. We'll try to reconnect.")
        self.restart()

    @staticmethod
    def on_connect_handler():
        logging.info('BAZARR SignalR client for Radarr is connected and waiting for events.')
        if not args.dev:
            scheduler.add_job(update_movies, kwargs={'send_event': False}, max_instances=1)

    def configure(self):
        self.apikey_radarr = settings.radarr.apikey
        self.connection = HubConnectionBuilder() \
            .with_url(url_radarr() + "/signalr/messages?access_token={}".format(self.apikey_radarr),
                      options={
                          "verify_ssl": False
                      }) \
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 15,
                "reconnect_interval": 180,
                "max_attempts": None
            }).build()
        self.connection.on_open(self.on_connect_handler)
        self.connection.on_reconnect(lambda: logging.info('BAZARR SignalR client for Radarr connection as been lost. '
                                                          'Trying to reconnect...'))
        self.connection.on_close(lambda: logging.debug('BAZARR SignalR client for Radarr is disconnected.'))
        self.connection.on_error(self.exception_handler)
        self.connection.on("receiveMessage", dispatcher)


def dispatcher(data):
    topic = media_id = action = None
    if isinstance(data, dict):
        topic = data['name']
        try:
            media_id = data['body']['resource']['id']
            action = data['body']['action']
        except KeyError:
            return
    elif isinstance(data, list):
        topic = data[0]['name']
        try:
            media_id = data[0]['body']['resource']['id']
            action = data[0]['body']['action']
        except KeyError:
            return

    if topic == 'series':
        update_one_series(series_id=media_id, action=action)
    elif topic == 'episode':
        sync_one_episode(episode_id=media_id)
    elif topic == 'movie':
        update_one_movie(movie_id=media_id, action=action)
    else:
        return


sonarr_signalr_client = SonarrSignalrClient()
radarr_signalr_client = RadarrSignalrClient()

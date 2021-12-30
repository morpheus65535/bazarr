# coding=utf-8

import logging

import json
import os
import time
from requests import Session
from signalr import Connection
from requests.exceptions import ConnectionError
from signalrcore.hub_connection_builder import HubConnectionBuilder

from config import settings, url_sonarr, url_radarr
from get_episodes import sync_episodes, sync_one_episode
from get_series import update_series, update_one_series
from get_movies import update_movies, update_one_movie
from scheduler import scheduler
from utils import get_sonarr_info
from get_args import args


headers = {"User-Agent": os.environ["SZ_USER_AGENT"]}


class SonarrSignalrClientLegacy:
    def __init__(self):
        super(SonarrSignalrClientLegacy, self).__init__()
        self.apikey_sonarr = None
        self.session = Session()
        self.session.timeout = 60
        self.session.verify = False
        self.session.headers = headers
        self.connection = None

    def start(self):
        if get_sonarr_info.is_legacy():
            logging.warning('BAZARR can only sync from Sonarr v3 SignalR feed to get real-time update. You should '
                            'consider upgrading your version({}).'.format(get_sonarr_info.version()))
        else:
            logging.info('BAZARR trying to connect to Sonarr SignalR feed...')
            self.configure()
            while not self.connection.started:
                try:
                    self.connection.start()
                except ConnectionError:
                    time.sleep(5)
                except json.decoder.JSONDecodeError:
                    logging.error("BAZARR cannot parse JSON returned by SignalR feed. This is caused by a permissions "
                                  "issue when Sonarr try to access its /config/.config directory. You should fix "
                                  "permissions on that directory and restart Sonarr. Also, if you're a Docker image "
                                  "user, you should make sure you properly defined PUID/PGID environment variables. "
                                  "Otherwise, please contact Sonarr support.")
                else:
                    logging.info('BAZARR SignalR client for Sonarr is connected and waiting for events.')
                finally:
                    if not args.dev:
                        scheduler.add_job(update_series, kwargs={'send_event': True}, max_instances=1)
                        scheduler.add_job(sync_episodes, kwargs={'send_event': True}, max_instances=1)

    def stop(self, log=True):
        try:
            self.connection.close()
        except Exception as e:
            pass
        if log:
            logging.info('BAZARR SignalR client for Sonarr is now disconnected.')

    def restart(self):
        if self.connection:
            if self.connection.started:
                try:
                    self.stop(log=False)
                except:
                    self.connection.started = False
        if settings.general.getboolean('use_sonarr'):
            self.start()

    def exception_handler(self, type, exception, traceback):
        logging.error('BAZARR connection to Sonarr SignalR feed has been lost.')
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


class SonarrSignalrClient:
    def __init__(self):
        super(SonarrSignalrClient, self).__init__()
        self.apikey_sonarr = None
        self.connection = None

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
        if settings.general.getboolean('use_sonarr'):
            self.start()

    def exception_handler(self):
        logging.error("BAZARR connection to Sonarr SignalR feed has failed. We'll try to reconnect.")
        self.restart()

    @staticmethod
    def on_connect_handler():
        logging.info('BAZARR SignalR client for Sonarr is connected and waiting for events.')
        if not args.dev:
            scheduler.add_job(update_series, kwargs={'send_event': True}, max_instances=1)
            scheduler.add_job(sync_episodes, kwargs={'send_event': True}, max_instances=1)

    def configure(self):
        self.apikey_sonarr = settings.sonarr.apikey
        self.connection = HubConnectionBuilder() \
            .with_url(url_sonarr() + "/signalr/messages?access_token={}".format(self.apikey_sonarr),
                      options={
                          "verify_ssl": False,
                          "headers": headers
                      }) \
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 5,
                "reconnect_interval": 180,
                "max_attempts": None
            }).build()
        self.connection.on_open(self.on_connect_handler)
        self.connection.on_reconnect(lambda: logging.error('BAZARR SignalR client for Sonarr connection as been lost. '
                                                           'Trying to reconnect...'))
        self.connection.on_close(lambda: logging.debug('BAZARR SignalR client for Sonarr is disconnected.'))
        self.connection.on_error(self.exception_handler)
        self.connection.on("receiveMessage", dispatcher)


class RadarrSignalrClient:
    def __init__(self):
        super(RadarrSignalrClient, self).__init__()
        self.apikey_radarr = None
        self.connection = None

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
        if settings.general.getboolean('use_radarr'):
            self.start()

    def exception_handler(self):
        logging.error("BAZARR connection to Radarr SignalR feed has failed. We'll try to reconnect.")
        self.restart()

    @staticmethod
    def on_connect_handler():
        logging.info('BAZARR SignalR client for Radarr is connected and waiting for events.')
        if not args.dev:
            scheduler.add_job(update_movies, kwargs={'send_event': True}, max_instances=1)

    def configure(self):
        self.apikey_radarr = settings.radarr.apikey
        self.connection = HubConnectionBuilder() \
            .with_url(url_radarr() + "/signalr/messages?access_token={}".format(self.apikey_radarr),
                      options={
                          "verify_ssl": False,
                          "headers": headers
                      }) \
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 5,
                "reconnect_interval": 180,
                "max_attempts": None
            }).build()
        self.connection.on_open(self.on_connect_handler)
        self.connection.on_reconnect(lambda: logging.error('BAZARR SignalR client for Radarr connection as been lost. '
                                                           'Trying to reconnect...'))
        self.connection.on_close(lambda: logging.debug('BAZARR SignalR client for Radarr is disconnected.'))
        self.connection.on_error(self.exception_handler)
        self.connection.on("receiveMessage", dispatcher)


def dispatcher(data):
    try:
        topic = media_id = action = None
        episodesChanged = None
        if isinstance(data, dict):
            topic = data['name']
            try:
                media_id = data['body']['resource']['id']
                action = data['body']['action']
                if 'episodesChanged' in data['body']['resource']:
                    episodesChanged = data['body']['resource']['episodesChanged']
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
            if episodesChanged:
                # this will happen if a season monitored status is changed.
                sync_episodes(series_id=media_id, send_event=True)
        elif topic == 'episode':
            sync_one_episode(episode_id=media_id)
        elif topic == 'movie':
            update_one_movie(movie_id=media_id, action=action)
    except Exception as e:
        logging.debug('BAZARR an exception occurred while parsing SignalR feed: {}'.format(repr(e)))
    finally:
        return


sonarr_signalr_client = SonarrSignalrClientLegacy() if get_sonarr_info.version().startswith(('0.', '2.', '3.')) else \
    SonarrSignalrClient()
radarr_signalr_client = RadarrSignalrClient()

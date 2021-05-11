# coding=utf-8

import logging

import gevent
import threading
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


class SonarrSignalrClient(threading.Thread):
    def __init__(self):
        super(SonarrSignalrClient, self).__init__()
        self.stopped = True
        self.apikey_sonarr = None
        self.session = Session()
        self.connection = None

    def stop(self):
        self.connection.close()
        self.stopped = True
        logging.info('BAZARR SignalR client for Sonarr is now disconnected.')

    def restart(self):
        if not self.stopped:
            self.stop()
        if settings.general.getboolean('use_sonarr'):
            self.run()

    def run(self):
        if get_sonarr_version().startswith('2.'):
            logging.warning('BAZARR can only sync from Sonarr v3 SignalR feed to get real-time update. You should '
                            'consider upgrading.')
            return
        self.apikey_sonarr = settings.sonarr.apikey
        self.connection = Connection(url_sonarr() + "/signalr", self.session)
        self.connection.qs = {'apikey': self.apikey_sonarr}
        sonarr_hub = self.connection.register_hub('')  # Sonarr doesn't use named hub

        sonarr_method = ['series', 'episode']
        for item in sonarr_method:
            sonarr_hub.client.on(item, dispatcher)

        while True:
            if not self.stopped:
                return
            if self.connection.started:
                gevent.sleep(5)
            else:
                try:
                    logging.debug('BAZARR connecting to Sonarr SignalR feed...')
                    self.connection.start()
                except ConnectionError:
                    logging.error('BAZARR connection to Sonarr SignalR feed has been lost. Reconnecting...')
                    gevent.sleep(15)
                else:
                    self.stopped = False
                    logging.info('BAZARR SignalR client for Sonarr is connected and waiting for events.')
                    if not args.dev:
                        scheduler.execute_job_now('update_series')
                        scheduler.execute_job_now('sync_episodes')
                    gevent.sleep()


class RadarrSignalrClient(threading.Thread):
    def __init__(self):
        super(RadarrSignalrClient, self).__init__()
        self.apikey_radarr = None
        self.connection = None

        self.configure()
        self.start()

    def start(self):
        logging.debug('BAZARR connecting to Radarr SignalR feed...')
        self.connection.start()
        gevent.sleep()

    def stop(self):
        logging.info('BAZARR SignalR client for Radarr is now disconnected.')
        self.connection.stop()

    def restart(self):
        if self.connection.transport.state.value in [0, 1, 2]:
            self.stop()
        if settings.general.getboolean('use_radarr'):
            self.configure()
            self.start()

    def configure(self):
        self.apikey_radarr = settings.radarr.apikey
        self.connection = HubConnectionBuilder() \
            .with_url(url_radarr() + "/signalr/messages?access_token={}".format(self.apikey_radarr),
                      options={
                          "verify_ssl": False
                      }) \
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 5,
                "reconnect_interval": 5,
                "max_attempts": None
            }).build()
        self.connection.on_open(lambda: logging.info('BAZARR SignalR client for Radarr is connected and waiting for '
                                                     'events.'))
        self.connection.on_reconnect(lambda: logging.info('BAZARR SignalR client for Radarr connection as been lost. '
                                                          'Trying to reconnect...'))
        self.connection.on_close(lambda: logging.debug('BAZARR SignalR client for Radarr is disconnected.'))
        self.connection.on_error(lambda data: logging.debug(f"BAZARR SignalR client for Radarr: An exception was thrown"
                                                            f" closed{data.error}"))
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

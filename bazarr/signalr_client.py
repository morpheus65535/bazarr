# coding=utf-8

import logging
from requests import Session
from signalr import Connection
from requests.exceptions import ConnectionError
from signalrcore.hub_connection_builder import HubConnectionBuilder

from config import settings, url_sonarr, url_radarr
from get_episodes import sync_episodes, sync_one_episode
from get_series import update_series, update_one_series
from get_movies import update_movies, update_one_movie
from scheduler import scheduler


class SonarrSignalrClient:
    def __init__(self):
        self.apikey_sonarr = settings.sonarr.apikey
        self.session = Session()
        self.connection = None

    def start(self):
        self.connection = Connection(url_sonarr() + "/signalr", self.session)
        self.connection.qs = {'apikey': self.apikey_sonarr}
        sonarr_hub = self.connection.register_hub('')  # Sonarr doesn't use named hub

        sonarr_method = ['series', 'episode']
        for item in sonarr_method:
            sonarr_hub.client.on(item, dispatcher)

        try:
            self.connection.start()
        except ConnectionError:
            pass
        else:
            logging.debug('BAZARR SignalR client for Sonarr is connected.')
            scheduler.execute_job_now('update_series')
            scheduler.execute_job_now('sync_episodes')


class RadarrSignalrClient:
    def __init__(self):
        self.apikey_radarr = settings.radarr.apikey

    def start(self):
        hub_connection = HubConnectionBuilder() \
            .with_url(url_radarr() + "/signalr/messages?access_token={}".format(self.apikey_radarr),
                      options={
                          "verify_ssl": False
                      }).build()
        hub_connection.on_open(lambda: logging.debug("BAZARR SignalR client for Radarr is connected."))
        hub_connection.on_close(lambda: logging.debug("BAZARR SignalR client for Radarr is disconnected."))
        hub_connection.on_error(lambda data: logging.debug(f"BAZARR SignalR client for Radarr: An exception was thrown "
                                                           f"closed{data.error}"))
        hub_connection.on("receiveMessage", dispatcher)

        try:
            hub_connection.start()
        except ConnectionError:
            pass
        else:
            logging.debug('BAZARR SignalR client for Radarr is connected.')
            scheduler.execute_job_now('update_movies')


def dispatcher(data):
    if isinstance(data, dict):
        topic = data['name']
    elif isinstance(data, list):
        topic = data[0]['name']

    if topic == 'series':
        update_one_series(data)
    elif topic == 'episode':
        sync_one_episode(data)
    elif topic == 'movie':
        update_one_movie(data[0])
    else:
        return


sonarr_signalr_client = SonarrSignalrClient()
radarr_signalr_client = RadarrSignalrClient()

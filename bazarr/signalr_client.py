# coding=utf-8

import logging
from requests import Session
from signalr import Connection
from requests.exceptions import ConnectionError

from config import settings, url_sonarr
from get_episodes import sync_episodes, sync_one_episode
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
            scheduler.add_job(sync_episodes)


def dispatcher(data):
    topic = data['name']
    action = data['body']['action']
    if topic == 'series':
        series_id = data['body']['resource']['id']
        episode_id = None
    elif topic == 'episode':
        sync_one_episode(data, action)


sonarr_signalr_client = SonarrSignalrClient()

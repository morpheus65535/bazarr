# coding=utf-8

import apprise
import os
import logging

from get_args import args
from database import database


def update_notifier():
    # define apprise object
    a = apprise.Apprise()
    
    # Retrieve all of the details
    results = a.details()
    
    notifiers_new = []
    notifiers_old = []
    
    notifiers_current_db = database.execute("SELECT name FROM table_settings_notifier")

    notifiers_current = []
    for notifier in notifiers_current_db:
        notifiers_current.append(notifier['name'])

    for x in results['schemas']:
        if x['service_name'] not in notifiers_current:
            notifiers_new.append(x['service_name'])
            logging.debug('Adding new notifier agent: ' + x['service_name'])
        else:
            notifiers_old.append(x['service_name'])
    notifier_current = [i for i in notifiers_current]
    
    notifiers_to_delete = list(set(notifier_current) - set(notifiers_old))
    
    for notifier_new in notifiers_new:
        database.execute("INSERT INTO table_settings_notifier (name, enabled) VALUES (?, ?)", (notifier_new, 0))
    
    for notifier_to_delete in notifiers_to_delete:
        database.execute("DELETE FROM table_settings_notifier WHERE name=?", (notifier_to_delete,))


def get_notifier_providers():
    providers = database.execute("SELECT name, url FROM table_settings_notifier WHERE enabled=1")
    return providers


def get_series_name(sonarrSeriesId):
    data = database.execute("SELECT title FROM table_shows WHERE sonarrSeriesId=?", (sonarrSeriesId,), only_one=True)
    
    return data['title'] or None


def get_episode_name(sonarrEpisodeId):
    data = database.execute("SELECT title, season, episode FROM table_episodes WHERE sonarrEpisodeId=?",
                            (sonarrEpisodeId,), only_one=True)
    
    return data['title'], data['season'], data['episode']


def get_movies_name(radarrId):
    data = database.execute("SELECT title FROM table_movies WHERE radarrId=?", (radarrId,), only_one=True)

    return data['title']


def send_notifications(sonarrSeriesId, sonarrEpisodeId, message):
    providers = get_notifier_providers()
    series = get_series_name(sonarrSeriesId)
    episode = get_episode_name(sonarrEpisodeId)
    
    apobj = apprise.Apprise()
    
    for provider in providers:
        if provider['url'] is not None:
            apobj.add(provider['url'])
    
    apobj.notify(
        title='Bazarr notification',
        body=(series + ' - S' + str(episode[1]).zfill(2) + 'E' + str(episode[2]).zfill(2) + ' - ' + episode[0] + ' : ' + message),
    )


def send_notifications_movie(radarrId, message):
    providers = get_notifier_providers()
    movie = get_movies_name(radarrId)
    
    apobj = apprise.Apprise()
    
    for provider in providers:
        if provider['url'] is not None:
            apobj.add(provider['url'])
    
    apobj.notify(
        title='Bazarr notification',
        body=movie + ' : ' + message,
    )

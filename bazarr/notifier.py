# coding=utf-8

import apprise
import os
import logging

from get_args import args
from database import TableSettingsNotifier, TableShows, TableEpisodes, TableMovies


def update_notifier():
    # define apprise object
    a = apprise.Apprise()
    
    # Retrieve all of the details
    results = a.details()
    
    notifiers_new = []
    notifiers_old = []
    
    notifiers_current_db = TableSettingsNotifier.select(
        TableSettingsNotifier.name
    )

    notifiers_current = []
    for notifier in notifiers_current_db:
        notifiers_current.append(notifier.name)

    for x in results['schemas']:
        if x['service_name'] not in notifiers_current:
            notifiers_new.append(x['service_name'])
            logging.debug('Adding new notifier agent: ' + x['service_name'])
        else:
            notifiers_old.append(x['service_name'])
    notifier_current = [i for i in notifiers_current]
    
    notifiers_to_delete = list(set(notifier_current) - set(notifiers_old))
    
    for notifier_new in notifiers_new:
        TableSettingsNotifier.insert(
            {
                TableSettingsNotifier.name: notifier_new,
                TableSettingsNotifier.enabled: 0
            }
        ).execute()
    
    for notifier_to_delete in notifiers_to_delete:
        TableSettingsNotifier.delete().where(
            TableSettingsNotifier.name == notifier_to_delete
        ).execute()


def get_notifier_providers():
    providers = TableSettingsNotifier.select(
        TableSettingsNotifier.name,
        TableSettingsNotifier.url
    ).where(
        TableSettingsNotifier.enabled == 1
    )
    
    return providers


def get_series_name(sonarrSeriesId):
    data = TableShows.select(
        TableShows.title
    ).where(
        TableShows.sonarr_series_id == sonarrSeriesId
    ).first()
    
    return data.title


def get_episode_name(sonarrEpisodeId):
    data = TableEpisodes.select(
        TableEpisodes.title,
        TableEpisodes.season,
        TableEpisodes.episode
    ).where(
        TableEpisodes.sonarr_episode_id == sonarrEpisodeId
    ).first()
    
    return data.title, data.season, data.episode


def get_movies_name(radarrId):
    data = TableMovies.select(
        TableMovies.title
    ).where(
        TableMovies.radarr_id == radarrId
    ).first()
    
    return data.title


def send_notifications(sonarrSeriesId, sonarrEpisodeId, message):
    providers = get_notifier_providers()
    series = get_series_name(sonarrSeriesId)
    episode = get_episode_name(sonarrEpisodeId)
    
    apobj = apprise.Apprise()
    
    for provider in providers:
        if provider.url is not None:
            apobj.add(provider.url)
    
    apobj.notify(
        title='Bazarr notification',
        body=(series + ' - S' + str(episode[1]).zfill(2) + 'E' + str(episode[2]).zfill(2) + ' - ' + episode[0] + ' : ' + message),
    )


def send_notifications_movie(radarrId, message):
    providers = get_notifier_providers()
    movie = get_movies_name(radarrId)
    
    apobj = apprise.Apprise()
    
    for provider in providers:
        if provider.url is not None:
            apobj.add(provider.url)
    
    apobj.notify(
        title='Bazarr notification',
        body=movie + ' : ' + message,
    )

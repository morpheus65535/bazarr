# coding=utf-8

import apprise
import logging

from database import TableSettingsNotifier, TableEpisodes, TableShows, TableMovies


def update_notifier():
    # define apprise object
    a = apprise.Apprise()

    # Retrieve all of the details
    results = a.details()

    notifiers_new = []
    notifiers_old = []

    notifiers_current_db = TableSettingsNotifier.select(TableSettingsNotifier.name).dicts()

    notifiers_current = []
    for notifier in notifiers_current_db:
        notifiers_current.append([notifier['name']])

    for x in results['schemas']:
        if [str(x['service_name'])] not in notifiers_current:
            notifiers_new.append({'name': str(x['service_name']), 'enabled': 0})
            logging.debug('Adding new notifier agent: ' + str(x['service_name']))
        else:
            notifiers_old.append([str(x['service_name'])])

    notifiers_to_delete = [item for item in notifiers_current if item not in notifiers_old]

    TableSettingsNotifier.insert_many(notifiers_new).execute()

    for item in notifiers_to_delete:
        TableSettingsNotifier.delete().where(TableSettingsNotifier.name == item).execute()


def get_notifier_providers():
    providers = TableSettingsNotifier.select(TableSettingsNotifier.name,
                                             TableSettingsNotifier.url)\
        .where(TableSettingsNotifier.enabled == 1)\
        .dicts()

    return providers


def get_series(sonarr_series_id):
    data = TableShows.select(TableShows.title, TableShows.year)\
        .where(TableShows.sonarrSeriesId == sonarr_series_id)\
        .dicts()\
        .get()

    return {'title': data['title'], 'year': data['year']}


def get_episode_name(sonarr_episode_id):
    data = TableEpisodes.select(TableEpisodes.title, TableEpisodes.season, TableEpisodes.episode)\
        .where(TableEpisodes.sonarrEpisodeId == sonarr_episode_id)\
        .dicts()\
        .get()

    return data['title'], data['season'], data['episode']


def get_movie(radarr_id):
    data = TableMovies.select(TableMovies.title, TableMovies.year)\
        .where(TableMovies.radarrId == radarr_id)\
        .dicts()\
        .get()

    return {'title': data['title'], 'year': data['year']}


def send_notifications(sonarr_series_id, sonarr_episode_id, message):
    providers = get_notifier_providers()
    series = get_series(sonarr_series_id)
    series_title = series['title']
    series_year = series['year']
    if series_year not in [None, '', '0']:
        series_year = ' ({})'.format(series_year)
    else:
        series_year = ''
    episode = get_episode_name(sonarr_episode_id)

    asset = apprise.AppriseAsset(async_mode=False)

    apobj = apprise.Apprise(asset=asset)

    for provider in providers:
        if provider['url'] is not None:
            apobj.add(provider['url'])

    apobj.notify(
        title='Bazarr notification',
        body="{}{} - S{:02d}E{:02d} - {} : {}".format(series_title, series_year, episode[1], episode[2], episode[0],
                                                      message),
    )


def send_notifications_movie(radarr_id, message):
    providers = get_notifier_providers()
    movie = get_movie(radarr_id)
    movie_title = movie['title']
    movie_year = movie['year']
    if movie_year not in [None, '', '0']:
        movie_year = ' ({})'.format(movie_year)
    else:
        movie_year = ''

    asset = apprise.AppriseAsset(async_mode=False)

    apobj = apprise.Apprise(asset=asset)

    for provider in providers:
        if provider['url'] is not None:
            apobj.add(provider['url'])

    apobj.notify(
        title='Bazarr notification',
        body="{}{} : {}".format(movie_title, movie_year, message),
    )

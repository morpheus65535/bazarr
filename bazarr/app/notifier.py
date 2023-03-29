# coding=utf-8

import apprise
import logging

from .database import TableSettingsNotifier, TableEpisodes, TableShows, TableMovies, database, rows_as_list_of_dicts, \
    insert, delete


def update_notifier():
    # define apprise object
    a = apprise.Apprise()

    # Retrieve all of the details
    results = a.details()

    notifiers_added = []
    notifiers_kept = []

    notifiers_in_db = [row.name for row in database.query(TableSettingsNotifier.name)]

    for x in results['schemas']:
        if x['service_name'] not in notifiers_in_db:
            notifiers_added.append({'name': str(x['service_name']), 'enabled': 0})
            logging.debug('Adding new notifier agent: ' + str(x['service_name']))
        else:
            notifiers_kept.append(x['service_name'])

    notifiers_to_delete = [item for item in notifiers_in_db if item not in notifiers_kept]

    for item in notifiers_to_delete:
        database.execute(delete(TableSettingsNotifier).where(TableSettingsNotifier.name == item))

    database.execute(insert(TableSettingsNotifier).values(notifiers_added))

    database.commit()


def get_notifier_providers():
    providers = rows_as_list_of_dicts(database.query(TableSettingsNotifier.name,
                                                     TableSettingsNotifier.url)
                                      .where(TableSettingsNotifier.enabled == 1))

    return providers


def get_series(sonarr_series_id):
    data = database.query(TableShows.title, TableShows.year)\
        .where(TableShows.sonarrSeriesId == sonarr_series_id).first()

    if not data:
        return

    return {'title': data.title, 'year': data.year}


def get_episode_name(sonarr_episode_id):
    data = database.query(TableEpisodes.title, TableEpisodes.season, TableEpisodes.episode)\
        .where(TableEpisodes.sonarrEpisodeId == sonarr_episode_id).first()

    if not data:
        return

    return data.title, data.season, data.episode


def get_movie(radarr_id):
    data = database.query(TableMovies.title, TableMovies.year).where(TableMovies.radarrId == radarr_id).first()

    if not data:
        return

    return {'title': data.title, 'year': data.year}


def send_notifications(sonarr_series_id, sonarr_episode_id, message):
    providers = get_notifier_providers()
    if not len(providers):
        return
    series = get_series(sonarr_series_id)
    if not series:
        return
    series_title = series['title']
    series_year = series['year']
    if series_year not in [None, '', '0']:
        series_year = ' ({})'.format(series_year)
    else:
        series_year = ''
    episode = get_episode_name(sonarr_episode_id)
    if not episode:
        return

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
    if not len(providers):
        return
    movie = get_movie(radarr_id)
    if not movie:
        return
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

# coding=utf-8

import apprise
import logging

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
        notifiers_current.append([notifier['name']])

    for x in results['schemas']:
        if [x['service_name']] not in notifiers_current:
            notifiers_new.append([x['service_name'], 0])
            logging.debug('Adding new notifier agent: ' + x['service_name'])
        else:
            notifiers_old.append([x['service_name']])

    notifiers_to_delete = [item for item in notifiers_current if item not in notifiers_old]

    database.execute("INSERT INTO table_settings_notifier (name, enabled) VALUES (?, ?)", notifiers_new,
                     execute_many=True)

    database.execute("DELETE FROM table_settings_notifier WHERE name=?", notifiers_to_delete, execute_many=True)


def get_notifier_providers():
    providers = database.execute("SELECT name, url FROM table_settings_notifier WHERE enabled=1")

    return providers


def get_series(sonarr_series_id):
    data = database.execute("SELECT title, year FROM table_shows WHERE sonarrSeriesId=?", (sonarr_series_id,),
                            only_one=True)

    return {'title': data['title'], 'year': data['year']}


def get_episode_name(sonarr_episode_id):
    data = database.execute("SELECT title, season, episode FROM table_episodes WHERE sonarrEpisodeId=?",
                            (sonarr_episode_id,), only_one=True)

    return data['title'], data['season'], data['episode']


def get_movie(radarr_id):
    data = database.execute("SELECT title, year FROM table_movies WHERE radarrId=?", (radarr_id,), only_one=True)

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

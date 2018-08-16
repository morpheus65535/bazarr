from get_argv import config_dir

import apprise
import os
import sqlite3

def get_notifier_providers():
    conn_db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    providers = c_db.execute('SELECT name, url FROM table_settings_notifier WHERE enabled = 1').fetchall()
    c_db.close()

    return providers

def get_series_name(sonarrSeriesId):
    conn_db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    data = c_db.execute('SELECT title FROM table_shows WHERE sonarrSeriesId = ?', (sonarrSeriesId,)).fetchone()
    c_db.close()

    return data[0]

def get_episode_name(sonarrEpisodeId):
    conn_db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    data = c_db.execute('SELECT title FROM table_episodes WHERE sonarrEpisodeId = ?', (sonarrEpisodeId,)).fetchone()
    c_db.close()

    return data[0]

def get_movies_name(radarrId):
    conn_db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    data = c_db.execute('SELECT title FROM table_movies WHERE radarrId = ?', (radarrId,)).fetchone()
    c_db.close()

    return data[0]

def send_notifications(sonarrSeriesId, sonarrEpisodeId, message):
    providers = get_notifier_providers()
    series = get_series_name(sonarrSeriesId)
    episode = get_episode_name(sonarrEpisodeId)

    apobj = apprise.Apprise()

    for provider in providers:
        if provider[1] is not None:
            apobj.add(provider[1])

    apobj.notify(
        title='Bazarr notification',
        body=series + ' - ' + episode + ' : ' + message,
    )


def send_notifications_movie(radarrId, message):
    providers = get_notifier_providers()
    movie = get_movies_name(radarrId)

    apobj = apprise.Apprise()

    for provider in providers:
        if provider[1] is not None:
            apobj.add(provider[1])

    apobj.notify(
        title='Bazarr notification',
        body=movie + ' : ' + message,
    )
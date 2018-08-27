from get_argv import config_dir

import apprise
import os
import sqlite3
import ast

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

def get_season(sonarrEpisodeId):
    conn_db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    data = c_db.execute('SELECT season FROM table_episodes WHERE sonarrEpisodeId = ?', (sonarrEpisodeId,)).fetchone()
    c_db.close()

    return data[0]

def get_episode(sonarrEpisodeId):
    conn_db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    data = c_db.execute('SELECT episode FROM table_episodes WHERE sonarrEpisodeId = ?', (sonarrEpisodeId,)).fetchone()
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
    episode_name = get_episode_name(sonarrEpisodeId)
    season = str(get_season(sonarrEpisodeId))
    episode = str(get_episode(sonarrEpisodeId))
    
    if len(season) == 1:
        season = '0' + season
        
    if len(episode) == 1:
        episode = '0' + episode

    apobj = apprise.Apprise()

    for provider in providers:
        if provider[1] is not None:
            apobj.add(provider[1])

    apobj.notify(
        title='Bazarr notification',
        body=(series + ' - S' + season + 'E' + episode + ' - ' + episode_name + ' : ' + message),
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
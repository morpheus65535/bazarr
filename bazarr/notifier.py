# coding=utf-8

import apprise
import os
import sqlite3
import logging

from get_args import args


def update_notifier():
    # define apprise object
    a = apprise.Apprise()
    
    # Retrieve all of the details
    results = a.details()
    
    notifiers_new = []
    notifiers_old = []
    
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    notifiers_current = c_db.execute('SELECT name FROM table_settings_notifier').fetchall()
    for x in results['schemas']:
        if x['service_name'] not in str(notifiers_current):
            notifiers_new.append(x['service_name'])
            logging.debug('Adding new notifier agent: ' + x['service_name'])
        else:
            notifiers_old.append(x['service_name'])
    notifier_current = [i[0] for i in notifiers_current]
    
    notifiers_to_delete = list(set(notifier_current) - set(notifiers_old))
    
    for notifier_new in notifiers_new:
        c_db.execute('INSERT INTO `table_settings_notifier` (name, enabled) VALUES (?, ?);', (notifier_new, '0'))
    
    for notifier_to_delete in notifiers_to_delete:
        c_db.execute('DELETE FROM `table_settings_notifier` WHERE name=?', (notifier_to_delete,))
    
    conn_db.commit()
    c_db.close()


def get_notifier_providers():
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    providers = c_db.execute('SELECT name, url FROM table_settings_notifier WHERE enabled = 1').fetchall()
    c_db.close()
    
    return providers


def get_series_name(sonarrSeriesId):
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    data = c_db.execute('SELECT title FROM table_shows WHERE sonarrSeriesId = ?', (sonarrSeriesId,)).fetchone()
    c_db.close()
    
    return data[0]


def get_episode_name(sonarrEpisodeId):
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    data = c_db.execute('SELECT title, season, episode FROM table_episodes WHERE sonarrEpisodeId = ?',
                        (sonarrEpisodeId,)).fetchone()
    c_db.close()
    
    return data[0], data[1], data[2]


def get_movies_name(radarrId):
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
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
        body=(series + ' - S' + str(episode[1]).zfill(2) + 'E' + str(episode[2]).zfill(2) + ' - ' + episode[
            0] + ' : ' + message),
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

# coding=utf-8
import os
import sqlite3
import requests
import logging
from queueconfig import q4ws

from get_argv import config_dir
from config import settings, url_sonarr
from helper import path_replace
from list_subtitles import list_missing_subtitles, store_subtitles, series_full_scan_subtitles, movies_full_scan_subtitles


def update_all_episodes():
    series_full_scan_subtitles()
    logging.info('BAZARR All existing episode subtitles indexed from disk.')
    list_missing_subtitles()
    logging.info('BAZARR All missing episode subtitles updated in database.')


def update_all_movies():
    movies_full_scan_subtitles()
    logging.info('BAZARR All existing movie subtitles indexed from disk.')
    list_missing_subtitles()
    logging.info('BAZARR All missing movie subtitles updated in database.')


def sync_episodes():
    q4ws.append('Episodes sync from Sonarr started...')
    logging.debug('BAZARR Starting episodes sync from Sonarr.')
    apikey_sonarr = settings.sonarr.apikey
    
    # Open database connection
    db = sqlite3.connect(os.path.join(config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()

    # Get current episodes id in DB
    current_episodes_db = c.execute('SELECT sonarrEpisodeId FROM table_episodes').fetchall()

    current_episodes_db_list = [x[0] for x in current_episodes_db]
    current_episodes_sonarr = []
    episodes_to_update = []
    episodes_to_add = []

    # Get sonarrId for each series from database
    seriesIdList = c.execute("SELECT sonarrSeriesId, title FROM table_shows").fetchall()

    # Close database connection
    c.close()

    for seriesId in seriesIdList:
        q4ws.append('Getting episodes data for this show: ' + seriesId[1])
        # Get episodes data for a series from Sonarr
        url_sonarr_api_episode = url_sonarr + "/api/episode?seriesId=" + str(seriesId[0]) + "&apikey=" + apikey_sonarr
        try:
            r = requests.get(url_sonarr_api_episode, timeout=15, verify=False)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logging.exception("BAZARR Error trying to get episodes from Sonarr. Http error.")
        except requests.exceptions.ConnectionError as errc:
            logging.exception("BAZARR Error trying to get episodes from Sonarr. Connection Error.")
        except requests.exceptions.Timeout as errt:
            logging.exception("BAZARR Error trying to get episodes from Sonarr. Timeout Error.")
        except requests.exceptions.RequestException as err:
            logging.exception("BAZARR Error trying to get episodes from Sonarr.")
        else:
            for episode in r.json():
                if 'hasFile' in episode:
                    if episode['hasFile'] is True:
                        if 'episodeFile' in episode:
                            if episode['episodeFile']['size'] > 20480:
                                # Add shows in Sonarr to current shows list
                                if 'sceneName' in episode['episodeFile']:
                                    sceneName = episode['episodeFile']['sceneName']
                                else:
                                    sceneName = None

                                # Add episodes in sonarr to current episode list
                                current_episodes_sonarr.append(episode['id'])

                                if episode['id'] in current_episodes_db_list:
                                    episodes_to_update.append((episode['title'], episode['episodeFile']['path'], episode['seasonNumber'], episode['episodeNumber'], sceneName, str(bool(episode['monitored'])), episode['id']))
                                else:
                                    episodes_to_add.append((episode['seriesId'], episode['id'], episode['title'], episode['episodeFile']['path'], episode['seasonNumber'], episode['episodeNumber'], sceneName, str(bool(episode['monitored']))))

    removed_episodes = list(set(current_episodes_db_list) - set(current_episodes_sonarr))

    # Update or insert movies in DB
    db = sqlite3.connect(os.path.join(config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()

    updated_result = c.executemany('''UPDATE table_episodes SET title = ?, path = ?, season = ?, episode = ?, scene_name = ?, monitored = ? WHERE sonarrEpisodeId = ?''', episodes_to_update)
    db.commit()

    added_result = c.executemany('''INSERT OR IGNORE INTO table_episodes(sonarrSeriesId, sonarrEpisodeId, title, path, season, episode, scene_name, monitored) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', episodes_to_add)
    db.commit()

    for removed_episode in removed_episodes:
        c.execute('DELETE FROM table_episodes WHERE sonarrEpisodeId = ?', (removed_episode,))
        db.commit()

    # Close database connection
    c.close()

    # TODO: Commented until I find a way to make it store only episodes really updated.
    #for updated_episode in episodes_to_update:
    #    store_subtitles(path_replace(updated_episode[1]))

    for added_episode in episodes_to_add:
        store_subtitles(path_replace(added_episode[3]))

    logging.debug('BAZARR All episodes synced from Sonarr into database.')

    list_missing_subtitles()
    logging.debug('BAZARR All missing subtitles updated in database.')

    q4ws.append('Episodes sync from Sonarr ended.')

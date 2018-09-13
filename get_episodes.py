from get_argv import config_dir

import os
import sqlite3
import requests
import logging

from get_settings import path_replace
from list_subtitles import list_missing_subtitles, store_subtitles, series_full_scan_subtitles, movies_full_scan_subtitles
    
def update_all_episodes():
    series_full_scan_subtitles()
    logging.info('All existing episode subtitles indexed from disk.')
    list_missing_subtitles()
    logging.info('All missing episode subtitles updated in database.')

def update_all_movies():
    movies_full_scan_subtitles()
    logging.info('All existing movie subtitles indexed from disk.')
    list_missing_subtitles()
    logging.info('All missing movie subtitles updated in database.')

def sync_episodes():
    logging.debug('Starting episode sync from Sonarr.')
    from get_settings import get_sonarr_settings
    url_sonarr = get_sonarr_settings()[6]
    apikey_sonarr = get_sonarr_settings()[4]
    
    # Open database connection
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()

    # Get current episodes id in DB
    current_episodes_db = c.execute('SELECT sonarrSeriesId, sonarrEpisodeId, title, path, season, episode, scene_name, monitored FROM table_episodes').fetchall()

    # Get sonarrId for each series from database
    current_episodes_sonarr = []
    seriesIdList = c.execute("SELECT sonarrSeriesId FROM table_shows").fetchall()
    for seriesId in seriesIdList:
        # Get episodes data for a series from Sonarr
        url_sonarr_api_episode = url_sonarr + "/api/episode?seriesId=" + str(seriesId[0]) + "&apikey=" + apikey_sonarr
        try:
            r = requests.get(url_sonarr_api_episode, timeout=15, verify=False)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logging.exception("Error trying to get episodes from Sonarr. Http error.")
        except requests.exceptions.ConnectionError as errc:
            logging.exception("Error trying to get episodes from Sonarr. Connection Error.")
        except requests.exceptions.Timeout as errt:
            logging.exception("Error trying to get episodes from Sonarr. Timeout Error.")
        except requests.exceptions.RequestException as err:
            logging.exception("Error trying to get episodes from Sonarr.")
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
                                current_episodes_sonarr.append((episode['seriesId'], episode['id'], episode['title'], episode['episodeFile']['path'], episode['seasonNumber'], episode['episodeNumber'], sceneName, str(bool(episode['monitored']))))

    added_episodes = list(set(current_episodes_sonarr) - set(current_episodes_db))
    removed_episodes = list(set(current_episodes_db) - set(current_episodes_sonarr))

    for removed_episode in removed_episodes:
        c.execute('DELETE FROM table_episodes WHERE sonarrEpisodeId = ?', (removed_episode[1],))
        db.commit()

    for added_episode in added_episodes:
        try:
            c.execute('''INSERT INTO table_episodes(sonarrSeriesId, sonarrEpisodeId, title, path, season, episode, scene_name, monitored) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', added_episode)
        except sqlite3.IntegrityError as e:
            logging.exception("You're probably an early adopter of Bazarr and this is a known issue. Please open an issue on Github and we'll fix this.")
        else:
            db.commit()
            store_subtitles(path_replace(added_episode[3]))

    # Close database connection
    c.close()

    logging.debug('All episodes synced from Sonarr into database.')

    list_missing_subtitles()
    logging.debug('All missing subtitles updated in database.')
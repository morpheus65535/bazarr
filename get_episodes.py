import os
import sqlite3
import requests
import logging

from get_general_settings import *
from list_subtitles import *
    
def update_all_episodes():
    full_scan_subtitles()
    logging.info('All existing subtitles indexed from disk.')
    list_missing_subtitles()
    logging.info('All missing subtitles updated in database.')

def sync_episodes():
    from get_sonarr_settings import get_sonarr_settings
    url_sonarr = get_sonarr_settings()[0]
    apikey_sonarr = get_sonarr_settings()[2]
    
    # Open database connection
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()

    # Get current episodes id in DB
    current_episodes_db = c.execute('SELECT sonarrSeriesId, sonarrEpisodeId, title, path, season, episode, scene_name FROM table_episodes').fetchall()

    # Get sonarrId for each series from database
    current_episodes_sonarr = []
    seriesIdList = c.execute("SELECT sonarrSeriesId FROM table_shows").fetchall()
    for seriesId in seriesIdList:
        # Get episodes data for a series from Sonarr
        url_sonarr_api_episode = url_sonarr + "/api/episode?seriesId=" + str(seriesId[0]) + "&apikey=" + apikey_sonarr
        r = requests.get(url_sonarr_api_episode)
        for episode in r.json():
            if episode['hasFile'] is True:
                if 'episodeFile' in episode:
                    if episode['episodeFile']['size'] > 20480:
                        # Add shows in Sonarr to current shows list
                        if 'sceneName' in episode['episodeFile']:
                            sceneName = episode['episodeFile']['sceneName']
                        else:
                            sceneName = None
                        current_episodes_sonarr.append((episode['seriesId'], episode['id'], episode['title'], episode['episodeFile']['path'], episode['seasonNumber'], episode['episodeNumber'], sceneName))

    added_episodes = list(set(current_episodes_sonarr) - set(current_episodes_db))
    removed_episodes = list(set(current_episodes_db) - set(current_episodes_sonarr))

    for removed_episode in removed_episodes:
        c.execute('DELETE FROM table_episodes WHERE sonarrEpisodeId = ?', (removed_episode[1],))
        db.commit()

    for added_episode in added_episodes:
        c.execute('''INSERT INTO table_episodes(sonarrSeriesId, sonarrEpisodeId, title, path, season, episode, scene_name) VALUES (?, ?, ?, ?, ?, ?, ?)''', added_episode)
        db.commit()
        store_subtitles(path_replace(added_episode[3]))

    # Close database connection
    c.close()

    logging.debug('All episodes synced from Sonarr into database.')

    list_missing_subtitles()
    logging.debug('All missing subtitles updated in database.')
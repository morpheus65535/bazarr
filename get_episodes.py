import os
import sqlite3
import requests
import logging

from get_general_settings import *
from list_subtitles import *
    
def update_all_episodes():
    from get_sonarr_settings import get_sonarr_settings
    url_sonarr = get_sonarr_settings()[0]
    url_sonarr_short = get_sonarr_settings()[1]
    apikey_sonarr = get_sonarr_settings()[2]
    
    # Open database connection
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()

    # Get Sonarr API URL from database config table
    c.execute('''SELECT * FROM table_settings_sonarr''')
    config_sonarr = c.fetchone()
    if config_sonarr[3] == 1:
        protocol_sonarr = "https"
    else:
        protocol_sonarr = "http"
    if config_sonarr[2] == "":
        base_url_sonarr = ""
    else:
        base_url_sonarr = "/" + config_sonarr[2].strip("/")
    apikey_sonarr = config_sonarr[4]

    # Get current episodes id in DB
    current_episodes_db = c.execute('SELECT sonarrEpisodeId FROM table_episodes').fetchall()
    current_episodes_db_list = [x[0] for x in current_episodes_db]
    
    # Get sonarrId for each series from database
    current_episodes_sonarr = []
    c.execute("SELECT sonarrSeriesId FROM table_shows")
    seriesIdList = c.fetchall()
    for seriesId in seriesIdList:
        # Get episodes data for a series from Sonarr
        url_sonarr_api_episode = protocol_sonarr + "://" + config_sonarr[0] + ":" + str(config_sonarr[1]) + base_url_sonarr + "/api/episode?seriesId=" + str(seriesId[0]) + "&apikey=" + apikey_sonarr
        r = requests.get(url_sonarr_api_episode)
        for episode in r.json():
            if episode['hasFile'] and episode['episodeFile']['size'] > 20480:
                # Add shows in Sonarr to current shows list
                current_episodes_sonarr.append(episode['id'])

                try:
                    c.execute('''INSERT INTO table_episodes(sonarrSeriesId, sonarrEpisodeId, title, path, season, episode) VALUES (?, ?, ?, ?, ?, ?)''', (episode['seriesId'], episode['id'], episode['title'], episode['episodeFile']['path'], episode['seasonNumber'], episode['episodeNumber']))
                    db.commit()
                except sqlite3.Error:
                    c.execute('''UPDATE table_episodes SET sonarrSeriesId = ?, sonarrEpisodeId = ?, title = ?, path = ?, season = ?, episode = ? WHERE sonarrEpisodeId = ?''', (episode['seriesId'], episode['id'], episode['title'], episode['episodeFile']['path'], episode['seasonNumber'], episode['episodeNumber'], episode['id']))
                    db.commit()
            else:
                continue
        continue

    # Delete episodes not in Sonarr anymore
    deleted_items = []
    for item in current_episodes_db_list:
        if item not in current_episodes_sonarr:
            deleted_items.append(tuple([item]))
    c.executemany('DELETE FROM table_episodes WHERE sonarrEpisodeId = ?',deleted_items)
    db.commit()

    # Close database connection
    c.close()

    logging.info('All episodes updated in database.')
    
    # Store substitles for all episodes
    full_scan_subtitles()
    logging.info('All existing subtitles indexed from disk.')
    list_missing_subtitles()
    logging.info('All missing subtitles updated in database.')

def add_new_episodes():
    from get_sonarr_settings import get_sonarr_settings
    url_sonarr = get_sonarr_settings()[0]
    url_sonarr_short = get_sonarr_settings()[1]
    apikey_sonarr = get_sonarr_settings()[2]
    
    # Open database connection
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()

    # Get Sonarr API URL from database config table
    c.execute('''SELECT * FROM table_settings_sonarr''')
    config_sonarr = c.fetchone()
    if config_sonarr[3] == 1:
        protocol_sonarr = "https"
    else:
        protocol_sonarr = "http"
    if config_sonarr[2] == "":
        base_url_sonarr = ""
    else:
        base_url_sonarr = "/" + config_sonarr[2].strip("/")
    apikey_sonarr = config_sonarr[4]

    if apikey_sonarr == None:
        # Close database connection
        c.close()
        pass
    else:
        # Get current episodes in DB
        current_episodes_db = c.execute('SELECT sonarrEpisodeId FROM table_episodes').fetchall()
        current_episodes_db_list = [x[0] for x in current_episodes_db]
        current_episodes_sonarr = []

        # Get sonarrId for each series from database
        c.execute("SELECT sonarrSeriesId FROM table_shows")
        seriesIdList = c.fetchall()
        for seriesId in seriesIdList:
            # Get episodes data for a series from Sonarr
            url_sonarr_api_episode = protocol_sonarr + "://" + config_sonarr[0] + ":" + str(config_sonarr[1]) + base_url_sonarr + "/api/episode?seriesId=" + str(seriesId[0]) + "&apikey=" + apikey_sonarr
            r = requests.get(url_sonarr_api_episode)
            for episode in r.json():
                if episode['hasFile'] and episode['episodeFile']['size'] > 20480:
                    # Add shows in Sonarr to current shows list
                    current_episodes_sonarr.append(episode['id'])

                    try:
                        c.execute('''INSERT INTO table_episodes(sonarrSeriesId, sonarrEpisodeId, title, path, season, episode) VALUES (?, ?, ?, ?, ?, ?)''', (episode['seriesId'], episode['id'], episode['title'], episode['episodeFile']['path'], episode['seasonNumber'], episode['episodeNumber']))
                    except:
                        pass
            db.commit()

        # Delete episodes not in Sonarr anymore
        deleted_items = []
        for item in current_episodes_db_list:
            if item not in current_episodes_sonarr:
                deleted_items.append(tuple([item]))
        c.executemany('DELETE FROM table_episodes WHERE sonarrEpisodeId = ?',deleted_items)
        
        # Commit changes to database table
        db.commit()

        # Close database connection
        c.close()
    
        # Store substitles from episodes we've just added
        new_scan_subtitles()
        try:
            list_missing_subtitles()
        except:
            pass

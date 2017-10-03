import sqlite3
import requests

from list_subtitles import *

def update_all_episodes():
    # Open database connection
    db = sqlite3.connect('bazarr.db')
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

    # Get sonarrId for each series from database
    c.execute("SELECT sonarrSeriesId FROM table_shows")
    seriesIdList = c.fetchall()
    for seriesId in seriesIdList:
        # Get episodes data for a series from Sonarr
        url_sonarr_api_episode = protocol_sonarr + "://" + config_sonarr[0] + ":" + str(config_sonarr[1]) + base_url_sonarr + "/api/episode?seriesId=" + str(seriesId[0]) + "&apikey=" + config_sonarr[4]
        r = requests.get(url_sonarr_api_episode)
        for episode in r.json():
            if episode['hasFile']:
                try:
                    c.execute('''INSERT INTO table_episodes(sonarrSeriesId, sonarrEpisodeId, title, path, season, episode) VALUES (?, ?, ?, ?, ?, ?)''', (episode['seriesId'], episode['id'], episode['title'], episode['episodeFile']['path'], episode['seasonNumber'], episode['episodeNumber']))
                except sqlite3.Error:
                    test = c.execute('''UPDATE table_episodes SET sonarrSeriesId = ?, sonarrEpisodeId = ?, title = ?, path = ?, season = ?, episode = ? WHERE path = ?''', (episode['seriesId'], episode['id'], episode['title'], episode['episodeFile']['path'], episode['seasonNumber'], episode['episodeNumber'], episode['episodeFile']['path']))
            else:
                continue
        continue

    # Commit changes to database table
    db.commit()

    # Close database connection
    c.close()
                
    # Store substitles from episodes we've just added
    new_scan_subtitles()
    list_missing_subtitles()

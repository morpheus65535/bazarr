from get_argv import config_dir

import os
import sqlite3
import time

def history_log(action, sonarrSeriesId, sonarrEpisodeId, description):
    # Open database connection
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()

    # Get Sonarr API URL from database config table
    history = c.execute('''INSERT INTO table_history(action, sonarrSeriesId, sonarrEpisodeId, timestamp, description) VALUES (?, ?, ?, ?, ?)''', (action, sonarrSeriesId, sonarrEpisodeId, time.time(), description))

    # Commit changes to DB
    db.commit()
    
    # Close database connection
    db.close()


def history_log_movie(action, radarrId, description):
    # Open database connection
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()

    history = c.execute('''INSERT INTO table_history_movie(action, radarrId, timestamp, description) VALUES (?, ?, ?, ?)''', (action, radarrId, time.time(), description))

    # Commit changes to DB
    db.commit()

    # Close database connection
    db.close()

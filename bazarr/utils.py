# coding=utf-8

import os
import sqlite3
import time

from get_args import args


def history_log(action, sonarrSeriesId, sonarrEpisodeId, description, video_path=None, language=None, provider=None, score=None):
    # Open database connection
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()

    # Get Sonarr API URL from database config table
    history = c.execute(
        '''INSERT INTO table_history(action, sonarrSeriesId, sonarrEpisodeId, timestamp, description, video_path, language, provider, score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (action, sonarrSeriesId, sonarrEpisodeId, time.time(), description, video_path, language, provider, score))

    # Commit changes to DB
    db.commit()

    # Close database connection
    db.close()


def history_log_movie(action, radarrId, description, video_path=None, language=None, provider=None, score=None):
    # Open database connection
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()

    history = c.execute(
        '''INSERT INTO table_history_movie(action, radarrId, timestamp, description, video_path, language, provider, score) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (action, radarrId, time.time(), description, video_path, language, provider, score))

    # Commit changes to DB
    db.commit()

    # Close database connection
    db.close()

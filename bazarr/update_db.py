# coding=utf-8

import os
import sqlite3

from get_args import args
from scheduler import execute_now
from config import settings

# Check if database exist
if os.path.exists(os.path.join(args.config_dir, 'db', 'bazarr.db')):
    # Open database connection
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    
    # Execute tables modifications
    try:
        c.execute('alter table table_settings_providers add column "username" "text"')
    except:
        pass
    else:
        c.execute('UPDATE table_settings_providers SET username=""')
    
    try:
        c.execute('alter table table_settings_providers add column "password" "text"')
    except:
        pass
    else:
        c.execute('UPDATE table_settings_providers SET password=""')
    
    try:
        c.execute('alter table table_shows add column "audio_language" "text"')
    except:
        pass
    
    try:
        c.execute('alter table table_shows add column "sortTitle" "text"')
    except:
        pass
    
    try:
        c.execute('alter table table_movies add column "sortTitle" "text"')
    except:
        pass
    
    try:
        rows = c.execute('SELECT name FROM table_settings_notifier WHERE name = "Kodi/XBMC"').fetchall()
        if len(rows) == 0:
            providers = [['KODI', 'Kodi/XBMC'], ['Windows', 'Windows Notification'], ['Super Toasty', 'Toasty'],
                         ['PushBullet', 'Pushbullet'], ['Mattermost', 'MatterMost']]
            for provider_old, provider_new in providers:
                c.execute('UPDATE table_settings_notifier SET name=? WHERE name=?', (provider_new, provider_old))
    except:
        pass
    
    try:
        c.execute('alter table table_movies add column "failedAttempts" "text"')
        c.execute('alter table table_episodes add column "failedAttempts" "text"')
    except:
        pass
    
    try:
        c.execute('alter table table_settings_languages add column "code3b" "text"')
    except:
        pass
    
    # Commit change to db
    db.commit()
    
    try:
        c.execute('alter table table_episodes add column "scene_name" TEXT')
        db.commit()
    except:
        pass
    else:
        if settings.general.getboolean('use_sonarr'):
            execute_now('sync_episodes')
        if settings.general.getboolean('use_radarr'):
            execute_now('update_movies')
    
    try:
        c.execute('alter table table_episodes add column "monitored" TEXT')
        db.commit()
    except:
        pass
    else:
        if settings.general.getboolean('use_sonarr'):
            execute_now('sync_episodes')
    
    try:
        c.execute('alter table table_movies add column "monitored" TEXT')
        db.commit()
    except:
        pass
    else:
        if settings.general.getboolean('use_radarr'):
            execute_now('update_movies')

    try:
        c.execute('alter table table_shows add column "year" "text"')
        c.execute('alter table table_shows add column "alternateTitles" "text"')

        c.execute('alter table table_episodes add column "format" "text"')
        c.execute('alter table table_episodes add column "resolution" "text"')
        c.execute('alter table table_episodes add column "video_codec" "text"')
        c.execute('alter table table_episodes add column "audio_codec" "text"')

        c.execute('alter table table_movies add column "year" "text"')
        c.execute('alter table table_movies add column "alternativeTitles" "text"')
        c.execute('alter table table_movies add column "format" "text"')
        c.execute('alter table table_movies add column "resolution" "text"')
        c.execute('alter table table_movies add column "video_codec" "text"')
        c.execute('alter table table_movies add column "audio_codec" "text"')
        c.execute('alter table table_movies add column "imdbId" "text"')
        db.commit()
    except:
        pass
    else:
        if settings.general.getboolean('use_sonarr'):
            execute_now('update_series')
            execute_now('sync_episodes')
        if settings.general.getboolean('use_radarr'):
            execute_now('update_movies')

    try:
        c.execute('alter table table_history add column "video_path" "text"')
        c.execute('alter table table_history add column "language" "text"')
        c.execute('alter table table_history add column "provider" "text"')
        c.execute('alter table table_history add column "score" "text"')

        c.execute('alter table table_history_movie add column "video_path" "text"')
        c.execute('alter table table_history_movie add column "language" "text"')
        c.execute('alter table table_history_movie add column "provider" "text"')
        c.execute('alter table table_history_movie add column "score" "text"')

        db.commit()
    except:
        pass

    try:
        c.execute('alter table table_shows add column "forced" "text"')
    except:
        pass
    else:
        c.execute('UPDATE table_shows SET forced="False"')
        db.commit()

    try:
        c.execute('alter table table_movies add column "forced" "text"')
        db.commit()
    except:
        pass
    else:
        c.execute('UPDATE table_movies SET forced="False"')
        db.commit()

    db.close()

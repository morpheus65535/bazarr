import os
import sqlite3

# Check if database exist
if os.path.exists(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db')) == True:
    # Open database connection
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
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
        c.execute('alter table table_settings_general add column "configured" "integer"')
        c.execute('alter table table_settings_general add column "updated" "integer"')
    except:
        pass

    try:
        c.execute('alter table table_settings_general add column "single_language" "text"')
    except:
        pass
    else:
        c.execute('UPDATE table_settings_general SET single_language="False"')

    try:
        c.execute('CREATE TABLE `table_settings_notifier` (`name` TEXT, `url` TEXT, `enabled` INTEGER);')
    except:
        pass
    else:
        providers = ['Boxcar','Faast','Growl','Join','KODI','Mattermost','Notify My Android','Prowl','Pushalot','PushBullet','Pushjet','Pushover','Rocket.Chat','Slack','Super Toasty','Telegram','Twitter','XBMC']
        for provider in providers:
            c.execute('INSERT INTO `table_settings_notifier` (name, enabled) VALUES (?, ?);', (provider,'0'))

    try:
        c.execute('alter table table_settings_general add column "minimum_score" "text"')
    except:
        pass
    else:
        c.execute('UPDATE table_settings_general SET minimum_score="0"')

    try:
        c.execute('alter table table_settings_general add column "use_scenename" "text"')
    except:
        pass
    else:
        c.execute('UPDATE table_settings_general SET use_scenename="True"')

    try:
        c.execute('alter table table_settings_general add column "use_postprocessing" "text"')
    except:
        pass
    else:
        c.execute('UPDATE table_settings_general SET use_postprocessing="False"')

    try:
        c.execute('alter table table_settings_general add column "postprocessing_cmd" "text"')
    except:
        pass

    try:
        c.execute('alter table table_settings_sonarr add column "full_update" "text"')
    except:
        pass
    else:
        c.execute('UPDATE table_settings_sonarr SET full_update="Daily"')

    try:
        c.execute('alter table table_shows add column "sortTitle" "text"')
    except:
        pass

    try:
        c.execute('CREATE TABLE "table_movies" ( `tmdbId` TEXT NOT NULL UNIQUE, `title` TEXT NOT NULL, `path` TEXT NOT NULL UNIQUE, `languages` TEXT, `subtitles` TEXT, `missing_subtitles` TEXT, `hearing_impaired` TEXT, `radarrId` INTEGER NOT NULL UNIQUE, `overview` TEXT, `poster` TEXT, `fanart` TEXT, "audio_language" "text", `sceneName` TEXT, PRIMARY KEY(`tmdbId`) )')
    except:
        pass

    try:
        c.execute('CREATE TABLE "table_history_movie" ( `id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, `action` INTEGER NOT NULL, `radarrId` INTEGER NOT NULL, `timestamp` INTEGER NOT NULL, `description` TEXT NOT NULL )')
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
        from scheduler import execute_now
        execute_now('update_all_episodes_and_movies')

    # Close database connection
    db.close()

from get_argv import config_dir

import os
import sqlite3

# Check if database exist
if os.path.exists(os.path.join(config_dir, 'db/bazarr.db')) == True:
    # Open database connection
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
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
        c.execute('CREATE TABLE `table_settings_notifier` (`name` TEXT, `url` TEXT, `enabled` INTEGER);')
    except:
        pass
    else:
        providers = ['Boxcar','Faast','Growl','Join','KODI','Mattermost','Notify My Android','Prowl','Pushalot','PushBullet','Pushjet','Pushover','Rocket.Chat','Slack','Super Toasty','Telegram','Twitter','XBMC']
        for provider in providers:
            c.execute('INSERT INTO `table_settings_notifier` (name, enabled) VALUES (?, ?);', (provider,'0'))

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

    try:
        c.execute('DELETE FROM table_settings_notifier WHERE rowid > 24') #Modify this if we add more notification provider
        rows = c.execute('SELECT name FROM table_settings_notifier WHERE name = "Discord"').fetchall()
        if len(rows) == 0:
            providers = ['Discord', 'E-Mail', 'Emby', 'IFTTT', 'Stride', 'Windows']
            for provider in providers:
                c.execute('INSERT INTO `table_settings_notifier` (name, enabled) VALUES (?, ?);', (provider, '0'))
    except:
        pass

    try:
        c.execute('CREATE TABLE `system` ( `configured` TEXT, `updated` TEXT)')
        c.execute('INSERT INTO `system` (configured, updated) VALUES (?, ?);', ('0', '0'))
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
        from get_settings import get_general_settings
        integration = get_general_settings()
        if integration[12] is True:
            execute_now('sync_episodes')
        if integration[13] is True:
            execute_now('update_movies')


    try:
        c.execute('alter table table_episodes add column "monitored" TEXT')
        db.commit()
    except:
        pass
    else:
        from scheduler import execute_now
        from get_settings import get_general_settings
        integration = get_general_settings()
        if integration[12] is True:
            execute_now('sync_episodes')

    try:
        c.execute('alter table table_movies add column "monitored" TEXT')
        db.commit()
    except:
        pass
    else:
        from scheduler import execute_now
        from get_settings import get_general_settings
        integration = get_general_settings()
        if integration[13] is True:
            execute_now('update_movies')

    db.close()
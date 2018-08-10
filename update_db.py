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
        c.execute('CREATE TABLE "table_settings_radarr" ( `ip` TEXT NOT NULL, `port` INTEGER NOT NULL, `base_url` TEXT, `ssl` INTEGER, `apikey` TEXT , "full_update" TEXT)')
    except:
        pass
    else:
        c.execute('INSERT INTO `table_settings_radarr` (ip, port, base_url, ssl, apikey, full_update) VALUES ("127.0.0.1", "7878", "/", "False", Null, "Daily")')

    try:
        c.execute('CREATE TABLE "table_movies" ( `tmdbId` TEXT NOT NULL UNIQUE, `title` TEXT NOT NULL, `path` TEXT NOT NULL UNIQUE, `languages` TEXT, `subtitles` TEXT, `missing_subtitles` TEXT, `hearing_impaired` TEXT, `radarrId` INTEGER NOT NULL UNIQUE, `overview` TEXT, `poster` TEXT, `fanart` TEXT, "audio_language" "text", `sceneName` TEXT, PRIMARY KEY(`tmdbId`) )')
    except:
        pass

    try:
        c.execute('CREATE TABLE "table_history_movie" ( `id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, `action` INTEGER NOT NULL, `radarrId` INTEGER NOT NULL, `timestamp` INTEGER NOT NULL, `description` TEXT NOT NULL )')
    except:
        pass

    try:
        c.execute('alter table table_settings_general add column "use_sonarr" "text"')
    except:
        pass
    else:
        c.execute('UPDATE table_settings_general SET use_sonarr="True"')

    try:
        c.execute('alter table table_settings_general add column "use_radarr" "text"')
    except:
        pass
    else:
        c.execute('UPDATE table_settings_general SET use_radarr="False"')

    try:
        c.execute('alter table table_settings_general add column "path_mapping_movie" "text"')
    except:
        pass

    try:
        c.execute('alter table table_settings_general add column "serie_default_enabled" "text"')
    except:
        pass
    else:
        c.execute('UPDATE table_settings_general SET serie_default_enabled="False"')

    try:
        c.execute('alter table table_settings_general add column "serie_default_languages" "text"')
    except:
        pass

    try:
        c.execute('alter table table_settings_general add column "serie_default_hi" "text"')
    except:
        pass

    try:
        c.execute('alter table table_settings_general add column "movie_default_enabled" "text"')
    except:
        pass
    else:
        c.execute('UPDATE table_settings_general SET movie_default_enabled="False"')

    try:
        c.execute('alter table table_settings_general add column "movie_default_languages" "text"')
    except:
        pass

    try:
        c.execute('alter table table_settings_general add column "movie_default_hi" "text"')
    except:
        pass

    try:
        c.execute('alter table table_settings_general add column "page_size" "text"')
    except:
        pass
    else:
        c.execute('UPDATE table_settings_general SET page_size="25"')

    try:
        c.execute('alter table table_settings_general add column "minimum_score_movie" "text"')
    except:
        pass
    else:
        c.execute('UPDATE table_settings_general SET minimum_score_movie="0"')

    try:
        c.execute('DELETE FROM table_settings_notifier WHERE rowid > 24') #Modify this if we add more notification provider
        c.execute('SELECT name FROM table_settings_notifier WHERE name = "Discord"').fetchone()
    except:
        providers = ['Discord', 'E-Mail', 'Emby', 'IFTTT', 'Stride', 'Windows']
        for provider in providers:
            c.execute('INSERT INTO `table_settings_notifier` (name, enabled) VALUES (?, ?);', (provider, '0'))

    try:
        c.execute('alter table table_settings_general add column "use_embedded_subs" "text"')
    except:
        pass
    else:
        c.execute('UPDATE table_settings_general SET use_embedded_subs="True"')

    try:
        c.execute('CREATE TABLE `table_settings_auth` (	`enabled` TEXT, `username` TEXT, `password` TEXT);')
    except:
        pass
    else:
        c.execute('INSERT INTO `table_settings_auth` (enabled, username, password) VALUES ("False", "", "")')

    try:
        c.execute('alter table table_settings_general add column "only_monitored" "text"')
        db.commit()
    except:
        pass
    else:
        c.execute('UPDATE table_settings_general SET only_monitored="False"')

    # Commit change to db
    db.commit()

    try:
        c.execute('alter table table_episodes add column "scene_name" TEXT')
        db.commit()
    except:
        pass
    else:
        from scheduler import execute_now
        from get_general_settings import get_general_settings
        integration = get_general_settings()
        if integration[12] == "True":
            execute_now('sync_episodes')
        if integration[13] == "True":
            execute_now('update_movies')

    try:
        c.execute('alter table table_episodes add column "monitored" TEXT')
        db.commit()
    except:
        pass
    else:
        from scheduler import execute_now
        from get_general_settings import get_general_settings
        integration = get_general_settings()
        if integration[12] == "True":
            execute_now('sync_episodes')

    try:
        c.execute('alter table table_movies add column "monitored" TEXT')
        db.commit()
    except:
        pass
    else:
        from scheduler import execute_now
        from get_general_settings import get_general_settings
        integration = get_general_settings()
        if integration[13] == "True":
            execute_now('update_movies')

    db.close()
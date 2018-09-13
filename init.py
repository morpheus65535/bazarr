import os
import sqlite3
import logging

from configparser import ConfigParser
from get_argv import config_dir

# Check if config_dir exist
if os.path.exists(config_dir) is False:
    # Create config_dir directory tree
    try:
        os.mkdir(os.path.join(config_dir))
        logging.debug("Created data directory")
    except OSError:
        logging.exception("The configuration directory doesn't exist and Bazarr cannot create it (permission issue?).")
        exit(2)

if os.path.exists(os.path.join(config_dir, 'config')) is False:
    os.mkdir(os.path.join(config_dir, 'config'))
    logging.debug("Created config folder")
if os.path.exists(os.path.join(config_dir, 'db')) is False:
    os.mkdir(os.path.join(config_dir, 'db'))
    logging.debug("Created db folder")
if os.path.exists(os.path.join(config_dir, 'log')) is False:
    os.mkdir(os.path.join(config_dir, 'log'))
    logging.debug("Created log folder")

config_file = os.path.normpath(os.path.join(config_dir, 'config/config.ini'))

cfg = ConfigParser()
try:
    # Open database connection
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()

    # Get general settings from database table
    c.execute("SELECT * FROM table_settings_general")
    general_settings = c.fetchone()
    c.execute('''SELECT * FROM table_settings_auth''')
    auth_settings = c.fetchone()
    c.execute('''SELECT * FROM table_settings_sonarr''')
    sonarr_settings = c.fetchone()
    c.execute('''SELECT * FROM table_settings_radarr''')
    radarr_settings = c.fetchone()

    c.execute("DROP TABLE table_settings_general")
    c.execute("DROP TABLE table_settings_auth")
    c.execute("DROP TABLE table_settings_sonarr")
    c.execute("DROP TABLE table_settings_radarr")

    # Close database connection
    db.close()

    section = 'general'

    if not cfg.has_section(section):
        cfg.add_section(section)

    cfg.set(section, 'ip', str(general_settings[0]))
    cfg.set(section, 'port', str(general_settings[1]))
    cfg.set(section, 'base_url', general_settings[2])
    cfg.set(section, 'path_mappings', general_settings[3])
    cfg.set(section, 'log_level', general_settings[4])
    cfg.set(section, 'branch', general_settings[5])
    cfg.set(section, 'auto_update', general_settings[6])
    cfg.set(section, 'single_language', general_settings[9])
    cfg.set(section, 'minimum_score', general_settings[10])
    cfg.set(section, 'use_scenename', general_settings[11])
    cfg.set(section, 'use_postprocessing', general_settings[12])
    cfg.set(section, 'postprocessing_cmd', general_settings[13])
    cfg.set(section, 'use_sonarr', general_settings[14])
    cfg.set(section, 'use_radarr', general_settings[15])
    cfg.set(section, 'path_mappings_movie', general_settings[16])
    cfg.set(section, 'serie_default_enabled', general_settings[17])
    cfg.set(section, 'serie_default_language', general_settings[18])
    cfg.set(section, 'serie_default_hi', general_settings[19])
    cfg.set(section, 'movie_default_enabled', general_settings[20])
    cfg.set(section, 'movie_default_language', general_settings[21])
    cfg.set(section, 'movie_default_hi', general_settings[22])
    cfg.set(section, 'page_size', general_settings[23])
    cfg.set(section, 'minimum_score_movie', general_settings[24])
    cfg.set(section, 'use_embedded_subs', general_settings[25])
    cfg.set(section, 'only_monitored', general_settings[26])

    section = 'auth'

    if not cfg.has_section(section):
        cfg.add_section(section)

    cfg.set(section, 'enabled', auth_settings[0])
    cfg.set(section, 'username', auth_settings[1])
    cfg.set(section, 'password', auth_settings[2])

    section = 'sonarr'

    if not cfg.has_section(section):
        cfg.add_section(section)

    cfg.set(section, 'ip', sonarr_settings[0])
    cfg.set(section, 'port', str(sonarr_settings[1]))
    cfg.set(section, 'base_url', sonarr_settings[2])
    cfg.set(section, 'ssl', sonarr_settings[3])
    cfg.set(section, 'apikey', sonarr_settings[4])
    cfg.set(section, 'full_update', sonarr_settings[5])

    section = 'radarr'

    if not cfg.has_section(section):
        cfg.add_section(section)

    cfg.set(section, 'ip', radarr_settings[0])
    cfg.set(section, 'port', str(radarr_settings[1]))
    cfg.set(section, 'base_url', radarr_settings[2])
    cfg.set(section, 'ssl', radarr_settings[3])
    cfg.set(section, 'apikey', radarr_settings[4])
    cfg.set(section, 'full_update', radarr_settings[5])

    with open(config_file, 'w+') as configfile:
        cfg.write(configfile)


    logging.info('Config file succesfully migrated from database')

except sqlite3.OperationalError:
    if os.path.exists(config_file) is False:
        cfg = ConfigParser()

        section = 'general'

        if not cfg.has_section(section):
            cfg.add_section(section)

        cfg.set(section, 'ip', "0.0.0.0")
        cfg.set(section, 'port', "6767")
        cfg.set(section, 'base_url', "/")
        cfg.set(section, 'path_mappings', '[]')
        cfg.set(section, 'log_level', "INFO")
        cfg.set(section, 'branch', "master")
        cfg.set(section, 'auto_update', "True")
        cfg.set(section, 'single_language', "False")
        cfg.set(section, 'minimum_score', "90")
        cfg.set(section, 'use_scenename', "False")
        cfg.set(section, 'use_postprocessing', "False")
        cfg.set(section, 'postprocessing_cmd', "False")
        cfg.set(section, 'use_sonarr', "False")
        cfg.set(section, 'use_radarr', "False")
        cfg.set(section, 'path_mappings_movie', '[]')
        cfg.set(section, 'serie_default_enabled', "False")
        cfg.set(section, 'serie_default_language', '')
        cfg.set(section, 'serie_default_hi', "False")
        cfg.set(section, 'movie_default_enabled', "False")
        cfg.set(section, 'movie_default_language', '')
        cfg.set(section, 'movie_default_hi', "False")
        cfg.set(section, 'page_size', "25")
        cfg.set(section, 'minimum_score_movie', "70")
        cfg.set(section, 'use_embedded_subs', "False")
        cfg.set(section, 'only_monitored', "False")
        cfg.set(section, 'adaptive_searching', "False")

        section = 'auth'

        if not cfg.has_section(section):
            cfg.add_section(section)

        cfg.set(section, 'type', "None")
        cfg.set(section, 'username', "")
        cfg.set(section, 'password', "")

        section = 'sonarr'

        if not cfg.has_section(section):
            cfg.add_section(section)

        cfg.set(section, 'ip', "127.0.0.1")
        cfg.set(section, 'port', "8989")
        cfg.set(section, 'base_url', "/")
        cfg.set(section, 'ssl', "False")
        cfg.set(section, 'apikey', "")
        cfg.set(section, 'full_update', "Daily")

        section = 'radarr'

        if not cfg.has_section(section):
            cfg.add_section(section)

        cfg.set(section, 'ip', "127.0.0.1")
        cfg.set(section, 'port', "7878")
        cfg.set(section, 'base_url', "/")
        cfg.set(section, 'ssl', "False")
        cfg.set(section, 'apikey', "")
        cfg.set(section, 'full_update', "Daily")


        with open(config_file, 'w+') as configfile:
            cfg.write(configfile)

        logging.info('Config file created successfully')
try:
    # Get SQL script from file
    fd = open(os.path.join(os.path.dirname(__file__), 'create_db.sql'), 'r')
    script = fd.read()

    # Close SQL script file
    fd.close()

    # Open database connection
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()

    # Execute script and commit change to database
    c.executescript(script)

    # Close database connection
    db.close()

    logging.info('Database created successfully')
except:
    pass

# Remove unused settings
try:
    with open(config_file, 'r') as f:
        cfg.read_file(f)
except Exception:
    pass
cfg.remove_option('auth', 'enabled')
with open(config_file, 'w+') as configfile:
    cfg.write(configfile)

from cork import Cork
import time
if os.path.exists(os.path.normpath(os.path.join(config_dir, 'config/users.json'))) is False:
    cork = Cork(os.path.normpath(os.path.join(config_dir, 'config')), initialize=True)

    cork._store.roles[''] = 100
    cork._store.save_roles()

    tstamp = str(time.time())
    username = password = ''
    cork._store.users[username] = {
        'role': '',
        'hash': cork._hash(username, password),
        'email_addr': username,
        'desc': username,
        'creation_date': tstamp
    }
    cork._store.save_users()

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
        logging.debug("BAZARR Created data directory")
    except OSError:
        logging.exception("BAZARR The configuration directory doesn't exist and Bazarr cannot create it (permission issue?).")
        exit(2)

if os.path.exists(os.path.join(config_dir, 'config')) is False:
    os.mkdir(os.path.join(config_dir, 'config'))
    logging.debug("BAZARR Created config folder")
if os.path.exists(os.path.join(config_dir, 'db')) is False:
    os.mkdir(os.path.join(config_dir, 'db'))
    logging.debug("BAZARR Created db folder")
if os.path.exists(os.path.join(config_dir, 'log')) is False:
    os.mkdir(os.path.join(config_dir, 'log'))
    logging.debug("BAZARR Created log folder")

config_file = os.path.normpath(os.path.join(config_dir, 'config/config.ini'))

cfg = ConfigParser()
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

    logging.info('BAZARR Database created successfully')
except:
    pass

# Remove unused settings
try:
    with open(config_file, 'r') as f:
        cfg.read_file(f)
except Exception:
    pass
if cfg.has_section('auth'):
    if cfg.has_option('auth', 'enabled'):
        enabled = cfg.getboolean('auth', 'enabled')
        if enabled is True:
            cfg.set('auth', 'type', 'basic')
        elif enabled is False:
            cfg.set('auth', 'type', 'None')
        cfg.remove_option('auth', 'enabled')
        with open(config_file, 'w+') as configfile:
            cfg.write(configfile)
            
if cfg.has_section('general'):
    if cfg.has_option('general', 'log_level'):
        cfg.remove_option('general', 'log_level')
        cfg.set('general', 'debug', 'False')
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

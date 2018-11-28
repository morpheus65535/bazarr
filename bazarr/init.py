# coding=utf-8

import os
import sqlite3
import logging
import time

from cork import Cork
from configparser import ConfigParser
from get_args import args

# Check if args.config_dir exist
if not os.path.exists(args.config_dir):
    # Create config_dir directory tree
    try:
        os.mkdir(os.path.join(args.config_dir))
        logging.debug("BAZARR Created data directory")
    except OSError:
        logging.exception(
            "BAZARR The configuration directory doesn't exist and Bazarr cannot create it (permission issue?).")
        exit(2)

if not os.path.exists(os.path.join(args.config_dir, 'config')):
    os.mkdir(os.path.join(args.config_dir, 'config'))
    logging.debug("BAZARR Created config folder")
if not os.path.exists(os.path.join(args.config_dir, 'db')):
    os.mkdir(os.path.join(args.config_dir, 'db'))
    logging.debug("BAZARR Created db folder")
if not os.path.exists(os.path.join(args.config_dir, 'log')):
    os.mkdir(os.path.join(args.config_dir, 'log'))
    logging.debug("BAZARR Created log folder")
    
if not os.path.exists(os.path.join(config_dir, 'config', 'releases.txt')):
    from check_update import check_releases
    check_releases()
    logging.debug("BAZARR Created releases file")

config_file = os.path.normpath(os.path.join(args.config_dir, 'config', 'config.ini'))

cfg = ConfigParser()
try:
    # Get SQL script from file
    fd = open(os.path.join(os.path.dirname(__file__), 'create_db.sql'), 'r')
    script = fd.read()

    # Close SQL script file
    fd.close()

    # Open database connection
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
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
        if enabled:
            cfg.set('auth', 'type', 'basic')
        else:
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

if not os.path.exists(os.path.normpath(os.path.join(args.config_dir, 'config', 'users.json'))):
    cork = Cork(os.path.normpath(os.path.join(args.config_dir, 'config')), initialize=True)

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

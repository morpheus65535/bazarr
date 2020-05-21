# coding=utf-8

import os
import rarfile
import json
import hashlib

from config import settings, configure_captcha_func
from get_args import args
from logger import configure_logging
from helper import path_mappings

from dogpile.cache.region import register_backend as register_cache_backend
import subliminal
import datetime

# set subliminal_patch user agent
os.environ["SZ_USER_AGENT"] = "Bazarr/1"

# set anti-captcha provider and key
configure_captcha_func()

# Check if args.config_dir exist
if not os.path.exists(args.config_dir):
    # Create config_dir directory tree
    try:
        os.mkdir(os.path.join(args.config_dir))
    except OSError:
        print("BAZARR The configuration directory doesn't exist and Bazarr cannot create it (permission issue?).")
        exit(2)

if not os.path.exists(os.path.join(args.config_dir, 'config')):
    os.mkdir(os.path.join(args.config_dir, 'config'))
if not os.path.exists(os.path.join(args.config_dir, 'db')):
    os.mkdir(os.path.join(args.config_dir, 'db'))
if not os.path.exists(os.path.join(args.config_dir, 'log')):
    os.mkdir(os.path.join(args.config_dir, 'log'))
if not os.path.exists(os.path.join(args.config_dir, 'cache')):
    os.mkdir(os.path.join(args.config_dir, 'cache'))

configure_logging(settings.general.getboolean('debug') or args.debug)
import logging

# create random api_key if there's none in config.ini
if not settings.auth.apikey:
    from binascii import hexlify
    settings.auth.apikey = hexlify(os.urandom(16)).decode()
    with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
        settings.write(handle)

# change default base_url to ''
if settings.general.base_url == '/':
    settings.general.base_url = ''
    with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
        settings.write(handle)

# create database file
if not os.path.exists(os.path.join(args.config_dir, 'db', 'bazarr.db')):
    import sqlite3
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

# upgrade database schema
from database import db_upgrade
db_upgrade()

# Configure dogpile file caching for Subliminal request
register_cache_backend("subzero.cache.file", "subzero.cache_backends.file", "SZFileBackend")
subliminal.region.configure('subzero.cache.file', expiration_time=datetime.timedelta(days=30),
                            arguments={'appname': "sz_cache", 'app_cache_dir': args.config_dir})
subliminal.region.backend.sync()

if not os.path.exists(os.path.join(args.config_dir, 'config', 'releases.txt')):
    from check_update import check_releases
    check_releases()
    logging.debug("BAZARR Created releases file")

config_file = os.path.normpath(os.path.join(args.config_dir, 'config', 'config.ini'))

# Reset form login password for Bazarr after migration from 0.8.x to 0.9. Password will be equal to username.
if settings.auth.type == 'form' and \
        os.path.exists(os.path.normpath(os.path.join(args.config_dir, 'config', 'users.json'))):
    username = False
    with open(os.path.normpath(os.path.join(args.config_dir, 'config', 'users.json'))) as json_file:
        try:
            data = json.load(json_file)
            username = next(iter(data))
        except:
            logging.error('BAZARR is unable to migrate credentials. You should disable login by modifying config.ini '
                          'file and settings [auth]-->type = None')
    if username:
        settings.auth.username = username
        settings.auth.password = hashlib.md5(username.encode('utf-8')).hexdigest()
        with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
            settings.write(handle)
        os.remove(os.path.normpath(os.path.join(args.config_dir, 'config', 'users.json')))
        os.remove(os.path.normpath(os.path.join(args.config_dir, 'config', 'roles.json')))
        os.remove(os.path.normpath(os.path.join(args.config_dir, 'config', 'register.json')))
        logging.info('BAZARR your login credentials have been migrated successfully and your password is now equal '
                     'to your username. Please change it as soon as possible in settings.')
else:
    if os.path.exists(os.path.normpath(os.path.join(args.config_dir, 'config', 'users.json'))):
        try:
            os.remove(os.path.normpath(os.path.join(args.config_dir, 'config', 'users.json')))
            os.remove(os.path.normpath(os.path.join(args.config_dir, 'config', 'roles.json')))
            os.remove(os.path.normpath(os.path.join(args.config_dir, 'config', 'register.json')))
        except:
            logging.error("BAZARR cannot delete those file. Please do it manually: users.json, roles.json, "
                          "register.json")


def init_binaries():
    from utils import get_binary
    exe = get_binary("unrar")
    
    rarfile.UNRAR_TOOL = exe
    rarfile.ORIG_UNRAR_TOOL = exe
    try:
        rarfile.custom_check([rarfile.UNRAR_TOOL], True)
    except:
        logging.debug("custom check failed for: %s", exe)
    
    rarfile.OPEN_ARGS = rarfile.ORIG_OPEN_ARGS
    rarfile.EXTRACT_ARGS = rarfile.ORIG_EXTRACT_ARGS
    rarfile.TEST_ARGS = rarfile.ORIG_TEST_ARGS
    logging.debug("Using UnRAR from: %s", exe)
    unrar = exe
    
    return unrar


init_binaries()
path_mappings.update()

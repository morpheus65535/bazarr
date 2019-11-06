# coding=utf-8

import os
import time
import rarfile

from cork import Cork
from ConfigParser2 import ConfigParser
from config import settings
from get_args import args
from logger import configure_logging

from dogpile.cache.region import register_backend as register_cache_backend
import subliminal
import datetime

# set subliminal_patch user agent
os.environ["SZ_USER_AGENT"] = "Bazarr/1"

# set anti-captcha provider and key
if settings.general.anti_captcha_provider == 'anti-captcha' and settings.anticaptcha.anti_captcha_key != "":
    os.environ["ANTICAPTCHA_CLASS"] = 'AntiCaptchaProxyLess'
    os.environ["ANTICAPTCHA_ACCOUNT_KEY"] = settings.anticaptcha.anti_captcha_key
elif settings.general.anti_captcha_provider == 'death-by-captcha' and settings.deathbycaptcha.username != "" and settings.deathbycaptcha.password != "":
    os.environ["ANTICAPTCHA_CLASS"] = 'DeathByCaptchaProxyLess'
    os.environ["ANTICAPTCHA_ACCOUNT_KEY"] = ':'.join(
        {settings.deathbycaptcha.username, settings.deathbycaptcha.password})
else:
    os.environ["ANTICAPTCHA_CLASS"] = ''

# Check if args.config_dir exist
if not os.path.exists(args.config_dir):
    # Create config_dir directory tree
    try:
        os.mkdir(os.path.join(args.config_dir))
    except OSError:
        print "BAZARR The configuration directory doesn't exist and Bazarr cannot create it (permission issue?)."
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

cfg = ConfigParser()

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

# coding=utf-8

import os
import sqlite3
import logging
import time
import rarfile

from cork import Cork
from ConfigParser2 import ConfigParser
from config import settings
from check_update import check_releases
from get_args import args
from utils import get_binary

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
if not os.path.exists(os.path.join(args.config_dir, 'cache')):
    os.mkdir(os.path.join(args.config_dir, 'cache'))
    logging.debug("BAZARR Created cache folder")

# Configure dogpile file caching for Subliminal request
register_cache_backend("subzero.cache.file", "subzero.cache_backends.file", "SZFileBackend")
subliminal.region.configure('subzero.cache.file', expiration_time=datetime.timedelta(days=30),
                            arguments={'appname': "sz_cache", 'app_cache_dir': args.config_dir})
subliminal.region.backend.sync()

if not os.path.exists(os.path.join(args.config_dir, 'config', 'releases.txt')):
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
    
    if cfg.has_option('general', 'only_monitored'):
        only_monitored = cfg.get('general', 'only_monitored')
        cfg.set('sonarr', 'only_monitored', str(only_monitored))
        cfg.set('radarr', 'only_monitored', str(only_monitored))
        cfg.remove_option('general', 'only_monitored')
        with open(config_file, 'w+') as configfile:
            cfg.write(configfile)

# Move providers settings from DB to config file
try:
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    enabled_providers = c.execute("SELECT * FROM table_settings_providers WHERE enabled = 1").fetchall()
    settings_providers = c.execute("SELECT * FROM table_settings_providers").fetchall()
    c.execute("DROP TABLE table_settings_providers")
    db.close()
    
    providers_list = []
    if enabled_providers:
        for provider in enabled_providers:
            providers_list.append(provider[0])
    else:
        providers_list = None
    
    if settings_providers:
        for provider in settings_providers:
            if provider[0] == 'opensubtitles':
                settings.opensubtitles.username = provider[2]
                settings.opensubtitles.password = provider[3]
            elif provider[0] == 'addic7ed':
                settings.addic7ed.username = provider[2]
                settings.addic7ed.password = provider[3]
            elif provider[0] == 'legendastv':
                settings.legendastv.username = provider[2]
                settings.legendastv.password = provider[3]
    
    settings.general.enabled_providers = u'' if not providers_list else ','.join(providers_list)
    with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
        settings.write(handle)
except:
    pass

if settings.general.throtteled_providers == '' or None:
    settings.general.throtteled_providers = '{}'
    with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
        settings.write(handle)

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
    logging.info("Using UnRAR from: %s", exe)
    unrar = exe
    
    return unrar


init_binaries()

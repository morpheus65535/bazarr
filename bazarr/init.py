# coding=utf-8

import os
import io
import rarfile
import sys
import subprocess

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

# deploy requirements.txt
if not args.no_update:
    try:
        import lxml, numpy, webrtcvad
    except ImportError:
        try:
            import pip
        except ImportError:
            logging.info('BAZARR unable to install requirements (pip not installed).')
        else:
            if os.path.expanduser("~") == '/':
                logging.info('BAZARR unable to install requirements (user without home directory).')
            else:
                logging.info('BAZARR installing requirements...')
                subprocess.call([sys.executable, '-m', 'pip', 'install', '--user', '-r',
                                 os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logging.info('BAZARR requirements installed.')
                try:
                    restart_file = io.open(os.path.join(args.config_dir, "bazarr.restart"), "w", encoding='UTF-8')
                except Exception as e:
                    logging.error('BAZARR Cannot create bazarr.restart file: ' + repr(e))
                else:
                    logging.info('Bazarr is being restarted...')
                    restart_file.write(str(''))
                    restart_file.close()
                    os._exit(0)

# create random api_key if there's none in config.ini
if not settings.auth.apikey or settings.auth.apikey.startswith("b'"):
    from binascii import hexlify
    settings.auth.apikey = hexlify(os.urandom(16)).decode()
    with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
        settings.write(handle)

# create random Flask secret_key if there's none in config.ini
if not settings.general.flask_secret_key:
    from binascii import hexlify
    settings.general.flask_secret_key = hexlify(os.urandom(16)).decode()
    with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
        settings.write(handle)

# change default base_url to ''
settings.general.base_url = settings.general.base_url.rstrip('/')
with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
    settings.write(handle)

# migrate enabled_providers from comma separated string to list
if isinstance(settings.general.enabled_providers, str) and not settings.general.enabled_providers.startswith('['):
    settings.general.enabled_providers = str(settings.general.enabled_providers.split(","))
    with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
        settings.write(handle)

# make sure settings.general.branch is properly set when running inside a docker container
package_info_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'package_info')
if os.path.isfile(package_info_file):
    try:
        package_info = {}
        with open(package_info_file) as file:
            for line in file.readlines():
                if line == '\n':
                    break
                splitted_line = line.split('=')
                if len(splitted_line) == 2:
                    package_info[splitted_line[0].lower()] = splitted_line[1].replace('\n', '')
                else:
                    continue
        if 'branch' in package_info:
            settings.general.branch = package_info['branch']
    except:
        pass
    else:
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

# Move GA visitor from config.ini to dedicated file
if settings.analytics.visitor:
    with open(os.path.normpath(os.path.join(args.config_dir, 'config', 'analytics.dat')), 'w+') as handle:
        handle.write(settings.analytics.visitor)
    with open(os.path.normpath(os.path.join(args.config_dir, 'config', 'config.ini')), 'w+') as handle:
        settings.remove_option('analytics', 'visitor')
        settings.write(handle)

# Clean unused settings from config.ini
with open(os.path.normpath(os.path.join(args.config_dir, 'config', 'config.ini')), 'w+') as handle:
    settings.remove_option('general', 'throtteled_providers')
    settings.remove_option('general', 'update_restart')
    settings.write(handle)


# Commenting out the password reset process as it could be having unwanted effects and most of the users have already
# moved to new password hashing algorithm.

# Reset form login password for Bazarr after migration from 0.8.x to 0.9. Password will be equal to username.
# if settings.auth.type == 'form' and \
#         os.path.exists(os.path.normpath(os.path.join(args.config_dir, 'config', 'users.json'))):
#     username = False
#     with open(os.path.normpath(os.path.join(args.config_dir, 'config', 'users.json'))) as json_file:
#         try:
#             data = json.load(json_file)
#             username = next(iter(data))
#         except:
#             logging.error('BAZARR is unable to migrate credentials. You should disable login by modifying config.ini '
#                           'file and settings [auth]-->type = None')
#     if username:
#         settings.auth.username = username
#         settings.auth.password = hashlib.md5(username.encode('utf-8')).hexdigest()
#         with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
#             settings.write(handle)
#         os.remove(os.path.normpath(os.path.join(args.config_dir, 'config', 'users.json')))
#         os.remove(os.path.normpath(os.path.join(args.config_dir, 'config', 'roles.json')))
#         os.remove(os.path.normpath(os.path.join(args.config_dir, 'config', 'register.json')))
#         logging.info('BAZARR your login credentials have been migrated successfully and your password is now equal '
#                      'to your username. Please change it as soon as possible in settings.')
# else:
#     if os.path.exists(os.path.normpath(os.path.join(args.config_dir, 'config', 'users.json'))):
#         try:
#             os.remove(os.path.normpath(os.path.join(args.config_dir, 'config', 'users.json')))
#             os.remove(os.path.normpath(os.path.join(args.config_dir, 'config', 'roles.json')))
#             os.remove(os.path.normpath(os.path.join(args.config_dir, 'config', 'register.json')))
#         except:
#             logging.error("BAZARR cannot delete those file. Please do it manually: users.json, roles.json, "
#                           "register.json")


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

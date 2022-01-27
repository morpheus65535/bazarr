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
import time

# set start time global variable as epoch
global startTime
startTime = time.time()

# set subliminal_patch user agent
os.environ["SZ_USER_AGENT"] = "Bazarr/{}".format(os.environ["BAZARR_VERSION"])

# set subliminal_patch hearing-impaired extension to use when naming subtitles
os.environ["SZ_HI_EXTENSION"] = settings.general.hi_extension

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
import logging  # noqa E402


def is_virtualenv():
    # return True if Bazarr have been start from within a virtualenv or venv
    base_prefix = getattr(sys, "base_prefix", None)
    # real_prefix will return None if not in a virtualenv enviroment or the default python path
    real_prefix = getattr(sys, "real_prefix", None) or sys.prefix
    return base_prefix != real_prefix


# deploy requirements.txt
if not args.no_update:
    try:
        import lxml, numpy, webrtcvad, setuptools  # noqa E401
    except ImportError:
        try:
            import pip  # noqa W0611
        except ImportError:
            logging.info('BAZARR unable to install requirements (pip not installed).')
        else:
            if os.path.expanduser("~") == '/':
                logging.info('BAZARR unable to install requirements (user without home directory).')
            else:
                logging.info('BAZARR installing requirements...')
                try:
                    pip_command = [sys.executable, '-m', 'pip', 'install', '-qq', '--disable-pip-version-check',
                                   '-r', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'requirements.txt')]
                    if not is_virtualenv():
                        # --user only make sense if not running under venv
                        pip_command.insert(4, '--user')
                    subprocess.check_output(pip_command, stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as e:
                    logging.exception('BAZARR requirements.txt installation result: {}'.format(e.stdout))
                    os._exit(1)
                else:
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

# Read package_info (if exists) to override some settings by package maintainers
# This file can also provide some info about the package version and author
package_info_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'package_info')
if os.path.isfile(package_info_file):
    try:
        splitted_lines = []
        package_info = {}
        with open(package_info_file) as file:
            lines = file.readlines()
            for line in lines:
                splitted_lines += line.split(r'\n')
            for line in splitted_lines:
                splitted_line = line.split('=', 1)
                if len(splitted_line) == 2:
                    package_info[splitted_line[0].lower()] = splitted_line[1].replace('\n', '')
                else:
                    continue
        # package author can force a branch to follow
        if 'branch' in package_info:
            settings.general.branch = package_info['branch']
        # package author can disable update
        if package_info.get('updatemethod', '') == 'External':
            os.environ['BAZARR_UPDATE_ALLOWED'] = '0'
            os.environ['BAZARR_UPDATE_MESSAGE'] = package_info.get('updatemethodmessage', '')
        # package author can provide version and contact info
        os.environ['BAZARR_PACKAGE_VERSION'] = package_info.get('packageversion', '')
        os.environ['BAZARR_PACKAGE_AUTHOR'] = package_info.get('packageauthor', '')
    except Exception:
        pass
    else:
        with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
            settings.write(handle)

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


def init_binaries():
    from utils import get_binary
    exe = get_binary("unrar")

    rarfile.UNRAR_TOOL = exe
    rarfile.ORIG_UNRAR_TOOL = exe
    try:
        rarfile.custom_check([rarfile.UNRAR_TOOL], True)
    except Exception:
        logging.debug("custom check failed for: %s", exe)

    logging.debug("Using UnRAR from: %s", exe)
    unrar = exe

    return unrar


from database import init_db, migrate_db  # noqa E402
init_db()
migrate_db()
init_binaries()
path_mappings.update()

# coding=utf-8

import os
import sys
import subprocess
import subliminal
import datetime
import time
import rarfile

from dogpile.cache.region import register_backend as register_cache_backend

from app.config import settings, configure_captcha_func, write_config
from app.get_args import args
from app.logger import configure_logging
from utilities.binaries import get_binary, BinaryNotFound
from utilities.path_mappings import path_mappings
from utilities.backup import restore_from_backup

from app.database import init_db

from literals import (EXIT_CONFIG_CREATE_ERROR, ENV_BAZARR_ROOT_DIR, DIR_BACKUP, DIR_CACHE, DIR_CONFIG, DIR_DB, DIR_LOG,
                      DIR_RESTORE, EXIT_REQUIREMENTS_ERROR)
from utilities.central import make_bazarr_dir, restart_bazarr, stop_bazarr

# set start time global variable as epoch
global startTime
startTime = time.time()

# set subliminal_patch user agent
os.environ["SZ_USER_AGENT"] = f"Bazarr/{os.environ['BAZARR_VERSION']}"

# Check if args.config_dir exist
if not os.path.exists(args.config_dir):
    # Create config_dir directory tree
    try:
        os.mkdir(os.path.join(args.config_dir))
    except OSError:
        print("BAZARR The configuration directory doesn't exist and Bazarr cannot create it (permission issue?).")
        stop_bazarr(EXIT_CONFIG_CREATE_ERROR)

os.environ[ENV_BAZARR_ROOT_DIR] = os.path.join(args.config_dir)
make_bazarr_dir(DIR_BACKUP)
make_bazarr_dir(DIR_CACHE)
make_bazarr_dir(DIR_CONFIG)
make_bazarr_dir(DIR_DB)
make_bazarr_dir(DIR_LOG)
make_bazarr_dir(DIR_RESTORE)

# set subliminal_patch hearing-impaired extension to use when naming subtitles
os.environ["SZ_HI_EXTENSION"] = settings.general.hi_extension

# set anti-captcha provider and key
configure_captcha_func()

# import Google Analytics module to make sure logging is properly configured afterwards
from ga4mp import GtagMP  # noqa E402

# configure logging
configure_logging(settings.general.debug or args.debug)
import logging  # noqa E402

# restore backup if required
restore_from_backup()


def is_virtualenv():
    # return True if Bazarr have been start from within a virtualenv or venv
    base_prefix = getattr(sys, "base_prefix", None)
    # real_prefix will return None if not in a virtualenv environment or the default python path
    real_prefix = getattr(sys, "real_prefix", None) or sys.prefix
    return base_prefix != real_prefix


# deploy requirements.txt
if not args.no_update:
    try:
        if os.name == 'nt':
            import win32api, win32con  # noqa E401
        import lxml, numpy, webrtcvad, setuptools, PIL  # noqa E401
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
                    logging.exception(f'BAZARR requirements.txt installation result: {e.stdout}')
                    os._exit(EXIT_REQUIREMENTS_ERROR)
                else:
                    logging.info('BAZARR requirements installed.')

                restart_bazarr()

# change default base_url to ''
settings.general.base_url = settings.general.base_url.rstrip('/')
write_config()

# migrate enabled_providers from comma separated string to list
if isinstance(settings.general.enabled_providers, str) and not settings.general.enabled_providers.startswith('['):
    settings.general.enabled_providers = str(settings.general.enabled_providers.split(","))
    write_config()

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
        write_config()

# Configure dogpile file caching for Subliminal request
register_cache_backend("subzero.cache.file", "subzero.cache_backends.file", "SZFileBackend")
subliminal.region.configure('subzero.cache.file', expiration_time=datetime.timedelta(days=30),
                            arguments={'appname': "sz_cache", 'app_cache_dir': args.config_dir},
                            replace_existing_backend=True)
subliminal.region.backend.sync()

if not os.path.exists(os.path.join(args.config_dir, 'config', 'releases.txt')):
    from app.check_update import check_releases
    check_releases(startup=True)
    logging.debug("BAZARR Created releases file")

if not os.path.exists(os.path.join(args.config_dir, 'config', 'announcements.txt')):
    from app.announcements import get_announcements_to_file
    get_announcements_to_file(startup=True)
    logging.debug("BAZARR Created announcements file")

# Move GA visitor from config to dedicated file
if 'visitor' in settings.analytics:
    with open(os.path.normpath(os.path.join(args.config_dir, 'config', 'analytics.dat')), 'w+') as handle:
        handle.write(settings.analytics.visitor)
    settings['analytics'].pop('visitor', None)

# Clean unused settings from config
settings['general'].pop('throtteled_providers', None)
settings['general'].pop('update_restart', None)
write_config()


# Remove deprecated providers from enabled providers in config
from subliminal_patch.extensions import provider_registry  # noqa E401
existing_providers = provider_registry.names()
enabled_providers = settings.general.enabled_providers
settings.general.enabled_providers = [x for x in enabled_providers if x in existing_providers]
write_config()


def init_binaries():
    try:
        exe = get_binary("unar")
        rarfile.UNAR_TOOL = exe
        rarfile.UNRAR_TOOL = None
        rarfile.SEVENZIP_TOOL = None
        rarfile.tool_setup(unrar=False, unar=True, bsdtar=False, sevenzip=False, force=True)
    except (BinaryNotFound, rarfile.RarCannotExec):
        try:
            exe = get_binary("unrar")
            rarfile.UNRAR_TOOL = exe
            rarfile.UNAR_TOOL = None
            rarfile.SEVENZIP_TOOL = None
            rarfile.tool_setup(unrar=True, unar=False, bsdtar=False, sevenzip=False, force=True)
        except (BinaryNotFound, rarfile.RarCannotExec):
            try:
                exe = get_binary("7z")
                rarfile.UNRAR_TOOL = None
                rarfile.UNAR_TOOL = None
                rarfile.SEVENZIP_TOOL = "7z"
                rarfile.tool_setup(unrar=False, unar=False, bsdtar=False, sevenzip=True, force=True)
            except (BinaryNotFound, rarfile.RarCannotExec):
                logging.exception("BAZARR requires a rar archive extraction utilities (unrar, unar, 7zip) and it can't be found.")
                raise BinaryNotFound
            else:
                logging.debug("Using 7zip from: %s", exe)
                return exe
        else:
            logging.debug("Using UnRAR from: %s", exe)
            return exe
    else:
        logging.debug("Using unar from: %s", exe)
        return exe


init_db()
init_binaries()
path_mappings.update()

# Initialize Plex OAuth configuration
from app.config import initialize_plex
initialize_plex()

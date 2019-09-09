# coding=utf-8

import os
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

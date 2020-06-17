# coding=utf-8

import os
import time
import platform
import logging
import requests

from whichcraft import which
from get_args import args
from config import settings, url_sonarr, url_radarr
from database import database
from event_handler import event_stream

from subliminal import region as subliminal_cache_region
import datetime
import glob


class BinaryNotFound(Exception):
    pass


def history_log(action, sonarr_series_id, sonarr_episode_id, description, video_path=None, language=None, provider=None,
                score=None):
    database.execute("INSERT INTO table_history (action, sonarrSeriesId, sonarrEpisodeId, timestamp, description,"
                     "video_path, language, provider, score) VALUES (?,?,?,?,?,?,?,?,?)",
                     (action, sonarr_series_id, sonarr_episode_id, time.time(), description, video_path, language,
                      provider, score))
    event_stream(type='episodeHistory')


def history_log_movie(action, radarr_id, description, video_path=None, language=None, provider=None, score=None):
    database.execute("INSERT INTO table_history_movie (action, radarrId, timestamp, description, video_path, language, "
                     "provider, score) VALUES (?,?,?,?,?,?,?,?)",
                     (action, radarr_id, time.time(), description, video_path, language, provider, score))
    event_stream(type='movieHistory')


def get_binary(name):
    binaries_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'bin'))

    exe = None
    installed_exe = which(name)

    if installed_exe and os.path.isfile(installed_exe):
        return installed_exe
    else:
        if name == 'ffprobe':
            dir_name = 'ffmpeg'
        else:
            dir_name = name

        if platform.system() == "Windows":  # Windows
            exe = os.path.abspath(os.path.join(binaries_dir, "Windows", "i386", dir_name, "%s.exe" % name))
        elif platform.system() == "Darwin":  # MacOSX
            exe = os.path.abspath(os.path.join(binaries_dir, "MacOSX", "i386", dir_name, name))
        elif platform.system() == "Linux":  # Linux
            exe = os.path.abspath(os.path.join(binaries_dir, "Linux", platform.machine(), dir_name, name))

    if exe and os.path.isfile(exe):
        return exe
    else:
        raise BinaryNotFound


def cache_maintenance():
    main_cache_validity = 14  # days
    pack_cache_validity = 4  # days

    logging.info("BAZARR Running cache maintenance")
    now = datetime.datetime.now()

    def remove_expired(path, expiry):
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
        if mtime + datetime.timedelta(days=expiry) < now:
            try:
                os.remove(path)
            except (IOError, OSError):
                logging.debug("Couldn't remove cache file: %s", os.path.basename(path))

    # main cache
    for fn in subliminal_cache_region.backend.all_filenames:
        remove_expired(fn, main_cache_validity)

    # archive cache
    for fn in glob.iglob(os.path.join(args.config_dir, "*.archive")):
        remove_expired(fn, pack_cache_validity)


def get_sonarr_version():
    sonarr_version = ''
    if settings.general.getboolean('use_sonarr'):
        try:
            sv = url_sonarr() + "/api/system/status?apikey=" + settings.sonarr.apikey
            sonarr_version = requests.get(sv, timeout=60, verify=False).json()['version']
        except Exception:
            logging.debug('BAZARR cannot get Sonarr version')
    return sonarr_version


def get_sonarr_platform():
    sonarr_platform = ''
    if settings.general.getboolean('use_sonarr'):
        try:
            sv = url_sonarr() + "/api/system/status?apikey=" + settings.sonarr.apikey
            response = requests.get(sv, timeout=60, verify=False).json()
            if response['isLinux'] or response['isOsx']:
                sonarr_platform = 'posix'
            elif response['isWindows']:
                sonarr_platform = 'nt'
        except Exception:
            logging.debug('BAZARR cannot get Sonarr platform')
    return sonarr_platform


def get_radarr_version():
    radarr_version = ''
    if settings.general.getboolean('use_radarr'):
        try:
            rv = url_radarr() + "/api/system/status?apikey=" + settings.radarr.apikey
            radarr_version = requests.get(rv, timeout=60, verify=False).json()['version']
        except Exception:
            logging.debug('BAZARR cannot get Radarr version')
    return radarr_version


def get_radarr_platform():
    radarr_platform = ''
    if settings.general.getboolean('use_radarr'):
        try:
            rv = url_radarr() + "/api/system/status?apikey=" + settings.radarr.apikey
            response = requests.get(rv, timeout=60, verify=False).json()
            if response['isLinux'] or response['isOsx']:
                radarr_platform = 'posix'
            elif response['isWindows']:
                radarr_platform = 'nt'
        except Exception:
            logging.debug('BAZARR cannot get Radarr platform')
    return radarr_platform

# coding=utf-8

from __future__ import absolute_import
import os
import time
import platform
import sys
import logging
import requests

from whichcraft import which
from get_args import args
from config import settings, url_sonarr, url_radarr
from database import TableHistory, TableHistoryMovie

from subliminal import region as subliminal_cache_region
import datetime
import glob


def history_log(action, sonarrSeriesId, sonarrEpisodeId, description, video_path=None, language=None, provider=None,
                score=None, forced=False):
    TableHistory.insert(
        {
            TableHistory.action: action,
            TableHistory.sonarr_series_id: sonarrSeriesId,
            TableHistory.sonarr_episode_id: sonarrEpisodeId,
            TableHistory.timestamp: time.time(),
            TableHistory.description: description,
            TableHistory.video_path: video_path,
            TableHistory.language: language,
            TableHistory.provider: provider,
            TableHistory.score: score
        }
    ).execute()


def history_log_movie(action, radarrId, description, video_path=None, language=None, provider=None, score=None,
                      forced=False):
    TableHistoryMovie.insert(
        {
            TableHistoryMovie.action: action,
            TableHistoryMovie.radarr_id: radarrId,
            TableHistoryMovie.timestamp: time.time(),
            TableHistoryMovie.description: description,
            TableHistoryMovie.video_path: video_path,
            TableHistoryMovie.language: language,
            TableHistoryMovie.provider: provider,
            TableHistoryMovie.score: score
        }
    ).execute()


def get_binary(name):
    binaries_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'bin'))

    exe = None
    installed_exe = which(name)

    if installed_exe and os.path.isfile(installed_exe):
        return installed_exe
    else:
        if platform.system() == "Windows":  # Windows
            exe = os.path.abspath(os.path.join(binaries_dir, "Windows", "i386", name, "%s.exe" % name))

        elif platform.system() == "Darwin":  # MacOSX
            exe = os.path.abspath(os.path.join(binaries_dir, "MacOSX", "i386", name, name))

        elif platform.system() == "Linux":  # Linux
            exe = os.path.abspath(os.path.join(binaries_dir, "Linux", platform.machine(), name, name))

    if exe and os.path.isfile(exe):
        return exe


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
    use_sonarr = settings.general.getboolean('use_sonarr')
    apikey_sonarr = settings.sonarr.apikey
    sv = url_sonarr + "/api/system/status?apikey=" + apikey_sonarr
    sonarr_version = ''
    if use_sonarr:
        try:
            sonarr_version = requests.get(sv, timeout=15, verify=False).json()['version']
        except:
            sonarr_version = ''

    return sonarr_version


def get_radarr_version():
    use_radarr = settings.general.getboolean('use_radarr')
    apikey_radarr = settings.radarr.apikey
    rv = url_radarr + "/api/system/status?apikey=" + apikey_radarr
    radarr_version = ''
    if use_radarr:
        try:
            radarr_version = requests.get(rv, timeout=15, verify=False).json()['version']
        except:
            radarr_version = ''

    return radarr_version

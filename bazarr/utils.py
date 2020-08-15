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
from get_languages import alpha2_from_alpha3, language_from_alpha3, alpha3_from_alpha2
from helper import path_mappings
from list_subtitles import store_subtitles, store_subtitles_movie
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language
from subliminal import region as subliminal_cache_region
import datetime
import glob


class BinaryNotFound(Exception):
    pass


def history_log(action, sonarr_series_id, sonarr_episode_id, description, video_path=None, language=None, provider=None,
                score=None, subs_id=None, subtitles_path=None):
    database.execute("INSERT INTO table_history (action, sonarrSeriesId, sonarrEpisodeId, timestamp, description,"
                     "video_path, language, provider, score, subs_id, subtitles_path) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                     (action, sonarr_series_id, sonarr_episode_id, time.time(), description, video_path, language,
                      provider, score, subs_id, subtitles_path))
    event_stream(type='episodeHistory')


def blacklist_log(sonarr_series_id, sonarr_episode_id, provider, subs_id, language):
    database.execute("INSERT INTO table_blacklist (sonarr_series_id, sonarr_episode_id, timestamp, provider, "
                     "subs_id, language) VALUES (?,?,?,?,?,?)",
                     (sonarr_series_id, sonarr_episode_id, time.time(), provider, subs_id, language))
    event_stream(type='episodeBlacklist')


def blacklist_delete(provider, subs_id):
    database.execute("DELETE FROM table_blacklist WHERE provider=? AND subs_id=?", (provider, subs_id))
    event_stream(type='episodeBlacklist')


def blacklist_delete_all():
    database.execute("DELETE FROM table_blacklist")
    event_stream(type='episodeBlacklist')


def history_log_movie(action, radarr_id, description, video_path=None, language=None, provider=None, score=None,
                      subs_id=None, subtitles_path=None):
    database.execute("INSERT INTO table_history_movie (action, radarrId, timestamp, description, video_path, language, "
                     "provider, score, subs_id, subtitles_path) VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (action, radarr_id, time.time(), description, video_path, language, provider, score, subs_id, subtitles_path))
    event_stream(type='movieHistory')


def blacklist_log_movie(radarr_id, provider, subs_id, language):
    database.execute("INSERT INTO table_blacklist_movie (radarr_id, timestamp, provider, subs_id, language) "
                     "VALUES (?,?,?,?,?)", (radarr_id, time.time(), provider, subs_id, language))
    event_stream(type='movieBlacklist')


def blacklist_delete_movie(provider, subs_id):
    database.execute("DELETE FROM table_blacklist_movie WHERE provider=? AND subs_id=?", (provider, subs_id))
    event_stream(type='movieBlacklist')


def blacklist_delete_all_movie():
    database.execute("DELETE FROM table_blacklist_movie")
    event_stream(type='movieBlacklist')


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


def get_blacklist(media_type):
    if media_type == 'series':
        blacklist_db = database.execute("SELECT provider, subs_id FROM table_blacklist")
    else:
        blacklist_db = database.execute("SELECT provider, subs_id FROM table_blacklist_movie")

    blacklist_list = []
    for item in blacklist_db:
        blacklist_list.append((item['provider'], item['subs_id']))

    return blacklist_list


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


def notify_sonarr(sonarr_series_id):
    try:
        url = url_sonarr() + "/api/command?apikey=" + settings.sonarr.apikey
        data = {
            'name': 'RescanSeries',
            'seriesId': int(sonarr_series_id)
        }
        requests.post(url, json=data, timeout=60, verify=False)
    except Exception as e:
        logging.debug('BAZARR notify Sonarr')


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


def notify_radarr(radarr_id):
    try:
        url = url_radarr() + "/api/command?apikey=" + settings.radarr.apikey
        data = {
            'name': 'RescanMovie',
            'movieId': int(radarr_id)
        }
        requests.post(url, json=data, timeout=60, verify=False)
    except Exception as e:
        logging.debug('BAZARR notify Radarr')


def delete_subtitles(media_type, language, forced, media_path, subtitles_path, sonarr_series_id=None,
                     sonarr_episode_id=None, radarr_id=None):
    if not subtitles_path.endswith('.srt'):
        logging.error('BAZARR can only delete .srt files.')
        return False
    language_log = alpha2_from_alpha3(language) + ':forced' if forced in [True, 'true'] else alpha2_from_alpha3(language)
    language_string = language_from_alpha3(language) + ' forced' if forced in [True, 'true'] else language_from_alpha3(language)
    result = language_string + " subtitles deleted from disk."

    if media_type == 'series':
        try:
            os.remove(path_mappings.path_replace(subtitles_path))
        except OSError:
            logging.exception('BAZARR cannot delete subtitles file: ' + subtitles_path)
            store_subtitles(path_mappings.path_replace_reverse(media_path), media_path)
            return False
        else:
            history_log(0, sonarr_series_id, sonarr_episode_id, result, language=language_log,
                        video_path=path_mappings.path_replace_reverse(media_path),
                        subtitles_path=path_mappings.path_replace_reverse(subtitles_path))
            store_subtitles(path_mappings.path_replace_reverse(media_path), media_path)
            notify_sonarr(sonarr_series_id)
    else:
        try:
            os.remove(path_mappings.path_replace_movie(subtitles_path))
        except OSError:
            logging.exception('BAZARR cannot delete subtitles file: ' + subtitles_path)
            store_subtitles_movie(path_mappings.path_replace_reverse_movie(media_path), media_path)
            return False
        else:
            history_log_movie(0, radarr_id, result, language=language_log,
                              video_path=path_mappings.path_replace_reverse_movie(media_path),
                              subtitles_path=path_mappings.path_replace_reverse_movie(subtitles_path))
            store_subtitles_movie(path_mappings.path_replace_reverse_movie(media_path), media_path)
            notify_radarr(radarr_id)
            return True


def subtitles_apply_mods(language, subtitle_path, mods):

    if language == 'pob':
        lang_obj = Language('por', 'BR')
    else:
        lang_obj = Language(language)

    sub = Subtitle(lang_obj, mods=mods)
    with open(subtitle_path, 'rb') as f:
        sub.content = f.read()

    if not sub.is_valid():
        logging.exception('BAZARR Invalid subtitle file: ' + subtitle_path)
        return

    content = sub.get_modified_content()
    if content:
        if os.path.exists(subtitle_path):
            os.remove(subtitle_path)

        with open(subtitle_path, 'wb') as f:
            f.write(content)



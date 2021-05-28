# coding=utf-8

import os
import time
import platform
import logging
import requests
import pysubs2
import json
import hashlib
import stat

from whichcraft import which
from get_args import args
from config import settings, url_sonarr, url_radarr
from custom_lang import CustomLanguage
from database import TableHistory, TableHistoryMovie, TableBlacklist, TableBlacklistMovie, TableShowsRootfolder, \
    TableMoviesRootfolder
from event_handler import event_stream
from get_languages import alpha2_from_alpha3, language_from_alpha3, language_from_alpha2, alpha3_from_alpha2
from helper import path_mappings
from list_subtitles import store_subtitles, store_subtitles_movie
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.core import get_subtitle_path
from subzero.language import Language
from subliminal import region as subliminal_cache_region
from deep_translator import GoogleTranslator
from dogpile.cache import make_region
import datetime
import glob

region = make_region().configure('dogpile.cache.memory')
headers = {"User-Agent": os.environ["SZ_USER_AGENT"]}


class BinaryNotFound(Exception):
    pass


def history_log(action, sonarr_series_id, sonarr_episode_id, description, video_path=None, language=None, provider=None,
                score=None, subs_id=None, subtitles_path=None):
    TableHistory.insert({
        TableHistory.action: action,
        TableHistory.sonarrSeriesId: sonarr_series_id,
        TableHistory.sonarrEpisodeId: sonarr_episode_id,
        TableHistory.timestamp: time.time(),
        TableHistory.description: description,
        TableHistory.video_path: video_path,
        TableHistory.language: language,
        TableHistory.provider: provider,
        TableHistory.score: score,
        TableHistory.subs_id: subs_id,
        TableHistory.subtitles_path: subtitles_path
    }).execute()
    event_stream(type='episode-history')


def blacklist_log(sonarr_series_id, sonarr_episode_id, provider, subs_id, language):
    TableBlacklist.insert({
        TableBlacklist.sonarr_series_id: sonarr_series_id,
        TableBlacklist.sonarr_episode_id: sonarr_episode_id,
        TableBlacklist.timestamp: time.time(),
        TableBlacklist.provider: provider,
        TableBlacklist.subs_id: subs_id,
        TableBlacklist.language: language
    }).execute()
    event_stream(type='episode-blacklist')


def blacklist_delete(provider, subs_id):
    TableBlacklist.delete().where((TableBlacklist.provider == provider) and
                                  (TableBlacklist.subs_id == subs_id))\
        .execute()
    event_stream(type='episode-blacklist', action='delete')


def blacklist_delete_all():
    TableBlacklist.delete().execute()
    event_stream(type='episode-blacklist', action='delete')


def history_log_movie(action, radarr_id, description, video_path=None, language=None, provider=None, score=None,
                      subs_id=None, subtitles_path=None):
    TableHistoryMovie.insert({
        TableHistoryMovie.action: action,
        TableHistoryMovie.radarrId: radarr_id,
        TableHistoryMovie.timestamp: time.time(),
        TableHistoryMovie.description: description,
        TableHistoryMovie.video_path: video_path,
        TableHistoryMovie.language: language,
        TableHistoryMovie.provider: provider,
        TableHistoryMovie.score: score,
        TableHistoryMovie.subs_id: subs_id,
        TableHistoryMovie.subtitles_path: subtitles_path
    }).execute()
    event_stream(type='movie-history')


def blacklist_log_movie(radarr_id, provider, subs_id, language):
    TableBlacklistMovie.insert({
        TableBlacklistMovie.radarr_id: radarr_id,
        TableBlacklistMovie.timestamp: time.time(),
        TableBlacklistMovie.provider: provider,
        TableBlacklistMovie.subs_id: subs_id,
        TableBlacklistMovie.language: language
    }).execute()
    event_stream(type='movie-blacklist')


def blacklist_delete_movie(provider, subs_id):
    TableBlacklistMovie.delete().where((TableBlacklistMovie.provider == provider) and
                                       (TableBlacklistMovie.subs_id == subs_id))\
        .execute()
    event_stream(type='movie-blacklist', action='delete')


def blacklist_delete_all_movie():
    TableBlacklistMovie.delete().execute()
    event_stream(type='movie-blacklist', action='delete')


@region.cache_on_arguments()
def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


@region.cache_on_arguments()
def get_binaries_from_json():
    try:
        binaries_json_file = os.path.realpath(os.path.join(os.path.dirname(__file__), 'binaries.json'))
        with open(binaries_json_file) as json_file:
            binaries_json = json.load(json_file)
    except OSError:
        logging.exception('BAZARR cannot access binaries.json')
        return []
    else:
        return binaries_json


def get_binary(name):
    installed_exe = which(name)

    if installed_exe and os.path.isfile(installed_exe):
        logging.debug('BAZARR returning this binary: {}'.format(installed_exe))
        return installed_exe
    else:
        logging.debug('BAZARR binary not found in path, searching for it...')
        binaries_dir = os.path.realpath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bin'))
        system = platform.system()
        machine = platform.machine()
        dir_name = name

        # deals with exceptions
        if platform.system() == "Windows":  # Windows
            machine = "i386"
            name = "%s.exe" % name
        elif platform.system() == "Darwin":  # MacOSX
            system = 'MacOSX'
        if name in ['ffprobe', 'ffprobe.exe']:
            dir_name = 'ffmpeg'

        exe_dir = os.path.abspath(os.path.join(binaries_dir, system, machine, dir_name))
        exe = os.path.abspath(os.path.join(exe_dir, name))

        binaries_json = get_binaries_from_json()
        binary = next((item for item in binaries_json if item['system'] == system and item['machine'] == machine and
                       item['directory'] == dir_name and item['name'] == name), None)
        if not binary:
            logging.debug('BAZARR binary not found in binaries.json')
            raise BinaryNotFound
        else:
            logging.debug('BAZARR found this in binaries.json: {}'.format(binary))

        if os.path.isfile(exe) and md5(exe) == binary['checksum']:
            logging.debug('BAZARR returning this existing and up-to-date binary: {}'.format(exe))
            return exe
        else:
            try:
                logging.debug('BAZARR creating directory tree for {}'.format(exe_dir))
                os.makedirs(exe_dir, exist_ok=True)
                logging.debug('BAZARR downloading {0} from {1}'.format(name, binary['url']))
                r = requests.get(binary['url'])
                logging.debug('BAZARR saving {0} to {1}'.format(name, exe_dir))
                with open(exe, 'wb') as f:
                    f.write(r.content)
                if system != 'Windows':
                    logging.debug('BAZARR adding execute permission on {}'.format(exe))
                    st = os.stat(exe)
                    os.chmod(exe, st.st_mode | stat.S_IEXEC)
            except Exception:
                logging.exception('BAZARR unable to download {0} to {1}'.format(name, exe_dir))
                raise BinaryNotFound
            else:
                logging.debug('BAZARR returning this new binary: {}'.format(exe))
                return exe


def get_blacklist(media_type):
    if media_type == 'series':
        blacklist_db = TableBlacklist.select(TableBlacklist.provider, TableBlacklist.subs_id).dicts()
    else:
        blacklist_db = TableBlacklistMovie.select(TableBlacklistMovie.provider, TableBlacklistMovie.subs_id).dicts()

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
            sonarr_version = requests.get(sv, timeout=60, verify=False, headers=headers).json()['version']
        except Exception:
            logging.debug('BAZARR cannot get Sonarr version')
            sonarr_version = 'unknown'
    return sonarr_version


def get_sonarr_platform():
    sonarr_platform = ''
    if settings.general.getboolean('use_sonarr'):
        try:
            sv = url_sonarr() + "/api/system/status?apikey=" + settings.sonarr.apikey
            response = requests.get(sv, timeout=60, verify=False, headers=headers).json()
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
        requests.post(url, json=data, timeout=60, verify=False, headers=headers)
    except Exception as e:
        logging.debug('BAZARR notify Sonarr')


def get_radarr_version():
    radarr_version = ''
    if settings.general.getboolean('use_radarr'):
        try:
            rv = url_radarr() + "/api/system/status?apikey=" + settings.radarr.apikey
            radarr_version = requests.get(rv, timeout=60, verify=False, headers=headers).json()['version']
        except Exception:
            logging.debug('BAZARR cannot get Radarr version')
            radarr_version = 'unknown'
    return radarr_version


def get_radarr_platform():
    radarr_platform = ''
    if settings.general.getboolean('use_radarr'):
        try:
            rv = url_radarr() + "/api/system/status?apikey=" + settings.radarr.apikey
            response = requests.get(rv, timeout=60, verify=False, headers=headers).json()
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
        requests.post(url, json=data, timeout=60, verify=False, headers=headers)
    except Exception as e:
        logging.debug('BAZARR notify Radarr')


def delete_subtitles(media_type, language, forced, hi, media_path, subtitles_path, sonarr_series_id=None,
                     sonarr_episode_id=None, radarr_id=None):
    if not subtitles_path.endswith('.srt'):
        logging.error('BAZARR can only delete .srt files.')
        return False

    language_log = language
    language_string = language_from_alpha2(language)
    if hi in [True, 'true', 'True']:
        language_log += ':hi'
        language_string += ' HI'
    elif forced in [True, 'true', 'True']:
        language_log += ':forced'
        language_string += ' forced'
        
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
            event_stream(type='episode-wanted', action='update', payload=sonarr_episode_id)
            return True
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
            event_stream(type='movie-wanted', action='update', payload=radarr_id)
            return True


def subtitles_apply_mods(language, subtitle_path, mods):
    language = alpha3_from_alpha2(language)
    custom = CustomLanguage.from_value(language, "alpha3")
    if custom is None:
        lang_obj = Language(language)
    else:
        lang_obj = custom.subzero_language()

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


def translate_subtitles_file(video_path, source_srt_file, to_lang, forced, hi):
    to_lang = alpha3_from_alpha2(to_lang)
    lang_obj = Language(to_lang)
    if forced:
        lang_obj = Language.rebuild(lang_obj, forced=True)
    if hi:
        lang_obj = Language.rebuild(lang_obj, hi=True)

    logging.debug('BAZARR is translating in {0} this subtitles {1}'.format(lang_obj, source_srt_file))

    max_characters = 5000

    dest_srt_file = get_subtitle_path(video_path, language=lang_obj, extension='.srt', forced_tag=forced, hi_tag=hi)

    subs = pysubs2.load(source_srt_file, encoding='utf-8')
    lines_list = [x.plaintext for x in subs]
    joined_lines_str = '\n\n\n'.join(lines_list)

    logging.debug('BAZARR splitting subtitles into {} characters blocks'.format(max_characters))
    lines_block_list = []
    translated_lines_list = []
    while len(joined_lines_str):
        partial_lines_str = joined_lines_str[:max_characters]

        if len(joined_lines_str) > max_characters:
            new_partial_lines_str = partial_lines_str.rsplit('\n\n\n', 1)[0]
        else:
            new_partial_lines_str = partial_lines_str

        lines_block_list.append(new_partial_lines_str)
        joined_lines_str = joined_lines_str.replace(new_partial_lines_str, '')

    logging.debug('BAZARR is sending {} blocks to Google Translate'.format(len(lines_block_list)))
    for block_str in lines_block_list:
        try:
            translated_partial_srt_text = GoogleTranslator(source='auto',
                                                           target=lang_obj.basename).translate(text=block_str)
        except:
            return False
        else:
            translated_partial_srt_list = translated_partial_srt_text.split('\n\n\n')
            translated_lines_list += translated_partial_srt_list

    logging.debug('BAZARR saving translated subtitles to {}'.format(dest_srt_file))
    for i, line in enumerate(subs):
        line.plaintext = translated_lines_list[i]
    subs.save(dest_srt_file)

    return dest_srt_file


def check_credentials(user, pw):
    username = settings.auth.username
    password = settings.auth.password
    return hashlib.md5(pw.encode('utf-8')).hexdigest() == password and user == username


def check_health():
    from get_rootfolder import check_sonarr_rootfolder, check_radarr_rootfolder
    if settings.general.getboolean('use_sonarr'):
        check_sonarr_rootfolder()
    if settings.general.getboolean('use_radarr'):
        check_radarr_rootfolder()
    event_stream(type='badges')


def get_health_issues():
    # this function must return a list of dictionaries consisting of to keys: object and issue
    health_issues = []

    # get Sonarr rootfolder issues
    if settings.general.getboolean('use_sonarr'):
        rootfolder = TableShowsRootfolder.select(TableShowsRootfolder.path,
                                                 TableShowsRootfolder.accessible,
                                                 TableShowsRootfolder.error)\
            .where(TableShowsRootfolder.accessible == 0)\
            .dicts()
        for item in rootfolder:
            health_issues.append({'object': path_mappings.path_replace(item['path']),
                                  'issue': item['error']})

    # get Radarr rootfolder issues
    if settings.general.getboolean('use_radarr'):
        rootfolder = TableMoviesRootfolder.select(TableMoviesRootfolder.path,
                                                  TableMoviesRootfolder.accessible,
                                                  TableMoviesRootfolder.error)\
            .where(TableMoviesRootfolder.accessible == 0)\
            .dicts()
        for item in rootfolder:
            health_issues.append({'object': path_mappings.path_replace_movie(item['path']),
                                  'issue': item['error']})

    return health_issues

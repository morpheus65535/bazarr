# coding=utf-8

import ast
from datetime import timedelta
from dateutil import rrule
import pretty
import time
from operator import itemgetter
import platform
import re
import json
import hashlib
import apprise
import gc

from get_args import args
from config import settings, base_url, save_settings, get_settings
from logger import empty_log

from init import *
import logging
from database import database, get_exclusion_clause, get_profiles_list, get_desired_languages, get_profile_id_name, \
    get_audio_profile_languages, update_profile_id_list
from helper import path_mappings
from get_languages import language_from_alpha2, language_from_alpha3, alpha2_from_alpha3, alpha3_from_alpha2
from get_subtitle import download_subtitle, series_download_subtitles, manual_search, manual_download_subtitle, \
    manual_upload_subtitle, wanted_search_missing_subtitles_series, wanted_search_missing_subtitles_movies, \
    episode_download_subtitles, movies_download_subtitles
from notifier import send_notifications, send_notifications_movie
from list_subtitles import store_subtitles, store_subtitles_movie, series_scan_subtitles, movies_scan_subtitles, \
    list_missing_subtitles, list_missing_subtitles_movies
from utils import history_log, history_log_movie, blacklist_log, blacklist_delete, blacklist_delete_all, \
    blacklist_log_movie, blacklist_delete_movie, blacklist_delete_all_movie, get_sonarr_version, get_radarr_version, \
    delete_subtitles, subtitles_apply_mods, translate_subtitles_file
from get_providers import get_providers, get_providers_auth, list_throttled_providers, reset_throttled_providers, \
    get_throttled_providers, set_throttled_providers
from event_handler import event_stream
from scheduler import scheduler
from subsyncer import subsync
from filesystem import browse_bazarr_filesystem, browse_sonarr_filesystem, browse_radarr_filesystem

from subliminal_patch.core import SUBTITLE_EXTENSIONS, guessit

from flask import Flask, jsonify, request, Response, Blueprint, url_for, make_response, session

from flask_restful import Resource, Api, abort
from functools import wraps


api_bp = Blueprint('api', __name__, url_prefix=base_url.rstrip('/')+'/api')
api = Api(api_bp)

None_Keys = ['null', 'undefined', '']

def check_credentials(user, pw):
    username = settings.auth.username
    password = settings.auth.password
    if hashlib.md5(pw.encode('utf-8')).hexdigest() == password and user == username:
        return True
    return False

def authenticate(actual_method):
    @wraps(actual_method)
    def wrapper(*args, **kwargs):
        if settings.auth.type == 'basic':
            auth = request.authorization
            if not (auth and check_credentials(request.authorization.username, request.authorization.password)):
                return ('Unauthorized', 401, {
                    'WWW-Authenticate': 'Basic realm="Login Required"'
                })
        elif settings.auth.type == 'form':
            if 'logged_in' not in session:
                return abort(401, message="Unauthorized")

        apikey_settings = settings.auth.apikey
        apikey_get = request.args.get('apikey')
        apikey_post = request.form.get('apikey')
        apikey_header = None
        if 'X-API-KEY' in request.headers:
            apikey_header = request.headers['X-API-KEY']

        if apikey_settings in [apikey_get, apikey_post, apikey_header]:
            return actual_method(*args, **kwargs)

        return abort(401)

    return wrapper

def postprocess(item):
    # Parse tags
    if "tags" in item:
        item['tags'] = ast.literal_eval(item['tags'])

    if 'monitored' in item:
        item['monitored'] = item['monitored'] == 'True'
        
    if 'hearing_impaired' in item:
        item['hearing_impaired'] = item['hearing_impaired'] == 'True'

    if 'language' in item:
        if item['language'] == 'None':
            item['language'] = None
        elif item['language'] is not None:
            splitted_language = item['language'].split(':')
            item['language'] = {"name": language_from_alpha2(splitted_language[0]),
                                "code2": splitted_language[0],
                                "code3": alpha3_from_alpha2(splitted_language[0]),
                                "forced": True if item['language'].endswith(':forced') else False,
                                "hi": True if item['language'].endswith(':hi') else False}

def postprocessSeries(item):
    postprocess(item)
    # Parse audio language
    if 'audio_language' in item:
        item['audio_language'] = get_audio_profile_languages(series_id=item['sonarrSeriesId'])

    if 'alternateTitles' in item:
        item['alternativeTitles'] = ast.literal_eval(item['alternateTitles'])
        del item["alternateTitles"]

    # Parse seriesType
    if 'seriesType' in item:
        item['seriesType'] = item['seriesType'].capitalize()

    if 'path' in item:
        item['path'] = path_mappings.path_replace(item['path'])
        # Confirm if path exist
        item['exist'] = os.path.isdir(item['path'])

    # map poster and fanart to server proxy
    if 'poster' in item:
        poster = item['poster']
        item['poster'] = f"{base_url}images/series{poster}"

    if 'fanart' in item:
        fanart = item['fanart']
        item['fanart'] = f"{base_url}images/series{fanart}"

def postprocessEpisode(item, desired = []):
    postprocess(item)
    if 'audio_language' in item:
        item['audio_language'] = get_audio_profile_languages(episode_id=item['sonarrEpisodeId'])

    if 'subtitles' in item:
        raw_subtitles = ast.literal_eval(item['subtitles'])
        subtitles = []

        for subs in raw_subtitles:
            subtitle = subs[0].split(':')
            sub = {"name": language_from_alpha2(subtitle[0]),
                   "code2": subtitle[0],
                   "code3": alpha3_from_alpha2(subtitle[0]),
                   "path": subs[1],
                   "forced": False,
                   "hi": False}
            if len(subtitle) > 1:
                sub["forced"] = True if subtitle[1] == 'forced' else False
                sub["hi"] = True if subtitle[1] == 'hi' else False

            subtitles.append(sub)

        item.update({"subtitles": subtitles})

        if settings.general.getboolean('embedded_subs_show_desired'):
            item['subtitles'] = [x for x in item['subtitles'] if
                                 x['code2'] in desired or x['path']]

    # Parse missing subtitles
    if 'missing_subtitles' in item:
        item.update({"missing_subtitles": ast.literal_eval(item['missing_subtitles'])})
        for i, subs in enumerate(item['missing_subtitles']):
            subtitle = subs.split(':')
            item['missing_subtitles'][i] = {"name": language_from_alpha2(subtitle[0]),
                                            "code2": subtitle[0],
                                            "code3": alpha3_from_alpha2(subtitle[0]),
                                            "forced": False,
                                            "hi": False}
            if len(subtitle) > 1:
                item['missing_subtitles'][i].update({
                    "forced": True if subtitle[1] == 'forced' else False,
                    "hi": True if subtitle[1] == 'hi' else False
                })

    if "scene_name" in item:
        item["sceneName"] = item["scene_name"]
        del item["scene_name"]

    if 'path' in item:
        # Provide mapped path
        item['path'] = path_mappings.path_replace(item['path'])
        item['exist'] = os.path.isfile(item['path'])


# TODO: Move
def postprocessMovie(item):
    postprocess(item)
    # Parse audio language
    if 'audio_language' in item:
        item['audio_language'] = get_audio_profile_languages(movie_id=item['radarrId'])

    # Parse alternate titles
    if 'alternativeTitles' in item:
        item['alternativeTitles'] = ast.literal_eval(item['alternativeTitles'])

    # Parse failed attempts
    if 'failedAttempts' in item and item['failedAttempts'] is not None:
        item['failedAttempts'] = ast.literal_eval(item['failedAttempts'])

    # Parse subtitles
    if 'subtitles' in item:
        item['subtitles'] = ast.literal_eval(item['subtitles'])
        for i, subs in enumerate(item['subtitles']):
            language = subs[0].split(':')
            item['subtitles'][i] = {"path": subs[1],
                                    "name": language_from_alpha2(language[0]),
                                    "code2": language[0],
                                    "code3": alpha3_from_alpha2(language[0]),
                                    "forced": False,
                                    "hi": False}
            if len(language) > 1:
                item['subtitles'][i].update({
                    "forced": True if language[1] == 'forced' else False,
                    "hi": True if language[1] == 'hi' else False
                })

        if settings.general.getboolean('embedded_subs_show_desired'):
            desired_lang_list = []
            if isinstance(item['languages'], list):
                desired_lang_list = [x['code2'] for x in item['languages']]
            item['subtitles'] = [x for x in item['subtitles'] if x['code2'] in desired_lang_list or x['path']]

        item['subtitles'] = sorted(item['subtitles'], key=itemgetter('name', 'forced'))

    # Parse missing subtitles
    if 'missing_subtitles' in item:
        item['missing_subtitles'] = ast.literal_eval(item['missing_subtitles'])
        for i, subs in enumerate(item['missing_subtitles']):
            language = subs.split(':')
            item['missing_subtitles'][i] = {"name": language_from_alpha2(language[0]),
                                            "code2": language[0],
                                            "code3": alpha3_from_alpha2(language[0]),
                                            "forced": False,
                                            "hi": False}
            if len(language) > 1:
                item['missing_subtitles'][i].update({
                    "forced": True if language[1] == 'forced' else False,
                    "hi": True if language[1] == 'hi' else False
                })

    # Provide mapped path
    if 'path' in item:
        item['path'] = path_mappings.path_replace_movie(item['path'])
        # Confirm if path exist
        item['exist'] = os.path.isfile(item['path'])

    if 'subtitles_path' in item:
        # Provide mapped subtitles path
        item['subtitles_path'] = path_mappings.path_replace_movie(item['subtitles_path'])

    # map poster and fanart to server proxy
    if 'poster' in item:
        poster = item['poster']
        item['poster'] = f"{base_url}images/movies{poster}"

    if 'fanart' in item:
        fanart = item['fanart']
        item['fanart'] = f"{base_url}images/movies{fanart}"


class SystemAccount(Resource):
    def post(self):
        if settings.auth.type != 'form':
            return '', 405

        action = request.args.get('action')
        if action == 'login':
            username = request.form.get('username')
            password = request.form.get('password')
            if check_credentials(username, password):
                session['logged_in'] = True
                return '', 204
        elif action == 'logout':
            if settings.auth.type == 'basic':
                return abort(401)
            elif settings.auth.type == 'form':
                session.clear()
                gc.collect()
                return '', 204

        return '', 401


class System(Resource):
    @authenticate
    def post(self):
        from server import webserver
        action = request.args.get('action')
        if action == "shutdown":
            webserver.shutdown()
        elif action == "restart":
            webserver.restart()
        return '', 204


class BadgesSeries(Resource):
    @authenticate
    def get(self):
        missing_episodes = database.execute("SELECT table_shows.tags, table_episodes.monitored, table_shows.seriesType "
                                            "FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId ="
                                            " table_episodes.sonarrSeriesId WHERE missing_subtitles is not null AND "
                                            "missing_subtitles != '[]'" + get_exclusion_clause('series'))
        missing_episodes = len(missing_episodes)

        result = {
            "value": missing_episodes
        }
        return jsonify(result)


class BadgesMovies(Resource):
    @authenticate
    def get(self):
        missing_movies = database.execute("SELECT tags, monitored FROM table_movies WHERE missing_subtitles is not "
                                          "null AND missing_subtitles != '[]'" + get_exclusion_clause('movie'))
        missing_movies = len(missing_movies)

        result = {
            "value": missing_movies
        }
        return jsonify(result)


class BadgesProviders(Resource):
    @authenticate
    def get(self):
        result = {
            "value": len(eval(str(get_throttled_providers())))
        }
        return jsonify(result)


class Languages(Resource):
    @authenticate
    def get(self):
        enabled = request.args.get('enabled')
        if enabled.lower() in ['true', '1']:
            result = database.execute("SELECT * FROM table_settings_languages WHERE enabled=1 ORDER BY name")
        else:
            result = database.execute("SELECT * FROM table_settings_languages ORDER BY name")
        return jsonify(result)


class LanguagesProfiles(Resource):
    @authenticate
    def get(self):
        return jsonify(get_profiles_list())


class Notifications(Resource):
    @authenticate
    def patch(self):
        protocol = request.form.get("protocol")
        provider = request.form.get("path")

        asset = apprise.AppriseAsset(async_mode=False)

        apobj = apprise.Apprise(asset=asset)

        apobj.add(protocol + "://" + provider)

        apobj.notify(
                title='Bazarr test notification',
                body='Test notification'
        )

        return '', 204


class SystemSettings(Resource):
    @authenticate
    def get(self):
        data = get_settings()

        notifications = database.execute("SELECT * FROM table_settings_notifier ORDER BY name")
        for i, item in enumerate(notifications):
            item["enabled"] = item["enabled"] == 1
            notifications[i] = item

        data['notifications'] = dict()
        data['notifications']['providers'] = notifications

        return jsonify(data)

    @authenticate
    def post(self):
        enabled_languages = request.form.getlist('languages-enabled')
        if len(enabled_languages) != 0:
            database.execute("UPDATE table_settings_languages SET enabled=0")
            for code in enabled_languages:
                database.execute("UPDATE table_settings_languages SET enabled=1 WHERE code2=?", (code,))

        languages_profiles = request.form.get('languages-profiles')
        if languages_profiles:
            existing_ids = database.execute('SELECT profileId FROM table_languages_profiles')
            existing = [x['profileId'] for x in existing_ids]
            for item in json.loads(languages_profiles):
                if item['profileId'] in existing:
                    # Update existing profiles
                    database.execute('UPDATE table_languages_profiles SET name = ?, cutoff = ?, items = ? '
                                     'WHERE profileId = ?', (item['name'],
                                                             item['cutoff'] if item['cutoff'] != 'null' else None,
                                                             json.dumps(item['items']),
                                                             item['profileId']))
                    existing.remove(item['profileId'])
                else:
                    # Add new profiles
                    database.execute('INSERT INTO table_languages_profiles (profileId, name, cutoff, items) '
                                     'VALUES (?, ?, ?, ?)', (item['profileId'],
                                                             item['name'],
                                                             item['cutoff'] if item['cutoff'] != 'null' else None,
                                                             json.dumps(item['items'])))
            for profileId in existing:
                # Unassign this profileId from series and movies
                database.execute('UPDATE table_shows SET profileId = null WHERE profileId = ?', (profileId,))
                database.execute('UPDATE table_movies SET profileId = null WHERE profileId = ?', (profileId,))
                # Remove deleted profiles
                database.execute('DELETE FROM table_languages_profiles WHERE profileId = ?', (profileId,))

            update_profile_id_list()

            if settings.general.getboolean('use_sonarr'):
                scheduler.add_job(list_missing_subtitles, kwargs={'send_event': False})
            if settings.general.getboolean('use_radarr'):
                scheduler.add_job(list_missing_subtitles_movies, kwargs={'send_event': False})

        # Update Notification
        notifications = request.form.getlist('notifications-providers')
        for item in notifications:
            item = json.loads(item)
            database.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = ?",
                            (item['enabled'], item['url'], item['name']))

        save_settings(zip(request.form.keys(), request.form.listvalues()))
        return '', 204


class SystemTasks(Resource):
    @authenticate
    def get(self):
        taskid = request.args.get('taskid')

        task_list = scheduler.get_task_list()

        if taskid:
            for item in task_list:
                if item['job_id'] == taskid:
                    task_list = [item]
                    continue

        return jsonify(data=task_list)

    @authenticate
    def post(self):
        taskid = request.form.get('taskid')

        scheduler.execute_job_now(taskid)

        return '', 204


class SystemLogs(Resource):
    @authenticate
    def get(self):
        logs = []
        with io.open(os.path.join(args.config_dir, 'log', 'bazarr.log'), encoding='UTF-8') as file:
            for line in file.readlines():
                lin = []
                lin = line.split('|')
                log = dict()
                log["timestamp"] = lin[0]
                log["type"] = lin[1].rstrip()
                log["message"] = lin[3]
                logs.append(log)
            logs.reverse()
        return jsonify(data=logs)

    @authenticate
    def delete(self):
        empty_log()
        return '', 204


class SystemStatus(Resource):
    def get(self):
        system_status = {}
        system_status.update({'bazarr_version': os.environ["BAZARR_VERSION"]})
        system_status.update({'sonarr_version': get_sonarr_version()})
        system_status.update({'radarr_version': get_radarr_version()})
        system_status.update({'operating_system': platform.platform()})
        system_status.update({'python_version': platform.python_version()})
        system_status.update({'bazarr_directory': os.path.dirname(os.path.dirname(__file__))})
        system_status.update({'bazarr_config_directory': args.config_dir})
        return jsonify(data=system_status)


class SystemReleases(Resource):
    @authenticate
    def get(self):
        releases = []
        try:
            with io.open(os.path.join(args.config_dir, 'config', 'releases.txt'), 'r', encoding='UTF-8') as f:
                releases = json.loads(f.read())
            releases = releases[:5]
            for i, release in enumerate(releases):
                body = release['body'].replace('- ', '').split('\r\n')[1:]
                releases[i] = {"body": body,
                               "name": release['name'],
                               "date": release['date'][:10],
                               "prerelease": release['prerelease'],
                               "current": True if release['name'].lstrip('v') == os.environ["BAZARR_VERSION"] else False}

        except Exception as e:
            logging.exception(
                'BAZARR cannot parse releases caching file: ' + os.path.join(args.config_dir, 'config', 'releases.txt'))
        return jsonify(data=releases)


class Series(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        seriesId = request.args.get('seriesid')

        if seriesId:
            result = database.execute("SELECT * FROM table_shows WHERE sonarrSeriesId=? ORDER BY sortTitle ASC LIMIT ? "
                                      "OFFSET ?", (seriesId, length, start))
        else:
            result = database.execute("SELECT * FROM table_shows ORDER BY sortTitle ASC LIMIT ? OFFSET ?"
                                      , (length, start))

        for item in result:
            postprocessSeries(item)

            # Add missing subtitles episode count
            episodeMissingCount = database.execute("SELECT table_shows.tags, table_episodes.monitored, "
                                                   "table_shows.seriesType FROM table_episodes INNER JOIN table_shows "
                                                   "on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId "
                                                   "WHERE table_episodes.sonarrSeriesId=? AND missing_subtitles is not "
                                                   "null AND missing_subtitles != '[]'" +
                                                   get_exclusion_clause('series'), (item['sonarrSeriesId'],))
            episodeMissingCount = len(episodeMissingCount)
            item.update({"episodeMissingCount": episodeMissingCount})

            # Add episode count
            episodeFileCount = database.execute("SELECT table_shows.tags, table_episodes.monitored, "
                                                "table_shows.seriesType FROM table_episodes INNER JOIN table_shows on "
                                                "table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE "
                                                "table_episodes.sonarrSeriesId=?" + get_exclusion_clause('series'),
                                                (item['sonarrSeriesId'],))
            episodeFileCount = len(episodeFileCount)
            item.update({"episodeFileCount": episodeFileCount})


        return jsonify(data=result)

    @authenticate
    def post(self):
        seriesIdList = request.form.getlist('seriesid')
        profileIdList = request.form.getlist('profileid')

        for idx in range(len(seriesIdList)):
            seriesId = seriesIdList[idx]
            profileId = profileIdList[idx]

            if profileId in None_Keys:
                profileId = None
            else:
                try:
                    profileId = int(profileId)
                except Exception:
                    return '', 400

            database.execute("UPDATE table_shows SET profileId=? WHERE sonarrSeriesId=?", (profileId, seriesId))

            list_missing_subtitles(no=seriesId)

        # event_stream(type='series', action='update', series=seriesId)

        return '', 204

    @authenticate
    def patch(self):
        seriesid = request.form.get('seriesid')
        action = request.form.get('action')
        if action == "scan-disk":
            series_scan_subtitles(seriesid)
            return '', 204
        elif action == "search-missing":
            series_download_subtitles(seriesid)
            return '', 204
        elif action == "search-wanted":
            wanted_search_missing_subtitles_series()
            return '', 204

        return '', 400


class Episodes(Resource):
    @authenticate
    def get(self):
        seriesId = request.args.get('seriesid')
        episodeId = request.args.get('episodeid')
        if episodeId:
            result = database.execute("SELECT * FROM table_episodes WHERE sonarrEpisodeId=?", (episodeId,))
        elif seriesId:
            result = database.execute("SELECT * FROM table_episodes WHERE sonarrSeriesId=? ORDER BY season DESC, "
                                      "episode DESC", (seriesId,))
        else:
            return "Series ID not provided", 400

        profileId = database.execute("SELECT profileId FROM table_shows WHERE sonarrSeriesId = ?", (seriesId,),
                                     only_one=True)['profileId']
        desired_languages = str(get_desired_languages(profileId))
        desired = ast.literal_eval(desired_languages)

        for item in result:
            postprocessEpisode(item, desired)

        return jsonify(data=result)


# PATCH: Download Subtitles
# POST: Upload Subtitles
# DELETE: Delete Subtitles
class EpisodesSubtitles(Resource):
    @authenticate
    def patch(self):
        sonarrSeriesId = request.args.get('seriesid')
        sonarrEpisodeId = request.args.get('episodeid')
        episodeInfo = database.execute("SELECT title, path, scene_name, audio_language FROM table_episodes WHERE sonarrEpisodeId=?", (sonarrEpisodeId,), only_one=True)

        title = episodeInfo['title']
        episodePath = path_mappings.path_replace(episodeInfo['path'])
        sceneName = episodeInfo['scene_name']
        audio_language = episodeInfo['audio_language']
        if sceneName is None: sceneName = "None"

        language = request.form.get('language')
        hi = request.form.get('hi').capitalize()
        forced = request.form.get('forced').capitalize()

        providers_list = get_providers()
        providers_auth = get_providers_auth()

        audio_language_list = get_audio_profile_languages(episode_id=sonarrEpisodeId)
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = None

        try:
            result = download_subtitle(episodePath, language, audio_language, hi, forced, providers_list, providers_auth, sceneName,
                                       title, 'series')
            if result is not None:
                message = result[0]
                path = result[1]
                forced = result[5]
                if result[8]:
                    language_code = result[2] + ":hi"
                elif forced:
                    language_code = result[2] + ":forced"
                else:
                    language_code = result[2]
                provider = result[3]
                score = result[4]
                subs_id = result[6]
                subs_path = result[7]
                history_log(1, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score, subs_id, subs_path)
                send_notifications(sonarrSeriesId, sonarrEpisodeId, message)
                store_subtitles(path, episodePath)
            else:
                event_stream(type='episode', action='update', series=int(sonarrSeriesId), episode=int(sonarrEpisodeId))

        except OSError:
            pass

        return '', 204

    @authenticate
    def post(self):
        sonarrSeriesId = request.args.get('seriesid')
        sonarrEpisodeId = request.args.get('episodeid')
        episodeInfo = database.execute("SELECT title, path, scene_name, audio_language FROM table_episodes WHERE sonarrEpisodeId=?", (sonarrEpisodeId,), only_one=True)

        title = episodeInfo['title']
        episodePath = path_mappings.path_replace(episodeInfo['path'])
        sceneName = episodeInfo['scene_name']
        audio_language = episodeInfo['audio_language']
        if sceneName is None: sceneName = "None"

        language = request.form.get('language')
        forced = True if request.form.get('forced') == 'on' else False
        subFile = request.files.get('file')

        _, ext = os.path.splitext(subFile.filename)

        if ext not in SUBTITLE_EXTENSIONS:
            raise ValueError('A subtitle of an invalid format was uploaded.')

        try:
            result = manual_upload_subtitle(path=episodePath,
                                            language=language,
                                            forced=forced,
                                            title=title,
                                            scene_name=sceneName,
                                            media_type='series',
                                            subtitle=subFile,
                                            audio_language=audio_language)

            if result is not None:
                message = result[0]
                path = result[1]
                subs_path = result[2]
                if forced:
                    language_code = language + ":forced"
                else:
                    language_code = language
                provider = "manual"
                score = 360
                history_log(4, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score, subtitles_path=subs_path)
                if not settings.general.getboolean('dont_notify_manual_actions'):
                    send_notifications(sonarrSeriesId, sonarrEpisodeId, message)
                store_subtitles(path, episodePath)

        except OSError:
            pass

        return '', 204

    @authenticate
    def delete(self):
        sonarrSeriesId = request.args.get('seriesid')
        sonarrEpisodeId = request.args.get('episodeid')
        episodeInfo = database.execute("SELECT title, path, scene_name, audio_language FROM table_episodes WHERE sonarrEpisodeId=?", (sonarrEpisodeId,), only_one=True)

        episodePath = path_mappings.path_replace(episodeInfo['path'])

        language = request.form.get('language')
        forced = request.form.get('forced')
        hi = request.form.get('hi')
        subtitlesPath = request.form.get('path')

        result = delete_subtitles(media_type='series',
                                  language=language,
                                  forced=forced,
                                  hi=hi,
                                  media_path=episodePath,
                                  subtitles_path=subtitlesPath,
                                  sonarr_series_id=sonarrSeriesId,
                                  sonarr_episode_id=sonarrEpisodeId)

        return '', 204


class Movies(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        id = request.args.get('radarrid')

        if id:
            result = database.execute("SELECT * FROM table_movies WHERE radarrId=? ORDER BY sortTitle ASC LIMIT ? "
                                      "OFFSET ?", (id, length, start))
        else:
            result = database.execute("SELECT * FROM table_movies ORDER BY sortTitle ASC LIMIT ? OFFSET ?",
                                      (length, start))
        for item in result:
            postprocessMovie(item)

        return jsonify(data=result)

    @authenticate
    def post(self):
        radarrIdList = request.form.getlist('radarrid')
        profileIdList = request.form.getlist('profileid')

        for idx in range(len(radarrIdList)):
            radarrId = radarrIdList[idx]
            profileId = profileIdList[idx]

            if profileId in None_Keys:
                profileId = None
            else:
                try:
                    profileId = int(profileId)
                except Exception:
                    return '', 400

            database.execute("UPDATE table_movies SET profileId=? WHERE radarrId=?", (profileId, radarrId))

            list_missing_subtitles_movies(no=radarrId)

        # event_stream(type='movies', action='update', movie=radarrId)

        return '', 204

    @authenticate
    def patch(self):
        radarrid = request.form.get('radarrid')
        action = request.form.get('action')
        if action == "scan-disk":
            movies_scan_subtitles(radarrid)
            return '', 204
        elif action == "search-missing":
            movies_download_subtitles(radarrid)
            return '', 204
        elif action == "search-wanted":
            wanted_search_missing_subtitles_movies()
            return '', 204

        return '', 400

"""
:param language: Alpha2 language code
"""
class MoviesSubtitles(Resource):
    @authenticate
    def patch(self):
        # Download
        radarrId = request.args.get('radarrid')

        movieInfo = database.execute("SELECT title, path, sceneName, audio_language FROM table_movies WHERE radarrId=?", (radarrId,), only_one=True)

        moviePath = path_mappings.path_replace_movie(movieInfo['path'])
        sceneName = movieInfo['sceneName']
        if sceneName is None: sceneName = 'None'

        title = movieInfo['title']
        audio_language = movieInfo['audio_language']

        language = request.form.get('language')
        hi = request.form.get('hi').capitalize()
        forced = request.form.get('forced').capitalize()

        providers_list = get_providers()
        providers_auth = get_providers_auth()

        audio_language_list = get_audio_profile_languages(movie_id=radarrId)
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = None

        try:
            result = download_subtitle(moviePath, language, audio_language, hi, forced, providers_list,
                                       providers_auth, sceneName, title, 'movie')
            if result is not None:
                message = result[0]
                path = result[1]
                forced = result[5]
                if result[8]:
                    language_code = result[2] + ":hi"
                elif forced:
                    language_code = result[2] + ":forced"
                else:
                    language_code = result[2]
                provider = result[3]
                score = result[4]
                subs_id = result[6]
                subs_path = result[7]
                history_log_movie(1, radarrId, message, path, language_code, provider, score, subs_id, subs_path)
                send_notifications_movie(radarrId, message)
                store_subtitles_movie(path, moviePath)
            else:
                event_stream(type='movie', action='update', movie=int(radarrId))
        except OSError:
            pass

        return '', 204

    @authenticate
    def post(self):
        # Upload
        # TODO: Support Multiply Upload
        radarrId = request.args.get('radarrid')
        movieInfo = database.execute("SELECT title, path, sceneName, audio_language FROM table_movies WHERE radarrId=?", (radarrId,), only_one=True)

        moviePath = path_mappings.path_replace_movie(movieInfo['path'])
        sceneName = movieInfo['sceneName']
        if sceneName is None: sceneName = 'None'

        title = movieInfo['title']
        audioLanguage = movieInfo['audio_language']

        language = request.form.get('language')
        forced = True if request.form.get('forced') == 'true' else False
        subFile = request.files.get('file')

        _, ext = os.path.splitext(subFile.filename)

        if ext not in SUBTITLE_EXTENSIONS:
            raise ValueError('A subtitle of an invalid format was uploaded.')

        try:
            result = manual_upload_subtitle(path=moviePath,
                                            language=language,
                                            forced=forced,
                                            title=title,
                                            scene_name=sceneName,
                                            media_type='movie',
                                            subtitle=subFile,
                                            audio_language=audioLanguage)

            if result is not None:
                message = result[0]
                path = result[1]
                subs_path = result[2]
                if forced:
                    language_code = language + ":forced"
                else:
                    language_code = language
                provider = "manual"
                score = 120
                history_log_movie(4, radarrId, message, path, language_code, provider, score, subtitles_path=subs_path)
                if not settings.general.getboolean('dont_notify_manual_actions'):
                    send_notifications_movie(radarrId, message)
                store_subtitles_movie(path, moviePath)
        except OSError:
            pass

        return '', 204

    @authenticate
    def delete(self):
        # Delete
        radarrId = request.args.get('radarrid')
        movieInfo = database.execute("SELECT path FROM table_movies WHERE radarrId=?", (radarrId,), only_one=True)

        moviePath = path_mappings.path_replace_movie(movieInfo['path'])

        language = request.form.get('language')
        forced = request.form.get('forced')
        hi = request.form.get('hi')
        subtitlesPath = request.form.get('path')

        result = delete_subtitles(media_type='movie',
                                  language=language,
                                  forced=forced,
                                  hi=hi,
                                  media_path=moviePath,
                                  subtitles_path=subtitlesPath,
                                  radarr_id=radarrId)
        if result:
            return '', 202
        else:
            return '', 204

class Providers(Resource):
    @authenticate
    def get(self):
        throttled_providers = list_throttled_providers()

        providers = list()
        for provider in throttled_providers:
            providers.append({
                "name": provider[0],
                "status": provider[1] if provider[1] is not None else "Good",
                "retry": provider[2] if provider[2] != "now" else "-"
            })
        return jsonify(data=providers)

    @authenticate
    def post(self):
        action = request.form.get('action')

        if action == 'reset':
            reset_throttled_providers()
            return '', 204

        return '', 400

class ProviderMovies(Resource):
    @authenticate
    def get(self):
        # Manual Search
        radarrId = request.args.get('radarrid')
        movieInfo = database.execute("SELECT title, path, sceneName, profileId FROM table_movies WHERE radarrId=?", (radarrId,), only_one=True)

        title = movieInfo['title']
        moviePath = path_mappings.path_replace_movie(movieInfo['path'])
        sceneName = movieInfo['sceneName']
        profileId = movieInfo['profileId']
        if sceneName is None: sceneName = "None"


        providers_list = get_providers()
        providers_auth = get_providers_auth()

        data = manual_search(moviePath, profileId, providers_list, providers_auth, sceneName, title,
                             'movie')
        if not data:
            data = []
        return jsonify(data=data)

    @authenticate
    def post(self):
        # Manual Download
        radarrId = request.args.get('radarrid')
        movieInfo = database.execute("SELECT title, path, sceneName, audio_language FROM table_movies WHERE radarrId=?", (radarrId,), only_one=True)

        title = movieInfo['title']
        moviePath = path_mappings.path_replace_movie(movieInfo['path'])
        sceneName = movieInfo['sceneName']
        if sceneName is None: sceneName = "None"
        audio_language = movieInfo['audio_language']

        language = request.form.get('language')
        hi = request.form.get('hi').capitalize()
        forced = request.form.get('forced').capitalize()
        selected_provider = request.form.get('provider')
        subtitle = request.form.get('subtitle')

        providers_auth = get_providers_auth()

        audio_language_list = get_audio_profile_languages(movie_id=radarrId)
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = 'None'

        try:
            result = manual_download_subtitle(moviePath, language, audio_language, hi, forced, subtitle,
                                              selected_provider, providers_auth, sceneName, title, 'movie')
            if result is not None:
                message = result[0]
                path = result[1]
                forced = result[5]
                if result[8]:
                    language_code = result[2] + ":hi"
                elif forced:
                    language_code = result[2] + ":forced"
                else:
                    language_code = result[2]
                provider = result[3]
                score = result[4]
                subs_id = result[6]
                subs_path = result[7]
                history_log_movie(2, radarrId, message, path, language_code, provider, score, subs_id, subs_path)
                if not settings.general.getboolean('dont_notify_manual_actions'):
                    send_notifications_movie(radarrId, message)
                store_subtitles_movie(path, moviePath)
        except OSError:
            pass

        return '', 204


class ProviderEpisodes(Resource):
    @authenticate
    def get(self):
        # Manual Search
        sonarrEpisodeId = request.args.get('episodeid')
        episodeInfo = database.execute("SELECT title, path, scene_name, audio_language, sonarrSeriesId FROM table_episodes WHERE sonarrEpisodeId=?", (sonarrEpisodeId,), only_one=True)

        title = episodeInfo['title']
        episodePath = path_mappings.path_replace(episodeInfo['path'])
        sceneName = episodeInfo['scene_name']
        seriesId = episodeInfo['sonarrSeriesId']

        seriesInfo = database.execute("SELECT profileId FROM table_shows WHERE sonarrSeriesId=?", (seriesId,), only_one=True)

        profileId = seriesInfo['profileId']
        if sceneName is None: sceneName = "None"

        providers_list = get_providers()
        providers_auth = get_providers_auth()

        data = manual_search(episodePath, profileId, providers_list, providers_auth, sceneName, title,
                             'series')
        if not data:
            data = []
        return jsonify(data=data)

    @authenticate
    def post(self):
        # Manual Download
        sonarrSeriesId = request.args.get('seriesid')
        sonarrEpisodeId = request.args.get('episodeid')
        episodeInfo = database.execute("SELECT title, path, scene_name FROM table_episodes WHERE sonarrEpisodeId=?", (sonarrEpisodeId,), only_one=True)

        title = episodeInfo['title']
        episodePath = episodeInfo['path']
        sceneName = episodeInfo['scene_name']
        if sceneName is None: sceneName = "None"

        language = request.form.get('language')
        hi = request.form.get('hi').capitalize()
        forced = request.form.get('forced').capitalize()
        selected_provider = request.form.get('provider')
        subtitle = request.form.get('subtitle')
        providers_auth = get_providers_auth()

        audio_language_list = get_audio_profile_languages(episode_id=sonarrEpisodeId)
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = 'None'

        try:
            result = manual_download_subtitle(episodePath, language, audio_language, hi, forced, subtitle, selected_provider, providers_auth, sceneName, title, 'series')
            if result is not None:
                message = result[0]
                path = result[1]
                forced = result[5]
                if result[8]:
                    language_code = result[2] + ":hi"
                elif forced:
                    language_code = result[2] + ":forced"
                else:
                    language_code = result[2]
                provider = result[3]
                score = result[4]
                subs_id = result[6]
                subs_path = result[7]
                history_log(2, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score, subs_id, subs_path)
                if not settings.general.getboolean('dont_notify_manual_actions'):
                    send_notifications(sonarrSeriesId, sonarrEpisodeId, message)
                store_subtitles(path, episodePath)
            return result, 201
        except OSError:
            pass

        return '', 204


class EpisodesHistory(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        episodeid = request.args.get('episodeid')

        upgradable_episodes_not_perfect = []
        if settings.general.getboolean('upgrade_subs'):
            days_to_upgrade_subs = settings.general.days_to_upgrade_subs
            minimum_timestamp = ((datetime.datetime.now() - timedelta(days=int(days_to_upgrade_subs))) -
                                 datetime.datetime(1970, 1, 1)).total_seconds()

            if settings.general.getboolean('upgrade_manual'):
                query_actions = [1, 2, 3, 6]
            else:
                query_actions = [1, 3]

            upgradable_episodes = database.execute(
                "SELECT video_path, MAX(timestamp) as timestamp, score, table_shows.tags, table_episodes.monitored, "
                "table_shows.seriesType FROM table_history INNER JOIN table_episodes on "
                "table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId INNER JOIN table_shows on "
                "table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE action IN (" +
                ','.join(map(str, query_actions)) + ") AND  timestamp > ? AND score is not null" +
                get_exclusion_clause('series') + " GROUP BY table_history.video_path", (minimum_timestamp,))

            for upgradable_episode in upgradable_episodes:
                if upgradable_episode['timestamp'] > minimum_timestamp:
                    try:
                        int(upgradable_episode['score'])
                    except ValueError:
                        pass
                    else:
                        if int(upgradable_episode['score']) < 360:
                            upgradable_episodes_not_perfect.append(upgradable_episode)

        # TODO: Find a better solution
        query_limit = ""
        if episodeid:
            query_limit = f"AND table_episodes.sonarrEpisodeId={episodeid}"

        episode_history = database.execute("SELECT table_shows.title as seriesTitle, table_episodes.monitored, "
                                    "table_episodes.season || 'x' || table_episodes.episode as episode_number, "
                                    "table_episodes.title as episodeTitle, table_history.timestamp, table_history.subs_id, "
                                    "table_history.description, table_history.sonarrSeriesId, table_episodes.path, "
                                    "table_history.language, table_history.score, table_shows.tags, table_history.action, "
                                    "table_history.subtitles_path, table_history.sonarrEpisodeId, table_history.provider, "
                                    "table_shows.seriesType FROM table_history LEFT JOIN table_shows on "
                                    "table_shows.sonarrSeriesId = table_history.sonarrSeriesId LEFT JOIN table_episodes on "
                                    "table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId WHERE "
                                    "table_episodes.title is not NULL " + query_limit + " ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                                    (length, start))

        for item in episode_history:
            # Mark episode as upgradable or not
            item.update({"upgradable": False})
            if {"video_path": str(item['path']), "timestamp": float(item['timestamp']), "score": str(item['score']), "tags": str(item['tags']), "monitored": str(item['monitored']), "seriesType": str(item['seriesType'])} in upgradable_episodes_not_perfect:
                if os.path.isfile(path_mappings.path_replace(item['subtitles_path'])):
                    item.update({"upgradable": True})

            postprocessEpisode(item)

            if item['score']:
                item['score'] = str(round((int(item['score']) * 100 / 360), 2)) + "%"

            # Make timestamp pretty
            if item['timestamp']:
                item['timestamp'] = pretty.date(int(item['timestamp']))

            # Check if subtitles is blacklisted
            # if item['action'] not in [0, 4, 5]:
            #     blacklist_db = database.execute("SELECT provider, subs_id FROM table_blacklist WHERE provider=? AND "
            #                                     "subs_id=?", (item['provider'], item['subs_id']))
            # else:
            #     blacklist_db = []

            # if len(blacklist_db):
            #     item.update({"blacklisted": True})
            # else:
            #     item.update({"blacklisted": False})

        return jsonify(data=episode_history)


class MoviesHistory(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        radarrid = request.args.get('radarrid')

        upgradable_movies = []
        upgradable_movies_not_perfect = []
        if settings.general.getboolean('upgrade_subs'):
            days_to_upgrade_subs = settings.general.days_to_upgrade_subs
            minimum_timestamp = ((datetime.datetime.now() - timedelta(days=int(days_to_upgrade_subs))) -
                                 datetime.datetime(1970, 1, 1)).total_seconds()

            if settings.general.getboolean('upgrade_manual'):
                query_actions = [1, 2, 3, 6]
            else:
                query_actions = [1, 3]

            upgradable_movies = database.execute(
                "SELECT video_path, MAX(timestamp) as timestamp, score, tags, monitored FROM table_history_movie "
                "INNER JOIN table_movies on table_movies.radarrId=table_history_movie.radarrId WHERE action IN (" +
                ','.join(map(str, query_actions)) + ") AND timestamp > ? AND score is not NULL" +
                get_exclusion_clause('movie') + " GROUP BY video_path", (minimum_timestamp,))

            for upgradable_movie in upgradable_movies:
                if upgradable_movie['timestamp'] > minimum_timestamp:
                    try:
                        int(upgradable_movie['score'])
                    except ValueError:
                        pass
                    else:
                        if int(upgradable_movie['score']) < 120:
                            upgradable_movies_not_perfect.append(upgradable_movie)

        # TODO: Find a better solution
        query_limit = ""
        if radarrid:
            query_limit = f"AND table_movies.radarrid={radarrid}"

        movie_history = database.execute(
            "SELECT table_history_movie.action, table_movies.title, table_history_movie.timestamp, "
            "table_history_movie.description, table_history_movie.radarrId, table_movies.monitored,"
            "table_history_movie.video_path as path, table_history_movie.language, table_movies.tags, "
            "table_history_movie.score, table_history_movie.subs_id, table_history_movie.provider, "
            "table_history_movie.subtitles_path, table_history_movie.subtitles_path FROM "
            "table_history_movie LEFT JOIN table_movies on table_movies.radarrId = "
            "table_history_movie.radarrId WHERE table_movies.title is not NULL " + query_limit + " ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (length, start))

        for item in movie_history:
            # Mark movies as upgradable or not
            item.update({"upgradable": False})
            if {"video_path": str(item['path']), "timestamp": float(item['timestamp']), "score": str(item['score']), "tags": str(item['tags']), "monitored": str(item['monitored'])} in upgradable_movies_not_perfect:
                if os.path.isfile(path_mappings.path_replace_movie(item['subtitles_path'])):
                    item.update({"upgradable": True})

            postprocessMovie(item)

            if item['score']:
                item['score'] = str(round((int(item['score']) * 100 / 120), 2)) + "%"

            # Make timestamp pretty
            if item['timestamp']:
                item['timestamp'] = pretty.date(int(item['timestamp']))

            # Check if subtitles is blacklisted
            # if item['action'] not in [0, 4, 5]:
            #     blacklist_db = database.execute("SELECT provider, subs_id FROM table_blacklist_movie WHERE provider=? "
            #                                     "AND subs_id=?", (item['provider'], item['subs_id']))
            # else:
            #     blacklist_db = []

            # if len(blacklist_db):
            #     item.update({"blacklisted": True})
            # else:
            #     item.update({"blacklisted": False})

        return jsonify(data=movie_history)


class HistoryStats(Resource):
    @authenticate
    def get(self):
        timeframe = request.args.get('timeframe') or 'month'
        action = request.args.get('action') or 'All'
        provider = request.args.get('provider') or 'All'
        language = request.args.get('language') or 'All'

        history_where_clause = " WHERE id"

        # timeframe must be in ['week', 'month', 'trimester', 'year']
        if timeframe == 'year':
            days = 364
        elif timeframe == 'trimester':
            days = 90
        elif timeframe == 'month':
            days = 30
        elif timeframe == 'week':
            days = 6

        history_where_clause += " AND datetime(timestamp, 'unixepoch') BETWEEN datetime('now', '-" + str(days) + \
                                " days') AND datetime('now', 'localtime')"
        if action != 'All':
            history_where_clause += " AND action = " + action
        else:
            history_where_clause += " AND action IN (1,2,3)"
        if provider != 'All':
            history_where_clause += " AND provider = '" + provider + "'"
        if language != 'All':
            history_where_clause += " AND language = '" + language + "'"

        data_series = database.execute("SELECT strftime ('%Y-%m-%d',datetime(timestamp, 'unixepoch')) as date, "
                                       "COUNT(id) as count FROM table_history" + history_where_clause +
                                       " GROUP BY strftime ('%Y-%m-%d',datetime(timestamp, 'unixepoch'))")
        data_movies = database.execute("SELECT strftime ('%Y-%m-%d',datetime(timestamp, 'unixepoch')) as date, "
                                       "COUNT(id) as count FROM table_history_movie" + history_where_clause +
                                       " GROUP BY strftime ('%Y-%m-%d',datetime(timestamp, 'unixepoch'))")

        for dt in rrule.rrule(rrule.DAILY,
                              dtstart=datetime.datetime.now() - datetime.timedelta(days=days),
                              until=datetime.datetime.now()):
            if not any(d['date'] == dt.strftime('%Y-%m-%d') for d in data_series):
                data_series.append({'date': dt.strftime('%Y-%m-%d'), 'count': 0})
            if not any(d['date'] == dt.strftime('%Y-%m-%d') for d in data_movies):
                data_movies.append({'date': dt.strftime('%Y-%m-%d'), 'count': 0})

        sorted_data_series = sorted(data_series, key=lambda i: i['date'])
        sorted_data_movies = sorted(data_movies, key=lambda i: i['date'])

        return jsonify(data_series=sorted_data_series, data_movies=sorted_data_movies)

# GET: Get Wanted Episodes
class EpisodesWanted(Resource):
    @authenticate
    def get(self):
        data = database.execute("SELECT table_shows.title as seriesTitle, table_episodes.monitored, "
                                "table_episodes.season || 'x' || table_episodes.episode as episode_number, "
                                "table_episodes.title as episodeTitle, table_episodes.missing_subtitles, "
                                "table_episodes.sonarrSeriesId, table_episodes.path, "
                                "table_episodes.sonarrEpisodeId, table_episodes.scene_name as sceneName, table_shows.tags, "
                                "table_episodes.failedAttempts, table_shows.seriesType FROM table_episodes INNER JOIN "
                                "table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE "
                                "table_episodes.missing_subtitles != '[]'" + get_exclusion_clause('series') +
                                " ORDER BY table_episodes._rowid_ ")

        for item in data:
            postprocessEpisode(item)

        return jsonify(data=data)


# GET: get blacklist
# POST: add blacklist
# DELETE: remove blacklist
class EpisodesBlacklist(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1

        data = database.execute("SELECT table_shows.title as seriesTitle, table_episodes.season || 'x' || "
                                "table_episodes.episode as episode_number, table_episodes.title as episodeTitle, "
                                "table_episodes.sonarrSeriesId, table_blacklist.provider, table_blacklist.subs_id, "
                                "table_blacklist.language, table_blacklist.timestamp FROM table_blacklist INNER JOIN "
                                "table_episodes on table_episodes.sonarrEpisodeId = table_blacklist.sonarr_episode_id "
                                "INNER JOIN table_shows on table_shows.sonarrSeriesId = "
                                "table_blacklist.sonarr_series_id ORDER BY table_blacklist.timestamp DESC LIMIT ? "
                                "OFFSET ?", (length, start))

        for item in data:
            # Make timestamp pretty
            item.update({'timestamp': pretty.date(datetime.datetime.fromtimestamp(item['timestamp']))})

            postprocessEpisode(item)

        return jsonify(data=data)

    @authenticate
    def post(self):
        sonarr_series_id = int(request.args.get('seriesid'))
        sonarr_episode_id = int(request.args.get('episodeid'))
        provider = request.form.get('provider')
        subs_id = request.form.get('subs_id')
        language = request.form.get('language')
        forced = request.form.get('forced')
        hi = request.form.get('hi')
        if hi == 'true':
            language_str = language + ':hi'
        elif forced == 'true':
            language_str = language + ':forced'
        else:
            language_str = language
        media_path = request.form.get('path')
        subtitles_path = request.form.get('subtitles_path')

        blacklist_log(sonarr_series_id=sonarr_series_id,
                      sonarr_episode_id=sonarr_episode_id,
                      provider=provider,
                      subs_id=subs_id,
                      language=language_str)
        delete_subtitles(media_type='series',
                         language=alpha3_from_alpha2(language),
                         forced=forced,
                         hi=hi,
                         media_path=media_path,
                         subtitles_path=subtitles_path,
                         sonarr_series_id=sonarr_series_id,
                         sonarr_episode_id=sonarr_episode_id)
        episode_download_subtitles(sonarr_episode_id)
        event_stream(type='episodeHistory')
        return '', 200

    @authenticate
    def delete(self):
        if request.args.get("all") == "true":
            blacklist_delete_all()
        else:
            provider = request.form.get('provider')
            subs_id = request.form.get('subs_id')
            blacklist_delete(provider=provider, subs_id=subs_id)
        return '', 204

# GET: get blacklist
# POST: add blacklist
# DELETE: remove blacklist
class MoviesBlacklist(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1

        data = database.execute("SELECT table_movies.title, table_movies.radarrId, table_blacklist_movie.provider, "
                                "table_blacklist_movie.subs_id, table_blacklist_movie.language, "
                                "table_blacklist_movie.timestamp FROM table_blacklist_movie INNER JOIN "
                                "table_movies on table_movies.radarrId = table_blacklist_movie.radarr_id "
                                "ORDER BY table_blacklist_movie.timestamp DESC LIMIT ? "
                                "OFFSET ?", (length, start))

        for item in data:

            postprocessMovie(item)

            # Make timestamp pretty
            item.update({'timestamp': pretty.date(datetime.datetime.fromtimestamp(item['timestamp']))})

        return jsonify(data=data)

    @authenticate
    def post(self):
        radarr_id = int(request.args.get('radarrid'))
        provider = request.form.get('provider')
        subs_id = request.form.get('subs_id')
        language = request.form.get('language')
        forced = request.form.get('forced')
        hi = request.form.get('hi')
        if hi == 'true':
            language_str = language + ':hi'
        elif forced == 'true':
            language_str = language + ':forced'
        else:
            language_str = language
        media_path = request.form.get('path')
        subtitles_path = request.form.get('subtitles_path')

        blacklist_log_movie(radarr_id=radarr_id,
                            provider=provider,
                            subs_id=subs_id,
                            language=language_str)
        delete_subtitles(media_type='movie',
                         language=alpha3_from_alpha2(language),
                         forced=forced,
                         hi=hi,
                         media_path=media_path,
                         subtitles_path=subtitles_path,
                         radarr_id=radarr_id)
        movies_download_subtitles(radarr_id)
        event_stream(type='movieHistory')
        return '', 200

    @authenticate
    def delete(self):
        if request.args.get("all") == "true":
            blacklist_delete_all_movie()
        else:
            provider = request.form.get('provider')
            subs_id = request.form.get('subs_id')
            blacklist_delete_movie(provider=provider, subs_id=subs_id)
        return '', 200


class Subtitles(Resource):
    @authenticate
    def patch(self):
        action = request.args.get('action')

        language = request.form.get('language')
        subtitles_path = request.form.get('path')
        media_type = request.form.get('type')
        id = request.form.get('id')

        if media_type == 'episode':
            subtitles_path = path_mappings.path_replace(subtitles_path)
            metadata = database.execute("SELECT path, sonarrSeriesId FROM table_episodes"
                                        " WHERE sonarrEpisodeId = ?", (id,), only_one=True)
            video_path = path_mappings.path_replace(metadata['path'])
        else:
            subtitles_path = path_mappings.path_replace_movie(subtitles_path)
            metadata = database.execute("SELECT path FROM table_movies WHERE radarrId = ?",
                                        (id,), only_one=True)
            video_path = path_mappings.path_replace_movie(metadata['path'])

        if action == 'sync':
            if media_type == 'episode':
                subsync.sync(video_path=video_path, srt_path=subtitles_path,
                             srt_lang=language, media_type='series', sonarr_series_id=metadata['sonarrSeriesId'],
                             sonarr_episode_id=int(id))
            else:
                subsync.sync(video_path=video_path, srt_path=subtitles_path,
                            srt_lang=language, media_type='movies', radarr_id=id)
        elif action == 'translate':
            dest_language = language
            forced = True if request.form.get('forced') == 'true' else False
            hi = True if request.form.get('hi') == 'true' else False
            result = translate_subtitles_file(video_path=video_path, source_srt_file=subtitles_path, to_lang=dest_language,
                                          forced=forced, hi=hi)
            if result:
                if media_type == 'episode':
                    store_subtitles(path_mappings.path_replace_reverse(video_path), video_path)
                else:
                    store_subtitles_movie(path_mappings.path_replace_reverse_movie(video_path), video_path)
                return '', 200
            else:
                return '', 404
        else:
            subtitles_apply_mods(language, subtitles_path, [action])

        return '', 204

class SubtitleNameInfo(Resource):
    @authenticate
    def get(self):
        names = request.args.getlist('filenames[]')
        results = []
        for name in names:
            opts = dict()
            opts['type'] = 'episode'
            result = guessit(name, options=opts)
            result['filename'] = name
            if 'subtitle_language' in result:
                result['subtitle_language'] = str(result['subtitle_language'])

            if 'episode' in result:
                result['episode'] = result['episode']
            else:
                result['episode'] = 0

            if 'season' in result:
                result['season'] = result['season']
            else:
                result['season'] = 0

            results.append(result)

        return jsonify(data=results)


class BrowseBazarrFS(Resource):
    @authenticate
    def get(self):
        path = request.args.get('path') or ''
        data = []
        try:
            result = browse_bazarr_filesystem(path)
            if result is None:
                raise ValueError
        except Exception:
            return jsonify([])
        for item in result['directories']:
            data.append({'name': item['name'], 'children': True, 'path': item['path']})
        return jsonify(data)


class BrowseSonarrFS(Resource):
    @authenticate
    def get(self):
        path = request.args.get('path') or ''
        data = []
        try:
            result = browse_sonarr_filesystem(path)
            if result is None:
                raise ValueError
        except Exception:
            return jsonify([])
        for item in result['directories']:
            data.append({'name': item['name'], 'children': True, 'path': item['path']})
        return jsonify(data)


class BrowseRadarrFS(Resource):
    @authenticate
    def get(self):
        path = request.args.get('path') or ''
        data = []
        try:
            result = browse_radarr_filesystem(path)
            if result is None:
                raise ValueError
        except Exception:
            return jsonify([])
        for item in result['directories']:
            data.append({'name': item['name'], 'children': True, 'path': item['path']})
        return jsonify(data)


api.add_resource(BadgesSeries, '/badges/series')
api.add_resource(BadgesMovies, '/badges/movies')
api.add_resource(BadgesProviders, '/badges/providers')

api.add_resource(Providers, '/providers')
api.add_resource(ProviderMovies, '/providers/movies')
api.add_resource(ProviderEpisodes, '/providers/episodes')

api.add_resource(SystemAccount, '/system/account')
api.add_resource(System, '/system')
api.add_resource(SystemTasks, '/system/tasks')
api.add_resource(SystemLogs, '/system/logs')
api.add_resource(SystemStatus, '/system/status')
api.add_resource(SystemReleases, '/system/releases')
api.add_resource(SystemSettings, '/system/settings')
api.add_resource(Languages, '/system/languages')
api.add_resource(LanguagesProfiles, '/system/languages/profiles')
api.add_resource(Notifications, '/system/notifications')

api.add_resource(Subtitles, '/subtitles')
api.add_resource(SubtitleNameInfo, '/subtitles/info')

api.add_resource(Series, '/series')

api.add_resource(Episodes, '/episodes')
api.add_resource(EpisodesWanted, '/episodes/wanted')
api.add_resource(EpisodesSubtitles, '/episodes/subtitles')
api.add_resource(EpisodesHistory, '/episodes/history')
api.add_resource(EpisodesBlacklist, '/episodes/blacklist')

api.add_resource(Movies, '/movies')
api.add_resource(MoviesSubtitles, '/movies/subtitles')
api.add_resource(MoviesHistory, '/movies/history')
api.add_resource(MoviesBlacklist, '/movies/blacklist')

api.add_resource(HistoryStats, '/history/stats')

api.add_resource(BrowseBazarrFS, '/files')
api.add_resource(BrowseSonarrFS, '/files/sonarr')
api.add_resource(BrowseRadarrFS, '/files/radarr')

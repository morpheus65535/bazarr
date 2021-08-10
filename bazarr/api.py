# coding=utf-8

import sys
import os
import ast
from datetime import timedelta
from dateutil import rrule
import pretty
import time
import operator
from operator import itemgetter
from functools import reduce
import platform
import re
import json
import hashlib
import apprise
import gc
from peewee import fn, Value
import requests
from bs4 import BeautifulSoup as bso

from get_args import args
from config import settings, base_url, save_settings, get_settings
from logger import empty_log

from init import *
import logging
from database import get_exclusion_clause, get_profiles_list, get_desired_languages, get_profile_id_name, \
    get_audio_profile_languages, update_profile_id_list, convert_list_to_clause, TableEpisodes, TableShows, \
    TableMovies, TableSettingsLanguages, TableSettingsNotifier, TableLanguagesProfiles, TableHistory, \
    TableHistoryMovie, TableBlacklist, TableBlacklistMovie
from helper import path_mappings
from get_languages import language_from_alpha2, language_from_alpha3, alpha2_from_alpha3, alpha3_from_alpha2
from get_subtitle import download_subtitle, series_download_subtitles, manual_search, manual_download_subtitle, \
    manual_upload_subtitle, wanted_search_missing_subtitles_series, wanted_search_missing_subtitles_movies, \
    episode_download_subtitles, movies_download_subtitles
from notifier import send_notifications, send_notifications_movie
from list_subtitles import store_subtitles, store_subtitles_movie, series_scan_subtitles, movies_scan_subtitles, \
    list_missing_subtitles, list_missing_subtitles_movies
from utils import history_log, history_log_movie, blacklist_log, blacklist_delete, blacklist_delete_all, \
    blacklist_log_movie, blacklist_delete_movie, blacklist_delete_all_movie, get_sonarr_info, get_radarr_info, \
    delete_subtitles, subtitles_apply_mods, translate_subtitles_file, check_credentials, get_health_issues
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

api_bp = Blueprint('api', __name__, url_prefix=base_url.rstrip('/') + '/api')
api = Api(api_bp)

None_Keys = ['null', 'undefined', '', None]

False_Keys = ['False', 'false', '0']


def authenticate(actual_method):
    @wraps(actual_method)
    def wrapper(*args, **kwargs):
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
    # Remove ffprobe_cache
    if 'ffprobe_cache' in item:
        del (item['ffprobe_cache'])

    # Parse tags
    if 'tags' in item:
        if item['tags'] is None:
            item['tags'] = []
        else:
            item['tags'] = ast.literal_eval(item['tags'])

    if 'monitored' in item:
        if item['monitored'] is None:
            item['monitored'] = False
        else:
            item['monitored'] = item['monitored'] == 'True'

    if 'hearing_impaired' in item and item['hearing_impaired'] is not None:
        if item['hearing_impaired'] is None:
            item['hearing_impaired'] = False
        else:
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
    if 'audio_language' in item and item['audio_language'] is not None:
        item['audio_language'] = get_audio_profile_languages(series_id=item['sonarrSeriesId'])

    if 'alternateTitles' in item:
        if item['alternateTitles'] is None:
            item['alternativeTitles'] = []
        else:
            item['alternativeTitles'] = ast.literal_eval(item['alternateTitles'])
        del item["alternateTitles"]

    # Parse seriesType
    if 'seriesType' in item and item['seriesType'] is not None:
        item['seriesType'] = item['seriesType'].capitalize()

    if 'path' in item:
        item['path'] = path_mappings.path_replace(item['path'])

    # map poster and fanart to server proxy
    if 'poster' in item:
        poster = item['poster']
        item['poster'] = f"{base_url}/images/series{poster}"

    if 'fanart' in item:
        fanart = item['fanart']
        item['fanart'] = f"{base_url}/images/series{fanart}"


def postprocessEpisode(item):
    postprocess(item)
    if 'audio_language' in item and item['audio_language'] is not None:
        item['audio_language'] = get_audio_profile_languages(episode_id=item['sonarrEpisodeId'])

    if 'subtitles' in item:
        if item['subtitles'] is None:
            raw_subtitles = []
        else:
            raw_subtitles = ast.literal_eval(item['subtitles'])
        subtitles = []

        for subs in raw_subtitles:
            subtitle = subs[0].split(':')
            sub = {"name": language_from_alpha2(subtitle[0]),
                   "code2": subtitle[0],
                   "code3": alpha3_from_alpha2(subtitle[0]),
                   "path": path_mappings.path_replace(subs[1]),
                   "forced": False,
                   "hi": False}
            if len(subtitle) > 1:
                sub["forced"] = True if subtitle[1] == 'forced' else False
                sub["hi"] = True if subtitle[1] == 'hi' else False

            subtitles.append(sub)

        item.update({"subtitles": subtitles})

    # Parse missing subtitles
    if 'missing_subtitles' in item:
        if item['missing_subtitles'] is None:
            item['missing_subtitles'] = []
        else:
            item['missing_subtitles'] = ast.literal_eval(item['missing_subtitles'])
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

    if 'scene_name' in item:
        item["sceneName"] = item["scene_name"]
        del item["scene_name"]

    if 'path' in item and item['path']:
        # Provide mapped path
        item['path'] = path_mappings.path_replace(item['path'])


# TODO: Move
def postprocessMovie(item):
    postprocess(item)
    # Parse audio language
    if 'audio_language' in item and item['audio_language'] is not None:
        item['audio_language'] = get_audio_profile_languages(movie_id=item['radarrId'])

    # Parse alternate titles
    if 'alternativeTitles' in item:
        if item['alternativeTitles'] is None:
            item['alternativeTitles'] = []
        else:
            item['alternativeTitles'] = ast.literal_eval(item['alternativeTitles'])

    # Parse failed attempts
    if 'failedAttempts' in item:
        if item['failedAttempts']:
            item['failedAttempts'] = ast.literal_eval(item['failedAttempts'])

    # Parse subtitles
    if 'subtitles' in item:
        if item['subtitles'] is None:
            item['subtitles'] = []
        else:
            item['subtitles'] = ast.literal_eval(item['subtitles'])
        for i, subs in enumerate(item['subtitles']):
            language = subs[0].split(':')
            item['subtitles'][i] = {"path": path_mappings.path_replace_movie(subs[1]),
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
            desired_lang_list = get_desired_languages(item['profileId'])
            item['subtitles'] = [x for x in item['subtitles'] if x['code2'] in desired_lang_list or x['path']]

        item['subtitles'] = sorted(item['subtitles'], key=itemgetter('name', 'forced'))

    # Parse missing subtitles
    if 'missing_subtitles' in item:
        if item['missing_subtitles'] is None:
            item['missing_subtitles'] = []
        else:
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
        if item['path']:
            item['path'] = path_mappings.path_replace_movie(item['path'])

    if 'subtitles_path' in item:
        # Provide mapped subtitles path
        item['subtitles_path'] = path_mappings.path_replace_movie(item['subtitles_path'])

    # map poster and fanart to server proxy
    if 'poster' in item:
        poster = item['poster']
        item['poster'] = f"{base_url}/images/movies{poster}"

    if 'fanart' in item:
        fanart = item['fanart']
        item['fanart'] = f"{base_url}/images/movies{fanart}"


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


class Badges(Resource):
    @authenticate
    def get(self):
        episodes_conditions = [(TableEpisodes.missing_subtitles is not None),
                               (TableEpisodes.missing_subtitles != '[]')]
        episodes_conditions += get_exclusion_clause('series')
        missing_episodes = TableEpisodes.select(TableShows.tags,
                                                TableShows.seriesType,
                                                TableEpisodes.monitored)\
            .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId))\
            .where(reduce(operator.and_, episodes_conditions))\
            .count()

        movies_conditions = [(TableMovies.missing_subtitles is not None),
                             (TableMovies.missing_subtitles != '[]')]
        movies_conditions += get_exclusion_clause('movie')
        missing_movies = TableMovies.select(TableMovies.tags,
                                            TableMovies.monitored)\
            .where(reduce(operator.and_, movies_conditions))\
            .count()

        throttled_providers = len(eval(str(get_throttled_providers())))

        health_issues = len(get_health_issues())

        result = {
            "episodes": missing_episodes,
            "movies": missing_movies,
            "providers": throttled_providers,
            "status": health_issues
        }
        return jsonify(result)


class Languages(Resource):
    @authenticate
    def get(self):
        history = request.args.get('history')
        if history and history not in False_Keys:
            languages = list(TableHistory.select(TableHistory.language)
                             .where(TableHistory.language != None)
                             .dicts())
            languages += list(TableHistoryMovie.select(TableHistoryMovie.language)
                             .where(TableHistoryMovie.language != None)
                              .dicts())
            languages_list = list(set([l['language'].split(':')[0] for l in languages]))
            languages_dicts = []
            for language in languages_list:
                code2 = None
                if len(language) == 2:
                    code2 = language
                elif len(language) == 3:
                    code2 = alpha2_from_alpha3(language)
                else:
                    continue

                if not any(x['code2'] == code2 for x in languages_dicts):
                    try:
                        languages_dicts.append({
                            'code2': code2,
                            'name': language_from_alpha2(code2),
                            # Compatibility: Use false temporarily
                            'enabled': False
                        })
                    except:
                        continue
            return jsonify(sorted(languages_dicts, key=itemgetter('name')))

        result = TableSettingsLanguages.select(TableSettingsLanguages.name,
                                               TableSettingsLanguages.code2,
                                               TableSettingsLanguages.enabled)\
            .order_by(TableSettingsLanguages.name).dicts()
        result = list(result)
        for item in result:
            item['enabled'] = item['enabled'] == 1
        return jsonify(result)


class LanguagesProfiles(Resource):
    @authenticate
    def get(self):
        return jsonify(get_profiles_list())


class Notifications(Resource):
    @authenticate
    def patch(self):
        url = request.form.get("url")

        asset = apprise.AppriseAsset(async_mode=False)

        apobj = apprise.Apprise(asset=asset)

        apobj.add(url)

        apobj.notify(
            title='Bazarr test notification',
            body='Test notification'
        )

        return '', 204


class Searches(Resource):
    @authenticate
    def get(self):
        query = request.args.get('query')
        search_list = []

        if query:
            if settings.general.getboolean('use_sonarr'):
                # Get matching series
                series = TableShows.select(TableShows.title,
                                           TableShows.sonarrSeriesId,
                                           TableShows.year)\
                    .where(TableShows.title.contains(query))\
                    .order_by(TableShows.title)\
                    .dicts()
                series = list(series)
                search_list += series

            if settings.general.getboolean('use_radarr'):
                # Get matching movies
                movies = TableMovies.select(TableMovies.title,
                                            TableMovies.radarrId,
                                            TableMovies.year) \
                    .where(TableMovies.title.contains(query)) \
                    .order_by(TableMovies.title) \
                    .dicts()
                movies = list(movies)
                search_list += movies

        return jsonify(search_list)


class SystemSettings(Resource):
    @authenticate
    def get(self):
        data = get_settings()

        notifications = TableSettingsNotifier.select().order_by(TableSettingsNotifier.name).dicts()
        notifications = list(notifications)
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
            TableSettingsLanguages.update({
                TableSettingsLanguages.enabled: 0
            }).execute()
            for code in enabled_languages:
                TableSettingsLanguages.update({
                    TableSettingsLanguages.enabled: 1
                })\
                    .where(TableSettingsLanguages.code2 == code)\
                    .execute()
            event_stream("languages")

        languages_profiles = request.form.get('languages-profiles')
        if languages_profiles:
            existing_ids = TableLanguagesProfiles.select(TableLanguagesProfiles.profileId).dicts()
            existing_ids = list(existing_ids)
            existing = [x['profileId'] for x in existing_ids]
            for item in json.loads(languages_profiles):
                if item['profileId'] in existing:
                    # Update existing profiles
                    TableLanguagesProfiles.update({
                        TableLanguagesProfiles.name: item['name'],
                        TableLanguagesProfiles.cutoff: item['cutoff'] if item['cutoff'] != 'null' else None,
                        TableLanguagesProfiles.items: json.dumps(item['items'])
                    })\
                        .where(TableLanguagesProfiles.profileId == item['profileId'])\
                        .execute()
                    existing.remove(item['profileId'])
                else:
                    # Add new profiles
                    TableLanguagesProfiles.insert({
                        TableLanguagesProfiles.profileId: item['profileId'],
                        TableLanguagesProfiles.name: item['name'],
                        TableLanguagesProfiles.cutoff: item['cutoff'] if item['cutoff'] != 'null' else None,
                        TableLanguagesProfiles.items: json.dumps(item['items'])
                    }).execute()
            for profileId in existing:
                # Unassign this profileId from series and movies
                TableShows.update({
                    TableShows.profileId: None
                }).where(TableShows.profileId == profileId).execute()
                TableMovies.update({
                    TableMovies.profileId: None
                }).where(TableMovies.profileId == profileId).execute()
                # Remove deleted profiles
                TableLanguagesProfiles.delete().where(TableLanguagesProfiles.profileId == profileId).execute()

            update_profile_id_list()
            event_stream("languages")

            if settings.general.getboolean('use_sonarr'):
                scheduler.add_job(list_missing_subtitles, kwargs={'send_event': False})
            if settings.general.getboolean('use_radarr'):
                scheduler.add_job(list_missing_subtitles_movies, kwargs={'send_event': False})

        # Update Notification
        notifications = request.form.getlist('notifications-providers')
        for item in notifications:
            item = json.loads(item)
            TableSettingsNotifier.update({
                TableSettingsNotifier.enabled: item['enabled'],
                TableSettingsNotifier.url: item['url']
            }).where(TableSettingsNotifier.name == item['name']).execute()

        save_settings(zip(request.form.keys(), request.form.listvalues()))
        event_stream("settings")
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
            raw_lines = file.read()
            lines = raw_lines.split('|\n')
            for line in lines:
                if line == '':
                    continue
                raw_message = line.split('|')
                raw_message_len = len(raw_message)
                if raw_message_len > 3:
                    log = dict()
                    log["timestamp"] = raw_message[0]
                    log["type"] = raw_message[1].rstrip()
                    log["message"] = raw_message[3]
                    if raw_message_len > 4 and raw_message[4] != '\n':
                        log['exception'] = raw_message[4].strip('\'').replace('  ', '\u2003\u2003')
                logs.append(log)

            logs.reverse()
        return jsonify(data=logs)

    @authenticate
    def delete(self):
        empty_log()
        return '', 204


class SystemStatus(Resource):
    @authenticate
    def get(self):
        system_status = {}
        system_status.update({'bazarr_version': os.environ["BAZARR_VERSION"]})
        system_status.update({'sonarr_version': get_sonarr_info.version()})
        system_status.update({'radarr_version': get_radarr_info.version()})
        system_status.update({'operating_system': platform.platform()})
        system_status.update({'python_version': platform.python_version()})
        system_status.update({'bazarr_directory': os.path.dirname(os.path.dirname(__file__))})
        system_status.update({'bazarr_config_directory': args.config_dir})
        return jsonify(data=system_status)


class SystemHealth(Resource):
    @authenticate
    def get(self):
        return jsonify(data=get_health_issues())


class SystemReleases(Resource):
    @authenticate
    def get(self):
        filtered_releases = []
        try:
            with io.open(os.path.join(args.config_dir, 'config', 'releases.txt'), 'r', encoding='UTF-8') as f:
                releases = json.loads(f.read())

            for release in releases:
                if settings.general.branch == 'master' and not release['prerelease']:
                    filtered_releases.append(release)
                elif settings.general.branch != 'master' and any(not x['prerelease'] for x in filtered_releases):
                    continue
                elif settings.general.branch != 'master':
                    filtered_releases.append(release)
            if settings.general.branch == 'master':
                filtered_releases = filtered_releases[:5]

            current_version = os.environ["BAZARR_VERSION"]

            for i, release in enumerate(filtered_releases):
                body = release['body'].replace('- ', '').split('\n')[1:]
                filtered_releases[i] = {"body": body,
                                        "name": release['name'],
                                        "date": release['date'][:10],
                                        "prerelease": release['prerelease'],
                                        "current": release['name'].lstrip('v') == current_version}

        except Exception as e:
            logging.exception(
                'BAZARR cannot parse releases caching file: ' + os.path.join(args.config_dir, 'config', 'releases.txt'))
        return jsonify(data=filtered_releases)


class Series(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        seriesId = request.args.getlist('seriesid[]')

        count = TableShows.select().count()

        if len(seriesId) != 0:
            result = TableShows.select()\
                .where(TableShows.sonarrSeriesId.in_(seriesId))\
                .order_by(TableShows.sortTitle).dicts()
        else:
            result = TableShows.select().order_by(TableShows.sortTitle).limit(length).offset(start).dicts()

        result = list(result)

        for item in result:
            postprocessSeries(item)

            # Add missing subtitles episode count
            episodes_missing_conditions = [(TableEpisodes.sonarrSeriesId == item['sonarrSeriesId']),
                                           (TableEpisodes.missing_subtitles != '[]')]
            episodes_missing_conditions += get_exclusion_clause('series')

            episodeMissingCount = TableEpisodes.select(TableShows.tags,
                                                       TableEpisodes.monitored,
                                                       TableShows.seriesType)\
                .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId))\
                .where(reduce(operator.and_, episodes_missing_conditions))\
                .count()
            item.update({"episodeMissingCount": episodeMissingCount})

            # Add episode count
            episodeFileCount = TableEpisodes.select(TableShows.tags,
                                                    TableEpisodes.monitored,
                                                    TableShows.seriesType)\
                .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId))\
                .where(TableEpisodes.sonarrSeriesId == item['sonarrSeriesId'])\
                .count()
            item.update({"episodeFileCount": episodeFileCount})

        return jsonify(data=result, total=count)

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

            TableShows.update({
                TableShows.profileId: profileId
            })\
                .where(TableShows.sonarrSeriesId == seriesId)\
                .execute()

            list_missing_subtitles(no=seriesId, send_event=False)

            event_stream(type='series', payload=seriesId)

            episode_id_list = TableEpisodes\
                .select(TableEpisodes.sonarrEpisodeId)\
                .where(TableEpisodes.sonarrSeriesId == seriesId)\
                .dicts()
            
            for item in episode_id_list:
                event_stream(type='episode-wanted', payload=item['sonarrEpisodeId'])

        event_stream(type='badges')

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
        seriesId = request.args.getlist('seriesid[]')
        episodeId = request.args.getlist('episodeid[]')

        if len(episodeId) > 0:
            result = TableEpisodes.select().where(TableEpisodes.sonarrEpisodeId.in_(episodeId)).dicts()
        elif len(seriesId) > 0:
            result = TableEpisodes.select()\
                .where(TableEpisodes.sonarrSeriesId.in_(seriesId))\
                .order_by(TableEpisodes.season.desc(), TableEpisodes.episode.desc())\
                .dicts()
        else:
            return "Series or Episode ID not provided", 400

        result = list(result)
        for item in result:
            postprocessEpisode(item)

        return jsonify(data=result)


# PATCH: Download Subtitles
# POST: Upload Subtitles
# DELETE: Delete Subtitles
class EpisodesSubtitles(Resource):
    @authenticate
    def patch(self):
        sonarrSeriesId = request.args.get('seriesid')
        sonarrEpisodeId = request.args.get('episodeid')
        episodeInfo = TableEpisodes.select(TableEpisodes.title,
                                           TableEpisodes.path,
                                           TableEpisodes.scene_name,
                                           TableEpisodes.audio_language)\
            .where(TableEpisodes.sonarrEpisodeId == sonarrEpisodeId)\
            .dicts()\
            .get()

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
            result = download_subtitle(episodePath, language, audio_language, hi, forced, providers_list,
                                       providers_auth, sceneName, title, 'series')
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
                history_log(1, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score, subs_id,
                            subs_path)
                send_notifications(sonarrSeriesId, sonarrEpisodeId, message)
                store_subtitles(path, episodePath)
            else:
                event_stream(type='episode', payload=sonarrEpisodeId)

        except OSError:
            pass

        return '', 204

    @authenticate
    def post(self):
        sonarrSeriesId = request.args.get('seriesid')
        sonarrEpisodeId = request.args.get('episodeid')
        episodeInfo = TableEpisodes.select(TableEpisodes.title,
                                           TableEpisodes.path,
                                           TableEpisodes.scene_name,
                                           TableEpisodes.audio_language)\
            .where(TableEpisodes.sonarrEpisodeId == sonarrEpisodeId)\
            .dicts()\
            .get()

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
                history_log(4, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score,
                            subtitles_path=subs_path)
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
        episodeInfo = TableEpisodes.select(TableEpisodes.title,
                                           TableEpisodes.path,
                                           TableEpisodes.scene_name,
                                           TableEpisodes.audio_language)\
            .where(TableEpisodes.sonarrEpisodeId == sonarrEpisodeId)\
            .dicts()\
            .get()

        episodePath = path_mappings.path_replace(episodeInfo['path'])

        language = request.form.get('language')
        forced = request.form.get('forced')
        hi = request.form.get('hi')
        subtitlesPath = request.form.get('path')

        subtitlesPath = path_mappings.path_replace_reverse(subtitlesPath)

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
        radarrId = request.args.getlist('radarrid[]')

        count = TableMovies.select().count()

        if len(radarrId) != 0:
            result = TableMovies.select()\
                .where(TableMovies.radarrId.in_(radarrId))\
                .order_by(TableMovies.sortTitle)\
                .dicts()
        else:
            result = TableMovies.select().order_by(TableMovies.sortTitle).limit(length).offset(start).dicts()
        result = list(result)
        for item in result:
            postprocessMovie(item)

        return jsonify(data=result, total=count)

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

            TableMovies.update({
                TableMovies.profileId: profileId
            })\
                .where(TableMovies.radarrId == radarrId)\
                .execute()

            list_missing_subtitles_movies(no=radarrId, send_event=False)

            event_stream(type='movie', payload=radarrId)
            event_stream(type='movie-wanted', payload=radarrId)
        event_stream(type='badges')

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

        movieInfo = TableMovies.select(TableMovies.title,
                                       TableMovies.path,
                                       TableMovies.sceneName,
                                       TableMovies.audio_language)\
            .where(TableMovies.radarrId == radarrId)\
            .dicts()\
            .get()

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
                event_stream(type='movie', payload=radarrId)
        except OSError:
            pass

        return '', 204

    @authenticate
    def post(self):
        # Upload
        # TODO: Support Multiply Upload
        radarrId = request.args.get('radarrid')
        movieInfo = TableMovies.select(TableMovies.title,
                                       TableMovies.path,
                                       TableMovies.sceneName,
                                       TableMovies.audio_language) \
            .where(TableMovies.radarrId == radarrId) \
            .dicts() \
            .get()

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
        movieInfo = TableMovies.select(TableMovies.path) \
            .where(TableMovies.radarrId == radarrId) \
            .dicts() \
            .get()

        moviePath = path_mappings.path_replace_movie(movieInfo['path'])

        language = request.form.get('language')
        forced = request.form.get('forced')
        hi = request.form.get('hi')
        subtitlesPath = request.form.get('path')

        subtitlesPath = path_mappings.path_replace_reverse_movie(subtitlesPath)

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
        history = request.args.get('history')
        if history and history not in False_Keys:
            providers = list(TableHistory.select(TableHistory.provider)
                             .where(TableHistory.provider != None and TableHistory.provider != "manual")
                             .dicts())
            providers += list(TableHistoryMovie.select(TableHistoryMovie.provider)
                              .where(TableHistoryMovie.provider != None and TableHistoryMovie.provider != "manual")
                              .dicts())
            providers_list = list(set([x['provider'] for x in providers]))
            providers_dicts = []
            for provider in providers_list:
                providers_dicts.append({
                    'name': provider,
                    'status': 'History',
                    'retry': '-'
                })
            return jsonify(data=sorted(providers_dicts, key=itemgetter('name')))

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
        movieInfo = TableMovies.select(TableMovies.title,
                                       TableMovies.path,
                                       TableMovies.sceneName,
                                       TableMovies.profileId) \
            .where(TableMovies.radarrId == radarrId) \
            .dicts() \
            .get()

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
        movieInfo = TableMovies.select(TableMovies.title,
                                       TableMovies.path,
                                       TableMovies.sceneName,
                                       TableMovies.audio_language) \
            .where(TableMovies.radarrId == radarrId) \
            .dicts() \
            .get()

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
        episodeInfo = TableEpisodes.select(TableEpisodes.title,
                                           TableEpisodes.path,
                                           TableEpisodes.scene_name,
                                           TableShows.profileId) \
            .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId))\
            .where(TableEpisodes.sonarrEpisodeId == sonarrEpisodeId) \
            .dicts() \
            .get()

        title = episodeInfo['title']
        episodePath = path_mappings.path_replace(episodeInfo['path'])
        sceneName = episodeInfo['scene_name']
        profileId = episodeInfo['profileId']
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
        episodeInfo = TableEpisodes.select(TableEpisodes.title,
                                           TableEpisodes.path,
                                           TableEpisodes.scene_name) \
            .where(TableEpisodes.sonarrEpisodeId == sonarrEpisodeId) \
            .dicts() \
            .get()

        title = episodeInfo['title']
        episodePath = path_mappings.path_replace(episodeInfo['path'])
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
            result = manual_download_subtitle(episodePath, language, audio_language, hi, forced, subtitle,
                                              selected_provider, providers_auth, sceneName, title, 'series')
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
                history_log(2, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score, subs_id,
                            subs_path)
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

            upgradable_episodes_conditions = [(TableHistory.action.in_(query_actions)),
                                              (TableHistory.timestamp > minimum_timestamp),
                                              (TableHistory.score is not None)]
            upgradable_episodes_conditions += get_exclusion_clause('series')
            upgradable_episodes = TableHistory.select(TableHistory.video_path,
                                                      fn.MAX(TableHistory.timestamp).alias('timestamp'),
                                                      TableHistory.score,
                                                      TableShows.tags,
                                                      TableEpisodes.monitored,
                                                      TableShows.seriesType)\
                .join(TableEpisodes, on=(TableHistory.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId))\
                .join(TableShows, on=(TableHistory.sonarrSeriesId == TableShows.sonarrSeriesId))\
                .where(reduce(operator.and_, upgradable_episodes_conditions))\
                .group_by(TableHistory.video_path)\
                .dicts()
            upgradable_episodes = list(upgradable_episodes)
            for upgradable_episode in upgradable_episodes:
                if upgradable_episode['timestamp'] > minimum_timestamp:
                    try:
                        int(upgradable_episode['score'])
                    except ValueError:
                        pass
                    else:
                        if int(upgradable_episode['score']) < 360:
                            upgradable_episodes_not_perfect.append(upgradable_episode)

        query_conditions = [(TableEpisodes.title is not None)]
        if episodeid:
            query_conditions.append((TableEpisodes.sonarrEpisodeId == episodeid))
        query_condition = reduce(operator.and_, query_conditions)
        episode_history = TableHistory.select(TableShows.title.alias('seriesTitle'),
                                              TableEpisodes.monitored,
                                              TableEpisodes.season.concat('x').concat(TableEpisodes.episode).alias('episode_number'),
                                              TableEpisodes.title.alias('episodeTitle'),
                                              TableHistory.timestamp,
                                              TableHistory.subs_id,
                                              TableHistory.description,
                                              TableHistory.sonarrSeriesId,
                                              TableEpisodes.path,
                                              TableHistory.language,
                                              TableHistory.score,
                                              TableShows.tags,
                                              TableHistory.action,
                                              TableHistory.subtitles_path,
                                              TableHistory.sonarrEpisodeId,
                                              TableHistory.provider,
                                              TableShows.seriesType)\
            .join(TableShows, on=(TableHistory.sonarrSeriesId == TableShows.sonarrSeriesId))\
            .join(TableEpisodes, on=(TableHistory.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId))\
            .where(query_condition)\
            .order_by(TableHistory.timestamp.desc())\
            .limit(length)\
            .offset(start)\
            .dicts()
        episode_history = list(episode_history)

        blacklist_db = TableBlacklist.select(TableBlacklist.provider, TableBlacklist.subs_id).dicts()
        blacklist_db = list(blacklist_db)

        for item in episode_history:
            # Mark episode as upgradable or not
            item.update({"upgradable": False})
            if {"video_path": str(item['path']), "timestamp": float(item['timestamp']), "score": str(item['score']),
                "tags": str(item['tags']), "monitored": str(item['monitored']),
                "seriesType": str(item['seriesType'])} in upgradable_episodes_not_perfect:
                if os.path.isfile(path_mappings.path_replace(item['subtitles_path'])):
                    item.update({"upgradable": True})

            del item['path']

            postprocessEpisode(item)

            if item['score']:
                item['score'] = str(round((int(item['score']) * 100 / 360), 2)) + "%"

            # Make timestamp pretty
            if item['timestamp']:
                item["raw_timestamp"] = int(item['timestamp'])
                item["parsed_timestamp"] = datetime.datetime.fromtimestamp(int(item['timestamp'])).strftime('%x %X')
                item['timestamp'] = pretty.date(item["raw_timestamp"])

            # Check if subtitles is blacklisted
            item.update({"blacklisted": False})
            if item['action'] not in [0, 4, 5]:
                for blacklisted_item in blacklist_db:
                    if blacklisted_item['provider'] == item['provider'] and \
                            blacklisted_item['subs_id'] == item['subs_id']:
                        item.update({"blacklisted": True})
                        break

        count = TableHistory.select()\
            .join(TableEpisodes, on=(TableHistory.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId))\
            .where(TableEpisodes.title is not None).count()

        return jsonify(data=episode_history, total=count)


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

            upgradable_movies_conditions = [(TableHistoryMovie.action.in_(query_actions)),
                                            (TableHistoryMovie.timestamp > minimum_timestamp),
                                            (TableHistoryMovie.score is not None)]
            upgradable_movies_conditions += get_exclusion_clause('movie')
            upgradable_movies = TableHistoryMovie.select(TableHistoryMovie.video_path,
                                                         fn.MAX(TableHistoryMovie.timestamp).alias('timestamp'),
                                                         TableHistoryMovie.score,
                                                         TableMovies.tags,
                                                         TableMovies.monitored)\
                .join(TableMovies, on=(TableHistoryMovie.radarrId == TableMovies.radarrId))\
                .where(reduce(operator.and_, upgradable_movies_conditions))\
                .group_by(TableHistoryMovie.video_path)\
                .dicts()
            upgradable_movies = list(upgradable_movies)

            for upgradable_movie in upgradable_movies:
                if upgradable_movie['timestamp'] > minimum_timestamp:
                    try:
                        int(upgradable_movie['score'])
                    except ValueError:
                        pass
                    else:
                        if int(upgradable_movie['score']) < 120:
                            upgradable_movies_not_perfect.append(upgradable_movie)

        query_conditions = [(TableMovies.title is not None)]
        if radarrid:
            query_conditions.append((TableMovies.radarrId == radarrid))
        query_condition = reduce(operator.and_, query_conditions)

        movie_history = TableHistoryMovie.select(TableHistoryMovie.action,
                                                 TableMovies.title,
                                                 TableHistoryMovie.timestamp,
                                                 TableHistoryMovie.description,
                                                 TableHistoryMovie.radarrId,
                                                 TableMovies.monitored,
                                                 TableHistoryMovie.video_path.alias('path'),
                                                 TableHistoryMovie.language,
                                                 TableMovies.tags,
                                                 TableHistoryMovie.score,
                                                 TableHistoryMovie.subs_id,
                                                 TableHistoryMovie.provider,
                                                 TableHistoryMovie.subtitles_path)\
            .join(TableMovies, on=(TableHistoryMovie.radarrId == TableMovies.radarrId))\
            .where(query_condition)\
            .order_by(TableHistoryMovie.timestamp.desc())\
            .limit(length)\
            .offset(start)\
            .dicts()
        movie_history = list(movie_history)

        blacklist_db = TableBlacklistMovie.select(TableBlacklistMovie.provider, TableBlacklistMovie.subs_id).dicts()
        blacklist_db = list(blacklist_db)

        for item in movie_history:
            # Mark movies as upgradable or not
            item.update({"upgradable": False})
            if {"video_path": str(item['path']), "timestamp": float(item['timestamp']), "score": str(item['score']),
                "tags": str(item['tags']), "monitored": str(item['monitored'])} in upgradable_movies_not_perfect:
                if os.path.isfile(path_mappings.path_replace_movie(item['subtitles_path'])):
                    item.update({"upgradable": True})

            del item['path']

            postprocessMovie(item)

            if item['score']:
                item['score'] = str(round((int(item['score']) * 100 / 120), 2)) + "%"

            # Make timestamp pretty
            if item['timestamp']:
                item["raw_timestamp"] = int(item['timestamp'])
                item["parsed_timestamp"] = datetime.datetime.fromtimestamp(int(item['timestamp'])).strftime('%x %X')
                item['timestamp'] = pretty.date(item["raw_timestamp"])

            # Check if subtitles is blacklisted
            item.update({"blacklisted": False})
            if item['action'] not in [0, 4, 5]:
                for blacklisted_item in blacklist_db:
                    if blacklisted_item['provider'] == item['provider'] and blacklisted_item['subs_id'] == item[
                        'subs_id']:
                        item.update({"blacklisted": True})
                        break

        count = TableHistoryMovie.select()\
            .join(TableMovies, on=(TableHistoryMovie.radarrId == TableMovies.radarrId))\
            .where(TableMovies.title is not None)\
            .count()

        return jsonify(data=movie_history, total=count)


class HistoryStats(Resource):
    @authenticate
    def get(self):
        timeframe = request.args.get('timeframe') or 'month'
        action = request.args.get('action') or 'All'
        provider = request.args.get('provider') or 'All'
        language = request.args.get('language') or 'All'

        # timeframe must be in ['week', 'month', 'trimester', 'year']
        if timeframe == 'year':
            delay = 364 * 24 * 60 * 60
        elif timeframe == 'trimester':
            delay = 90 * 24 * 60 * 60
        elif timeframe == 'month':
            delay = 30 * 24 * 60 * 60
        elif timeframe == 'week':
            delay = 6 * 24 * 60 * 60

        now = time.time()
        past = now - delay

        history_where_clauses = [(TableHistory.timestamp.between(past, now))]
        history_where_clauses_movie = [(TableHistoryMovie.timestamp.between(past, now))]

        if action != 'All':
            history_where_clauses.append((TableHistory.action == action))
            history_where_clauses_movie.append((TableHistoryMovie.action == action))
        else:
            history_where_clauses.append((TableHistory.action.in_([1, 2, 3])))
            history_where_clauses_movie.append((TableHistoryMovie.action.in_([1, 2, 3])))

        if provider != 'All':
            history_where_clauses.append((TableHistory.provider == provider))
            history_where_clauses_movie.append((TableHistoryMovie.provider == provider))

        if language != 'All':
            history_where_clauses.append((TableHistory.language == language))
            history_where_clauses_movie.append((TableHistoryMovie.language == language))

        history_where_clause = reduce(operator.and_, history_where_clauses)
        history_where_clause_movie = reduce(operator.and_, history_where_clauses_movie)

        data_series = TableHistory.select(fn.strftime('%Y-%m-%d', TableHistory.timestamp, 'unixepoch').alias('date'),
                                          fn.COUNT(TableHistory.id).alias('count'))\
            .where(history_where_clause) \
            .group_by(fn.strftime('%Y-%m-%d', TableHistory.timestamp, 'unixepoch'))\
            .dicts()
        data_series = list(data_series)

        data_movies = TableHistoryMovie.select(fn.strftime('%Y-%m-%d', TableHistoryMovie.timestamp, 'unixepoch').alias('date'),
                                               fn.COUNT(TableHistoryMovie.id).alias('count')) \
            .where(history_where_clause_movie) \
            .group_by(fn.strftime('%Y-%m-%d', TableHistoryMovie.timestamp, 'unixepoch')) \
            .dicts()
        data_movies = list(data_movies)

        for dt in rrule.rrule(rrule.DAILY,
                              dtstart=datetime.datetime.now() - datetime.timedelta(seconds=delay),
                              until=datetime.datetime.now()):
            if not any(d['date'] == dt.strftime('%Y-%m-%d') for d in data_series):
                data_series.append({'date': dt.strftime('%Y-%m-%d'), 'count': 0})
            if not any(d['date'] == dt.strftime('%Y-%m-%d') for d in data_movies):
                data_movies.append({'date': dt.strftime('%Y-%m-%d'), 'count': 0})

        sorted_data_series = sorted(data_series, key=lambda i: i['date'])
        sorted_data_movies = sorted(data_movies, key=lambda i: i['date'])

        return jsonify(series=sorted_data_series, movies=sorted_data_movies)


# GET: Get Wanted Episodes
class EpisodesWanted(Resource):
    @authenticate
    def get(self):
        episodeid = request.args.getlist('episodeid[]')

        wanted_conditions = [(TableEpisodes.missing_subtitles != '[]')]
        if len(episodeid) > 0:
            wanted_conditions.append((TableEpisodes.sonarrEpisodeId in episodeid))
        wanted_conditions += get_exclusion_clause('series')
        wanted_condition = reduce(operator.and_, wanted_conditions)

        if len(episodeid) > 0:
            data = TableEpisodes.select(TableShows.title.alias('seriesTitle'),
                                        TableEpisodes.monitored,
                                        TableEpisodes.season.concat('x').concat(TableEpisodes.episode).alias('episode_number'),
                                        TableEpisodes.title.alias('episodeTitle'),
                                        TableEpisodes.missing_subtitles,
                                        TableEpisodes.sonarrSeriesId,
                                        TableEpisodes.sonarrEpisodeId,
                                        TableEpisodes.scene_name.alias('sceneName'),
                                        TableShows.tags,
                                        TableEpisodes.failedAttempts,
                                        TableShows.seriesType)\
                .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId))\
                .where(wanted_condition)\
                .dicts()
        else:
            start = request.args.get('start') or 0
            length = request.args.get('length') or -1
            data = TableEpisodes.select(TableShows.title.alias('seriesTitle'),
                                        TableEpisodes.monitored,
                                        TableEpisodes.season.concat('x').concat(TableEpisodes.episode).alias('episode_number'),
                                        TableEpisodes.title.alias('episodeTitle'),
                                        TableEpisodes.missing_subtitles,
                                        TableEpisodes.sonarrSeriesId,
                                        TableEpisodes.sonarrEpisodeId,
                                        TableEpisodes.scene_name.alias('sceneName'),
                                        TableShows.tags,
                                        TableEpisodes.failedAttempts,
                                        TableShows.seriesType)\
                .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId))\
                .where(wanted_condition)\
                .order_by(TableEpisodes.rowid.desc())\
                .limit(length)\
                .offset(start)\
                .dicts()
        data = list(data)

        for item in data:
            postprocessEpisode(item)

        count_conditions = [(TableEpisodes.missing_subtitles != '[]')]
        count_conditions += get_exclusion_clause('series')
        count = TableEpisodes.select(TableShows.tags,
                                     TableShows.seriesType,
                                     TableEpisodes.monitored)\
            .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId))\
            .where(reduce(operator.and_, count_conditions))\
            .count()

        return jsonify(data=data, total=count)


# GET: Get Wanted Movies
class MoviesWanted(Resource):
    @authenticate
    def get(self):
        radarrid = request.args.getlist("radarrid[]")

        wanted_conditions = [(TableMovies.missing_subtitles != '[]')]
        if len(radarrid) > 0:
            wanted_conditions.append((TableMovies.radarrId.in_(radarrid)))
        wanted_conditions += get_exclusion_clause('movie')
        wanted_condition = reduce(operator.and_, wanted_conditions)

        if len(radarrid) > 0:
            result = TableMovies.select(TableMovies.title,
                                        TableMovies.missing_subtitles,
                                        TableMovies.radarrId,
                                        TableMovies.sceneName,
                                        TableMovies.failedAttempts,
                                        TableMovies.tags,
                                        TableMovies.monitored)\
                .where(wanted_condition)\
                .dicts()
        else:
            start = request.args.get('start') or 0
            length = request.args.get('length') or -1
            result = TableMovies.select(TableMovies.title,
                                        TableMovies.missing_subtitles,
                                        TableMovies.radarrId,
                                        TableMovies.sceneName,
                                        TableMovies.failedAttempts,
                                        TableMovies.tags,
                                        TableMovies.monitored)\
                .where(wanted_condition)\
                .order_by(TableMovies.rowid.desc())\
                .limit(length)\
                .offset(start)\
                .dicts()
        result = list(result)

        for item in result:
            postprocessMovie(item)

        count_conditions = [(TableMovies.missing_subtitles != '[]')]
        count_conditions += get_exclusion_clause('movie')
        count = TableMovies.select(TableMovies.monitored,
                                   TableMovies.tags)\
            .where(reduce(operator.and_, count_conditions))\
            .count()

        return jsonify(data=result, total=count)


# GET: get blacklist
# POST: add blacklist
# DELETE: remove blacklist
class EpisodesBlacklist(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1

        data = TableBlacklist.select(TableShows.title.alias('seriesTitle'),
                                     TableEpisodes.season.concat('x').concat(TableEpisodes.episode).alias('episode_number'),
                                     TableEpisodes.title.alias('episodeTitle'),
                                     TableEpisodes.sonarrSeriesId,
                                     TableBlacklist.provider,
                                     TableBlacklist.subs_id,
                                     TableBlacklist.language,
                                     TableBlacklist.timestamp)\
            .join(TableEpisodes, on=(TableBlacklist.sonarr_episode_id == TableEpisodes.sonarrEpisodeId))\
            .join(TableShows, on=(TableBlacklist.sonarr_series_id == TableShows.sonarrSeriesId))\
            .order_by(TableBlacklist.timestamp.desc())\
            .limit(length)\
            .offset(start)\
            .dicts()
        data = list(data)

        for item in data:
            # Make timestamp pretty
            item["parsed_timestamp"] = datetime.datetime.fromtimestamp(int(item['timestamp'])).strftime('%x %X')
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

        episodeInfo = TableEpisodes.select(TableEpisodes.path)\
            .where(TableEpisodes.sonarrEpisodeId == sonarr_episode_id)\
            .dicts()\
            .get()

        media_path = episodeInfo['path']
        subtitles_path = request.form.get('subtitles_path')

        blacklist_log(sonarr_series_id=sonarr_series_id,
                      sonarr_episode_id=sonarr_episode_id,
                      provider=provider,
                      subs_id=subs_id,
                      language=language)
        delete_subtitles(media_type='series',
                         language=language,
                         forced=False,
                         hi=False,
                         media_path=path_mappings.path_replace(media_path),
                         subtitles_path=subtitles_path,
                         sonarr_series_id=sonarr_series_id,
                         sonarr_episode_id=sonarr_episode_id)
        episode_download_subtitles(sonarr_episode_id)
        event_stream(type='episode-history')
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

        data = TableBlacklistMovie.select(TableMovies.title,
                                          TableMovies.radarrId,
                                          TableBlacklistMovie.provider,
                                          TableBlacklistMovie.subs_id,
                                          TableBlacklistMovie.language,
                                          TableBlacklistMovie.timestamp)\
            .join(TableMovies, on=(TableBlacklistMovie.radarr_id == TableMovies.radarrId))\
            .order_by(TableBlacklistMovie.timestamp.desc())\
            .limit(length)\
            .offset(start)\
            .dicts()
        data = list(data)

        for item in data:
            postprocessMovie(item)

            # Make timestamp pretty
            item["parsed_timestamp"] = datetime.datetime.fromtimestamp(int(item['timestamp'])).strftime('%x %X')
            item.update({'timestamp': pretty.date(datetime.datetime.fromtimestamp(item['timestamp']))})

        return jsonify(data=data)

    @authenticate
    def post(self):
        radarr_id = int(request.args.get('radarrid'))
        provider = request.form.get('provider')
        subs_id = request.form.get('subs_id')
        language = request.form.get('language')
        # TODO
        forced = False
        hi = False

        data = TableMovies.select(TableMovies.path).where(TableMovies.radarrId == radarr_id).dicts().get()

        media_path = data['path']
        subtitles_path = request.form.get('subtitles_path')

        blacklist_log_movie(radarr_id=radarr_id,
                            provider=provider,
                            subs_id=subs_id,
                            language=language)
        delete_subtitles(media_type='movie',
                         language=language,
                         forced=forced,
                         hi=hi,
                         media_path=path_mappings.path_replace_movie(media_path),
                         subtitles_path=subtitles_path,
                         radarr_id=radarr_id)
        movies_download_subtitles(radarr_id)
        event_stream(type='movie-history')
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
            metadata = TableEpisodes.select(TableEpisodes.path, TableEpisodes.sonarrSeriesId)\
                .where(TableEpisodes.sonarrEpisodeId == id)\
                .dicts()\
                .get()
            video_path = path_mappings.path_replace(metadata['path'])
        else:
            subtitles_path = path_mappings.path_replace_movie(subtitles_path)
            metadata = TableMovies.select(TableMovies.path).where(TableMovies.radarrId == id).dicts().get()
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
            result = translate_subtitles_file(video_path=video_path, source_srt_file=subtitles_path,
                                              to_lang=dest_language,
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

        # apply chmod if required
        chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
            'win') and settings.general.getboolean('chmod_enabled') else None
        if chmod:
            os.chmod(subtitles_path, chmod)

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


class WebHooksPlex(Resource):
    @authenticate
    def post(self):
        json_webhook = request.form.get('payload')
        parsed_json_webhook = json.loads(json_webhook)

        event = parsed_json_webhook['event']
        if event not in ['media.play']:
            return '', 204

        media_type = parsed_json_webhook['Metadata']['type']

        if media_type == 'episode':
            season = parsed_json_webhook['Metadata']['parentIndex']
            episode = parsed_json_webhook['Metadata']['index']
        else:
            season = episode = None

        ids = []
        for item in parsed_json_webhook['Metadata']['Guid']:
            splitted_id = item['id'].split('://')
            if len(splitted_id) == 2:
                ids.append({splitted_id[0]: splitted_id[1]})
        if not ids:
            return '', 404

        if media_type == 'episode':
            try:
                episode_imdb_id = [x['imdb'] for x in ids if 'imdb' in x][0]
                r = requests.get('https://imdb.com/title/{}'.format(episode_imdb_id),
                                 headers={"User-Agent": os.environ["SZ_USER_AGENT"]})
                soup = bso(r.content, "html.parser")
                series_imdb_id = soup.find('a', {'class': re.compile(r'SeriesParentLink__ParentTextLink')})['href'].split('/')[2]
            except:
                return '', 404
            else:
                sonarrEpisodeId = TableEpisodes.select(TableEpisodes.sonarrEpisodeId) \
                    .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId)) \
                    .where(TableShows.imdbId == series_imdb_id,
                           TableEpisodes.season == season,
                           TableEpisodes.episode == episode) \
                    .dicts() \
                    .get()

                if sonarrEpisodeId:
                    episode_download_subtitles(no=sonarrEpisodeId['sonarrEpisodeId'], send_progress=True)
        else:
            try:
                movie_imdb_id = [x['imdb'] for x in ids if 'imdb' in x][0]
            except:
                return '', 404
            else:
                radarrId = TableMovies.select(TableMovies.radarrId)\
                    .where(TableMovies.imdbId == movie_imdb_id)\
                    .dicts()\
                    .get()
                if radarrId:
                    movies_download_subtitles(no=radarrId['radarrId'])

        return '', 200


api.add_resource(Badges, '/badges')

api.add_resource(Providers, '/providers')
api.add_resource(ProviderMovies, '/providers/movies')
api.add_resource(ProviderEpisodes, '/providers/episodes')

api.add_resource(System, '/system')
api.add_resource(Searches, "/system/searches")
api.add_resource(SystemAccount, '/system/account')
api.add_resource(SystemTasks, '/system/tasks')
api.add_resource(SystemLogs, '/system/logs')
api.add_resource(SystemStatus, '/system/status')
api.add_resource(SystemHealth, '/system/health')
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
api.add_resource(MoviesWanted, '/movies/wanted')
api.add_resource(MoviesSubtitles, '/movies/subtitles')
api.add_resource(MoviesHistory, '/movies/history')
api.add_resource(MoviesBlacklist, '/movies/blacklist')

api.add_resource(HistoryStats, '/history/stats')

api.add_resource(BrowseBazarrFS, '/files')
api.add_resource(BrowseSonarrFS, '/files/sonarr')
api.add_resource(BrowseRadarrFS, '/files/radarr')

api.add_resource(WebHooksPlex, '/webhooks/plex')

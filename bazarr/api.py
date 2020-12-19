# coding=utf-8

import os
import ast
from datetime import timedelta
import datetime
from dateutil import rrule
import pretty
import time
from operator import itemgetter
import platform
import io
import re
import json

from get_args import args
from config import settings, base_url, save_settings

from init import *
import logging
from database import database, get_exclusion_clause
from helper import path_mappings
from get_languages import language_from_alpha3, language_from_alpha2, alpha2_from_alpha3, alpha2_from_language, \
    alpha3_from_language, alpha3_from_alpha2
from get_subtitle import download_subtitle, series_download_subtitles, movies_download_subtitles, \
    manual_search, manual_download_subtitle, manual_upload_subtitle, wanted_search_missing_subtitles_series, \
    wanted_search_missing_subtitles_movies, episode_download_subtitles, movies_download_subtitles
from notifier import send_notifications, send_notifications_movie
from list_subtitles import store_subtitles, store_subtitles_movie, series_scan_subtitles, movies_scan_subtitles, \
    list_missing_subtitles, list_missing_subtitles_movies
from utils import history_log, history_log_movie, blacklist_log, blacklist_delete, blacklist_delete_all, \
    blacklist_log_movie, blacklist_delete_movie, blacklist_delete_all_movie, get_sonarr_version, get_radarr_version, \
    delete_subtitles, subtitles_apply_mods
from get_providers import get_providers, get_providers_auth, list_throttled_providers, reset_throttled_providers
from event_handler import event_stream
from scheduler import scheduler
from subsyncer import subsync
from filesystem import browse_bazarr_filesystem, browse_sonarr_filesystem, browse_radarr_filesystem

from subliminal_patch.core import SUBTITLE_EXTENSIONS, guessit

from flask import Flask, jsonify, request, Response, Blueprint, url_for, make_response

from flask_restful import Resource, Api, abort
from functools import wraps

api_bp = Blueprint('api', __name__, url_prefix=base_url.rstrip('/')+'/api')
api = Api(api_bp)


def authenticate(actual_method):
    @wraps(actual_method)
    def wrapper(*args, **kwargs):
        apikey_settings = settings.auth.apikey
        apikey_get = request.args.get('apikey')
        apikey_post = request.form.get('apikey')
        apikey_header = None
        if 'X-Api-Key' in request.headers:
            apikey_header = request.headers['X-Api-Key']

        if apikey_settings in [apikey_get, apikey_post, apikey_header]:
            return actual_method(*args, **kwargs)

        return abort(401, message="Unauthorized")

    return wrapper


class Shutdown(Resource):
    @authenticate
    def get(self):
        from server import webserver
        webserver.shutdown()


class Restart(Resource):
    @authenticate
    def get(self):
        from server import webserver
        webserver.restart()


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
            "value": len(eval(str(settings.general.throtteled_providers)))
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


class Notifications(Resource):
    @authenticate
    def get(self):
        result = database.execute("SELECT * FROM table_settings_notifier ORDER BY name")
        return jsonify(data=result)

    @authenticate
    def post(self):
        notification_providers = json.loads(request.form.get('notification_providers'))
        for item in notification_providers:
            database.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = ?",
                             (item['enabled'], item['url'], item['name']))

        save_settings(zip(request.form.keys(), request.form.listvalues()))
        return '', 204


class Search(Resource):
    @authenticate
    def get(self):
        query = request.args.get('query')
        search_list = []

        if query:
            if settings.general.getboolean('use_sonarr'):
                # Get matching series
                series = database.execute("SELECT title, sonarrSeriesId, year FROM table_shows WHERE title LIKE ? "
                                          "ORDER BY title ASC", ("%"+query+"%",))
                for serie in series:
                    search_list.append({'name': re.sub(r'\ \(\d{4}\)', '', serie['title']) + ' (' + serie['year'] + ')',
                                        'url': url_for('episodes', no=serie['sonarrSeriesId'])})

            if settings.general.getboolean('use_radarr'):
                # Get matching movies
                movies = database.execute("SELECT title, radarrId, year FROM table_movies WHERE title LIKE ? ORDER BY "
                                          "title ASC", ("%"+query+"%",))
                for movie in movies:
                    search_list.append({'name': re.sub(r'\ \(\d{4}\)', '', movie['title']) + ' (' + movie['year'] + ')',
                                        'url': url_for('movie', no=movie['radarrId'])})

        return jsonify(search_list)


class ResetProviders(Resource):
    @authenticate
    def post(self):
        reset_throttled_providers()
        return '', 200


class SaveSettings(Resource):
    @authenticate
    def post(self):
        save_settings(zip(request.form.keys(), request.form.listvalues()))

        return '', 200


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

        return '', 200


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


class SystemProviders(Resource):
    @authenticate
    def get(self):
        throttled_providers = list_throttled_providers()

        providers = list()
        for i in range(len(throttled_providers)):
            provider = {
                "name": throttled_providers[i][0],
                "status": throttled_providers[i][1] if throttled_providers[i][1] is not None else "Good",
                "retry": throttled_providers[i][2] if throttled_providers[i][2] != "now" else "-"
            }
            providers.append(provider)
        return jsonify(data=providers)


class SystemStatus(Resource):
    @authenticate
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
                raw_releases = ast.literal_eval(f.read())
            for release in raw_releases:
                rel = dict()
                rel["version"] = release[0]

                changesets = release[1].replace('- ', '').split('\r\n')
                changesets.pop(0)
                rel["changesets"] = changesets
                releases.append(rel)

        except Exception as e:
            logging.exception(
                'BAZARR cannot parse releases caching file: ' + os.path.join(args.config_dir, 'config', 'releases.txt'))
        return jsonify(data=releases)


class Series(Resource):
    @authenticate
    def get(self, **kwargs):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1

        seriesId = request.args.get('seriesid')
        if seriesId:
            result = database.execute("SELECT * FROM table_shows WHERE sonarrSeriesId=? ORDER BY sortTitle ASC LIMIT ? "
                                      "OFFSET ?", (seriesId, length, start))
            desired_languages = database.execute("SELECT languages FROM table_shows WHERE sonarrSeriesId=?",
                                                 (seriesId,), only_one=True)['languages']
            if desired_languages == "None":
                desired_languages = '[]'
        else:
            result = database.execute("SELECT * FROM table_shows ORDER BY sortTitle ASC LIMIT ? OFFSET ?", (length, start))
        for item in result:
            # Parse audio language
            item.update({"audio_language": {"name": item['audio_language'],
                                            "code2": alpha2_from_language(item['audio_language']) or None,
                                            "code3": alpha3_from_language(item['audio_language']) or None}})

            # Parse desired languages
            if item['languages'] and item['languages'] != 'None':
                item.update({"languages": ast.literal_eval(item['languages'])})
                for i, subs in enumerate(item['languages']):
                    item['languages'][i] = {"name": language_from_alpha2(subs),
                                            "code2": subs,
                                            "code3": alpha3_from_alpha2(subs)}
            else:
                item.update({"languages": []})

            # Parse alternate titles
            if item['alternateTitles']:
                item.update({"alternateTitles": ast.literal_eval(item['alternateTitles'])})

            # Parse tags
            item.update({"tags": ast.literal_eval(item['tags'])})

            # Parse seriesType
            item.update({"seriesType": item['seriesType'].capitalize()})

            # Provide mapped path
            mapped_path = path_mappings.path_replace(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isdir(mapped_path)})

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

            # map poster and fanart to server proxy
            poster = item["poster"]
            fanart = item["fanart"]
            item.update({"poster": f"{base_url}images/series{poster}","fanart": f"{base_url}images/series{fanart}"})

            # Add the series desired subtitles language code2
            try:
                item.update({"desired_languages": ast.literal_eval(desired_languages)})
            except NameError:
                pass

            item.update({"forced": item["forced"] == "True"})
            item.update({"hearing_impaired": item["hearing_impaired"] == "True"})
        return jsonify(data=result)

    @authenticate
    def post(self):
        seriesId = request.args.get('seriesid')

        lang = request.form.getlist('languages')
        if len(lang) > 0:
            pass
        else:
            lang = 'None'

        single_language = settings.general.getboolean('single_language')
        if single_language:
            if str(lang) == "['None']":
                lang = 'None'
            else:
                lang = str(lang)
        else:
            if str(lang) == "['']":
                lang = '[]'

        hi = request.form.get('hi')
        forced = request.form.get('forced')

        if forced == "true":
            forced = "True"
        else:
            forced = "False"

        if hi == "true":
            hi = "True"
        else:
            hi = "False"

        result = database.execute("UPDATE table_shows SET languages=?, hearing_impaired=?, forced=? WHERE "
                                  "sonarrSeriesId=?", (str(lang), hi, forced, seriesId))

        list_missing_subtitles(no=seriesId)

        event_stream(type='series', action='update', series=seriesId)

        return '', 204


class SeriesEditor(Resource):
    @authenticate
    def get(self, **kwargs):
        result = database.execute("SELECT sonarrSeriesId, title, languages, hearing_impaired, forced, audio_language "
                                  "FROM table_shows ORDER BY sortTitle")

        for item in result:
            # Parse audio language
            item.update({"audio_language": {"name": item['audio_language'],
                                            "code2": alpha2_from_language(item['audio_language']) or None,
                                            "code3": alpha3_from_language(item['audio_language']) or None}})

            # Parse desired languages
            if item['languages'] and item['languages'] != 'None':
                item.update({"languages": ast.literal_eval(item['languages'])})
                for i, subs in enumerate(item['languages']):
                    item['languages'][i] = {"name": language_from_alpha2(subs),
                                            "code2": subs,
                                            "code3": alpha3_from_alpha2(subs)}
            else:
                item.update({"languages": []})

        return jsonify(data=result)


class SeriesEditSave(Resource):
    @authenticate
    def post(self):
        lang = request.form.getlist('languages[]')
        hi = request.form.getlist('hi[]')
        forced = request.form.getlist('forced[]')

        if lang == ['None']:
            lang = 'None'

        seriesIdList = []
        seriesidLangList = []
        seriesidHiList = []
        seriesidForcedList = []
        for item in request.form.getlist('seriesid[]'):
            seriesid = item.lstrip('row_')
            seriesIdList.append(seriesid)
            if len(lang):
                seriesidLangList.append([str(lang), seriesid])
            if len(hi):
                seriesidHiList.append([hi[0], seriesid])
            if len(forced):
                seriesidForcedList.append([forced[0], seriesid])

        try:
            if len(lang):
                database.execute("UPDATE table_shows SET languages=? WHERE sonarrSeriesId=?", seriesidLangList,
                                 execute_many=True)
            if len(hi):
                database.execute("UPDATE table_shows SET hearing_impaired=? WHERE  sonarrSeriesId=?", seriesidHiList,
                                 execute_many=True)
            if len(forced):
                database.execute("UPDATE table_shows SET forced=? WHERE sonarrSeriesId=?", seriesidForcedList,
                                 execute_many=True)
        except:
            pass
        else:
            for seriesId in seriesIdList:
                list_missing_subtitles(no=seriesId, send_event=False)

        event_stream(type='series_editor', action='update')
        event_stream(type='badges_series')

        return '', 204


class Episodes(Resource):
    @authenticate
    def get(self):
        seriesId = request.args.get('seriesid')
        episodeId = request.args.get('episodeid')
        if episodeId:
            result = database.execute("SELECT * FROM table_episodes WHERE sonarrEpisodeId=?", (episodeId,))
            desired_languages = database.execute("SELECT languages FROM table_shows WHERE sonarrSeriesId=?",
                                                 (seriesId,), only_one=True)['languages']
            if desired_languages == "None":
                desired_languages = '[]'
        elif seriesId:
            result = database.execute("SELECT * FROM table_episodes WHERE sonarrSeriesId=? ORDER BY season DESC, "
                                      "episode DESC", (seriesId,))
            desired_languages = database.execute("SELECT languages FROM table_shows WHERE sonarrSeriesId=?",
                                                 (seriesId,), only_one=True)['languages']
            if desired_languages == "None":
                desired_languages = '[]'
        else:
            return "Series ID not provided", 400
        for item in result:
            # Parse audio language
            item.update({"audio_language": {"name": item['audio_language'],
                                            "code2": alpha2_from_language(item['audio_language']) or None,
                                            "code3": alpha3_from_language(item['audio_language']) or None}})

            # Parse subtitles
            if item['subtitles']:
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
                    desired = ast.literal_eval(desired_languages)
                    item['subtitles'] = [x for x in item['subtitles'] if
                                         x['code2'] in desired or x['path']]
            else:
                item.update({"subtitles": []})

            # Parse missing subtitles
            if item['missing_subtitles']:
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
            else:
                item.update({"missing_subtitles": []})

            # Provide mapped path
            mapped_path = path_mappings.path_replace(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isfile(mapped_path)})

            # Add the series desired subtitles language code2
            item.update({"desired_languages": ast.literal_eval(desired_languages)})
            item.update({"monitored": item["monitored"] == "True"})
        return jsonify(data=result)

class SubtitleNameInfo(Resource):
    @authenticate
    def get(self):
        name = request.args.get('filename')
        if name is not None:
            opts = dict()
            opts['type'] = 'episode'
            result = guessit(name, options=opts)
            if 'subtitle_language' in result:
                result['subtitle_language'] = str(result['subtitle_language'])
            return jsonify(data=result)
        else:
            return '', 400


class EpisodesSubtitlesDownload(Resource):
    @authenticate
    def post(self):
        episodePath = request.form.get('episodePath')
        sceneName = request.form.get('sceneName')
        if sceneName == "null":
            sceneName = "None"
        language = request.form.get('language')
        hi = request.form.get('hi').capitalize()
        forced = request.form.get('forced').capitalize()
        sonarrSeriesId = request.form.get('sonarrSeriesId')
        sonarrEpisodeId = request.form.get('sonarrEpisodeId')
        title = request.form.get('title')
        providers_list = get_providers()
        providers_auth = get_providers_auth()
        audio_language = database.execute("SELECT audio_language FROM table_episodes WHERE sonarrEpisodeId=?",
                                          (sonarrEpisodeId,), only_one=True)['audio_language']

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
            return result, 201
        except OSError:
            pass

        return '', 204


class EpisodesSubtitlesManualSearch(Resource):
    @authenticate
    def post(self):
        episodePath = request.form.get('episodePath')
        sceneName = request.form.get('sceneName')
        if sceneName == "null":
            sceneName = "None"
        language = request.form.get('language')
        hi = request.form.get('hi').capitalize()
        forced = request.form.get('forced').capitalize()
        title = request.form.get('title')
        providers_list = get_providers()
        providers_auth = get_providers_auth()

        data = manual_search(episodePath, language, hi, forced, providers_list, providers_auth, sceneName, title,
                             'series')
        if not data:
            data = []
        return jsonify(data=data)


class EpisodesSubtitlesManualDownload(Resource):
    @authenticate
    def post(self):
        episodePath = request.form.get('episodePath')
        sceneName = request.form.get('sceneName')
        if sceneName == "null":
            sceneName = "None"
        language = request.form.get('language')
        hi = request.form.get('hi').capitalize()
        forced = request.form.get('forced').capitalize()
        selected_provider = request.form.get('provider')
        subtitle = request.form.get('subtitle')
        sonarrSeriesId = request.form.get('sonarrSeriesId')
        sonarrEpisodeId = request.form.get('sonarrEpisodeId')
        title = request.form.get('title')
        providers_auth = get_providers_auth()
        audio_language = database.execute("SELECT audio_language FROM table_episodes WHERE sonarrEpisodeId=?",
                                          (sonarrEpisodeId,), only_one=True)['audio_language']

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
                history_log(2, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score, subs_id, subs_path)
                if not settings.general.getboolean('dont_notify_manual_actions'):
                    send_notifications(sonarrSeriesId, sonarrEpisodeId, message)
                store_subtitles(path, episodePath)
            return result, 201
        except OSError:
            pass

        return '', 204


# POST: Upload Subtitles
# DELETE: Delete Subtitles
class EpisodesSubtitles(Resource):
    @authenticate
    def post(self):
        episodePath = request.form.get('episodePath')
        sceneName = request.form.get('sceneName')
        if sceneName == "null":
            sceneName = "None"
        language = request.form.get('language')
        forced = True if request.form.get('forced') == 'on' else False
        upload = request.files.get('upload')
        sonarrSeriesId = request.form.get('seriesId')
        sonarrEpisodeId = request.form.get('episodeId')
        title = request.form.get('title')
        audioLanguage = request.form.get('audioLanguage')

        _, ext = os.path.splitext(upload.filename)

        if ext not in SUBTITLE_EXTENSIONS:
            raise ValueError('A subtitle of an invalid format was uploaded.')

        try:
            result = manual_upload_subtitle(path=episodePath,
                                            language=language,
                                            forced=forced,
                                            title=title,
                                            scene_name=sceneName,
                                            media_type='series',
                                            subtitle=upload,
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
                score = 360
                history_log(4, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score, subtitles_path=subs_path)
                if not settings.general.getboolean('dont_notify_manual_actions'):
                    send_notifications(sonarrSeriesId, sonarrEpisodeId, message)
                store_subtitles(path, episodePath)

            return result, 201
        except OSError:
            pass

        return '', 204

    @authenticate
    def delete(self):
        episodePath = request.form.get('episodePath')
        language = request.form.get('language')
        forced = request.form.get('forced')
        hi = request.form.get('hi')
        subtitlesPath = request.form.get('subtitlesPath')
        sonarrSeriesId = request.form.get('sonarrSeriesId')
        sonarrEpisodeId = request.form.get('sonarrEpisodeId')

        result = delete_subtitles(media_type='series',
                                  language=language,
                                  forced=forced,
                                  hi=hi,
                                  media_path=episodePath,
                                  subtitles_path=subtitlesPath,
                                  sonarr_series_id=sonarrSeriesId,
                                  sonarr_episode_id=sonarrEpisodeId)
        if result:
            return '', 202
        else:
            return '', 204



class EpisodesScanDisk(Resource):
    @authenticate
    def get(self):
        seriesid = request.args.get('seriesid')
        series_scan_subtitles(seriesid)
        return '', 200


class EpisodesSearchMissing(Resource):
    @authenticate
    def get(self):
        seriesid = request.args.get('seriesid')
        series_download_subtitles(seriesid)
        return '', 200


class EpisodesHistory(Resource):
    @authenticate
    def get(self):
        episodeid = request.args.get('episodeid')

        episode_history = database.execute("SELECT action, timestamp, language, provider, score, sonarrSeriesId, "
                                           "sonarrEpisodeId, subs_id, video_path, subtitles_path FROM table_history "
                                           "WHERE sonarrEpisodeId=? ORDER BY timestamp DESC", (episodeid,))
        for item in episode_history:
            item['raw_timestamp'] = item['timestamp']
            item['timestamp'] = pretty.date(datetime.datetime.fromtimestamp(item['timestamp']))

            if item['language']:
                language = item['language'].split(':')
                item['language'] = {"name": language_from_alpha2(language[0]),
                                    "code2": language[0],
                                    "code3": alpha3_from_alpha2(language[0]),
                                    "forced": True if item['language'].endswith(':forced') else False,
                                    "hi": True if item['language'].endswith(':hi') else False}
            if item['score']:
                item['score'] = str(round((int(item['score']) * 100 / 360), 2)) + "%"

            if item['video_path']:
                # Provide mapped path
                mapped_path = path_mappings.path_replace(item['video_path'])
                item.update({"mapped_path": mapped_path})

                # Confirm if path exist
                item.update({"exist": os.path.isfile(mapped_path)})
            else:
                item.update({"mapped_path": None})
                item.update({"exist": False})

            if item['subtitles_path']:
                # Provide mapped subtitles path
                mapped_subtitles_path = path_mappings.path_replace_movie(item['subtitles_path'])
                item.update({"mapped_subtitles_path": mapped_subtitles_path})
            else:
                item.update({"mapped_subtitles_path": None})

            # Check if subtitles is blacklisted
            if item['action'] not in [0, 4, 5]:
                blacklist_db = database.execute(
                    "SELECT provider, subs_id FROM table_blacklist WHERE provider=? AND "
                    "subs_id=?", (item['provider'], item['subs_id']))
            else:
                blacklist_db = []

            if len(blacklist_db):
                item.update({"blacklisted": True})
            else:
                item.update({"blacklisted": False})

        return jsonify(data=episode_history)


class EpisodesTools(Resource):
    @authenticate
    def get(self):
        episodeid = request.args.get('episodeid')

        episode_ext_subs = database.execute("SELECT path, subtitles FROM table_episodes WHERE sonarrEpisodeId=?",
                                            (episodeid,), only_one=True)
        try:
            all_subs = ast.literal_eval(episode_ext_subs['subtitles'])
        except:
            episode_external_subtitles = None
        else:
            episode_external_subtitles = []
            for subs in all_subs:
                if subs[1]:
                    subtitle = subs[0].split(':')
                    subs[0] = {"name": language_from_alpha2(subtitle[0]),
                               "code2": subtitle[0],
                               "code3": alpha3_from_alpha2(subtitle[0]),
                               "forced": True if len(subtitle) > 1 else False}
                    episode_external_subtitles.append({'language': subs[0],
                                                       'path': path_mappings.path_replace(subs[1]),
                                                       'filename': os.path.basename(subs[1]),
                                                       'videopath': path_mappings.path_replace(episode_ext_subs['path'])})

        return jsonify(data=episode_external_subtitles)


class Movies(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1

        moviesId = request.args.get('radarrid')
        if moviesId:
            result = database.execute("SELECT * FROM table_movies WHERE radarrId=? ORDER BY sortTitle ASC LIMIT ? "
                                      "OFFSET ?", (moviesId, length, start))
            desired_languages = database.execute("SELECT languages FROM table_movies WHERE radarrId=?",
                                                 (moviesId,), only_one=True)['languages']
            if desired_languages == "None":
                desired_languages = '[]'
        else:
            result = database.execute("SELECT * FROM table_movies ORDER BY sortTitle ASC LIMIT ? OFFSET ?",
                                      (length, start))
        for item in result:
            # Parse audio language
            item.update({"audio_language": {"name": item['audio_language'],
                                            "code2": alpha2_from_language(item['audio_language']) or None,
                                            "code3": alpha3_from_language(item['audio_language']) or None}})

            # Parse desired languages
            if item['languages'] and item['languages'] != 'None':
                item.update({"languages": ast.literal_eval(item['languages'])})
                for i, subs in enumerate(item['languages']):
                    item['languages'][i] = {"name": language_from_alpha2(subs),
                                            "code2": subs,
                                            "code3": alpha3_from_alpha2(subs)}
            else:
                item.update({"languages": []})

            # Parse alternate titles
            if item['alternativeTitles']:
                item.update({"alternativeTitles": ast.literal_eval(item['alternativeTitles'])})

            # Parse failed attempts
            if item['failedAttempts']:
                item.update({"failedAttempts": ast.literal_eval(item['failedAttempts'])})

            # Parse subtitles
            if item['subtitles']:
                item.update({"subtitles": ast.literal_eval(item['subtitles'])})
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
            else:
                item.update({"subtitles": []})

            # Parse missing subtitles
            if item['missing_subtitles']:
                item.update({"missing_subtitles": ast.literal_eval(item['missing_subtitles'])})
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
            else:
                item.update({"missing_subtitles": []})

            # Parse tags
            item.update({"tags": ast.literal_eval(item['tags'])})

            # Provide mapped path
            mapped_path = path_mappings.path_replace_movie(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isfile(mapped_path)})

            # Add the movie desired subtitles language code2
            try:
                item.update({"desired_languages": ast.literal_eval(desired_languages)})
            except NameError:
                pass

            item.update({"monitored": item["monitored"] == "True"})
            item.update({"forced": item["forced"] == "True"})
            item.update({"hearing_impaired": item["hearing_impaired"] == "True"})
        return jsonify(data=result)

    @authenticate
    def post(self):
        radarrId = request.args.get('radarrid')

        lang = request.form.getlist('languages')
        if len(lang) > 0:
            pass
        else:
            lang = 'None'

        single_language = settings.general.getboolean('single_language')
        if single_language:
            if str(lang) == "['None']":
                lang = 'None'
            else:
                lang = str(lang)
        else:
            if str(lang) == "['']":
                lang = '[]'

        hi = request.form.get('hi')
        forced = request.form.get('forced')

        if forced == "true":
            forced = "True"
        else:
            forced = "False"

        if hi == "true":
            hi = "True"
        else:
            hi = "False"

        result = database.execute("UPDATE table_movies SET languages=?, hearing_impaired=?, forced=? WHERE "
                                  "radarrId=?", (str(lang), hi, forced, radarrId))

        list_missing_subtitles_movies(no=radarrId)

        event_stream(type='movies', action='update', movie=radarrId)

        return '', 204


class MoviesEditor(Resource):
    @authenticate
    def get(self):
        result = database.execute("SELECT radarrId, title, languages, hearing_impaired, forced, audio_language "
                                  "FROM table_movies ORDER BY sortTitle")

        for item in result:
            # Parse audio language
            item.update({"audio_language": {"name": item['audio_language'],
                                            "code2": alpha2_from_language(item['audio_language']) or None,
                                            "code3": alpha3_from_language(item['audio_language']) or None}})

            # Parse desired languages
            if item['languages'] and item['languages'] != 'None':
                item.update({"languages": ast.literal_eval(item['languages'])})
                for i, subs in enumerate(item['languages']):
                    item['languages'][i] = {"name": language_from_alpha2(subs),
                                            "code2": subs,
                                            "code3": alpha3_from_alpha2(subs)}
            else:
                item.update({"languages": []})

        return jsonify(data=result)


class MoviesEditSave(Resource):
    @authenticate
    def post(self):
        lang = request.form.getlist('languages[]')
        hi = request.form.getlist('hi[]')
        forced = request.form.getlist('forced[]')

        if lang == ['None']:
            lang = 'None'

        radarrIdList = []
        radarrIdLangList = []
        radarrIdHiList = []
        radarrIdForcedList = []
        for item in request.form.getlist('radarrid[]'):
            radarrid = item.lstrip('row_')
            radarrIdList.append(radarrid)
            if len(lang):
                radarrIdLangList.append([str(lang), radarrid])
            if len(hi):
                radarrIdHiList.append([hi[0], radarrid])
            if len(forced):
                radarrIdForcedList.append([forced[0], radarrid])
        try:
            if len(lang):
                database.execute("UPDATE table_movies SET languages=? WHERE radarrId=?", radarrIdLangList,
                                 execute_many=True)
            if len(hi):
                database.execute("UPDATE table_movies SET hearing_impaired=? WHERE  radarrId=?", radarrIdHiList,
                                 execute_many=True)
            if len(forced):
                database.execute("UPDATE table_movies SET forced=? WHERE radarrId=?", radarrIdForcedList,
                                 execute_many=True)
        except:
            pass
        else:
            for radarrId in radarrIdList:
                list_missing_subtitles_movies(no=radarrId, send_event=False)

        event_stream(type='movies_editor', action='update')
        event_stream(type='badges_movies')

        return '', 204


class MovieSubtitlesDelete(Resource):
    @authenticate
    def delete(self):
        moviePath = request.form.get('moviePath')
        language = request.form.get('language')
        forced = request.form.get('forced')
        hi = request.form.get('hi')
        subtitlesPath = request.form.get('subtitlesPath')
        radarrId = request.form.get('radarrId')

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


class MovieSubtitlesDownload(Resource):
    @authenticate
    def post(self):
        moviePath = request.form.get('moviePath')
        sceneName = request.form.get('sceneName')
        if sceneName == "null":
            sceneName = "None"
        language = request.form.get('language')
        hi = request.form.get('hi').capitalize()
        forced = request.form.get('forced').capitalize()
        radarrId = request.form.get('radarrId')
        title = request.form.get('title')
        providers_list = get_providers()
        providers_auth = get_providers_auth()
        audio_language = database.execute("SELECT audio_language FROM table_movies WHERE radarrId=?", (radarrId,),
                                          only_one=True)['audio_language']

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
            return result, 201
        except OSError:
            pass

        return '', 204


class MovieSubtitlesManualSearch(Resource):
    @authenticate
    def post(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1

        moviePath = request.form.get('moviePath')
        sceneName = request.form.get('sceneName')
        if sceneName == "null":
            sceneName = "None"
        language = request.form.get('language')
        hi = request.form.get('hi').capitalize()
        forced = request.form.get('forced').capitalize()
        title = request.form.get('title')
        providers_list = get_providers()
        providers_auth = get_providers_auth()

        data = manual_search(moviePath, language, hi, forced, providers_list, providers_auth, sceneName, title,
                             'movie')
        if not data:
            data = []
        return jsonify(data=data)


class MovieSubtitlesManualDownload(Resource):
    @authenticate
    def post(self):
        moviePath = request.form.get('moviePath')
        sceneName = request.form.get('sceneName')
        if sceneName == "null":
            sceneName = "None"
        language = request.form.get('language')
        hi = request.form.get('hi').capitalize()
        forced = request.form.get('forced').capitalize()
        selected_provider = request.form.get('provider')
        subtitle = request.form.get('subtitle')
        radarrId = request.form.get('radarrId')
        title = request.form.get('title')
        providers_auth = get_providers_auth()
        audio_language = database.execute("SELECT audio_language FROM table_movies WHERE radarrId=?", (radarrId,),
                                          only_one=True)['audio_language']

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
            return result, 201
        except OSError:
            pass

        return '', 204


class MovieSubtitlesUpload(Resource):
    @authenticate
    def post(self):
        moviePath = request.form.get('moviePath')
        sceneName = request.form.get('sceneName')
        if sceneName == "null":
            sceneName = "None"
        language = request.form.get('language')
        forced = True if request.form.get('forced') == 'on' else False
        upload = request.files.get('upload')
        radarrId = request.form.get('radarrId')
        title = request.form.get('title')
        audioLanguage = request.form.get('audioLanguage')

        _, ext = os.path.splitext(upload.filename)

        if ext not in SUBTITLE_EXTENSIONS:
            raise ValueError('A subtitle of an invalid format was uploaded.')

        try:
            result = manual_upload_subtitle(path=moviePath,
                                            language=language,
                                            forced=forced,
                                            title=title,
                                            scene_name=sceneName,
                                            media_type='movie',
                                            subtitle=upload,
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

            return result, 201
        except OSError:
            pass

        return '', 204


class MovieScanDisk(Resource):
    @authenticate
    def get(self):
        radarrid = request.args.get('radarrid')
        movies_scan_subtitles(radarrid)
        return '', 200


class MovieSearchMissing(Resource):
    @authenticate
    def get(self):
        radarrid = request.args.get('radarrid')
        movies_download_subtitles(radarrid)
        return '', 200


class MovieHistory(Resource):
    @authenticate
    def get(self):
        radarrid = request.args.get('radarrid')

        movie_history = database.execute("SELECT action, timestamp, language, provider, score, radarrId, subs_id, "
                                         "video_path, subtitles_path FROM table_history_movie WHERE radarrId=? ORDER "
                                         "BY timestamp DESC", (radarrid,))
        for item in movie_history:
            item['raw_timestamp'] = item['timestamp']
            item['timestamp'] = pretty.date(datetime.datetime.fromtimestamp(item['timestamp']))
            if item['language']:
                language = item['language'].split(':')
                item['language'] = {"name": language_from_alpha2(language[0]),
                                    "code2": language[0],
                                    "code3": alpha3_from_alpha2(language[0]),
                                    "forced": True if item['language'].endswith(':forced') else False,
                                    "hi": True if item['language'].endswith(':hi') else False}
            if item['score']:
                item['score'] = str(round((int(item['score']) * 100 / 120), 2)) + "%"

            if item['video_path']:
                # Provide mapped path
                mapped_path = path_mappings.path_replace(item['video_path'])
                item.update({"mapped_path": mapped_path})

                # Confirm if path exist
                item.update({"exist": os.path.isfile(mapped_path)})
            else:
                item.update({"mapped_path": None})
                item.update({"exist": False})

            if item['subtitles_path']:
                # Provide mapped subtitles path
                mapped_subtitles_path = path_mappings.path_replace_movie(item['subtitles_path'])
                item.update({"mapped_subtitles_path": mapped_subtitles_path})
            else:
                item.update({"mapped_subtitles_path": None})

            # Check if subtitles is blacklisted
            if item['action'] not in [0, 4, 5]:
                blacklist_db = database.execute(
                    "SELECT provider, subs_id FROM table_blacklist_movie WHERE provider=? AND "
                    "subs_id=?", (item['provider'], item['subs_id']))
            else:
                blacklist_db = []

            if len(blacklist_db):
                item.update({"blacklisted": True})
            else:
                item.update({"blacklisted": False})

        return jsonify(data=movie_history)


class MovieTools(Resource):
    @authenticate
    def get(self):
        movieid = request.args.get('movieid')

        movie_ext_subs = database.execute("SELECT path, subtitles FROM table_movies WHERE radarrId=?",
                                          (movieid,), only_one=True)
        try:
            all_subs = ast.literal_eval(movie_ext_subs['subtitles'])
        except:
            movie_external_subtitles = None
        else:
            movie_external_subtitles = []
            for subs in all_subs:
                if subs[1]:
                    subtitle = subs[0].split(':')
                    subs[0] = {"name": language_from_alpha2(subtitle[0]),
                               "code2": subtitle[0],
                               "code3": alpha3_from_alpha2(subtitle[0]),
                               "forced": True if len(subtitle) > 1 else False}
                    movie_external_subtitles.append({'language': subs[0],
                                                     'path': path_mappings.path_replace_movie(subs[1]),
                                                     'filename': os.path.basename(subs[1]),
                                                     'videopath': path_mappings.path_replace_movie(movie_ext_subs['path'])})

        return jsonify(data=movie_external_subtitles)


class HistorySeries(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1

        upgradable_episodes_not_perfect = []
        if settings.general.getboolean('upgrade_subs'):
            days_to_upgrade_subs = settings.general.days_to_upgrade_subs
            minimum_timestamp = ((datetime.datetime.now() - timedelta(days=int(days_to_upgrade_subs))) -
                                 datetime.datetime(1970, 1, 1)).total_seconds()

            if settings.general.getboolean('upgrade_manual'):
                query_actions = [1, 2, 3]
            else:
                query_actions = [1, 3]

            upgradable_episodes = database.execute(
                "SELECT video_path, MAX(timestamp) as timestamp, score, table_shows.tags, table_episodes.monitored, "
                "table_shows.seriesType FROM table_history INNER JOIN table_episodes on "
                "table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId INNER JOIN table_shows on "
                "table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE action IN (" +
                ','.join(map(str, query_actions)) + ") AND  timestamp > ? AND score is not null" + 
                get_exclusion_clause('series') + " GROUP BY table_history.video_path, table_history.language", 
                (minimum_timestamp,))

            for upgradable_episode in upgradable_episodes:
                if upgradable_episode['timestamp'] > minimum_timestamp:
                    try:
                        int(upgradable_episode['score'])
                    except ValueError:
                        pass
                    else:
                        if int(upgradable_episode['score']) < 360:
                            upgradable_episodes_not_perfect.append(upgradable_episode)

        data = database.execute("SELECT table_shows.title as seriesTitle, table_episodes.monitored, "
                                "table_episodes.season || 'x' || table_episodes.episode as episode_number, "
                                "table_episodes.title as episodeTitle, table_history.timestamp, table_history.subs_id, "
                                "table_history.description, table_history.sonarrSeriesId, table_episodes.path, "
                                "table_history.language, table_history.score, table_shows.tags, table_history.action, "
                                "table_history.subtitles_path, table_history.sonarrEpisodeId, table_history.provider "
                                "FROM table_history LEFT JOIN table_shows on table_shows.sonarrSeriesId = "
                                "table_history.sonarrSeriesId LEFT JOIN table_episodes on "
                                "table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId WHERE "
                                "table_episodes.title is not NULL ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                                (length, start))

        for item in data:
            # Mark episode as upgradable or not
            if {"video_path": str(item['path']), "timestamp": float(item['timestamp']), "score": str(item['score']), "tags": str(item['tags']), "monitored": str(item['monitored'])} in upgradable_episodes_not_perfect:
                item.update({"upgradable": True})
            else:
                item.update({"upgradable": False})

            # Parse language
            if item['language'] and item['language'] != 'None':
                splitted_language = item['language'].split(':')
                item['language'] = {"name": language_from_alpha2(splitted_language[0]),
                                    "code2": splitted_language[0],
                                    "code3": alpha3_from_alpha2(splitted_language[0]),
                                    "forced": True if item['language'].endswith(':forced') else False,
                                    "hi": True if item['language'].endswith(':hi') else False}

            # Make timestamp pretty
            if item['timestamp']:
                item['raw_timestamp'] = item['timestamp']
                item['timestamp'] = pretty.date(int(item['timestamp']))

            if item['path']:
                # Provide mapped path
                mapped_path = path_mappings.path_replace(item['path'])
                item.update({"mapped_path": mapped_path})

                # Confirm if path exist
                item.update({"exist": os.path.isfile(mapped_path)})
            else:
                item.update({"mapped_path": None})
                item.update({"exist": False})

            if item['subtitles_path']:
                # Provide mapped subtitles path
                mapped_subtitles_path = path_mappings.path_replace_movie(item['subtitles_path'])
                item.update({"mapped_subtitles_path": mapped_subtitles_path})
            else:
                item.update({"mapped_subtitles_path": None})

            # Check if subtitles is blacklisted
            if item['action'] not in [0, 4, 5]:
                blacklist_db = database.execute("SELECT provider, subs_id FROM table_blacklist WHERE provider=? AND "
                                                "subs_id=?", (item['provider'], item['subs_id']))
            else:
                blacklist_db = []

            if len(blacklist_db):
                item.update({"blacklisted": True})
            else:
                item.update({"blacklisted": False})

            item.update({"monitored": item["monitored"] == "True"})

        return jsonify(data=data)


class HistoryMovies(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1

        upgradable_movies = []
        upgradable_movies_not_perfect = []
        if settings.general.getboolean('upgrade_subs'):
            days_to_upgrade_subs = settings.general.days_to_upgrade_subs
            minimum_timestamp = ((datetime.datetime.now() - timedelta(days=int(days_to_upgrade_subs))) -
                                 datetime.datetime(1970, 1, 1)).total_seconds()

            if settings.general.getboolean('upgrade_manual'):
                query_actions = [1, 2, 3]
            else:
                query_actions = [1, 3]

            upgradable_movies = database.execute(
                "SELECT video_path, MAX(timestamp) as timestamp, score, tags, monitored FROM table_history_movie "
                "INNER JOIN table_movies on table_movies.radarrId=table_history_movie.radarrId WHERE action IN (" +
                ','.join(map(str, query_actions)) + ") AND timestamp > ? AND score is not NULL" + 
                get_exclusion_clause('movie') + " GROUP BY video_path, language", (minimum_timestamp,))

            for upgradable_movie in upgradable_movies:
                if upgradable_movie['timestamp'] > minimum_timestamp:
                    try:
                        int(upgradable_movie['score'])
                    except ValueError:
                        pass
                    else:
                        if int(upgradable_movie['score']) < 120:
                            upgradable_movies_not_perfect.append(upgradable_movie)

        data = database.execute("SELECT table_history_movie.action, table_movies.title, table_history_movie.timestamp, "
                                "table_history_movie.description, table_history_movie.radarrId, table_movies.monitored,"
                                " table_history_movie.video_path, table_history_movie.language, table_movies.tags, "
                                "table_history_movie.score, table_history_movie.subs_id, table_history_movie.provider, "
                                "table_history_movie.subtitles_path, table_history_movie.subtitles_path FROM "
                                "table_history_movie LEFT JOIN table_movies on table_movies.radarrId = "
                                "table_history_movie.radarrId WHERE table_movies.title is not NULL ORDER BY timestamp "
                                "DESC LIMIT ? OFFSET ?", (length, start))

        for item in data:
            # Mark movies as upgradable or not
            if {"video_path": str(item['video_path']), "timestamp": float(item['timestamp']), "score": str(item['score']), "tags": str(item['tags']), "monitored": str(item['monitored'])} in upgradable_movies_not_perfect:
                item.update({"upgradable": True})
            else:
                item.update({"upgradable": False})

            # Parse language
            if item['language'] and item['language'] != 'None':
                splitted_language = item['language'].split(':')
                item['language'] = {"name": language_from_alpha2(splitted_language[0]),
                                    "code2": splitted_language[0],
                                    "code3": alpha3_from_alpha2(splitted_language[0]),
                                    "forced": True if len(splitted_language) > 1 else False}

            # Make timestamp pretty
            if item['timestamp']:
                item['raw_timestamp'] = item['timestamp']
                item['timestamp'] = pretty.date(int(item['timestamp']))

            if item['video_path']:
                # Provide mapped path
                mapped_path = path_mappings.path_replace_movie(item['video_path'])
                item.update({"mapped_path": mapped_path})

                # Confirm if path exist
                item.update({"exist": os.path.isfile(mapped_path)})
            else:
                item.update({"mapped_path": None})
                item.update({"exist": False})

            if item['subtitles_path']:
                # Provide mapped subtitles path
                mapped_subtitles_path = path_mappings.path_replace_movie(item['subtitles_path'])
                item.update({"mapped_subtitles_path": mapped_subtitles_path})
            else:
                item.update({"mapped_subtitles_path": None})

            # Check if subtitles is blacklisted
            if item['action'] not in [0, 4, 5]:
                blacklist_db = database.execute("SELECT provider, subs_id FROM table_blacklist_movie WHERE provider=? "
                                                "AND subs_id=?", (item['provider'], item['subs_id']))
            else:
                blacklist_db = []

            if len(blacklist_db):
                item.update({"blacklisted": True})
            else:
                item.update({"blacklisted": False})

            item.update({"monitored": item["monitored"] == "True"})

        return jsonify(data=data)


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


class WantedSeries(Resource):
    @authenticate
    def get(self):

        data = database.execute("SELECT table_shows.title as seriesTitle, table_episodes.monitored, "
                                "table_episodes.season || 'x' || table_episodes.episode as episode_number, "
                                "table_episodes.title as episodeTitle, table_episodes.missing_subtitles, "
                                "table_episodes.sonarrSeriesId, table_episodes.path, table_shows.hearing_impaired, "
                                "table_episodes.sonarrEpisodeId, table_episodes.scene_name, table_shows.tags, "
                                "table_episodes.failedAttempts, table_shows.seriesType FROM table_episodes INNER JOIN "
                                "table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE "
                                "table_episodes.missing_subtitles != '[]'" + get_exclusion_clause('series') +
                                " ORDER BY table_episodes._rowid_ ")

        for item in data:
            # Parse missing subtitles
            if item['missing_subtitles']:
                item.update({"missing_subtitles": ast.literal_eval(item['missing_subtitles'])})
                for i, subs in enumerate(item['missing_subtitles']):
                    splitted_subs = subs.split(':')
                    item['missing_subtitles'][i] = {"name": language_from_alpha2(splitted_subs[0]),
                                                    "code2": splitted_subs[0],
                                                    "code3": alpha3_from_alpha2(splitted_subs[0]),
                                                    "forced": False,
                                                    "hi": False}
                    if len(splitted_subs) > 1:
                        item['missing_subtitles'][i].update({
                            "forced": True if splitted_subs[1] == 'forced' else False,
                            "hi": True if splitted_subs[1] == 'hi' else False
                        })
            else:
                item.update({"missing_subtitles": []})

            # Provide mapped path
            mapped_path = path_mappings.path_replace(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isfile(mapped_path)})
            item.update({"monitored": item["monitored"] == "True"})
            item.update({"hearing_impaired": item["hearing_impaired"] == "True"})

        return jsonify(data=data)


class WantedMovies(Resource):
    @authenticate
    def get(self):
        data = database.execute("SELECT title, missing_subtitles, radarrId, path, hearing_impaired, sceneName, "
                                "failedAttempts, tags, monitored FROM table_movies WHERE missing_subtitles != '[]'" +
                                get_exclusion_clause('movie') + " ORDER BY _rowid_ ")

        for item in data:
            # Parse missing subtitles
            if item['missing_subtitles']:
                item.update({"missing_subtitles": ast.literal_eval(item['missing_subtitles'])})
                for i, subs in enumerate(item['missing_subtitles']):
                    splitted_subs = subs.split(':')
                    item['missing_subtitles'][i] = {"name": language_from_alpha2(splitted_subs[0]),
                                                    "code2": splitted_subs[0],
                                                    "code3": alpha3_from_alpha2(splitted_subs[0]),
                                                    "forced": False,
                                                    "hi": False}
                    if len(splitted_subs) > 1:
                        item['missing_subtitles'][i].update({
                            "forced": True if splitted_subs[1] == 'forced' else False,
                            "hi": True if splitted_subs[1] == 'hi' else False
                        })
            else:
                item.update({"missing_subtitles": []})

            # Provide mapped path
            mapped_path = path_mappings.path_replace_movie(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isfile(mapped_path)})
            item.update({"monitored": item["monitored"] == "True"})
            item.update({"hearing_impaired": item["hearing_impaired"] == "True"})

        return jsonify(data=data)


class SearchWantedSeries(Resource):
    @authenticate
    def get(self):
        wanted_search_missing_subtitles_series()
        return '', 200


class SearchWantedMovies(Resource):
    @authenticate
    def get(self):
        wanted_search_missing_subtitles_movies()
        return '', 200


class BlacklistSeries(Resource):
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
            item['raw_timestamp'] = item['timestamp']
            # Make timestamp pretty
            item.update({'timestamp': pretty.date(datetime.datetime.fromtimestamp(item['timestamp']))})

            # Convert language code2 to name
            if item['language']:
                language = item['language'].split(':')
                item['language'] = {"name": language_from_alpha2(language[0]),
                                    "code2": language[0],
                                    "code3": alpha3_from_alpha2(language[0]),
                                    "forced": True if item['language'].endswith(':forced') else False,
                                    "hi": True if item['language'].endswith(':hi') else False}

        return jsonify(data=data)


class BlacklistEpisodeSubtitlesAdd(Resource):
    @authenticate
    def post(self):
        sonarr_series_id = int(request.form.get('sonarr_series_id'))
        sonarr_episode_id = int(request.form.get('sonarr_episode_id'))
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
        media_path = request.form.get('video_path')
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
                         media_path=path_mappings.path_replace(media_path),
                         subtitles_path=path_mappings.path_replace(subtitles_path),
                         sonarr_series_id=sonarr_series_id,
                         sonarr_episode_id=sonarr_episode_id)
        episode_download_subtitles(sonarr_episode_id)
        event_stream(type='episodeHistory')
        return '', 200


class BlacklistEpisodeSubtitlesRemove(Resource):
    @authenticate
    def delete(self):
        provider = request.form.get('provider')
        subs_id = request.form.get('subs_id')

        blacklist_delete(provider=provider, subs_id=subs_id)
        return '', 200


class BlacklistEpisodeSubtitlesRemoveAll(Resource):
    @authenticate
    def delete(self):
        blacklist_delete_all()
        return '', 200


class BlacklistMovies(Resource):
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
            item['raw_timestamp'] = item['timestamp']
            # Make timestamp pretty
            item.update({'timestamp': pretty.date(datetime.datetime.fromtimestamp(item['timestamp']))})

            # Convert language code2 to name
            if item['language']:
                language = item['language'].split(':')
                item['language'] = {"name": language_from_alpha2(language[0]),
                                    "code2": language[0],
                                    "code3": alpha3_from_alpha2(language[0]),
                                    "forced": True if item['language'].endswith(':forced') else False,
                                    "hi": True if item['language'].endswith(':hi') else False}

        return jsonify(data=data)


class BlacklistMovieSubtitlesAdd(Resource):
    @authenticate
    def post(self):
        radarr_id = int(request.form.get('radarr_id'))
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
        media_path = request.form.get('video_path')
        subtitles_path = request.form.get('subtitles_path')

        blacklist_log_movie(radarr_id=radarr_id,
                            provider=provider,
                            subs_id=subs_id,
                            language=language_str)
        delete_subtitles(media_type='movie',
                         language=alpha3_from_alpha2(language),
                         forced=forced,
                         hi=hi,
                         media_path=path_mappings.path_replace_movie(media_path),
                         subtitles_path=path_mappings.path_replace_movie(subtitles_path),
                         radarr_id=radarr_id)
        movies_download_subtitles(radarr_id)
        event_stream(type='movieHistory')
        return '', 200


class BlacklistMovieSubtitlesRemove(Resource):
    @authenticate
    def delete(self):
        provider = request.form.get('provider')
        subs_id = request.form.get('subs_id')

        blacklist_delete_movie(provider=provider, subs_id=subs_id)
        return '', 200


class BlacklistMovieSubtitlesRemoveAll(Resource):
    @authenticate
    def delete(self):
        blacklist_delete_all_movie()
        return '', 200


class SyncSubtitles(Resource):
    @authenticate
    def post(self):
        language = request.form.get('language')
        subtitles_path = request.form.get('subtitlesPath')
        video_path = request.form.get('videoPath')
        media_type = request.form.get('mediaType')

        if media_type == 'series':
            episode_metadata = database.execute("SELECT sonarrSeriesId, sonarrEpisodeId FROM table_episodes"
                                                " WHERE path = ?", (path_mappings.path_replace_reverse(video_path),),
                                                only_one=True)
            subsync.sync(video_path=video_path, srt_path=subtitles_path,
                         srt_lang=language, media_type=media_type, sonarr_series_id=episode_metadata['sonarrSeriesId'],
                         sonarr_episode_id=episode_metadata['sonarrEpisodeId'])
        else:
            movie_metadata = database.execute("SELECT radarrId FROM table_movies WHERE path = ?",
                                              (path_mappings.path_replace_reverse_movie(video_path),), only_one=True)
            subsync.sync(video_path=video_path, srt_path=subtitles_path,
                         srt_lang=language, media_type=media_type, radarr_id=movie_metadata['radarrId'])

        return '', 200


class SubMods(Resource):
    @authenticate
    def post(self):
        language = request.form.get('language')
        subtitles_path = request.form.get('subtitlesPath')
        mod = request.form.get('mod')

        subtitles_apply_mods(language, subtitles_path, [mod])

        return '', 200


class BrowseBazarrFS(Resource):
    @authenticate
    def get(self):
        path = request.args.get('path') or ''
        data = []
        result = browse_bazarr_filesystem(path)
        for item in result['directories']:
            data.append({'text': item['name'], 'children': True, 'path': item['path']})
        return jsonify(data)


class BrowseSonarrFS(Resource):
    @authenticate
    def get(self):
        path = request.args.get('path') or ''
        data = []
        result = browse_sonarr_filesystem(path)
        for item in result['directories']:
            data.append({'text': item['name'], 'children': True, 'path': item['path']})
        return jsonify(data)


class BrowseRadarrFS(Resource):
    @authenticate
    def get(self):
        path = request.args.get('path') or ''
        data = []
        result = browse_radarr_filesystem(path)
        for item in result['directories']:
            data.append({'text': item['name'], 'children': True, 'path': item['path']})
        return jsonify(data)


api.add_resource(Shutdown, '/system/shutdown')
api.add_resource(Restart, '/system/restart')

api.add_resource(BadgesSeries, '/badges/series')
api.add_resource(BadgesMovies, '/badges/movies')
api.add_resource(BadgesProviders, '/badges/providers')
api.add_resource(Languages, '/system/languages')
api.add_resource(Notifications, '/notifications')

api.add_resource(Search, '/search')

api.add_resource(ResetProviders, '/providers/reset')

api.add_resource(SaveSettings, '/settings')

api.add_resource(SystemTasks, '/system/tasks')
api.add_resource(SystemLogs, '/system/logs')
api.add_resource(SystemProviders, '/system/providers')
api.add_resource(SystemStatus, '/system/status')
api.add_resource(SystemReleases, '/system/releases')

api.add_resource(SubtitleNameInfo, '/subtitles/info')
api.add_resource(SyncSubtitles, '/subtitles/sync')
api.add_resource(SubMods, '/subtitles/mods')

api.add_resource(Series, '/series')
# api.add_resource(SeriesEditor, '/series_editor')
# api.add_resource(SeriesEditSave, '/series_edit_save')
api.add_resource(Episodes, '/episodes')
api.add_resource(EpisodesSubtitles, '/episodes/subtitles')

# api.add_resource(EpisodesSubtitlesDownload, '/episodes_subtitles_download')
# api.add_resource(EpisodesSubtitlesManualSearch, '/episodes_subtitles_manual_search')
# api.add_resource(EpisodesSubtitlesManualDownload, '/episodes_subtitles_manual_download')
# api.add_resource(EpisodesScanDisk, '/episodes_scan_disk')
# api.add_resource(EpisodesSearchMissing, '/episodes_search_missing')
api.add_resource(EpisodesHistory, '/episodes/history')
# api.add_resource(EpisodesTools, '/episodes_tools')

api.add_resource(Movies, '/movies')
# api.add_resource(MoviesEditor, '/movies_editor')
# api.add_resource(MoviesEditSave, '/movies_edit_save')
# api.add_resource(MovieSubtitlesDelete, '/movie_subtitles_delete')
# api.add_resource(MovieSubtitlesDownload, '/movie_subtitles_download')
# api.add_resource(MovieSubtitlesManualSearch, '/movie_subtitles_manual_search')
# api.add_resource(MovieSubtitlesManualDownload, '/movie_subtitles_manual_download')
# api.add_resource(MovieSubtitlesUpload, '/movie_subtitles_upload')
# api.add_resource(MovieScanDisk, '/movie_scan_disk')
# api.add_resource(MovieSearchMissing, '/movie_search_missing')
api.add_resource(MovieHistory, '/movies/history')
api.add_resource(MovieTools, '/movies/tools')

api.add_resource(HistorySeries, '/history/series')
api.add_resource(HistoryMovies, '/history/movies')
api.add_resource(HistoryStats, '/history/stats')

api.add_resource(WantedSeries, '/series/wanted')
api.add_resource(WantedMovies, '/movies/wanted')
api.add_resource(SearchWantedSeries, '/series/wanted/search')
api.add_resource(SearchWantedMovies, '/movies/wanted/search')

api.add_resource(BlacklistSeries, '/series/blacklist')
# api.add_resource(BlacklistEpisodeSubtitlesAdd, '/blacklist_episode_subtitles_add')
# api.add_resource(BlacklistEpisodeSubtitlesRemove, '/blacklist_episode_subtitles_remove')
# api.add_resource(BlacklistEpisodeSubtitlesRemoveAll, '/blacklist_episode_subtitles_remove_all')
api.add_resource(BlacklistMovies, '/movies/blacklist')
# api.add_resource(BlacklistMovieSubtitlesAdd, '/blacklist_movie_subtitles_add')
# api.add_resource(BlacklistMovieSubtitlesRemove, '/blacklist_movie_subtitles_remove')
# api.add_resource(BlacklistMovieSubtitlesRemoveAll, '/blacklist_movie_subtitles_remove_all')

api.add_resource(BrowseBazarrFS, '/browse_bazarr_filesystem')
api.add_resource(BrowseSonarrFS, '/browse_sonarr_filesystem')
api.add_resource(BrowseRadarrFS, '/browse_radarr_filesystem')

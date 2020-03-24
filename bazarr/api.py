# coding=utf-8

import os
import ast
import libs
from datetime import timedelta
import datetime
import pretty
import time
from operator import itemgetter
import platform
import io
from calendar import day_name
import importlib

from get_args import args
from config import settings, base_url, save_settings

from init import *
import logging
from database import database
from helper import path_replace, path_replace_reverse, path_replace_movie, path_replace_reverse_movie
from get_languages import language_from_alpha3, language_from_alpha2, alpha2_from_alpha3, alpha2_from_language, \
    alpha3_from_language, alpha3_from_alpha2
from get_subtitle import download_subtitle, series_download_subtitles, movies_download_subtitles, \
    manual_search, manual_download_subtitle, manual_upload_subtitle, wanted_search_missing_subtitles_series, \
    wanted_search_missing_subtitles_movies
from notifier import send_notifications, send_notifications_movie
from list_subtitles import store_subtitles, store_subtitles_movie, series_scan_subtitles, movies_scan_subtitles, \
    list_missing_subtitles, list_missing_subtitles_movies
from utils import history_log, history_log_movie, get_sonarr_version, get_radarr_version
from get_providers import get_providers, get_providers_auth, list_throttled_providers
from websocket_handler import event_stream
from scheduler import Scheduler

from subliminal_patch.core import SUBTITLE_EXTENSIONS

from flask import Flask, jsonify, request, Response, Blueprint

from flask_restful import Resource, Api

api_bp = Blueprint('api', __name__, url_prefix=base_url.rstrip('/')+'/api')
api = Api(api_bp)

scheduler = Scheduler()


class Badges(Resource):
    def get(self):
        result = {
            "missing_episodes": database.execute("SELECT COUNT(*) as count FROM table_episodes WHERE missing_subtitles "
                                                 "is not null AND missing_subtitles != '[]'", only_one=True)['count'],
            "missing_movies": database.execute("SELECT COUNT(*) as count FROM table_movies WHERE missing_subtitles "
                                               "is not null AND missing_subtitles != '[]'", only_one=True)['count'],
            "throttled_providers": len(eval(str(settings.general.throtteled_providers)))
        }
        return jsonify(result)


class Languages(Resource):
    def get(self):
        enabled = request.args.get('enabled')
        if enabled.lower() in ['true', '1']:
            result = database.execute("SELECT * FROM table_settings_languages WHERE enabled=1")
        else:
            result = database.execute("SELECT * FROM table_settings_languages")
        return jsonify(result)


class SaveSettings(Resource):
    def post(self):
        save_settings(request.form.items())

        return '', 200


class SystemTasks(Resource):
    def get(self):
        taskid = request.args.get('taskid')

        task_list = scheduler.get_task_list()

        for item in task_list:
            # Add Datatables rowId
            item.update({"DT_RowId": item['job_id']})

        if taskid:
            for item in task_list:
                if item['job_id'] == taskid:
                    task_list = [item]
                    continue

        return jsonify(data=task_list)


    def post(self):
        taskid = request.json['taskid']

        scheduler.execute_job_now(taskid)

        return '', 200


class SystemLogs(Resource):
    def get(self):
        logs = []
        with io.open(os.path.join(args.config_dir, 'log', 'bazarr.log'), encoding='UTF-8') as file:
            for line in file.readlines():
                lin = []
                lin = line.split('|')
                logs.append(lin)
            logs.reverse()
        return jsonify(data=logs)


class SystemProviders(Resource):
    def get(self):
        throttled_providers = list_throttled_providers()
        for i in range(len(throttled_providers)):
            throttled_providers[i][1] = throttled_providers[i][1] if throttled_providers[i][1] is not None else "Good"
            throttled_providers[i][2] = throttled_providers[i][2] if throttled_providers[i][2] != "now" else "-"
        return jsonify(data=throttled_providers)


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
    def get(self):
        releases = []
        try:
            with io.open(os.path.join(args.config_dir, 'config', 'releases.txt'), 'r', encoding='UTF-8') as f:
                releases = ast.literal_eval(f.read())
            for release in releases:
                release[1] = release[1].replace('- ', '')
                release[1] = release[1].split('\r\n')
                release[1].pop(0)
                release.append(True if release[0].lstrip('v') == os.environ["BAZARR_VERSION"] else False)

        except Exception as e:
            logging.exception(
                'BAZARR cannot parse releases caching file: ' + os.path.join(args.config_dir, 'config', 'releases.txt'))
        return jsonify(data=releases)


class Series(Resource):
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        draw = request.args.get('draw')

        seriesId = request.args.get('seriesid')
        row_count = database.execute("SELECT COUNT(*) as count FROM table_shows", only_one=True)['count']
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
            # Add Datatables rowId
            item.update({"DT_RowId": 'row_' + str(item['sonarrSeriesId'])})

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

            # Parse alternate titles
            if item['alternateTitles']:
                item.update({"alternateTitles": ast.literal_eval(item['alternateTitles'])})

            # Provide mapped path
            mapped_path = path_replace(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isdir(mapped_path)})

            # Add missing subtitles episode count
            item.update({"episodeMissingCount": database.execute("SELECT COUNT(*) as count FROM table_episodes WHERE "
                                                                 "sonarrSeriesId=? AND missing_subtitles is not null "
                                                                 "AND missing_subtitles != '[]'",
                                                                 (item['sonarrSeriesId'],), only_one=True)['count']})

            # Add episode count
            item.update({"episodeFileCount": database.execute("SELECT COUNT(*) as count FROM table_episodes WHERE "
                                                              "sonarrSeriesId=?", (item['sonarrSeriesId'],),
                                                              only_one=True)['count']})

            # Add the series desired subtitles language code2
            try:
                item.update({"desired_languages": desired_languages})
            except NameError:
                pass
        return jsonify(draw=draw, recordsTotal=row_count, recordsFiltered=row_count, data=result)


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

        if hi == "on":
            hi = "True"
        else:
            hi = "False"

        result = database.execute("UPDATE table_shows SET languages=?, hearing_impaired=?, forced=? WHERE "
                                  "sonarrSeriesId=?", (str(lang), hi, forced, seriesId))

        list_missing_subtitles(no=seriesId)

        event_stream.write(type='series', action='update', series=seriesId)

        return '', 204


class SeriesEditSave(Resource):
    def post(self):
        changed_series = request.json
        lang = changed_series['languages']
        hi = changed_series['hi']
        forced = changed_series['forced']

        if lang == ['None']:
            lang = 'None'

        for item in changed_series['seriesid']:
            seriesid = item.lstrip('row_')
            try:
                if len(lang):
                    database.execute("UPDATE table_shows SET languages=? WHERE sonarrSeriesId=?", (str(lang), seriesid))
                if len(hi):
                    database.execute("UPDATE table_shows SET hearing_impaired=? WHERE  sonarrSeriesId=?", (hi[0], seriesid))
                if len(forced):
                    database.execute("UPDATE table_shows SET forced=? WHERE sonarrSeriesId=?", (forced[0], seriesid))
            except:
                pass
            else:
                list_missing_subtitles(no=seriesid)

                event_stream.write(type='series', action='update', series=seriesid)

        return '', 204


class Episodes(Resource):
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        draw = request.args.get('draw')

        seriesId = request.args.get('seriesid')
        episodeId = request.args.get('episodeid')
        row_count = database.execute("SELECT COUNT(*) as count FROM table_episodes WHERE sonarrSeriesId=?",
                                     (seriesId,), only_one=True)['count']
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
            # Add Datatables rowId
            item.update({"DT_RowId": 'row_' + str(item['sonarrEpisodeId'])})

            # Parse subtitles
            if item['subtitles']:
                item.update({"subtitles": ast.literal_eval(item['subtitles'])})
                for subs in item['subtitles']:
                    subtitle = subs[0].split(':')
                    subs[0] = {"name": language_from_alpha2(subtitle[0]),
                               "code2": subtitle[0],
                               "code3": alpha3_from_alpha2(subtitle[0]),
                               "forced": True if len(subtitle) > 1 else False}

            # Parse missing subtitles
            if item['missing_subtitles']:
                item.update({"missing_subtitles": ast.literal_eval(item['missing_subtitles'])})
                for i, subs in enumerate(item['missing_subtitles']):
                    subtitle = subs.split(':')
                    item['missing_subtitles'][i] = {"name": language_from_alpha2(subtitle[0]),
                                                    "code2": subtitle[0],
                                                    "code3": alpha3_from_alpha2(subtitle[0]),
                                                    "forced": True if len(subtitle) > 1 else False}

            # Provide mapped path
            mapped_path = path_replace(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isfile(mapped_path)})

            # Add the series desired subtitles language code2
            item.update({"desired_languages": desired_languages})
        return jsonify(draw=draw, recordsTotal=row_count, recordsFiltered=row_count, data=result)

class EpisodesSubtitlesDelete(Resource):
    def delete(self):
        episodePath = request.form.get('episodePath')
        language = request.form.get('language')
        subtitlesPath = request.form.get('subtitlesPath')
        sonarrSeriesId = request.form.get('sonarrSeriesId')
        sonarrEpisodeId = request.form.get('sonarrEpisodeId')

        try:
            os.remove(path_replace(subtitlesPath))
            result = language_from_alpha3(language) + " subtitles deleted from disk."
            history_log(0, sonarrSeriesId, sonarrEpisodeId, result, language=alpha2_from_alpha3(language))
            store_subtitles(path_replace_reverse(episodePath), episodePath)
            return result, 202
        except OSError as e:
            logging.exception('BAZARR cannot delete subtitles file: ' + subtitlesPath)

        store_subtitles(path_replace_reverse(episodePath), episodePath)
        return '', 204


class EpisodesSubtitlesDownload(Resource):
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

        try:
            result = download_subtitle(episodePath, language, hi, forced, providers_list, providers_auth, sceneName,
                                       title,
                                       'series')
            if result is not None:
                message = result[0]
                path = result[1]
                forced = result[5]
                language_code = result[2] + ":forced" if forced else result[2]
                provider = result[3]
                score = result[4]
                history_log(1, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score)
                send_notifications(sonarrSeriesId, sonarrEpisodeId, message)
                store_subtitles(path, episodePath)
            else:
                event_stream.write(type='episode', action='update', series=int(sonarrSeriesId), episode=int(sonarrEpisodeId))
            return result, 201
        except OSError:
            pass

        return '', 204


class EpisodesSubtitlesManualSearch(Resource):
    def post(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        draw = request.args.get('draw')

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
        row_count = len(data)
        return jsonify(draw=draw, recordsTotal=row_count, recordsFiltered=row_count, data=data)


class EpisodesSubtitlesManualDownload(Resource):
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

        try:
            result = manual_download_subtitle(episodePath, language, hi, forced, subtitle, selected_provider,
                                              providers_auth,
                                              sceneName, title, 'series')
            if result is not None:
                message = result[0]
                path = result[1]
                forced = result[5]
                language_code = result[2] + ":forced" if forced else result[2]
                provider = result[3]
                score = result[4]
                history_log(2, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score)
                send_notifications(sonarrSeriesId, sonarrEpisodeId, message)
                store_subtitles(path, episodePath)
            return result, 201
        except OSError:
            pass

        return '', 204


class EpisodesSubtitlesUpload(Resource):
    def post(self):
        episodePath = request.form.get('episodePath')
        sceneName = request.form.get('sceneName')
        if sceneName == "null":
            sceneName = "None"
        language = request.form.get('language')
        forced = True if request.form.get('forced') == 'on' else False
        upload = request.files.get('upload')
        sonarrSeriesId = request.form.get('sonarrSeriesId')
        sonarrEpisodeId = request.form.get('sonarrEpisodeId')
        title = request.form.get('title')

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
                                            subtitle=upload)

            if result is not None:
                message = result[0]
                path = result[1]
                language_code = language + ":forced" if forced else language
                provider = "manual"
                score = 360
                history_log(4, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score)
                send_notifications(sonarrSeriesId, sonarrEpisodeId, message)
                store_subtitles(path, episodePath)

            return result, 201
        except OSError:
            pass

        return '', 204


class EpisodesScanDisk(Resource):
    def get(self):
        seriesid = request.args.get('seriesid')
        series_scan_subtitles(seriesid)
        return '', 200


class EpisodesSearchMissing(Resource):
    def get(self):
        seriesid = request.args.get('seriesid')
        series_download_subtitles(seriesid)
        return '', 200


class EpisodesHistory(Resource):
    def get(self):
        episodeid = request.args.get('episodeid')

        episode_history = database.execute("SELECT action, timestamp, language, provider, score FROM table_history "
                                           "WHERE sonarrEpisodeId=? ORDER BY timestamp DESC", (episodeid,))
        for item in episode_history:
            item['timestamp'] = "<div title='" + \
                                time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(item['timestamp'])) + \
                                "' data-toggle='tooltip' data-placement='left'>" + \
                                pretty.date(datetime.datetime.fromtimestamp(item['timestamp'])) + "</div>"
            if item['language']:
                item['language'] = language_from_alpha2(item['language'])
            else:
                item['language'] = "<i>undefined</i>"
            if item['score']:
                item['score'] = str(round((int(item['score']) * 100 / 360), 2)) + "%"

        return jsonify(data=episode_history)


class Movies(Resource):
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        draw = request.args.get('draw')

        moviesId = request.args.get('radarrid')
        row_count = database.execute("SELECT COUNT(*) as count FROM table_movies", only_one=True)['count']
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
            # Add Datatables rowId
            item.update({"DT_RowId": 'row_' + str(item['radarrId'])})

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
                                            "forced": True if len(language) > 1 else False}
                item['subtitles'] = sorted(item['subtitles'], key=itemgetter('name', 'forced'))

            # Parse missing subtitles
            if item['missing_subtitles']:
                item.update({"missing_subtitles": ast.literal_eval(item['missing_subtitles'])})
                for i, subs in enumerate(item['missing_subtitles']):
                    language = subs.split(':')
                    item['missing_subtitles'][i] = {"name": language_from_alpha2(language[0]),
                                                    "code2": language[0],
                                                    "code3": alpha3_from_alpha2(language[0]),
                                                    "forced": True if len(language) > 1 else False}

            # Provide mapped path
            mapped_path = path_replace_movie(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isfile(mapped_path)})

            # Add the movie desired subtitles language code2
            try:
                item.update({"desired_languages": desired_languages})
            except NameError:
                pass
        return jsonify(draw=draw, recordsTotal=row_count, recordsFiltered=row_count, data=result)


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

        if hi == "on":
            hi = "True"
        else:
            hi = "False"

        result = database.execute("UPDATE table_movies SET languages=?, hearing_impaired=?, forced=? WHERE "
                                  "radarrId=?", (str(lang), hi, forced, radarrId))

        list_missing_subtitles_movies(no=radarrId)

        event_stream.write(type='movie', action='update', movie=radarrId)

        return '', 204


class MoviesEditSave(Resource):
    def post(self):
        changed_movies = request.json
        lang = changed_movies['languages']
        hi = changed_movies['hi']
        forced = changed_movies['forced']

        if lang == ['None']:
            lang = 'None'

        for item in changed_movies['radarrid']:
            radarrid = item.lstrip('row_')
            try:
                if len(lang):
                    database.execute("UPDATE table_movies SET languages=? WHERE radarrId=?", (str(lang), radarrid))
                if len(hi):
                    database.execute("UPDATE table_movies SET hearing_impaired=? WHERE  radarrId=?", (hi[0], radarrid))
                if len(forced):
                    database.execute("UPDATE table_movies SET forced=? WHERE radarrId=?", (forced[0], radarrid))
            except:
                pass
            else:
                list_missing_subtitles_movies(no=radarrid)

                event_stream.write(type='movie', action='update', movie=radarrid)

        return '', 204

class MovieSubtitlesDelete(Resource):
    def delete(self):
        moviePath = request.form.get('moviePath')
        language = request.form.get('language')
        subtitlesPath = request.form.get('subtitlesPath')
        radarrId = request.form.get('radarrId')

        try:
            os.remove(path_replace_movie(subtitlesPath))
            result = language_from_alpha3(language) + " subtitles deleted from disk."
            history_log_movie(0, radarrId, result, language=alpha2_from_alpha3(language))
            store_subtitles_movie(path_replace_reverse_movie(moviePath), moviePath)
            return result, 202
        except OSError as e:
            logging.exception('BAZARR cannot delete subtitles file: ' + subtitlesPath)

        store_subtitles_movie(path_replace_reverse_movie(moviePath), moviePath)
        return '', 204


class MovieSubtitlesDownload(Resource):
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

        try:
            result = download_subtitle(moviePath, language, hi, forced, providers_list, providers_auth, sceneName,
                                       title, 'movie')
            if result is not None:
                message = result[0]
                path = result[1]
                forced = result[5]
                language_code = result[2] + ":forced" if forced else result[2]
                provider = result[3]
                score = result[4]
                history_log_movie(1, radarrId, message, path, language_code, provider, score)
                send_notifications_movie(radarrId, message)
                store_subtitles_movie(path, moviePath)
            else:
                event_stream.write(type='movie', action='update', movie=int(radarrId))
            return result, 201
        except OSError:
            pass

        return '', 204


class MovieSubtitlesManualSearch(Resource):
    def post(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        draw = request.args.get('draw')

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
        row_count = len(data)
        return jsonify(draw=draw, recordsTotal=row_count, recordsFiltered=row_count, data=data)


class MovieSubtitlesManualDownload(Resource):
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

        try:
            result = manual_download_subtitle(moviePath, language, hi, forced, subtitle, selected_provider,
                                              providers_auth, sceneName, title, 'movie')
            if result is not None:
                message = result[0]
                path = result[1]
                forced = result[5]
                language_code = result[2] + ":forced" if forced else result[2]
                provider = result[3]
                score = result[4]
                history_log_movie(2, radarrId, message, path, language_code, provider, score)
                send_notifications_movie(radarrId, message)
                store_subtitles_movie(path, moviePath)
            return result, 201
        except OSError:
            pass

        return '', 204


class MovieSubtitlesUpload(Resource):
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
                                            subtitle=upload)

            if result is not None:
                message = result[0]
                path = result[1]
                language_code = language + ":forced" if forced else language
                provider = "manual"
                score = 120
                history_log_movie(4, radarrId, message, path, language_code, provider, score)
                send_notifications_movie(radarrId, message)
                store_subtitles_movie(path, moviePath)

            return result, 201
        except OSError:
            pass

        return '', 204


class MovieScanDisk(Resource):
    def get(self):
        radarrid = request.args.get('radarrid')
        movies_scan_subtitles(radarrid)
        return '', 200


class MovieSearchMissing(Resource):
    def get(self):
        radarrid = request.args.get('radarrid')
        movies_download_subtitles(radarrid)
        return '', 200


class MovieHistory(Resource):
    def get(self):
        radarrid = request.args.get('radarrid')

        movie_history = database.execute("SELECT action, timestamp, language, provider, score "
                                           "FROM table_history_movie WHERE radarrId=? ORDER BY timestamp DESC",
                                           (radarrid,))
        for item in movie_history:
            item['timestamp'] = "<div title='" + \
                                time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(item['timestamp'])) + \
                                "' data-toggle='tooltip' data-placement='left'>" + \
                                pretty.date(datetime.datetime.fromtimestamp(item['timestamp'])) + "</div>"
            if item['language']:
                item['language'] = language_from_alpha2(item['language'])
            else:
                item['language'] = "<i>undefined</i>"
            if item['score']:
                item['score'] = str(round((int(item['score']) * 100 / 120), 2)) + "%"

        return jsonify(data=movie_history)


class HistorySeries(Resource):
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        draw = request.args.get('draw')

        upgradable_episodes_not_perfect = []
        if settings.general.getboolean('upgrade_subs'):
            days_to_upgrade_subs = settings.general.days_to_upgrade_subs
            minimum_timestamp = ((datetime.datetime.now() - timedelta(days=int(days_to_upgrade_subs))) -
                                 datetime.datetime(1970, 1, 1)).total_seconds()

            if settings.general.getboolean('upgrade_manual'):
                query_actions = [1, 2, 3]
            else:
                query_actions = [1, 3]

            if settings.sonarr.getboolean('only_monitored'):
                series_monitored_only_query_string = " AND monitored='True'"
            else:
                series_monitored_only_query_string = ''

            upgradable_episodes = database.execute(
                "SELECT video_path, MAX(timestamp) as timestamp, score FROM table_history "
                "INNER JOIN table_episodes on table_episodes.sonarrEpisodeId = "
                "table_history.sonarrEpisodeId WHERE action IN (" +
                ','.join(map(str, query_actions)) + ") AND  timestamp > ? AND "
                "score is not null" + series_monitored_only_query_string + " GROUP BY "
                "table_history.video_path, table_history.language",
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

        row_count = database.execute("SELECT COUNT(*) as count FROM table_history", only_one=True)['count']
        data = database.execute("SELECT table_history.action, table_shows.title as seriesTitle, "
                                "table_episodes.season || 'x' || table_episodes.episode as episode_number, "
                                "table_episodes.title as episodeTitle, table_history.timestamp, "
                                "table_history.description, table_history.sonarrSeriesId, table_episodes.path, "
                                "table_history.language, table_history.score FROM table_history LEFT JOIN table_shows "
                                "on table_shows.sonarrSeriesId = table_history.sonarrSeriesId LEFT JOIN table_episodes "
                                "on table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId WHERE "
                                "table_episodes.title is not NULL ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                                (length, start))

        for item in data:
            # Mark episode as upgradable or not
            if {"video_path": str(item['path']), "timestamp": float(item['timestamp']), "score": str(item['score'])} in upgradable_episodes_not_perfect:
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
                item['timestamp'] = pretty.date(int(item['timestamp']))

            # Provide mapped path
            mapped_path = path_replace(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isfile(mapped_path)})

        return jsonify(draw=draw, recordsTotal=row_count, recordsFiltered=row_count, data=data)


class HistoryMovies(Resource):
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        draw = request.args.get('draw')

        upgradable_movies = []
        upgradable_movies_not_perfect = []
        if settings.general.getboolean('upgrade_subs'):
            days_to_upgrade_subs = settings.general.days_to_upgrade_subs
            minimum_timestamp = ((datetime.datetime.now() - timedelta(days=int(days_to_upgrade_subs))) -
                                 datetime.datetime(1970, 1, 1)).total_seconds()

            if settings.radarr.getboolean('only_monitored'):
                movies_monitored_only_query_string = ' AND table_movies.monitored = "True"'
            else:
                movies_monitored_only_query_string = ""

            if settings.general.getboolean('upgrade_manual'):
                query_actions = [1, 2, 3]
            else:
                query_actions = [1, 3]

            upgradable_movies = database.execute(
                "SELECT video_path, MAX(timestamp) as timestamp, score FROM table_history_movie "
                "INNER JOIN table_movies on table_movies.radarrId=table_history_movie.radarrId WHERE action IN (" +
                ','.join(map(str, query_actions)) + ") AND timestamp > ? AND score is not NULL" +
                movies_monitored_only_query_string + " GROUP BY video_path, language", (minimum_timestamp,))

            for upgradable_movie in upgradable_movies:
                if upgradable_movie['timestamp'] > minimum_timestamp:
                    try:
                        int(upgradable_movie['score'])
                    except ValueError:
                        pass
                    else:
                        if int(upgradable_movie['score']) < 120:
                            upgradable_movies_not_perfect.append(upgradable_movie)

        row_count = database.execute("SELECT COUNT(*) as count FROM table_history_movie", only_one=True)['count']
        data = database.execute("SELECT table_history_movie.action, table_movies.title, table_history_movie.timestamp, "
                                "table_history_movie.description, table_history_movie.radarrId, "
                                "table_history_movie.video_path, table_history_movie.language, "
                                "table_history_movie.score FROM table_history_movie LEFT JOIN table_movies on "
                                "table_movies.radarrId = table_history_movie.radarrId ORDER BY timestamp DESC LIMIT ? "
                                "OFFSET ?", (length, start))

        for item in data:
            # Mark movies as upgradable or not
            if {"video_path": str(item['video_path']), "timestamp": float(item['timestamp']), "score": str(item['score'])} in upgradable_movies_not_perfect:
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
                item['timestamp'] = pretty.date(int(item['timestamp']))

            if item['video_path']:
                # Provide mapped path
                mapped_path = path_replace_movie(item['video_path'])
                item.update({"mapped_path": mapped_path})

                # Confirm if path exist
                item.update({"exist": os.path.isfile(mapped_path)})
            else:
                item.update({"mapped_path": None})
                item.update({"exist": False})

        return jsonify(draw=draw, recordsTotal=row_count, recordsFiltered=row_count, data=data)


class WantedSeries(Resource):
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        draw = request.args.get('draw')

        if settings.sonarr.getboolean('only_monitored'):
            monitored_only_query_string = " AND monitored='True'"
        else:
            monitored_only_query_string = ''

        row_count = database.execute("SELECT COUNT(*) as count FROM table_episodes WHERE missing_subtitles != '[]'" +
                                     monitored_only_query_string, only_one=True)['count']
        data = database.execute("SELECT table_shows.title as seriesTitle, "
                                "table_episodes.season || 'x' || table_episodes.episode as episode_number, "
                                "table_episodes.title as episodeTitle, table_episodes.missing_subtitles, "
                                "table_episodes.sonarrSeriesId, table_episodes.path, table_shows.hearing_impaired, "
                                "table_episodes.sonarrEpisodeId, table_episodes.scene_name, "
                                "table_episodes.failedAttempts FROM table_episodes INNER JOIN table_shows on "
                                "table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE "
                                "table_episodes.missing_subtitles != '[]'" + monitored_only_query_string +
                                " ORDER BY table_episodes._rowid_ DESC LIMIT ? OFFSET ?", (length, start))

        for item in data:
            # Parse missing subtitles
            if item['missing_subtitles']:
                item.update({"missing_subtitles": ast.literal_eval(item['missing_subtitles'])})
                for i, subs in enumerate(item['missing_subtitles']):
                    splitted_subs = subs.split(':')
                    item['missing_subtitles'][i] = {"name": language_from_alpha2(splitted_subs[0]),
                                                    "code2": splitted_subs[0],
                                                    "code3": alpha3_from_alpha2(splitted_subs[0]),
                                                    "forced": True if len(splitted_subs) > 1 else False}

            # Provide mapped path
            mapped_path = path_replace(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isfile(mapped_path)})

        return jsonify(draw=draw, recordsTotal=row_count, recordsFiltered=row_count, data=data)


class WantedMovies(Resource):
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        draw = request.args.get('draw')

        if settings.radarr.getboolean('only_monitored'):
            monitored_only_query_string = " AND monitored='True'"
        else:
            monitored_only_query_string = ''

        row_count = database.execute("SELECT COUNT(*) as count FROM table_movies WHERE missing_subtitles != '[]'" +
                                     monitored_only_query_string, only_one=True)['count']
        data = database.execute("SELECT title, missing_subtitles, radarrId, path, hearing_impaired, sceneName, "
                                "failedAttempts FROM table_movies WHERE missing_subtitles != '[]'" +
                                monitored_only_query_string + " ORDER BY _rowid_ DESC LIMIT ? OFFSET ?",
                                (length, start))

        for item in data:
            # Parse missing subtitles
            if item['missing_subtitles']:
                item.update({"missing_subtitles": ast.literal_eval(item['missing_subtitles'])})
                for i, subs in enumerate(item['missing_subtitles']):
                    splitted_subs = subs.split(':')
                    item['missing_subtitles'][i] = {"name": language_from_alpha2(splitted_subs[0]),
                                                    "code2": splitted_subs[0],
                                                    "code3": alpha3_from_alpha2(splitted_subs[0]),
                                                    "forced": True if len(splitted_subs) > 1 else False}

            # Provide mapped path
            mapped_path = path_replace_movie(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isfile(mapped_path)})

        return jsonify(draw=draw, recordsTotal=row_count, recordsFiltered=row_count, data=data)


class SearchWantedSeries(Resource):
    def get(self):
        wanted_search_missing_subtitles_series()
        return '', 200


class SearchWantedMovies(Resource):
    def get(self):
        wanted_search_missing_subtitles_movies()
        return '', 200


api.add_resource(Badges, '/badges')
api.add_resource(Languages, '/languages')

api.add_resource(SaveSettings, '/savesettings')

api.add_resource(SystemTasks, '/systemtasks')
api.add_resource(SystemLogs, '/systemlogs')
api.add_resource(SystemProviders, '/systemproviders')
api.add_resource(SystemStatus, '/systemstatus')
api.add_resource(SystemReleases, '/systemreleases')

api.add_resource(Series, '/series')
api.add_resource(SeriesEditSave, '/series_edit_save')
api.add_resource(Episodes, '/episodes')
api.add_resource(EpisodesSubtitlesDelete, '/episodes_subtitles_delete')
api.add_resource(EpisodesSubtitlesDownload, '/episodes_subtitles_download')
api.add_resource(EpisodesSubtitlesManualSearch, '/episodes_subtitles_manual_search')
api.add_resource(EpisodesSubtitlesManualDownload, '/episodes_subtitles_manual_download')
api.add_resource(EpisodesSubtitlesUpload, '/episodes_subtitles_upload')
api.add_resource(EpisodesScanDisk, '/episodes_scan_disk')
api.add_resource(EpisodesSearchMissing, '/episodes_search_missing')
api.add_resource(EpisodesHistory, '/episodes_history')

api.add_resource(Movies, '/movies')
api.add_resource(MoviesEditSave, '/movies_edit_save')
api.add_resource(MovieSubtitlesDelete, '/movie_subtitles_delete')
api.add_resource(MovieSubtitlesDownload, '/movie_subtitles_download')
api.add_resource(MovieSubtitlesManualSearch, '/movie_subtitles_manual_search')
api.add_resource(MovieSubtitlesManualDownload, '/movie_subtitles_manual_download')
api.add_resource(MovieSubtitlesUpload, '/movie_subtitles_upload')
api.add_resource(MovieScanDisk, '/movie_scan_disk')
api.add_resource(MovieSearchMissing, '/movie_search_missing')
api.add_resource(MovieHistory, '/movie_history')

api.add_resource(HistorySeries, '/history_series')
api.add_resource(HistoryMovies, '/history_movies')

api.add_resource(WantedSeries, '/wanted_series')
api.add_resource(WantedMovies, '/wanted_movies')
api.add_resource(SearchWantedSeries, '/search_wanted_series')
api.add_resource(SearchWantedMovies, '/search_wanted_movies')

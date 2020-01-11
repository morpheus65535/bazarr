import os
import ast
import libs
from datetime import timedelta
import datetime
import pretty

from get_args import args
from config import settings, base_url

from init import *
import logging
from database import database
from helper import path_replace, path_replace_reverse, path_replace_movie, path_replace_reverse_movie
from get_languages import language_from_alpha3, language_from_alpha2, alpha2_from_alpha3, alpha2_from_language, \
    alpha3_from_language, alpha3_from_alpha2
from get_subtitle import download_subtitle, series_download_subtitles, movies_download_subtitles, \
    manual_search, manual_download_subtitle, manual_upload_subtitle
from notifier import send_notifications, send_notifications_movie
from list_subtitles import store_subtitles, store_subtitles_movie, series_scan_subtitles, movies_scan_subtitles, \
    list_missing_subtitles, list_missing_subtitles_movies
from utils import history_log, history_log_movie
from get_providers import get_providers, get_providers_auth, list_throttled_providers

from subliminal_patch.core import SUBTITLE_EXTENSIONS

from flask import Flask, jsonify, request, Response, Blueprint

from flask_restful import Resource, Api

api_bp = Blueprint('api', __name__, url_prefix=base_url.rstrip('/')+'/api')
api = Api(api_bp)


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


class Series(Resource):
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        draw = request.args.get('draw')

        seriesId = request.args.get('id')
        row_count = database.execute("SELECT COUNT(*) as count FROM table_shows", only_one=True)['count']
        if seriesId:
            result = database.execute("SELECT * FROM table_shows WHERE sonarrSeriesId=? ORDER BY sortTitle ASC LIMIT ? "
                                      "OFFSET ?", (seriesId, length, start))
        else:
            result = database.execute("SELECT * FROM table_shows ORDER BY sortTitle ASC LIMIT ? OFFSET ?", (length, start))
        for item in result:
            # Parse audio language
            if item['audio_language']:
                item.update({"audio_language": {"name": item['audio_language'],
                                                "code2": alpha2_from_language(item['audio_language']),
                                                "code3": alpha3_from_language(item['audio_language'])}})

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
        return jsonify(draw=draw, recordsTotal=row_count, recordsFiltered=row_count, data=result)


class Episodes(Resource):
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        draw = request.args.get('draw')

        seriesId = request.args.get('id')
        row_count = database.execute("SELECT COUNT(*) as count FROM table_episodes WHERE sonarrSeriesId=?",
                                     (seriesId,), only_one=True)['count']
        if seriesId:
            result = database.execute("SELECT * FROM table_episodes WHERE sonarrSeriesId=? ORDER BY season DESC, "
                                      "episode DESC", (seriesId,))
            desired_languages = database.execute("SELECT languages FROM table_shows WHERE sonarrSeriesId=?",
                                                 (seriesId,), only_one=True)['languages']
            if desired_languages == "None":
                desired_languages = '[]'
        else:
            return "Series ID not provided", 400
        for item in result:
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


class Movies(Resource):
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        draw = request.args.get('draw')

        moviesId = request.args.get('id')
        row_count = database.execute("SELECT COUNT(*) as count FROM table_movies", only_one=True)['count']
        if moviesId:
            result = database.execute("SELECT * FROM table_movies WHERE radarrId=? ORDER BY sortTitle ASC LIMIT ? "
                                      "OFFSET ?", (length, start), (moviesId,))
        else:
            result = database.execute("SELECT * FROM table_movies ORDER BY sortTitle ASC LIMIT ? OFFSET ?",
                                      (length, start))
        for item in result:
            # Parse audio language
            if item['audio_language']:
                item.update({"audio_language": {"name": item['audio_language'],
                                                "code2": alpha2_from_language(item['audio_language']),
                                                "code3": alpha3_from_language(item['audio_language'])}})

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
                for subs in item['subtitles']:
                    subs[0] = {"name": language_from_alpha2(subs[0]),
                               "code2": subs[0],
                               "code3": alpha3_from_alpha2(subs[0])}

            # Parse missing subtitles
            if item['missing_subtitles']:
                item.update({"missing_subtitles": ast.literal_eval(item['missing_subtitles'])})
                for i, subs in enumerate(item['missing_subtitles']):
                    item['missing_subtitles'][i] = {"name": language_from_alpha2(subs),
                                                    "code2": subs,
                                                    "code3": alpha3_from_alpha2(subs)}

            # Provide mapped path
            mapped_path = path_replace_movie(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isfile(mapped_path)})
        return jsonify(draw=draw, recordsTotal=row_count, recordsFiltered=row_count, data=result)


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

        row_count = database.execute("SELECT COUNT(*) as count FROM table_episodes", only_one=True)['count']
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

        row_count = database.execute("SELECT COUNT(*) as count FROM table_movies", only_one=True)['count']
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


api.add_resource(Badges, '/badges')
api.add_resource(Series, '/series')
api.add_resource(Episodes, '/episodes')
api.add_resource(EpisodesSubtitlesDelete, '/episodes_subtitles_delete')
api.add_resource(EpisodesSubtitlesDownload, '/episodes_subtitles_download')
api.add_resource(EpisodesSubtitlesManualSearch, '/episodes_subtitles_manual_search')
api.add_resource(EpisodesSubtitlesManualDownload, '/episodes_subtitles_manual_download')
api.add_resource(EpisodesSubtitlesUpload, '/episodes_subtitles_upload')
api.add_resource(Movies, '/movies')
api.add_resource(HistorySeries, '/history_series')
api.add_resource(HistoryMovies, '/history_movies')
api.add_resource(WantedSeries, '/wanted_series')
api.add_resource(WantedMovies, '/wanted_movies')

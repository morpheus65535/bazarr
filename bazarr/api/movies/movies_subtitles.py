# coding=utf-8

import os

from flask import request
from flask_restful import Resource
from subliminal_patch.core import SUBTITLE_EXTENSIONS

from database import TableMovies, get_audio_profile_languages, get_profile_id
from ..utils import authenticate
from helper import path_mappings
from get_subtitle.upload import manual_upload_subtitle
from get_subtitle.download import generate_subtitles
from utils import history_log_movie, delete_subtitles
from notifier import send_notifications_movie
from list_subtitles import store_subtitles_movie
from event_handler import event_stream
from config import settings


# PATCH: Download Subtitles
# POST: Upload Subtitles
# DELETE: Delete Subtitles
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
        sceneName = movieInfo['sceneName'] or 'None'

        title = movieInfo['title']
        audio_language = movieInfo['audio_language']

        language = request.form.get('language')
        hi = request.form.get('hi').capitalize()
        forced = request.form.get('forced').capitalize()

        audio_language_list = get_audio_profile_languages(movie_id=radarrId)
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = None

        try:
            result = list(generate_subtitles(moviePath, [(language, hi, forced)], audio_language,
                                             sceneName, title, 'movie', profile_id=get_profile_id(movie_id=radarrId)))
            if result:
                result = result[0]
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
        sceneName = movieInfo['sceneName'] or 'None'

        title = movieInfo['title']
        audioLanguage = movieInfo['audio_language']

        language = request.form.get('language')
        forced = True if request.form.get('forced') == 'true' else False
        hi = True if request.form.get('hi') == 'true' else False
        subFile = request.files.get('file')

        _, ext = os.path.splitext(subFile.filename)

        if ext not in SUBTITLE_EXTENSIONS:
            raise ValueError('A subtitle of an invalid format was uploaded.')

        try:
            result = manual_upload_subtitle(path=moviePath,
                                            language=language,
                                            forced=forced,
                                            hi=hi,
                                            title=title,
                                            scene_name=sceneName,
                                            media_type='movie',
                                            subtitle=subFile,
                                            audio_language=audioLanguage)

            if result is not None:
                message = result[0]
                path = result[1]
                subs_path = result[2]
                if hi:
                    language_code = language + ":hi"
                elif forced:
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

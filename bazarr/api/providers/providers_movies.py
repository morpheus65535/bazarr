# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from database import TableMovies, get_audio_profile_languages, get_profile_id
from get_providers import get_providers, get_providers_auth
from get_subtitle import manual_search, manual_download_subtitle
from utils import history_log_movie
from config import settings
from notifier import send_notifications_movie
from list_subtitles import store_subtitles_movie

from ..utils import authenticate


class ProviderMovies(Resource):
    @authenticate
    def get(self):
        # Manual Search
        movieId = request.args.get('movieid')
        movieInfo = TableMovies.select(TableMovies.title,
                                       TableMovies.path,
                                       TableMovies.profileId) \
            .where(TableMovies.movieId == movieId) \
            .dicts() \
            .get()

        title = movieInfo['title']
        moviePath = movieInfo['path']
        profileId = movieInfo['profileId']

        providers_list = get_providers()
        providers_auth = get_providers_auth()

        data = manual_search(moviePath, profileId, providers_list, providers_auth, title, 'movie')
        if not data:
            data = []
        return jsonify(data=data)

    @authenticate
    def post(self):
        # Manual Download
        movieId = request.args.get('movieid')
        movieInfo = TableMovies.select(TableMovies.title,
                                       TableMovies.path,
                                       TableMovies.audio_language) \
            .where(TableMovies.movieId == movieId) \
            .dicts() \
            .get()

        title = movieInfo['title']
        moviePath = movieInfo['path']
        audio_language = movieInfo['audio_language']

        language = request.form.get('language')
        hi = request.form.get('hi').capitalize()
        forced = request.form.get('forced').capitalize()
        selected_provider = request.form.get('provider')
        subtitle = request.form.get('subtitle')

        providers_auth = get_providers_auth()

        audio_language_list = get_audio_profile_languages(movie_id=movieId)
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = 'None'

        try:
            result = manual_download_subtitle(moviePath, language, audio_language, hi, forced, subtitle,
                                              selected_provider, providers_auth, title, 'movie',
                                              profile_id=get_profile_id(movie_id=radarrId))
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
                history_log_movie(2, movieId, message, path, language_code, provider, score, subs_id, subs_path)
                if not settings.general.getboolean('dont_notify_manual_actions'):
                    send_notifications_movie(movieId, message)
                store_subtitles_movie(moviePath)
        except OSError:
            pass

        return '', 204

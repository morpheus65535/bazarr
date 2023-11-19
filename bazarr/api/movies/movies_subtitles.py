# coding=utf-8

import os
import logging

from flask_restx import Resource, Namespace, reqparse
from subliminal_patch.core import SUBTITLE_EXTENSIONS
from werkzeug.datastructures import FileStorage

from app.database import TableMovies, get_audio_profile_languages, get_profile_id, database, select
from utilities.path_mappings import path_mappings
from subtitles.upload import manual_upload_subtitle
from subtitles.download import generate_subtitles
from subtitles.tools.delete import delete_subtitles
from radarr.history import history_log_movie
from app.notifier import send_notifications_movie
from subtitles.indexer.movies import store_subtitles_movie
from app.event_handler import event_stream, show_message
from app.config import settings

from ..utils import authenticate

api_ns_movies_subtitles = Namespace('Movies Subtitles', description='Download, upload or delete movies subtitles')


@api_ns_movies_subtitles.route('movies/subtitles')
class MoviesSubtitles(Resource):
    patch_request_parser = reqparse.RequestParser()
    patch_request_parser.add_argument('radarrid', type=int, required=True, help='Movie ID')
    patch_request_parser.add_argument('language', type=str, required=True, help='Language code2')
    patch_request_parser.add_argument('forced', type=str, required=True, help='Forced true/false as string')
    patch_request_parser.add_argument('hi', type=str, required=True, help='HI true/false as string')

    @authenticate
    @api_ns_movies_subtitles.doc(parser=patch_request_parser)
    @api_ns_movies_subtitles.response(204, 'Success')
    @api_ns_movies_subtitles.response(401, 'Not Authenticated')
    @api_ns_movies_subtitles.response(404, 'Movie not found')
    @api_ns_movies_subtitles.response(409, 'Unable to save subtitles file. Permission or path mapping issue?')
    @api_ns_movies_subtitles.response(500, 'Custom error messages')
    def patch(self):
        """Download a movie subtitles"""
        args = self.patch_request_parser.parse_args()
        radarrId = args.get('radarrid')

        movieInfo = database.execute(
            select(
                TableMovies.title,
                TableMovies.path,
                TableMovies.sceneName,
                TableMovies.audio_language)
            .where(TableMovies.radarrId == radarrId)) \
            .first()

        if not movieInfo:
            return 'Movie not found', 404

        moviePath = path_mappings.path_replace_movie(movieInfo.path)

        if not os.path.exists(moviePath):
            return 'Movie file not found. Path mapping issue?', 500

        sceneName = movieInfo.sceneName or 'None'

        title = movieInfo.title

        language = args.get('language')
        hi = args.get('hi').capitalize()
        forced = args.get('forced').capitalize()
        if hi == 'True':
            language_str = f'{language}:hi'
        elif forced == 'True':
            language_str = f'{language}:forced'
        else:
            language_str = language

        audio_language_list = get_audio_profile_languages(movieInfo.audio_language)
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = None

        try:
            result = list(generate_subtitles(moviePath, [(language, hi, forced)], audio_language,
                                             sceneName, title, 'movie', profile_id=get_profile_id(movie_id=radarrId)))
            if isinstance(result, list) and len(result):
                result = result[0]
                if isinstance(result, tuple) and len(result):
                    result = result[0]
                history_log_movie(1, radarrId, result)
                store_subtitles_movie(result.path, moviePath)
            else:
                event_stream(type='movie', payload=radarrId)
                show_message(f'No {language_str.upper()} subtitles found')
                return '', 204
        except OSError:
            return 'Unable to save subtitles file. Permission or path mapping issue?', 409
        else:
            return '', 204

    # POST: Upload Subtitles
    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('radarrid', type=int, required=True, help='Movie ID')
    post_request_parser.add_argument('language', type=str, required=True, help='Language code2')
    post_request_parser.add_argument('forced', type=str, required=True, help='Forced true/false as string')
    post_request_parser.add_argument('hi', type=str, required=True, help='HI true/false as string')
    post_request_parser.add_argument('file', type=FileStorage, location='files', required=True,
                                     help='Subtitles file as file upload object')

    @authenticate
    @api_ns_movies_subtitles.doc(parser=post_request_parser)
    @api_ns_movies_subtitles.response(204, 'Success')
    @api_ns_movies_subtitles.response(401, 'Not Authenticated')
    @api_ns_movies_subtitles.response(404, 'Movie not found')
    @api_ns_movies_subtitles.response(409, 'Unable to save subtitles file. Permission or path mapping issue?')
    @api_ns_movies_subtitles.response(500, 'Movie file not found. Path mapping issue?')
    def post(self):
        """Upload a movie subtitles"""
        # TODO: Support Multiply Upload
        args = self.post_request_parser.parse_args()
        radarrId = args.get('radarrid')
        movieInfo = database.execute(
            select(TableMovies.path, TableMovies.audio_language)
            .where(TableMovies.radarrId == radarrId)) \
            .first()

        if not movieInfo:
            return 'Movie not found', 404

        moviePath = path_mappings.path_replace_movie(movieInfo.path)

        if not os.path.exists(moviePath):
            return 'Movie file not found. Path mapping issue?', 500

        audio_language = get_audio_profile_languages(movieInfo.audio_language)
        if len(audio_language) and isinstance(audio_language[0], dict):
            audio_language = audio_language[0]
        else:
            audio_language = {'name': '', 'code2': '', 'code3': ''}

        language = args.get('language')
        forced = args.get('forced') == 'true'
        hi = args.get('hi') == 'true'
        subFile = args.get('file')

        _, ext = os.path.splitext(subFile.filename)

        if not isinstance(ext, str) or ext.lower() not in SUBTITLE_EXTENSIONS:
            raise ValueError('A subtitle of an invalid format was uploaded.')

        try:
            result = manual_upload_subtitle(path=moviePath,
                                            language=language,
                                            forced=forced,
                                            hi=hi,
                                            media_type='movie',
                                            subtitle=subFile,
                                            audio_language=audio_language)

            if not result:
                logging.debug(f"BAZARR unable to process subtitles for this movie: {moviePath}")
            else:
                if isinstance(result, tuple) and len(result):
                    result = result[0]
                provider = "manual"
                score = 120
                history_log_movie(4, radarrId, result, fake_provider=provider, fake_score=score)
                if not settings.general.dont_notify_manual_actions:
                    send_notifications_movie(radarrId, result.message)
                store_subtitles_movie(result.path, moviePath)
        except OSError:
            return 'Unable to save subtitles file. Permission or path mapping issue?', 409
        else:
            return '', 204

    # DELETE: Delete Subtitles
    delete_request_parser = reqparse.RequestParser()
    delete_request_parser.add_argument('radarrid', type=int, required=True, help='Movie ID')
    delete_request_parser.add_argument('language', type=str, required=True, help='Language code2')
    delete_request_parser.add_argument('forced', type=str, required=True, help='Forced true/false as string')
    delete_request_parser.add_argument('hi', type=str, required=True, help='HI true/false as string')
    delete_request_parser.add_argument('path', type=str, required=True, help='Path of the subtitles file')

    @authenticate
    @api_ns_movies_subtitles.doc(parser=delete_request_parser)
    @api_ns_movies_subtitles.response(204, 'Success')
    @api_ns_movies_subtitles.response(401, 'Not Authenticated')
    @api_ns_movies_subtitles.response(404, 'Movie not found')
    @api_ns_movies_subtitles.response(500, 'Subtitles file not found or permission issue.')
    def delete(self):
        """Delete a movie subtitles"""
        args = self.delete_request_parser.parse_args()
        radarrId = args.get('radarrid')
        movieInfo = database.execute(
            select(TableMovies.path)
            .where(TableMovies.radarrId == radarrId)) \
            .first()

        if not movieInfo:
            return 'Movie not found', 404

        moviePath = path_mappings.path_replace_movie(movieInfo.path)

        language = args.get('language')
        forced = args.get('forced')
        hi = args.get('hi')
        subtitlesPath = args.get('path')

        subtitlesPath = path_mappings.path_replace_reverse_movie(subtitlesPath)

        if delete_subtitles(media_type='movie',
                            language=language,
                            forced=forced,
                            hi=hi,
                            media_path=moviePath,
                            subtitles_path=subtitlesPath,
                            radarr_id=radarrId):
            return '', 204
        else:
            return 'Subtitles file not found or permission issue.', 500

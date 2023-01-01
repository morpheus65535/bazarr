# coding=utf-8

import contextlib
import os
import logging

from flask_restx import Resource, Namespace, reqparse
from subliminal_patch.core import SUBTITLE_EXTENSIONS
from werkzeug.datastructures import FileStorage

from app.database import TableMovies, get_audio_profile_languages, get_profile_id
from utilities.path_mappings import path_mappings
from subtitles.upload import manual_upload_subtitle
from subtitles.download import generate_subtitles
from subtitles.tools.delete import delete_subtitles
from radarr.history import history_log_movie
from app.notifier import send_notifications_movie
from subtitles.indexer.movies import store_subtitles_movie
from app.event_handler import event_stream
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
    def patch(self):
        """Download a movie subtitles"""
        args = self.patch_request_parser.parse_args()
        radarrId = args.get('radarrid')

        movieInfo = TableMovies.select(
            TableMovies.title,
            TableMovies.path,
            TableMovies.sceneName,
            TableMovies.audio_language) \
                .where(TableMovies.radarrId == radarrId) \
                .dicts() \
                .get_or_none()

        if not movieInfo:
            return 'Movie not found', 404

        moviePath = path_mappings.path_replace_movie(movieInfo['path'])
        sceneName = movieInfo['sceneName'] or 'None'

        title = movieInfo['title']

        language = args.get('language')
        hi = args.get('hi').capitalize()
        forced = args.get('forced').capitalize()

        audio_language_list = get_audio_profile_languages(movieInfo["audio_language"])
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = None

        with contextlib.suppress(OSError):
            result = list(generate_subtitles(moviePath, [(language, hi, forced)], audio_language,
                                             sceneName, title, 'movie', profile_id=get_profile_id(movie_id=radarrId)))
            if result:
                result = result[0]
                message = result[0]
                path = result[1]
                forced = result[5]
                if result[8]:
                    language_code = f"{result[2]}:hi"
                elif forced:
                    language_code = f"{result[2]}:forced"
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
    def post(self):
        """Upload a movie subtitles"""
        # TODO: Support Multiply Upload
        args = self.post_request_parser.parse_args()
        radarrId = args.get('radarrid')
        movieInfo = TableMovies.select(TableMovies.title,
                                       TableMovies.path,
                                       TableMovies.sceneName,
                                       TableMovies.audio_language) \
                        .where(TableMovies.radarrId == radarrId) \
                        .dicts() \
                        .get_or_none()

        if not movieInfo:
            return 'Movie not found', 404

        moviePath = path_mappings.path_replace_movie(movieInfo['path'])
        sceneName = movieInfo['sceneName'] or 'None'

        title = movieInfo['title']
        audioLanguage = movieInfo['audio_language']

        language = args.get('language')
        forced = args.get('forced') == 'true'
        hi = args.get('hi') == 'true'
        subFile = args.get('file')

        _, ext = os.path.splitext(subFile.filename)

        if not isinstance(ext, str) or ext.lower() not in SUBTITLE_EXTENSIONS:
            raise ValueError('A subtitle of an invalid format was uploaded.')

        with contextlib.suppress(OSError):
            result = manual_upload_subtitle(path=moviePath,
                                            language=language,
                                            forced=forced,
                                            hi=hi,
                                            title=title,
                                            scene_name=sceneName,
                                            media_type='movie',
                                            subtitle=subFile,
                                            audio_language=audioLanguage)

            if not result:
                logging.debug(f"BAZARR unable to process subtitles for this movie: {moviePath}")
            else:
                message = result[0]
                path = result[1]
                subs_path = result[2]
                if hi:
                    language_code = f"{language}:hi"
                elif forced:
                    language_code = f"{language}:forced"
                else:
                    language_code = language
                provider = "manual"
                score = 120
                history_log_movie(4, radarrId, message, path, language_code, provider, score, subtitles_path=subs_path)
                if not settings.general.getboolean('dont_notify_manual_actions'):
                    send_notifications_movie(radarrId, message)
                store_subtitles_movie(path, moviePath)
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
    def delete(self):
        """Delete a movie subtitles"""
        args = self.delete_request_parser.parse_args()
        radarrId = args.get('radarrid')
        movieInfo = TableMovies.select(TableMovies.path) \
            .where(TableMovies.radarrId == radarrId) \
            .dicts() \
            .get_or_none()

        if not movieInfo:
            return 'Movie not found', 404

        moviePath = path_mappings.path_replace_movie(movieInfo['path'])

        language = args.get('language')
        forced = args.get('forced')
        hi = args.get('hi')
        subtitlesPath = args.get('path')

        subtitlesPath = path_mappings.path_replace_reverse_movie(subtitlesPath)

        delete_subtitles(media_type='movie',
                         language=language,
                         forced=forced,
                         hi=hi,
                         media_path=moviePath,
                         subtitles_path=subtitlesPath,
                         radarr_id=radarrId)

        return '', 204

# coding=utf-8

import os

from flask_restx import Resource, Namespace, reqparse, fields, marshal

from app.database import TableMovies, get_audio_profile_languages, get_profile_id, database, select
from utilities.path_mappings import path_mappings
from app.get_providers import get_providers
from subtitles.manual import manual_search, manual_download_subtitle
from radarr.history import history_log_movie
from app.config import settings
from app.notifier import send_notifications_movie
from subtitles.indexer.movies import store_subtitles_movie, list_missing_subtitles_movies
from subtitles.processing import ProcessSubtitlesResult

from ..utils import authenticate


api_ns_providers_movies = Namespace('Providers Movies', description='List and download movies subtitles manually')


@api_ns_providers_movies.route('providers/movies')
class ProviderMovies(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('radarrid', type=int, required=True, help='Movie ID')

    get_response_model = api_ns_providers_movies.model('ProviderMoviesGetResponse', {
        'dont_matches': fields.List(fields.String),
        'forced': fields.String(),
        'hearing_impaired': fields.String(),
        'language': fields.String(),
        'matches': fields.List(fields.String),
        'original_format': fields.String(),
        'orig_score': fields.Integer(),
        'provider': fields.String(),
        'release_info': fields.List(fields.String),
        'score': fields.Integer(),
        'score_without_hash': fields.Integer(),
        'subtitle': fields.String(),
        'uploader': fields.String(),
        'url': fields.String(),
    })

    @authenticate
    @api_ns_providers_movies.response(401, 'Not Authenticated')
    @api_ns_providers_movies.response(404, 'Movie not found')
    @api_ns_providers_movies.response(500, 'Custom error messages')
    @api_ns_providers_movies.doc(parser=get_request_parser)
    def get(self):
        """Search manually for a movie subtitles"""
        args = self.get_request_parser.parse_args()
        radarrId = args.get('radarrid')
        stmt = select(TableMovies.title,
                      TableMovies.path,
                      TableMovies.sceneName,
                      TableMovies.profileId,
                      TableMovies.subtitles,
                      TableMovies.missing_subtitles) \
            .where(TableMovies.radarrId == radarrId)
        movieInfo = database.execute(stmt).first()

        if not movieInfo:
            return 'Movie not found', 404
        elif movieInfo.subtitles is None:
            # subtitles indexing for this movie is incomplete, we'll do it again
            store_subtitles_movie(movieInfo.path, path_mappings.path_replace_movie(movieInfo.path))
            movieInfo = database.execute(stmt).first()
        elif movieInfo.missing_subtitles is None:
            # missing subtitles calculation for this movie is incomplete, we'll do it again
            list_missing_subtitles_movies(no=radarrId)
            movieInfo = database.execute(stmt).first()

        title = movieInfo.title
        moviePath = path_mappings.path_replace_movie(movieInfo.path)

        if not os.path.exists(moviePath):
            return 'Movie file not found. Path mapping issue?', 500

        sceneName = movieInfo.sceneName or "None"
        profileId = movieInfo.profileId

        providers_list = get_providers()

        data = manual_search(moviePath, profileId, providers_list, sceneName, title, 'movie')
        if isinstance(data, str):
            return data, 500
        return marshal(data, self.get_response_model, envelope='data')

    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('radarrid', type=int, required=True, help='Movie ID')
    post_request_parser.add_argument('hi', type=str, required=True, help='HI subtitles from ["True", "False"]')
    post_request_parser.add_argument('forced', type=str, required=True, help='Forced subtitles from ["True", "False"]')
    post_request_parser.add_argument('original_format', type=str, required=True,
                                     help='Use original subtitles format from ["True", "False"]')
    post_request_parser.add_argument('provider', type=str, required=True, help='Provider name')
    post_request_parser.add_argument('subtitle', type=str, required=True, help='Pickled subtitles as return by GET')

    @authenticate
    @api_ns_providers_movies.doc(parser=post_request_parser)
    @api_ns_providers_movies.response(204, 'Success')
    @api_ns_providers_movies.response(401, 'Not Authenticated')
    @api_ns_providers_movies.response(404, 'Movie not found')
    @api_ns_providers_movies.response(500, 'Custom error messages')
    def post(self):
        """Manually download a movie subtitles"""
        args = self.post_request_parser.parse_args()
        radarrId = args.get('radarrid')
        movieInfo = database.execute(
            select(TableMovies.title,
                   TableMovies.path,
                   TableMovies.sceneName,
                   TableMovies.audio_language)
            .where(TableMovies.radarrId == radarrId)) \
            .first()

        if not movieInfo:
            return 'Movie not found', 404

        title = movieInfo.title
        moviePath = path_mappings.path_replace_movie(movieInfo.path)
        sceneName = movieInfo.sceneName or "None"

        hi = args.get('hi').capitalize()
        forced = args.get('forced').capitalize()
        use_original_format = args.get('original_format').capitalize()
        selected_provider = args.get('provider')
        subtitle = args.get('subtitle')

        audio_language_list = get_audio_profile_languages(movieInfo.audio_language)
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = 'None'

        try:
            result = manual_download_subtitle(moviePath, audio_language, hi, forced, subtitle, selected_provider,
                                              sceneName, title, 'movie', use_original_format,
                                              profile_id=get_profile_id(movie_id=radarrId))
        except OSError:
            return 'Unable to save subtitles file', 500
        else:
            if isinstance(result, tuple) and len(result):
                result = result[0]
            if isinstance(result, ProcessSubtitlesResult):
                history_log_movie(2, radarrId, result)
                if not settings.general.dont_notify_manual_actions:
                    send_notifications_movie(radarrId, result.message)
                store_subtitles_movie(result.path, moviePath)
            elif isinstance(result, str):
                return result, 500
            else:
                return '', 204

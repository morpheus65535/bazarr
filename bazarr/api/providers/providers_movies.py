# coding=utf-8

from flask_restx import Resource, Namespace, reqparse, fields

from app.database import TableMovies, get_audio_profile_languages, get_profile_id
from utilities.path_mappings import path_mappings
from app.get_providers import get_providers
from subtitles.manual import manual_search, manual_download_subtitle
from radarr.history import history_log_movie
from app.config import settings
from app.notifier import send_notifications_movie
from subtitles.indexer.movies import store_subtitles_movie

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
    @api_ns_providers_movies.marshal_with(get_response_model, envelope='data', code=200)
    @api_ns_providers_movies.response(401, 'Not Authenticated')
    @api_ns_providers_movies.response(404, 'Movie not found')
    @api_ns_providers_movies.doc(parser=get_request_parser)
    def get(self):
        """Search manually for a movie subtitles"""
        args = self.get_request_parser.parse_args()
        radarrId = args.get('radarrid')
        movieInfo = TableMovies.select(TableMovies.title,
                                       TableMovies.path,
                                       TableMovies.sceneName,
                                       TableMovies.profileId) \
            .where(TableMovies.radarrId == radarrId) \
            .dicts() \
            .get_or_none()

        if not movieInfo:
            return 'Movie not found', 404

        title = movieInfo['title']
        moviePath = path_mappings.path_replace_movie(movieInfo['path'])
        sceneName = movieInfo['sceneName'] or "None"
        profileId = movieInfo['profileId']

        providers_list = get_providers()

        data = manual_search(moviePath, profileId, providers_list, sceneName, title, 'movie')
        if not data:
            data = []
        return data

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
    def post(self):
        """Manually download a movie subtitles"""
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

        title = movieInfo['title']
        moviePath = path_mappings.path_replace_movie(movieInfo['path'])
        sceneName = movieInfo['sceneName'] or "None"

        hi = args.get('hi').capitalize()
        forced = args.get('forced').capitalize()
        use_original_format = args.get('original_format').capitalize()
        selected_provider = args.get('provider')
        subtitle = args.get('subtitle')

        audio_language_list = get_audio_profile_languages(movie_id=radarrId)
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = 'None'

        try:
            result = manual_download_subtitle(moviePath, audio_language, hi, forced, subtitle, selected_provider,
                                              sceneName, title, 'movie', use_original_format,
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
                history_log_movie(2, radarrId, message, path, language_code, provider, score, subs_id, subs_path)
                if not settings.general.getboolean('dont_notify_manual_actions'):
                    send_notifications_movie(radarrId, message)
                store_subtitles_movie(path, moviePath)
        except OSError:
            pass

        return '', 204

# coding=utf-8

from flask_restx import Resource, Namespace, reqparse, fields

from app.database import TableMovies
from subtitles.indexer.movies import list_missing_subtitles_movies, movies_scan_subtitles
from app.event_handler import event_stream
from subtitles.wanted import wanted_search_missing_subtitles_movies
from subtitles.mass_download import movies_download_subtitles
from api.swaggerui import subtitles_model, subtitles_language_model, audio_language_model

from ..utils import authenticate, postprocessMovie, None_Keys


api_ns_movies = Namespace('Movies', description='List movies metadata, update movie languages profile or run actions '
                                                'for specific movies.')


@api_ns_movies.route('movies')
class Movies(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')
    get_request_parser.add_argument('radarrid[]', type=int, action='append', required=False, default=[],
                                    help='Movies IDs to get metadata for')

    get_subtitles_model = api_ns_movies.model('language_model', subtitles_model)
    get_subtitles_language_model = api_ns_movies.model('language_model', subtitles_language_model)
    get_audio_language_model = api_ns_movies.model('language_model', audio_language_model)

    data_model = api_ns_movies.model('data_model', {
        'alternativeTitles': fields.List(fields.String),
        'audio_codec': fields.String(),
        'audio_language': fields.Nested(get_audio_language_model),
        'failedAttempts': fields.String(),
        'fanart': fields.String(),
        'file_size': fields.Integer(),
        'format': fields.String(),
        'imdbId': fields.String(),
        'missing_subtitles': fields.Nested(get_subtitles_language_model),
        'monitored': fields.Boolean(),
        'movie_file_id': fields.Integer(),
        'overview': fields.String(),
        'path': fields.String(),
        'poster': fields.String(),
        'profileId': fields.Integer(),
        'radarrId': fields.Integer(),
        'resolution': fields.String(),
        'rowid': fields.Integer(),
        'sceneName': fields.String(),
        'sortTitle': fields.String(),
        'subtitles': fields.Nested(get_subtitles_model),
        'tags': fields.List(fields.String),
        'title': fields.String(),
        'tmdbId': fields.String(),
        'video_codec': fields.String(),
        'year': fields.String(),
    })

    get_response_model = api_ns_movies.model('MoviesGetResponse', {
        'data': fields.Nested(data_model),
        'total': fields.Integer(),
    })

    @authenticate
    @api_ns_movies.marshal_with(get_response_model, code=200)
    @api_ns_movies.doc(parser=get_request_parser)
    @api_ns_movies.response(200, 'Success')
    @api_ns_movies.response(401, 'Not Authenticated')
    def get(self):
        args = self.get_request_parser.parse_args()
        start = args.get('start')
        length = args.get('length')
        radarrId = args.get('radarrid[]')

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

        return {'data': result, 'total': count}

    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('radarrid', type=int, action='append', required=False, default=[],
                                     help='Radarr movie(s) ID')
    post_request_parser.add_argument('profileid', type=str, action='append', required=False, default=[],
                                     help='Languages profile(s) ID or "none"')

    @authenticate
    @api_ns_movies.doc(parser=post_request_parser)
    @api_ns_movies.response(204, 'Success')
    @api_ns_movies.response(401, 'Not Authenticated')
    @api_ns_movies.response(404, 'Languages profile not found')
    def post(self):
        args = self.post_request_parser.parse_args()
        radarrIdList = args.get('radarrid')
        profileIdList = args.get('profileid')

        for idx in range(len(radarrIdList)):
            radarrId = radarrIdList[idx]
            profileId = profileIdList[idx]

            if profileId in None_Keys:
                profileId = None
            else:
                try:
                    profileId = int(profileId)
                except Exception:
                    return 'Languages profile not found', 404

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

    patch_request_parser = reqparse.RequestParser()
    patch_request_parser.add_argument('radarrid', type=int, required=False, help='Radarr movie ID')
    patch_request_parser.add_argument('action', type=str, required=False, help='Action to perform from ["scan-disk", '
                                                                               '"search-missing", "search-wanted"]')

    @authenticate
    @api_ns_movies.doc(parser=patch_request_parser)
    @api_ns_movies.response(204, 'Success')
    @api_ns_movies.response(400, 'Unknown action')
    @api_ns_movies.response(401, 'Not Authenticated')
    def patch(self):
        args = self.patch_request_parser.parse_args()
        radarrid = args.get('radarrid')
        action = args.get('action')
        if action == "scan-disk":
            movies_scan_subtitles(radarrid)
            return '', 204
        elif action == "search-missing":
            movies_download_subtitles(radarrid)
            return '', 204
        elif action == "search-wanted":
            wanted_search_missing_subtitles_movies()
            return '', 204

        return 'Unknown action', 400

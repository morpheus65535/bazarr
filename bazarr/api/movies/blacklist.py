# coding=utf-8

import pretty

from flask_restx import Resource, Namespace, reqparse, fields

from app.database import TableMovies, TableBlacklistMovie, database, select
from subtitles.tools.delete import delete_subtitles
from radarr.blacklist import blacklist_log_movie, blacklist_delete_all_movie, blacklist_delete_movie
from utilities.path_mappings import path_mappings
from subtitles.mass_download import movies_download_subtitles
from app.event_handler import event_stream
from api.swaggerui import subtitles_language_model

from ..utils import authenticate, postprocess

api_ns_movies_blacklist = Namespace('Movies Blacklist', description='List, add or remove subtitles to or from '
                                                                    'movies blacklist')


@api_ns_movies_blacklist.route('movies/blacklist')
class MoviesBlacklist(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')

    get_language_model = api_ns_movies_blacklist.model('subtitles_language_model', subtitles_language_model)

    get_response_model = api_ns_movies_blacklist.model('MovieBlacklistGetResponse', {
        'title': fields.String(),
        'radarrId': fields.Integer(),
        'provider': fields.String(),
        'subs_id': fields.String(),
        'language': fields.Nested(get_language_model),
        'timestamp': fields.String(),
        'parsed_timestamp': fields.String(),
    })

    @authenticate
    @api_ns_movies_blacklist.marshal_with(get_response_model, envelope='data', code=200)
    @api_ns_movies_blacklist.response(401, 'Not Authenticated')
    @api_ns_movies_blacklist.doc(parser=get_request_parser)
    def get(self):
        """List blacklisted movies subtitles"""
        args = self.get_request_parser.parse_args()
        start = args.get('start')
        length = args.get('length')

        data = database.execute(
            select(TableMovies.title,
                   TableMovies.radarrId,
                   TableBlacklistMovie.provider,
                   TableBlacklistMovie.subs_id,
                   TableBlacklistMovie.language,
                   TableBlacklistMovie.timestamp)
            .join(TableMovies, TableBlacklistMovie.radarr_id == TableMovies.radarrId)
            .order_by(TableBlacklistMovie.timestamp.desc()))
        if length > 0:
            data = data.limit(length).offset(start)

        return [postprocess({
            'title': x.title,
            'radarrId': x.radarrId,
            'provider': x.provider,
            'subs_id': x.subs_id,
            'language': x.language,
            'timestamp': pretty.date(x.timestamp),
            'parsed_timestamp': x.timestamp.strftime('%x %X'),
        }) for x in data.all()]

    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('radarrid', type=int, required=True, help='Radarr ID')
    post_request_parser.add_argument('provider', type=str, required=True, help='Provider name')
    post_request_parser.add_argument('subs_id', type=str, required=True, help='Subtitles ID')
    post_request_parser.add_argument('language', type=str, required=True, help='Subtitles language')
    post_request_parser.add_argument('subtitles_path', type=str, required=True, help='Subtitles file path')

    @authenticate
    @api_ns_movies_blacklist.doc(parser=post_request_parser)
    @api_ns_movies_blacklist.response(200, 'Success')
    @api_ns_movies_blacklist.response(401, 'Not Authenticated')
    @api_ns_movies_blacklist.response(404, 'Movie not found')
    def post(self):
        """Add a movies subtitles to blacklist"""
        args = self.post_request_parser.parse_args()
        radarr_id = args.get('radarrid')
        provider = args.get('provider')
        subs_id = args.get('subs_id')
        language = args.get('language')
        # TODO
        forced = False
        hi = False

        data = database.execute(
            select(TableMovies.path)
            .where(TableMovies.radarrId == radarr_id))\
            .first()

        if not data:
            return 'Movie not found', 404

        media_path = data.path
        subtitles_path = args.get('subtitles_path')

        blacklist_log_movie(radarr_id=radarr_id,
                            provider=provider,
                            subs_id=subs_id,
                            language=language)
        delete_subtitles(media_type='movie',
                         language=language,
                         forced=forced,
                         hi=hi,
                         media_path=path_mappings.path_replace_movie(media_path),
                         subtitles_path=subtitles_path,
                         radarr_id=radarr_id)
        movies_download_subtitles(radarr_id)
        event_stream(type='movie-history')
        return '', 200

    delete_request_parser = reqparse.RequestParser()
    delete_request_parser.add_argument('all', type=str, required=False, help='Empty movies subtitles blacklist')
    delete_request_parser.add_argument('provider', type=str, required=True, help='Provider name')
    delete_request_parser.add_argument('subs_id', type=str, required=True, help='Subtitles ID')

    @authenticate
    @api_ns_movies_blacklist.doc(parser=delete_request_parser)
    @api_ns_movies_blacklist.response(204, 'Success')
    @api_ns_movies_blacklist.response(401, 'Not Authenticated')
    def delete(self):
        """Delete a movies subtitles from blacklist"""
        args = self.delete_request_parser.parse_args()
        if args.get("all") == "true":
            blacklist_delete_all_movie()
        else:
            provider = args.get('provider')
            subs_id = args.get('subs_id')
            blacklist_delete_movie(provider=provider, subs_id=subs_id)
        return '', 200

# coding=utf-8

from flask_restx import Resource, Namespace, reqparse, fields, marshal
from sqlalchemy import or_

from app.database import TableMovies, database, update, select, func
from radarr.sync.movies import update_one_movie
from subtitles.indexer.movies import list_missing_subtitles_movies, movies_scan_subtitles
from app.event_handler import event_stream
from subtitles.wanted import wanted_search_missing_subtitles_movies
from subtitles.mass_download import movies_download_subtitles
from api.swaggerui import subtitles_model, subtitles_language_model, audio_language_model

from api.utils import authenticate, None_Keys, postprocess, add_list_query_args, profile_filter_clause, \
    tags_filter_clause, audio_language_filter_clause, apply_sort

api_ns_movies = Namespace('Movies', description='List movies metadata, update movie languages profile or run actions '
                                                'for specific movies.')


@api_ns_movies.route('movies')
class Movies(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')
    get_request_parser.add_argument('radarrid[]', type=int, action='append', required=False, default=[],
                                     help='Movies IDs to get metadata for')
    add_list_query_args(get_request_parser)

    get_subtitles_model = api_ns_movies.model('subtitles_model', subtitles_model)
    get_subtitles_language_model = api_ns_movies.model('subtitles_language_model', subtitles_language_model)
    get_audio_language_model = api_ns_movies.model('audio_language_model', audio_language_model)

    data_model = api_ns_movies.model('movies_data_model', {
        'alternativeTitles': fields.List(fields.String),
        'audio_language': fields.Nested(get_audio_language_model),
        'created_at_timestamp': fields.String(),
        'fanart': fields.String(),
        'imdbId': fields.String(),
        'missing_subtitles': fields.Nested(get_subtitles_language_model),
        'monitored': fields.Boolean(),
        'overview': fields.String(),
        'path': fields.String(),
        'poster': fields.String(),
        'profileId': fields.Integer(),
        'radarrId': fields.Integer(),
        'sceneName': fields.String(),
        'subtitles': fields.Nested(get_subtitles_model),
        'tags': fields.List(fields.String),
        'title': fields.String(),
        'year': fields.String(),
    })

    get_response_model = api_ns_movies.model('MoviesGetResponse', {
        'data': fields.Nested(data_model),
        'total': fields.Integer(),
    })

    @authenticate
    @api_ns_movies.doc(parser=get_request_parser)
    @api_ns_movies.response(200, 'Success')
    @api_ns_movies.response(401, 'Not Authenticated')
    def get(self):
        """List movies metadata for specific movies"""
        args = self.get_request_parser.parse_args()
        start = args.get('start')
        length = args.get('length')
        radarrId = args.get('radarrid[]')
        sort_by = args.get('sort_by')
        sort_order = args.get('sort_order')
        monitored = args.get('monitored')
        profile_id = args.get('profileid')
        missing = args.get('missing')
        audio_language = args.get('audio_language')
        tags = args.get('tags[]')

        stmt = select(TableMovies.alternativeTitles,
                      TableMovies.audio_language,
                      TableMovies.created_at_timestamp,
                      TableMovies.fanart,
                      TableMovies.imdbId,
                      TableMovies.missing_subtitles,
                      TableMovies.monitored,
                      TableMovies.overview,
                      TableMovies.path,
                      TableMovies.poster,
                      TableMovies.profileId,
                      TableMovies.radarrId,
                      TableMovies.sceneName,
                      TableMovies.tags,
                      TableMovies.title,
                      TableMovies.year,
                      )

        where_clauses = []

        if len(radarrId) != 0:
            where_clauses.append(TableMovies.radarrId.in_(radarrId))
        if monitored is not None:
            where_clauses.append(TableMovies.monitored.is_(monitored == 'true'))
        if profile_id is not None:
            where_clauses.append(profile_filter_clause(TableMovies.profileId, profile_id))
        if missing is not None:
            if missing == 'true':
                where_clauses.append(TableMovies.missing_subtitles.is_not(None))
                where_clauses.append(TableMovies.missing_subtitles != '[]')
            else:
                where_clauses.append(or_(TableMovies.missing_subtitles.is_(None),
                                         TableMovies.missing_subtitles == '[]'))
        if audio_language is not None:
            where_clauses.append(audio_language_filter_clause(TableMovies.audio_language, audio_language))
        if tags:
            where_clauses.append(tags_filter_clause(TableMovies.tags, tags))

        if where_clauses:
            stmt = stmt.where(*where_clauses)

        stmt = apply_sort(stmt, {
            'title': TableMovies.sortTitle,
            'year': TableMovies.year,
            'profileId': TableMovies.profileId,
            'audio_language': TableMovies.audio_language,
            'audioLanguage': TableMovies.audio_language,
            'createdAtTimestamp': TableMovies.created_at_timestamp,
        }, TableMovies.sortTitle, sort_by, sort_order)

        if length > 0:
            stmt = stmt.limit(length).offset(start)

        results = [postprocess({
            'alternativeTitles': x.alternativeTitles,
            'audio_language': x.audio_language,
            'created_at_timestamp': x.created_at_timestamp,
            'fanart': x.fanart,
            'imdbId': x.imdbId,
            'missing_subtitles': x.missing_subtitles,
            'monitored': x.monitored,
            'overview': x.overview,
            'path': x.path,
            'poster': x.poster,
            'profileId': x.profileId,
            'radarrId': x.radarrId,
            'sceneName': x.sceneName,
            'tags': x.tags,
            'title': x.title,
            'year': x.year,
        }) for x in database.execute(stmt).all()]

        count_stmt = select(func.count()).select_from(TableMovies)
        if where_clauses:
            count_stmt = count_stmt.where(*where_clauses)

        count = database.execute(count_stmt).scalar()

        return marshal({'data': results, 'total': count}, self.get_response_model)

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
        """Update specific movies languages profile"""
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

            database.execute(
                update(TableMovies)
                .values(profileId=profileId)
                .where(TableMovies.radarrId == radarrId))

            list_missing_subtitles_movies(no=radarrId)

            event_stream(type='movie', payload=radarrId)
            event_stream(type='movie-wanted', payload=radarrId)
        event_stream(type='badges')

        return '', 204

    patch_request_parser = reqparse.RequestParser()
    patch_request_parser.add_argument('radarrid', type=int, required=False, help='Radarr movie ID')
    patch_request_parser.add_argument('action', type=str, required=False, help='Action to perform from ["scan-disk", '
                                                                               '"search-missing", "search-wanted", "sync"]')

    @authenticate
    @api_ns_movies.doc(parser=patch_request_parser)
    @api_ns_movies.response(204, 'Success')
    @api_ns_movies.response(400, 'Unknown action')
    @api_ns_movies.response(401, 'Not Authenticated')
    @api_ns_movies.response(500, 'Movie file not found. Path mapping issue?')
    def patch(self):
        """Run actions on specific movies"""
        args = self.patch_request_parser.parse_args()
        radarrid = args.get('radarrid')
        action = args.get('action')
        if action == "scan-disk":
            movies_scan_subtitles(radarrid)
            return '', 204
        elif action == "search-missing":
            try:
                movies_download_subtitles(radarrid)
            except OSError:
                return 'Movie file not found. Path mapping issue?', 500
            else:
                return '', 204
        elif action == "search-wanted":
            wanted_search_missing_subtitles_movies()
            return '', 204
        elif action == "sync":
            update_one_movie(radarrid, 'updated', True)
            return '', 204

        return 'Unknown action', 400

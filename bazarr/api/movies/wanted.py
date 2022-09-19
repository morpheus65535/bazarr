# coding=utf-8

import operator

from flask_restx import Resource, Namespace, reqparse, fields
from functools import reduce

from app.database import get_exclusion_clause, TableMovies
from api.swaggerui import subtitles_language_model

from ..utils import authenticate, postprocessMovie


api_ns_movies_wanted = Namespace('Movies Wanted', description='List movies wanted subtitles')


@api_ns_movies_wanted.route('movies/wanted')
# GET: Get Wanted Movies
class MoviesWanted(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')
    get_request_parser.add_argument('radarrid[]', type=int, action='append', required=False, default=[],
                                    help='Movies ID to list')

    get_subtitles_language_model = api_ns_movies_wanted.model('language_model', subtitles_language_model)

    data_model = api_ns_movies_wanted.model('data_model', {
        'title': fields.String(),
        'monitored': fields.Boolean(),
        'missing_subtitles': fields.Nested(get_subtitles_language_model),
        'radarrId': fields.Integer(),
        'sceneName': fields.String(),
        'tags': fields.List(fields.String),
        'failedAttempts': fields.String(),
    })

    get_response_model = api_ns_movies_wanted.model('MovieWantedGetResponse', {
        'data': fields.Nested(data_model),
        'total': fields.Integer(),
    })

    @authenticate
    @api_ns_movies_wanted.marshal_with(get_response_model, code=200)
    @api_ns_movies_wanted.response(401, 'Not Authenticated')
    @api_ns_movies_wanted.doc(parser=get_request_parser)
    def get(self):
        args = self.get_request_parser.parse_args()
        radarrid = args.get("radarrid[]")

        wanted_conditions = [(TableMovies.missing_subtitles != '[]')]
        if len(radarrid) > 0:
            wanted_conditions.append((TableMovies.radarrId.in_(radarrid)))
        wanted_conditions += get_exclusion_clause('movie')
        wanted_condition = reduce(operator.and_, wanted_conditions)

        if len(radarrid) > 0:
            result = TableMovies.select(TableMovies.title,
                                        TableMovies.missing_subtitles,
                                        TableMovies.radarrId,
                                        TableMovies.sceneName,
                                        TableMovies.failedAttempts,
                                        TableMovies.tags,
                                        TableMovies.monitored)\
                .where(wanted_condition)\
                .dicts()
        else:
            start = args.get('start')
            length = args.get('length')
            result = TableMovies.select(TableMovies.title,
                                        TableMovies.missing_subtitles,
                                        TableMovies.radarrId,
                                        TableMovies.sceneName,
                                        TableMovies.failedAttempts,
                                        TableMovies.tags,
                                        TableMovies.monitored)\
                .where(wanted_condition)\
                .order_by(TableMovies.rowid.desc())\
                .limit(length)\
                .offset(start)\
                .dicts()
        result = list(result)

        for item in result:
            postprocessMovie(item)

        count_conditions = [(TableMovies.missing_subtitles != '[]')]
        count_conditions += get_exclusion_clause('movie')
        count = TableMovies.select(TableMovies.monitored,
                                   TableMovies.tags)\
            .where(reduce(operator.and_, count_conditions))\
            .count()

        return {'data': result, 'total': count}

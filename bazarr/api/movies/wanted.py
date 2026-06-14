# coding=utf-8

import operator

from flask_restx import Resource, Namespace, reqparse, fields, marshal
from functools import reduce

from app.database import get_exclusion_clause, TableMovies, TableMissingSubtitles, database, select, func, get_subtitles_map
from api.swaggerui import subtitles_language_model
from subtitles.wanted_state import get_missing_languages_map

from api.utils import authenticate, postprocess


api_ns_movies_wanted = Namespace('Movies Wanted', description='List movies wanted subtitles')


@api_ns_movies_wanted.route('movies/wanted')
class MoviesWanted(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')
    get_request_parser.add_argument('radarrid[]', type=int, action='append', required=False, default=[],
                                    help='Movies ID to list')

    get_subtitles_language_model = api_ns_movies_wanted.model('subtitles_language_model', subtitles_language_model)

    data_model = api_ns_movies_wanted.model('wanted_movies_data_model', {
        'title': fields.String(),
        'missing_subtitles': fields.Nested(get_subtitles_language_model),
        'radarrId': fields.Integer(),
        'sceneName': fields.String(),
        'tags': fields.List(fields.String),
    })

    get_response_model = api_ns_movies_wanted.model('MovieWantedGetResponse', {
        'data': fields.Nested(data_model),
        'total': fields.Integer(),
    })

    @authenticate
    @api_ns_movies_wanted.response(401, 'Not Authenticated')
    @api_ns_movies_wanted.doc(parser=get_request_parser)
    def get(self):
        """List movies wanted subtitles"""
        args = self.get_request_parser.parse_args()
        radarrid = args.get("radarrid[]")

        wanted_conditions = [select(TableMissingSubtitles.id)
                             .where(TableMissingSubtitles.media_type == 'movie')
                             .where(TableMissingSubtitles.media_id == TableMovies.radarrId)
                             .exists()]
        if len(radarrid) > 0:
            wanted_conditions.append((TableMovies.radarrId.in_(radarrid)))
            start = 0
            length = 0
        else:
            start = args.get('start')
            length = args.get('length')

        wanted_conditions += get_exclusion_clause('movie')
        wanted_condition = reduce(operator.and_, wanted_conditions)

        stmt = select(TableMovies.title,
                      TableMovies.radarrId,
                      TableMovies.sceneName,
                      TableMovies.tags) \
            .where(wanted_condition)
        if length > 0:
            stmt = stmt.order_by(TableMovies.radarrId.desc()).limit(length).offset(start)

        movies = database.execute(stmt).all()
        missing_languages = get_missing_languages_map('movie', [x.radarrId for x in movies])
        subtitles_map = get_subtitles_map('movie', [x.radarrId for x in movies])

        results = [postprocess({
            'title': x.title,
            'missing_subtitles': missing_languages[x.radarrId],
            'radarrId': x.radarrId,
            'sceneName': x.sceneName,
            'tags': x.tags,
        }, subtitles=subtitles_map.get(x.radarrId, [])) for x in movies]

        count = database.execute(
            select(func.count())
            .select_from(TableMovies)
            .where(wanted_condition)) \
            .scalar()

        return marshal({'data': results, 'total': count}, self.get_response_model)

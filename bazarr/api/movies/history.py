# coding=utf-8

import operator
import pretty
import ast

from flask_restx import Resource, Namespace, reqparse, fields, marshal
from functools import reduce

from app.database import TableMovies, TableHistoryMovie, TableBlacklistMovie, database, select, func
from subtitles.upgrade import get_upgradable_movies_subtitles, _language_still_desired
from api.swaggerui import subtitles_language_model

from api.utils import authenticate, postprocess

api_ns_movies_history = Namespace('Movies History', description='List movies history events')


@api_ns_movies_history.route('movies/history')
class MoviesHistory(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')
    get_request_parser.add_argument('radarrid', type=int, required=False, help='Movie ID')

    get_language_model = api_ns_movies_history.model('subtitles_language_model', subtitles_language_model)

    data_model = api_ns_movies_history.model('history_movies_data_model', {
        'action': fields.Integer(),
        'title': fields.String(),
        'timestamp': fields.String(),
        'description': fields.String(),
        'radarrId': fields.Integer(),
        'monitored': fields.Boolean(),
        'path': fields.String(),
        'language': fields.Nested(get_language_model),
        'tags': fields.List(fields.String),
        'score': fields.String(),
        'subs_id': fields.String(),
        'provider': fields.String(),
        'subtitles_path': fields.String(),
        'upgradable': fields.Boolean(),
        'parsed_timestamp': fields.String(),
        'blacklisted': fields.Boolean(),
        'matches': fields.List(fields.String),
        'dont_matches': fields.List(fields.String),
    })

    get_response_model = api_ns_movies_history.model('MovieHistoryGetResponse', {
        'data': fields.Nested(data_model),
        'total': fields.Integer(),
    })

    @authenticate
    @api_ns_movies_history.response(401, 'Not Authenticated')
    @api_ns_movies_history.doc(parser=get_request_parser)
    def get(self):
        """List movies history events"""
        args = self.get_request_parser.parse_args()
        start = args.get('start')
        length = args.get('length')
        radarrid = args.get('radarrid')

        blacklisted_subtitles = select(TableBlacklistMovie.provider,
                                       TableBlacklistMovie.subs_id) \
            .subquery()

        query_conditions = [(TableMovies.title.is_not(None))]
        if radarrid:
            query_conditions.append((TableMovies.radarrId == radarrid))

        stmt = select(TableHistoryMovie.id,
                      TableHistoryMovie.action,
                      TableMovies.title,
                      TableHistoryMovie.timestamp,
                      TableHistoryMovie.description,
                      TableHistoryMovie.radarrId,
                      TableMovies.monitored,
                      TableMovies.path,
                      TableHistoryMovie.language,
                      TableMovies.tags,
                      TableHistoryMovie.score,
                      TableHistoryMovie.subs_id,
                      TableHistoryMovie.provider,
                      TableHistoryMovie.subtitles_path,
                      TableHistoryMovie.video_path,
                      TableHistoryMovie.matched,
                      TableHistoryMovie.not_matched,
                      TableMovies.profileId,
                      TableMovies.subtitles.label('external_subtitles'),
                      blacklisted_subtitles.c.subs_id.label('blacklisted')) \
            .select_from(TableHistoryMovie) \
            .join(TableMovies) \
            .join(blacklisted_subtitles, onclause=TableHistoryMovie.subs_id == blacklisted_subtitles.c.subs_id,
                  isouter=True) \
            .where(reduce(operator.and_, query_conditions)) \
            .order_by(TableHistoryMovie.timestamp.desc())
        if length > 0:
            stmt = stmt.limit(length).offset(start)
        movie_history = [{
            'id': x.id,
            'action': x.action,
            'title': x.title,
            'timestamp': x.timestamp,
            'description': x.description,
            'radarrId': x.radarrId,
            'monitored': x.monitored,
            'path': x.path,
            'language': x.language,
            'profileId': x.profileId,
            'tags': x.tags,
            'score': x.score,
            'subs_id': x.subs_id,
            'provider': x.provider,
            'subtitles_path': x.subtitles_path,
            'video_path': x.video_path,
            'matches': x.matched,
            'dont_matches': x.not_matched,
            'external_subtitles': [y[1] for y in ast.literal_eval(x.external_subtitles) if y[1]],
            'blacklisted': bool(x.blacklisted),
        } for x in database.execute(stmt).all()]

        upgradable_movies_not_perfect = get_upgradable_movies_subtitles(history_id_list=[x['id'] for x in
                                                                                         movie_history])

        for item in movie_history:
            # is this language still desired or should we simply skip this subtitles from upgrade logic?
            still_desired = _language_still_desired(item['language'], item['profileId'])

            item.update(postprocess(item))

            # Mark upgradable and get original_id
            item.update({'original_id': upgradable_movies_not_perfect.get(item['id'])})
            item.update({'upgradable': item['id'] in upgradable_movies_not_perfect.keys()})

            # Mark not upgradable if video/subtitles file doesn't exist anymore or if language isn't desired anymore
            if item['upgradable']:
                if (item['subtitles_path'] not in item['external_subtitles'] or item['video_path'] != item['path'] or
                        not still_desired):
                    item.update({"upgradable": False})

            del item['path']
            del item['video_path']
            del item['external_subtitles']
            del item['profileId']

            if item['score']:
                item['score'] = f"{round((int(item['score']) * 100 / 120), 2)}%"

            # Make timestamp pretty
            if item['timestamp']:
                item["parsed_timestamp"] = item['timestamp'].strftime('%x %X')
                item['timestamp'] = pretty.date(item["timestamp"])

            # Parse matches and dont_matches
            if item['matches']:
                item.update({'matches': ast.literal_eval(item['matches'])})
            else:
                item.update({'matches': []})

            if item['dont_matches']:
                item.update({'dont_matches': ast.literal_eval(item['dont_matches'])})
            else:
                item.update({'dont_matches': []})

        count = database.execute(
            select(func.count())
            .select_from(TableHistoryMovie)
            .join(TableMovies)
            .where(TableMovies.title.is_not(None))) \
            .scalar()

        return marshal({'data': movie_history, 'total': count}, self.get_response_model)

# coding=utf-8

import datetime
import os
import operator
import pretty

from flask_restx import Resource, Namespace, reqparse, fields
from functools import reduce
from peewee import fn
from datetime import timedelta

from app.database import get_exclusion_clause, TableMovies, TableHistoryMovie, TableBlacklistMovie
from app.config import settings
from utilities.path_mappings import path_mappings
from api.swaggerui import subtitles_language_model

from ..utils import authenticate, postprocessMovie

api_ns_movies_history = Namespace('Movies History', description='List movies history events')


@api_ns_movies_history.route('movies/history')
class MoviesHistory(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')
    get_request_parser.add_argument('radarrid', type=int, required=False, help='Movie ID')

    get_language_model = api_ns_movies_history.model('subtitles_language_model', subtitles_language_model)

    data_model = api_ns_movies_history.model('history_movies_data_model', {
        'id': fields.Integer(),
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
        'raw_timestamp': fields.Integer(),
        'parsed_timestamp': fields.String(),
        'blacklisted': fields.Boolean(),
    })

    get_response_model = api_ns_movies_history.model('MovieHistoryGetResponse', {
        'data': fields.Nested(data_model),
        'total': fields.Integer(),
    })

    @authenticate
    @api_ns_movies_history.marshal_with(get_response_model, code=200)
    @api_ns_movies_history.response(401, 'Not Authenticated')
    @api_ns_movies_history.doc(parser=get_request_parser)
    def get(self):
        """List movies history events"""
        args = self.get_request_parser.parse_args()
        start = args.get('start')
        length = args.get('length')
        radarrid = args.get('radarrid')

        upgradable_movies = []
        upgradable_movies_not_perfect = []
        if settings.general.getboolean('upgrade_subs'):
            days_to_upgrade_subs = settings.general.days_to_upgrade_subs
            minimum_timestamp = (datetime.datetime.now() - timedelta(days=int(days_to_upgrade_subs)))

            if settings.general.getboolean('upgrade_manual'):
                query_actions = [1, 2, 3, 6]
            else:
                query_actions = [1, 3]

            upgradable_movies_conditions = [(TableHistoryMovie.action.in_(query_actions)),
                                            (TableHistoryMovie.timestamp > minimum_timestamp),
                                            (TableHistoryMovie.score.is_null(False))]
            upgradable_movies_conditions += get_exclusion_clause('movie')
            upgradable_movies = TableHistoryMovie.select(TableHistoryMovie.video_path,
                                                         fn.MAX(TableHistoryMovie.timestamp).alias('timestamp'),
                                                         TableHistoryMovie.score,
                                                         TableMovies.tags,
                                                         TableMovies.monitored) \
                .join(TableMovies, on=(TableHistoryMovie.radarrId == TableMovies.radarrId)) \
                .where(reduce(operator.and_, upgradable_movies_conditions)) \
                .group_by(TableHistoryMovie.video_path,
                          TableHistoryMovie.score,
                          TableMovies.tags,
                          TableMovies.monitored
                          ) \
                .dicts()
            upgradable_movies = list(upgradable_movies)

            for upgradable_movie in upgradable_movies:
                if upgradable_movie['timestamp'] > minimum_timestamp:
                    try:
                        int(upgradable_movie['score'])
                    except ValueError:
                        pass
                    else:
                        if int(upgradable_movie['score']) < 120:
                            upgradable_movies_not_perfect.append(upgradable_movie)

        query_conditions = [(TableMovies.title.is_null(False))]
        if radarrid:
            query_conditions.append((TableMovies.radarrId == radarrid))
        query_condition = reduce(operator.and_, query_conditions)

        movie_history = TableHistoryMovie.select(TableHistoryMovie.id,
                                                 TableHistoryMovie.action,
                                                 TableMovies.title,
                                                 TableHistoryMovie.timestamp,
                                                 TableHistoryMovie.description,
                                                 TableHistoryMovie.radarrId,
                                                 TableMovies.monitored,
                                                 TableHistoryMovie.video_path.alias('path'),
                                                 TableHistoryMovie.language,
                                                 TableMovies.tags,
                                                 TableHistoryMovie.score,
                                                 TableHistoryMovie.subs_id,
                                                 TableHistoryMovie.provider,
                                                 TableHistoryMovie.subtitles_path,
                                                 TableHistoryMovie.video_path) \
            .join(TableMovies, on=(TableHistoryMovie.radarrId == TableMovies.radarrId)) \
            .where(query_condition) \
            .order_by(TableHistoryMovie.timestamp.desc())
        if length > 0:
            movie_history = movie_history.limit(length).offset(start)
        movie_history = list(movie_history.dicts())

        blacklist_db = TableBlacklistMovie.select(TableBlacklistMovie.provider, TableBlacklistMovie.subs_id).dicts()
        blacklist_db = list(blacklist_db)

        for item in movie_history:
            # Mark movies as upgradable or not
            item.update({"upgradable": False})
            if {"video_path": str(item['path']), "timestamp": item['timestamp'], "score": str(item['score']),
                "tags": str(item['tags']),
                "monitored": str(item['monitored'])} in upgradable_movies_not_perfect:  # noqa: E129
                if os.path.exists(path_mappings.path_replace_movie(item['subtitles_path'])) and \
                        os.path.exists(path_mappings.path_replace_movie(item['video_path'])):
                    item.update({"upgradable": True})

            del item['path']

            postprocessMovie(item)

            if item['score']:
                item['score'] = str(round((int(item['score']) * 100 / 120), 2)) + "%"

            # Make timestamp pretty
            if item['timestamp']:
                item["raw_timestamp"] = item['timestamp'].timestamp()
                item["parsed_timestamp"] = item['timestamp'].strftime('%x %X')
                item['timestamp'] = pretty.date(item["timestamp"])

            # Check if subtitles is blacklisted
            item.update({"blacklisted": False})
            if item['action'] not in [0, 4, 5]:
                for blacklisted_item in blacklist_db:
                    if blacklisted_item['provider'] == item['provider'] and blacklisted_item['subs_id'] == item[
                        'subs_id']:  # noqa: E125
                        item.update({"blacklisted": True})
                        break

        count = TableHistoryMovie.select() \
            .join(TableMovies, on=(TableHistoryMovie.radarrId == TableMovies.radarrId)) \
            .where(TableMovies.title.is_null(False)) \
            .count()

        return {'data': movie_history, 'total': count}

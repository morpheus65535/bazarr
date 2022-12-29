# coding=utf-8

import time
import datetime
import operator
import itertools

from dateutil import rrule
from flask_restx import Resource, Namespace, reqparse, fields
from functools import reduce

from app.database import TableHistory, TableHistoryMovie

from ..utils import authenticate

api_ns_history_stats = Namespace('History Statistics', description='Get history statistics')


@api_ns_history_stats.route('history/stats')
class HistoryStats(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('timeFrame', type=str, default='month',
                                    help='Timeframe to get stats for. Must be in ["week", "month", "trimester", '
                                         '"year"]')
    get_request_parser.add_argument('action', type=str, default='All', help='Action type to filter for.')
    get_request_parser.add_argument('provider', type=str, default='All', help='Provider name to filter for.')
    get_request_parser.add_argument('language', type=str, default='All', help='Language name to filter for')

    series_data_model = api_ns_history_stats.model('history_series_stats_data_model', {
        'date': fields.String(),
        'count': fields.Integer(),
    })

    movies_data_model = api_ns_history_stats.model('history_movies_stats_data_model', {
        'date': fields.String(),
        'count': fields.Integer(),
    })

    get_response_model = api_ns_history_stats.model('HistoryStatsGetResponse', {
        'series': fields.Nested(series_data_model),
        'movies': fields.Nested(movies_data_model),
    })

    @authenticate
    @api_ns_history_stats.marshal_with(get_response_model, code=200)
    @api_ns_history_stats.response(401, 'Not Authenticated')
    @api_ns_history_stats.doc(parser=get_request_parser)
    def get(self):
        """Get history statistics"""
        args = self.get_request_parser.parse_args()
        timeframe = args.get('timeFrame')
        action = args.get('action')
        provider = args.get('provider')
        language = args.get('language')

        # timeframe must be in ['week', 'month', 'trimester', 'year']
        if timeframe == 'year':
            delay = 364 * 24 * 60 * 60
        elif timeframe == 'trimester':
            delay = 90 * 24 * 60 * 60
        elif timeframe == 'month':
            delay = 30 * 24 * 60 * 60
        elif timeframe == 'week':
            delay = 6 * 24 * 60 * 60

        now = datetime.datetime.now()
        past = now - datetime.timedelta(seconds=delay)

        history_where_clauses = [(TableHistory.timestamp.between(past, now))]
        history_where_clauses_movie = [(TableHistoryMovie.timestamp.between(past, now))]

        if action != 'All':
            history_where_clauses.append((TableHistory.action == action))
            history_where_clauses_movie.append((TableHistoryMovie.action == action))
        else:
            history_where_clauses.append((TableHistory.action.in_([1, 2, 3])))
            history_where_clauses_movie.append((TableHistoryMovie.action.in_([1, 2, 3])))

        if provider != 'All':
            history_where_clauses.append((TableHistory.provider == provider))
            history_where_clauses_movie.append((TableHistoryMovie.provider == provider))

        if language != 'All':
            history_where_clauses.append((TableHistory.language == language))
            history_where_clauses_movie.append((TableHistoryMovie.language == language))

        history_where_clause = reduce(operator.and_, history_where_clauses)
        history_where_clause_movie = reduce(operator.and_, history_where_clauses_movie)

        data_series = TableHistory.select(TableHistory.timestamp, TableHistory.id)\
            .where(history_where_clause) \
            .dicts()
        data_series = [{'date': date[0], 'count': sum(1 for item in date[1])} for date in
                       itertools.groupby(list(data_series),
                                         key=lambda x: x['timestamp'].strftime(
                                             '%Y-%m-%d'))]

        data_movies = TableHistoryMovie.select(TableHistoryMovie.timestamp, TableHistoryMovie.id) \
            .where(history_where_clause_movie) \
            .dicts()
        data_movies = [{'date': date[0], 'count': sum(1 for item in date[1])} for date in
                       itertools.groupby(list(data_movies),
                                         key=lambda x: x['timestamp'].strftime(
                                             '%Y-%m-%d'))]

        for dt in rrule.rrule(rrule.DAILY,
                              dtstart=datetime.datetime.now() - datetime.timedelta(seconds=delay),
                              until=datetime.datetime.now()):
            if not any(d['date'] == dt.strftime('%Y-%m-%d') for d in data_series):
                data_series.append({'date': dt.strftime('%Y-%m-%d'), 'count': 0})
            if not any(d['date'] == dt.strftime('%Y-%m-%d') for d in data_movies):
                data_movies.append({'date': dt.strftime('%Y-%m-%d'), 'count': 0})

        sorted_data_series = sorted(data_series, key=lambda i: i['date'])
        sorted_data_movies = sorted(data_movies, key=lambda i: i['date'])

        return {'series': sorted_data_series, 'movies': sorted_data_movies}

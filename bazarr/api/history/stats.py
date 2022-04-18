# coding=utf-8

import time
import datetime
import operator

from dateutil import rrule
from flask import request, jsonify
from flask_restful import Resource
from functools import reduce
from peewee import fn

from database import TableHistory, TableHistoryMovie

from ..utils import authenticate


class HistoryStats(Resource):
    @authenticate
    def get(self):
        timeframe = request.args.get('timeframe') or 'month'
        action = request.args.get('action') or 'All'
        provider = request.args.get('provider') or 'All'
        language = request.args.get('language') or 'All'

        # timeframe must be in ['week', 'month', 'trimester', 'year']
        if timeframe == 'year':
            delay = 364 * 24 * 60 * 60
        elif timeframe == 'trimester':
            delay = 90 * 24 * 60 * 60
        elif timeframe == 'month':
            delay = 30 * 24 * 60 * 60
        elif timeframe == 'week':
            delay = 6 * 24 * 60 * 60

        now = time.time()
        past = now - delay

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

        data_series = TableHistory.select(fn.strftime('%Y-%m-%d', TableHistory.timestamp, 'unixepoch').alias('date'),
                                          fn.COUNT(TableHistory.id).alias('count'))\
            .where(history_where_clause) \
            .group_by(fn.strftime('%Y-%m-%d', TableHistory.timestamp, 'unixepoch'))\
            .dicts()
        data_series = list(data_series)

        data_movies = TableHistoryMovie.select(fn.strftime('%Y-%m-%d', TableHistoryMovie.timestamp, 'unixepoch').alias('date'),
                                               fn.COUNT(TableHistoryMovie.id).alias('count')) \
            .where(history_where_clause_movie) \
            .group_by(fn.strftime('%Y-%m-%d', TableHistoryMovie.timestamp, 'unixepoch')) \
            .dicts()
        data_movies = list(data_movies)

        for dt in rrule.rrule(rrule.DAILY,
                              dtstart=datetime.datetime.now() - datetime.timedelta(seconds=delay),
                              until=datetime.datetime.now()):
            if not any(d['date'] == dt.strftime('%Y-%m-%d') for d in data_series):
                data_series.append({'date': dt.strftime('%Y-%m-%d'), 'count': 0})
            if not any(d['date'] == dt.strftime('%Y-%m-%d') for d in data_movies):
                data_movies.append({'date': dt.strftime('%Y-%m-%d'), 'count': 0})

        sorted_data_series = sorted(data_series, key=lambda i: i['date'])
        sorted_data_movies = sorted(data_movies, key=lambda i: i['date'])

        return jsonify(series=sorted_data_series, movies=sorted_data_movies)

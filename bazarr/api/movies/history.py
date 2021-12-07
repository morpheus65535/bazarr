# coding=utf-8

import datetime
import os
import operator
import pretty

from flask import request, jsonify
from flask_restful import Resource
from functools import reduce
from peewee import fn

from database import get_exclusion_clause, TableMovies, TableHistoryMovie, TableBlacklistMovie
from ..utils import authenticate, postprocessMovie
from config import settings


class MoviesHistory(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        movieid = request.args.get('movieid')

        upgradable_movies = []
        upgradable_movies_not_perfect = []
        if settings.general.getboolean('upgrade_subs'):
            days_to_upgrade_subs = settings.general.days_to_upgrade_subs
            minimum_timestamp = ((datetime.datetime.now() - datetime.timedelta(days=int(days_to_upgrade_subs))) -
                                 datetime.datetime(1970, 1, 1)).total_seconds()

            if settings.general.getboolean('upgrade_manual'):
                query_actions = [1, 2, 3, 6]
            else:
                query_actions = [1, 3]

            upgradable_movies_conditions = [(TableHistoryMovie.action.in_(query_actions)),
                                            (TableHistoryMovie.timestamp > minimum_timestamp),
                                            (TableHistoryMovie.score is not None)]
            upgradable_movies_conditions += get_exclusion_clause('movie')
            upgradable_movies = TableHistoryMovie.select(TableHistoryMovie.video_path,
                                                         fn.MAX(TableHistoryMovie.timestamp).alias('timestamp'),
                                                         TableHistoryMovie.score,
                                                         TableMovies.tags,
                                                         TableMovies.monitored)\
                .join(TableMovies)\
                .where(reduce(operator.and_, upgradable_movies_conditions))\
                .group_by(TableHistoryMovie.video_path)\
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

        query_conditions = [(TableMovies.title is not None)]
        if movieid:
            query_conditions.append((TableMovies.movieId == movieid))
        query_condition = reduce(operator.and_, query_conditions)

        movie_history = TableHistoryMovie.select(TableHistoryMovie.id,
                                                 TableHistoryMovie.action,
                                                 TableMovies.title,
                                                 TableHistoryMovie.timestamp,
                                                 TableHistoryMovie.description,
                                                 TableHistoryMovie.movieId,
                                                 TableMovies.monitored,
                                                 TableHistoryMovie.video_path.alias('path'),
                                                 TableHistoryMovie.language,
                                                 TableMovies.tags,
                                                 TableHistoryMovie.score,
                                                 TableHistoryMovie.subs_id,
                                                 TableHistoryMovie.provider,
                                                 TableHistoryMovie.subtitles_path)\
            .join(TableMovies)\
            .where(query_condition)\
            .order_by(TableHistoryMovie.timestamp.desc())\
            .limit(length)\
            .offset(start)\
            .dicts()
        movie_history = list(movie_history)

        blacklist_db = TableBlacklistMovie.select(TableBlacklistMovie.provider, TableBlacklistMovie.subs_id).dicts()
        blacklist_db = list(blacklist_db)

        for item in movie_history:
            # Mark movies as upgradable or not
            item.update({"upgradable": False})
            if {
                "video_path": str(item["path"]),
                "timestamp": float(item["timestamp"]),
                "score": str(item["score"]),
                "tags": str(item["tags"]),
                "monitored": str(item["monitored"]),
            } in upgradable_movies_not_perfect:
                if os.path.isfile(item["subtitles_path"]):
                    item.update({"upgradable": True})

            del item["path"]

            postprocessMovie(item)

            if item['score']:
                item['score'] = str(round((int(item['score']) * 100 / 120), 2)) + "%"

            # Make timestamp pretty
            if item['timestamp']:
                item["raw_timestamp"] = int(item['timestamp'])
                item["parsed_timestamp"] = datetime.datetime.fromtimestamp(int(item['timestamp'])).strftime('%x %X')
                item['timestamp'] = pretty.date(item["raw_timestamp"])

            # Check if subtitles is blacklisted
            item.update({"blacklisted": False})
            if item['action'] not in [0, 4, 5]:
                for blacklisted_item in blacklist_db:
                    if blacklisted_item['provider'] == item['provider'] and \
                            blacklisted_item['subs_id'] == item['subs_id']:
                        item.update({"blacklisted": True})
                        break

        count = TableHistoryMovie.select()\
            .join(TableMovies)\
            .where(TableMovies.title is not None)\
            .count()

        return jsonify(data=movie_history, total=count)

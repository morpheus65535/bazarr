# coding=utf-8

import operator

from flask import request, jsonify
from flask_restx import Resource, Namespace
from functools import reduce

from app.database import get_exclusion_clause, TableMovies

from ..utils import authenticate, postprocessMovie


api_ns_movies_wanted = Namespace('moviesWanted', description='Movies wanted API endpoint')


@api_ns_movies_wanted.route('movies/wanted')
# GET: Get Wanted Movies
class MoviesWanted(Resource):
    @authenticate
    def get(self):
        radarrid = request.args.getlist("radarrid[]")

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
            start = request.args.get('start') or 0
            length = request.args.get('length') or -1
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

        return jsonify(data=result, total=count)

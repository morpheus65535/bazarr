# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from ..utils import authenticate
from config import settings
from database import TableShows, TableMovies


class Searches(Resource):
    @authenticate
    def get(self):
        query = request.args.get('query')
        search_list = []

        if query:
            if settings.general.getboolean('use_sonarr'):
                # Get matching series
                series = TableShows.select(TableShows.title,
                                           TableShows.sonarrSeriesId,
                                           TableShows.year)\
                    .where(TableShows.title.contains(query))\
                    .order_by(TableShows.title)\
                    .dicts()
                series = list(series)
                search_list += series

            if settings.general.getboolean('use_radarr'):
                # Get matching movies
                movies = TableMovies.select(TableMovies.title,
                                            TableMovies.radarrId,
                                            TableMovies.year) \
                    .where(TableMovies.title.contains(query)) \
                    .order_by(TableMovies.title) \
                    .dicts()
                movies = list(movies)
                search_list += movies

        return jsonify(search_list)

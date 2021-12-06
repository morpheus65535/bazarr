# coding=utf-8

from flask import jsonify
from flask_restful import Resource

import operator
from functools import reduce

from database import get_exclusion_clause, TableEpisodes, TableShows, TableMovies
from get_providers import get_throttled_providers
from utils import get_health_issues

from ..utils import authenticate


class Badges(Resource):
    @authenticate
    def get(self):
        episodes_conditions = [(TableEpisodes.missing_subtitles is not None),
                               (TableEpisodes.missing_subtitles != '[]')]
        episodes_conditions += get_exclusion_clause('series')
        missing_episodes = TableEpisodes.select(TableShows.tags,
                                                TableShows.seriesType,
                                                TableEpisodes.monitored)\
            .join(TableShows)\
            .where(reduce(operator.and_, episodes_conditions))\
            .count()

        movies_conditions = [(TableMovies.missing_subtitles is not None),
                             (TableMovies.missing_subtitles != '[]')]
        movies_conditions += get_exclusion_clause('movie')
        missing_movies = TableMovies.select(TableMovies.tags,
                                            TableMovies.monitored)\
            .where(reduce(operator.and_, movies_conditions))\
            .count()

        throttled_providers = len(eval(str(get_throttled_providers())))

        health_issues = len(get_health_issues())

        result = {
            "episodes": missing_episodes,
            "movies": missing_movies,
            "providers": throttled_providers,
            "status": health_issues
        }
        return jsonify(result)

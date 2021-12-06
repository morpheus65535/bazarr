# coding=utf-8

import operator

from flask import request, jsonify
from flask_restful import Resource
from functools import reduce

from database import get_exclusion_clause, TableEpisodes, TableShows
from ..utils import authenticate, postprocessEpisode


# GET: Get Wanted Episodes
class EpisodesWanted(Resource):
    @authenticate
    def get(self):
        episodeid = request.args.getlist('episodeid[]')

        wanted_conditions = [(TableEpisodes.missing_subtitles != '[]')]
        if len(episodeid) > 0:
            wanted_conditions.append((TableEpisodes.episodeId in episodeid))
        wanted_conditions += get_exclusion_clause('series')
        wanted_condition = reduce(operator.and_, wanted_conditions)

        if len(episodeid) > 0:
            data = TableEpisodes.select(TableShows.title.alias('seriesTitle'),
                                        TableEpisodes.monitored,
                                        TableEpisodes.season.concat('x').concat(TableEpisodes.episode).alias('episode_number'),
                                        TableEpisodes.title.alias('episodeTitle'),
                                        TableEpisodes.missing_subtitles,
                                        TableEpisodes.seriesId,
                                        TableEpisodes.episodeId,
                                        TableShows.tags,
                                        TableEpisodes.failedAttempts,
                                        TableShows.seriesType)\
                .join(TableShows)\
                .where(wanted_condition)\
                .dicts()
        else:
            start = request.args.get('start') or 0
            length = request.args.get('length') or -1
            data = TableEpisodes.select(TableShows.title.alias('seriesTitle'),
                                        TableEpisodes.monitored,
                                        TableEpisodes.season.concat('x').concat(TableEpisodes.episode).alias('episode_number'),
                                        TableEpisodes.title.alias('episodeTitle'),
                                        TableEpisodes.missing_subtitles,
                                        TableEpisodes.seriesId,
                                        TableEpisodes.episodeId,
                                        TableShows.tags,
                                        TableEpisodes.failedAttempts,
                                        TableShows.seriesType)\
                .join(TableShows)\
                .where(wanted_condition)\
                .order_by(TableEpisodes.episodeId.desc())\
                .limit(length)\
                .offset(start)\
                .dicts()
        data = list(data)

        for item in data:
            postprocessEpisode(item)

        count_conditions = [(TableEpisodes.missing_subtitles != '[]')]
        count_conditions += get_exclusion_clause('series')
        count = TableEpisodes.select(TableShows.tags,
                                     TableShows.seriesType,
                                     TableEpisodes.monitored)\
            .join(TableShows)\
            .where(reduce(operator.and_, count_conditions))\
            .count()

        return jsonify(data=data, total=count)

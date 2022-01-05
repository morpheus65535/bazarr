# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from database import TableEpisodes
from ..utils import authenticate, postprocessEpisode


class Episodes(Resource):
    @authenticate
    def get(self):
        seriesId = request.args.getlist('seriesid[]')
        episodeId = request.args.getlist('episodeid[]')

        if len(episodeId) > 0:
            result = TableEpisodes.select().where(TableEpisodes.sonarrEpisodeId.in_(episodeId)).dicts()
        elif len(seriesId) > 0:
            result = TableEpisodes.select()\
                .where(TableEpisodes.sonarrSeriesId.in_(seriesId))\
                .order_by(TableEpisodes.season.desc(), TableEpisodes.episode.desc())\
                .dicts()
        else:
            return "Series or Episode ID not provided", 400

        result = list(result)
        for item in result:
            postprocessEpisode(item)

        return jsonify(data=result)

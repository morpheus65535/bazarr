# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from database import TableEpisodes
from ..utils import authenticate, postprocessEpisode
from event_handler import event_stream


class Episodes(Resource):
    @authenticate
    def get(self):
        seriesId = request.args.getlist('seriesid[]')
        episodeId = request.args.getlist('episodeid[]')

        if len(episodeId) > 0:
            result = TableEpisodes.select().where(TableEpisodes.episodeId.in_(episodeId)).dicts()
        elif len(seriesId) > 0:
            result = TableEpisodes.select()\
                .where(TableEpisodes.seriesId.in_(seriesId))\
                .order_by(TableEpisodes.season.desc(), TableEpisodes.episode.desc())\
                .dicts()
        else:
            return "Series or Episode ID not provided", 400

        result = list(result)
        for item in result:
            postprocessEpisode(item)

        return jsonify(data=result)

    @authenticate
    def patch(self):
        episodeid = request.form.get('episodeid')
        action = request.form.get('action')
        value = request.form.get('value')
        if action == "monitored":
            if value == 'false':
                new_monitored_value = 'True'
            else:
                new_monitored_value = 'False'

            # update episode monitored status
            TableEpisodes.update({
                TableEpisodes.monitored: new_monitored_value
            }) \
                .where(TableEpisodes.episodeId == episodeid) \
                .execute()

            event_stream(type='episode', payload=episodeid)
            event_stream(type='badges')
            event_stream(type='episode-wanted', payload=episodeid)

            return '', 204

        return '', 400

# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource
from operator import itemgetter

from database import TableHistory, TableHistoryMovie
from get_providers import list_throttled_providers, reset_throttled_providers
from ..utils import authenticate, False_Keys


class Providers(Resource):
    @authenticate
    def get(self):
        history = request.args.get('history')
        if history and history not in False_Keys:
            providers = list(TableHistory.select(TableHistory.provider)
                             .where(TableHistory.provider != None and TableHistory.provider != "manual")
                             .dicts())
            providers += list(TableHistoryMovie.select(TableHistoryMovie.provider)
                              .where(TableHistoryMovie.provider != None and TableHistoryMovie.provider != "manual")
                              .dicts())
            providers_list = list(set([x['provider'] for x in providers]))
            providers_dicts = []
            for provider in providers_list:
                providers_dicts.append({
                    'name': provider,
                    'status': 'History',
                    'retry': '-'
                })
            return jsonify(data=sorted(providers_dicts, key=itemgetter('name')))

        throttled_providers = list_throttled_providers()

        providers = list()
        for provider in throttled_providers:
            providers.append({
                "name": provider[0],
                "status": provider[1] if provider[1] is not None else "Good",
                "retry": provider[2] if provider[2] != "now" else "-"
            })
        return jsonify(data=providers)

    @authenticate
    def post(self):
        action = request.form.get('action')

        if action == 'reset':
            reset_throttled_providers()
            return '', 204

        return '', 400

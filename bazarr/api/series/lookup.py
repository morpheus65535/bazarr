# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from ..utils import authenticate
from indexer.series.local.series_indexer import get_series_match


class SeriesLookup(Resource):
    @authenticate
    def get(self):
        # return possible matches from TMDB for a specific series directory
        dir_name = request.args.get('dir_name')
        matches = get_series_match(directory=dir_name)
        return jsonify(data=matches)

# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from ..utils import authenticate
from indexer.series.local.series_indexer import list_series_directories


class SeriesDirectories(Resource):
    @authenticate
    def get(self):
        # list series directories inside a specific root folder
        root_folder_id = request.args.get('id')
        return jsonify(data=list_series_directories(root_dir=root_folder_id))

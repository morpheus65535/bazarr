# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from ..utils import authenticate
from indexer.movies.local.movies_indexer import list_movies_directories


class MoviesDirectories(Resource):
    @authenticate
    def get(self):
        # list movies directories inside a specific root folder
        root_folder_id = request.args.get('id')
        return jsonify(data=list_movies_directories(root_dir=root_folder_id))

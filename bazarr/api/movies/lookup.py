# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from ..utils import authenticate
from indexer.movies.local.movies_indexer import get_movies_match


class MoviesLookup(Resource):
    @authenticate
    def get(self):
        # return possible matches from TMDB for a specific movie directory
        dir_name = request.args.get('dir_name')
        matches = get_movies_match(directory=dir_name)
        return jsonify(data=matches)

# coding=utf-8

from flask import Blueprint
from flask_restful import Api

from .movies import Movies
from .movies_subtitles import MoviesSubtitles
from .history import MoviesHistory
from .wanted import MoviesWanted
from .blacklist import MoviesBlacklist


api_bp_movies = Blueprint('api_movies', __name__)
api = Api(api_bp_movies)

api.add_resource(Movies, '/movies')
api.add_resource(MoviesWanted, '/movies/wanted')
api.add_resource(MoviesSubtitles, '/movies/subtitles')
api.add_resource(MoviesHistory, '/movies/history')
api.add_resource(MoviesBlacklist, '/movies/blacklist')

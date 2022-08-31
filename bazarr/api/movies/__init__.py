# coding=utf-8

from flask_restx import Namespace

from .movies import Movies
from .movies_subtitles import MoviesSubtitles
from .history import MoviesHistory
from .wanted import MoviesWanted
from .blacklist import MoviesBlacklist


api_ns_movies = Namespace('movies', description='Movies API endpoint')

api_ns_movies.add_resource(Movies, 'movies')
api_ns_movies.add_resource(MoviesWanted, 'movies/wanted')
api_ns_movies.add_resource(MoviesSubtitles, 'movies/subtitles')
api_ns_movies.add_resource(MoviesHistory, 'movies/history')
api_ns_movies.add_resource(MoviesBlacklist, 'movies/blacklist')

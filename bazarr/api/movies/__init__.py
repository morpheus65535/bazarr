# coding=utf-8

from .movies import api_ns_movies
from .movies_subtitles import api_ns_movies_subtitles
from .history import api_ns_movies_history
from .wanted import api_ns_movies_wanted
from .blacklist import api_ns_movies_blacklist


api_ns_list_movies = [
    api_ns_movies,
    api_ns_movies_blacklist,
    api_ns_movies_history,
    api_ns_movies_subtitles,
    api_ns_movies_wanted,
]

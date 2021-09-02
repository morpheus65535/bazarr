# -*- coding: utf-8 -*-

"""
tmdbsimple.genres
~~~~~~~~~~~~~~~~~
This module implements the Genres functionality of tmdbsimple.

Created by Celia Oakley on 2013-10-31.

:copyright: (c) 2013-2020 by Celia Oakley
:license: GPLv3, see LICENSE for more details
"""

from .base import TMDB


class Genres(TMDB):
    """
    Genres functionality.

    See: https://developers.themoviedb.org/3/genres
    """
    BASE_PATH = 'genre'
    URLS = {
        'movie_list': '/movie/list',
        'tv_list': '/tv/list',
        'movies': '/{id}/movies',    # backward compatability
    }

    def __init__(self, id=0):
        super(Genres, self).__init__()
        self.id = id

    def movie_list(self, **kwargs):
        """
        Get the list of official genres for movies.

        Args:
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('movie_list')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def tv_list(self, **kwargs):
        """
        Get the list of official genres for TV shows.

        Args:
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('tv_list')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    # backward compatability
    def movies(self, **kwargs):
        """
        Get the list of movies for a particular genre by id. By default, only
        movies with 10 or more votes are included.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            language: (optional) ISO 639-1 code.
            include_all_movies: (optional) Toggle the inclusion of all movies
                                and not just those with 10 or more ratings.
                                Expected value is: True or False.
            include_adult: (optional) Toggle the inclusion of adult titles.
                           Expected value is: True or False.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('movies')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

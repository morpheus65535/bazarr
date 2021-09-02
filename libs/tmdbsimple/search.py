# -*- coding: utf-8 -*-

"""
tmdbsimple.search
~~~~~~~~~~~~~~~~~
This module implements the Search functionality of tmdbsimple.

Created by Celia Oakley on 2013-10-31.

:copyright: (c) 2013-2020 by Celia Oakley
:license: GPLv3, see LICENSE for more details
"""

from .base import TMDB


class Search(TMDB):
    """
    Search functionality

    See: https://developers.themoviedb.org/3/search
    """
    BASE_PATH = 'search'
    URLS = {
        'company': '/company',
        'collection': '/collection',
        'keyword': '/keyword',
        'movie': '/movie',
        'multi': '/multi',
        'person': '/person',
        'tv': '/tv',
    }

    def company(self, **kwargs):
        """
        Search for companies.

        Args:
            query: CGI escpaed string.
            page: (optional) Minimum value of 1. Expected value is an integer.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('company')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def collection(self, **kwargs):
        """
        Search for collections.

        Args:
            query: CGI escpaed string.
            page: (optional) Minimum value of 1. Expected value is an integer.
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('collection')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def keyword(self, **kwargs):
        """
        Search for keywords.

        Args:
            query: CGI escpaed string.
            page: (optional) Minimum value of 1. Expected value is an integer.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('keyword')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def movie(self, **kwargs):
        """
        Search for movies.

        Args:
            query: CGI escpaed string.
            page: (optional) Minimum value of 1. Expected value is an integer.
            language: (optional) ISO 639-1 code.
            include_adult: (optional) Toggle the inclusion of adult titles.
                           Expected value is True or False.
            year: (optional) Filter the results release dates to matches that
                  include this value.
            primary_release_year: (optional) Filter the results so that only
                                  the primary release dates have this value.
            search_type: (optional) By default, the search type is 'phrase'.
                         This is almost guaranteed the option you will want.
                         It's a great all purpose search type and by far the
                         most tuned for every day querying. For those wanting
                         more of an "autocomplete" type search, set this
                         option to 'ngram'.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('movie')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def multi(self, **kwargs):
        """
        Search multiple models in a single request. Multi search currently
        supports searching for movies, tv shows and people in a single request.

        Args:
            query: CGI escpaed string.
            page: (optional) Minimum value of 1. Expected value is an integer.
            language: (optional) ISO 639-1 code.
            include_adult: (optional) Toggle the inclusion of adult titles.
                           Expected value is True or False.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('multi')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def person(self, **kwargs):
        """
        Search for people.

        Args:
            query: CGI escpaed string.
            page: (optional) Minimum value of 1. Expected value is an integer.
            include_adult: (optional) Toggle the inclusion of adult titles.
                           Expected value is True or False.
            search_type: (optional) By default, the search type is 'phrase'.
                         This is almost guaranteed the option you will want.
                         It's a great all purpose search type and by far the
                         most tuned for every day querying. For those wanting
                         more of an "autocomplete" type search, set this
                         option to 'ngram'.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('person')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def tv(self, **kwargs):
        """
        Search for a TV show.

        Args:
            query: CGI escpaed string.
            page: (optional) Minimum value of 1. Expected value is an integer.
            language: (optional) ISO 639-1 code.
            first_air_date_year: (optional) Filter the results to only match
                                 shows that have a air date with with value.
            search_type: (optional) By default, the search type is 'phrase'.
                         This is almost guaranteed the option you will want.
                         It's a great all purpose search type and by far the
                         most tuned for every day querying. For those wanting
                         more of an "autocomplete" type search, set this
                         option to 'ngram'.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('tv')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

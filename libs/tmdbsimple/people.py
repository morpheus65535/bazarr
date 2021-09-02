# -*- coding: utf-8 -*-

"""
tmdbsimple.people
~~~~~~~~~~~~~~~~~
This module implements the People, Credits, and Jobs functionality
of tmdbsimple.

Created by Celia Oakley on 2013-10-31.

:copyright: (c) 2013-2020 by Celia Oakley
:license: GPLv3, see LICENSE for more details
"""

from .base import TMDB


class People(TMDB):
    """
    People functionality.

    See: https://developers.themoviedb.org/3/people
    """
    BASE_PATH = 'person'
    URLS = {
        'info': '/{id}',
        'changes': '/{id}/changes',
        'movie_credits': '/{id}/movie_credits',
        'tv_credits': '/{id}/tv_credits',
        'combined_credits': '/{id}/combined_credits',
        'external_ids': '/{id}/external_ids',
        'images': '/{id}/images',
        'tagged_images': '/{id}/tagged_images',
        'translations': '/{id}/translations',
        'latest': '/latest',
        'popular': '/popular',
    }

    def __init__(self, id=0):
        super(People, self).__init__()
        self.id = id

    def info(self, **kwargs):
        """
        Get the primary person details by id.

        Supports append_to_response. Read more about this at
        https://developers.themoviedb.org/3/getting-started/append-to-response.

        Args:
            append_to_response: (optional) Comma separated, any person method.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def changes(self, **kwargs):
        """
        Get the changes for a person. By default only the last 24 hours are returned.

        You can query up to 14 days in a single query by using the start_date
        and end_date query parameters.

        Args:
            start_date: (optional) Expected format is 'YYYY-MM-DD'.
            end_date: (optional) Expected format is 'YYYY-MM-DD'.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('changes')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def movie_credits(self, **kwargs):
        """
        Get the movie credits for a person.

        Args:
            language: (optional) ISO 639-1 code.
            append_to_response: (optional) Comma separated, any person method.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('movie_credits')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def tv_credits(self, **kwargs):
        """
        Get the TV show credits for a person.

        You can query for some extra details about the credit with the credit
        method.

        Args:
            language: (optional) ISO 639-1 code.
            append_to_response: (optional) Comma separated, any person method.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('tv_credits')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def combined_credits(self, **kwargs):
        """
        Get the movie and TV credits together in a single response.

        Args:
            language: (optional) ISO 639-1 code.
            append_to_response: (optional) Comma separated, any person method.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('combined_credits')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def external_ids(self, **kwargs):
        """
        Get the external ids for a person. We currently support the following external sources.

        External Sources
            - IMDB ID
            - Facebook
            - Freebase MID
            - Freebase ID
            - Instagram
            - TVRage ID
            - Twitter

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('external_ids')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def images(self, **kwargs):
        """
        Get the images for a person.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('images')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def tagged_images(self, **kwargs):
        """
        Get the images that this person has been tagged in.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('tagged_images')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def translations(self, **kwargs):
        """
        Get a list of translations that have been created for a person.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('translations')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def latest(self, **kwargs):
        """
        Get the most newly created person. This is a live response and will
        continuously change.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('latest')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def popular(self, **kwargs):
        """
        Get the list of popular people on TMDb. This list updates daily.

        Args:
            page: (optional) Minimum 1, maximum 1000.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('popular')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class Credits(TMDB):
    """
    Credits functionality.

    See: https://developers.themoviedb.org/3/credits
    """
    BASE_PATH = 'credit'
    URLS = {
        'info': '/{credit_id}',
    }

    def __init__(self, credit_id):
        super(Credits, self).__init__()
        self.credit_id = credit_id

    def info(self, **kwargs):
        """
        Get a movie or TV credit details by id.

        Args:
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_credit_id_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class Jobs(TMDB):
    """
    Jobs functionality.

    See: https://developers.themoviedb.org/3/jobs
    """
    BASE_PATH = 'job'
    URLS = {
        'list': '/list',
    }

    def list(self, **kwargs):
        """
        Get a list of valid jobs.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('list')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

# -*- coding: utf-8 -*-

"""
tmdbsimple.account
~~~~~~~~~~~~~~~~~~
This module implements the Account, Authentication, and Lists functionality
of tmdbsimple.

Created by Celia Oakley on 2013-10-31.

:copyright: (c) 2013-2020 by Celia Oakley
:license: GPLv3, see LICENSE for more details
"""

from .base import TMDB


class Account(TMDB):
    """
    Account functionality.

    See: https://developers.themoviedb.org/3/account
         https://www.themoviedb.org/documentation/api/sessions
    """
    BASE_PATH = 'account'
    URLS = {
        'info': '',
        'lists': '/{id}/lists',
        'favorite_movies': '/{id}/favorite/movies',
        'favorite_tv': '/{id}/favorite/tv',
        'favorite': '/{id}/favorite',
        'rated_movies': '/{id}/rated/movies',
        'rated_tv': '/{id}/rated/tv',
        'rated_tv_episodes': '/{id}/rated/tv/episodes',
        'watchlist_movies': '/{id}/watchlist/movies',
        'watchlist_tv': '/{id}/watchlist/tv',
        'watchlist': '/{id}/watchlist',
    }

    def __init__(self, session_id):
        super(Account, self).__init__()
        self.session_id = session_id

    def info(self, **kwargs):
        """
        Get your account details.

        Call this method first, before calling other Account methods.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('info')
        kwargs.update({'session_id': self.session_id})

        response = self._GET(path, kwargs)
        self.id = response['id']
        self._set_attrs_to_values(response)
        return response

    def lists(self, **kwargs):
        """
        Get all of the lists created by an account. Will include private lists if you are the owner.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('lists')
        kwargs.update({'session_id': self.session_id})

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def favorite_movies(self, **kwargs):
        """
        Get the list of your favorite movies.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            sort_by: (optional) 'created_at.asc' | 'created_at.desc'
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('favorite_movies')
        kwargs.update({'session_id': self.session_id})

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def favorite_tv(self, **kwargs):
        """
        Get the list of your favorite TV shows.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            sort_by: (optional) 'created_at.asc' | 'created_at.desc'
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('favorite_tv')
        kwargs.update({'session_id': self.session_id})

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def favorite(self, **kwargs):
        """
        This method allows you to mark a movie or TV show as a favorite item.

        Args:
            media_type: 'movie' | 'tv'
            media_id: The id of the media.
            favorite: True (to add) | False (to remove).

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('favorite')
        kwargs.update({'session_id': self.session_id})

        payload = {
            'media_type': kwargs.pop('media_type', None),
            'media_id': kwargs.pop('media_id', None),
            'favorite': kwargs.pop('favorite', None),
        }

        response = self._POST(path, kwargs, payload)
        self._set_attrs_to_values(response)
        return response

    def rated_movies(self, **kwargs):
        """
        Get a list of all the movies you have rated.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            sort_by: (optional) 'created_at.asc' | 'created_at.desc'
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('rated_movies')
        kwargs.update({'session_id': self.session_id})

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def rated_tv(self, **kwargs):
        """
        Get a list of all the TV shows you have rated.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            sort_by: (optional) 'created_at.asc' | 'created_at.desc'
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('rated_tv')
        kwargs.update({'session_id': self.session_id})

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def rated_tv_episodes(self, **kwargs):
        """
        Get a list of all the TV episodes you have rated.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            sort_by: (optional) 'created_at.asc' | 'created_at.desc'
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('rated_tv_episodes')
        kwargs.update({'session_id': self.session_id})

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def watchlist_movies(self, **kwargs):
        """
        Get a list of all the movies you have added to your watchlist.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            sort_by: (optional) 'created_at.asc' | 'created_at.desc'
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('watchlist_movies')
        kwargs.update({'session_id': self.session_id})

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def watchlist_tv(self, **kwargs):
        """
        Get a list of all the TV shows you have added to your watchlist.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            sort_by: (optional) 'created_at.asc' | 'created_at.desc'
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('watchlist_tv')
        kwargs.update({'session_id': self.session_id})

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def watchlist(self, **kwargs):
        """
        Add a movie or TV show to your watchlist.

        Args:
            media_type: 'movie' | 'tv'
            media_id: The id of the media.
            watchlist: True (to add) | False (to remove).

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('watchlist')
        kwargs.update({'session_id': self.session_id})

        payload = {
            'media_type': kwargs.pop('media_type', None),
            'media_id': kwargs.pop('media_id', None),
            'watchlist': kwargs.pop('watchlist', None),
        }

        response = self._POST(path, kwargs, payload)
        self._set_attrs_to_values(response)
        return response


class Authentication(TMDB):
    """
    Authentication functionality.

    See: https://developers.themoviedb.org/3/authentication
         https://www.themoviedb.org/documentation/api/sessions
    """
    BASE_PATH = 'authentication'
    URLS = {
        'guest_session_new': '/guest_session/new',
        'token_new': '/token/new',
        'session_new': '/session/new',
        'token_validate_with_login': '/token/validate_with_login',
    }

    def guest_session_new(self, **kwargs):
        """
        This method will let you create a new guest session. Guest sessions
        are a type of session that will let a user rate movies and TV shows
        but not require them to have a TMDb user account. More
        information about user authentication can be found here
        (https://developers.themoviedb.org/3/authentication/how-do-i-generate-a-session-id).

        Please note, you should only generate a single guest session per
        user (or device) as you will be able to attach the ratings to a
        TMDb user account in the future. There is also IP limits in place
        so you should always make sure it's the end user doing the guest
        session actions.

        If a guest session is not used for the first time within 24 hours,
        it will be automatically deleted.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('guest_session_new')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def token_new(self, **kwargs):
        """
        Create a temporary request token that can be used to validate a TMDb
        user login. More details about how this works can be found here
        (https://developers.themoviedb.org/3/authentication/how-do-i-generate-a-session-id).

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('token_new')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def session_new(self, **kwargs):
        """
        You can use this method to create a fully valid session ID once a user
        has validated the request token. More information about how this works
        can be found here
        (https://developers.themoviedb.org/3/authentication/how-do-i-generate-a-session-id).

        Args:
            request_token: The token you generated for the user to approve.
                           The token needs to be approved before being
                           used here.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('session_new')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def token_validate_with_login(self, **kwargs):
        """
        This method allows an application to validate a request token by entering
        a username and password.

        Not all applications have access to a web view so this can be used as a
        substitute.

        Please note, the preferred method of validating a request token is to
        have a user authenticate the request via the TMDb website. You can read
        about that method here
        (https://developers.themoviedb.org/3/authentication/how-do-i-generate-a-session-id).

        If you decide to use this method please use HTTPS.

        Args:
            username: The user's username on TMDb.
            password: The user's password on TMDb.
            request_token: The token you generated for the user to approve.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('token_validate_with_login')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class GuestSessions(TMDB):
    """
    Guest Sessions functionality.

    See: https://developers.themoviedb.org/3/guest-sessions
    """
    BASE_PATH = 'guest_session'
    URLS = {
        'rated_movies': '/{guest_session_id}/rated/movies',
        'rated_tv': '/{guest_session_id}/rated/tv',
        'rated_tv_episodes': '/{guest_session_id}/rated/tv/episodes',
    }

    def __init__(self, guest_session_id=0):
        super(GuestSessions, self).__init__()
        self.guest_session_id = guest_session_id

    def rated_movies(self, **kwargs):
        """
        Get the rated movies for a guest session.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            sort_by: (optional) 'created_at.asc' | 'created_at.desc'
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_guest_session_id_path('rated_movies')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def rated_tv(self, **kwargs):
        """
        Get the rated TV shows for a guest session.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            sort_by: (optional) 'created_at.asc' | 'created_at.desc'
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_guest_session_id_path('rated_tv')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def rated_tv_episodes(self, **kwargs):
        """
        Get the rated TV episodes for a guest session.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            sort_by: (optional) 'created_at.asc' | 'created_at.desc'
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_guest_session_id_path('rated_tv_episodes')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class Lists(TMDB):
    """
    Lists functionality.

    See: https://developers.themoviedb.org/3/lists
    """
    BASE_PATH = 'list'
    URLS = {
        'info': '/{id}',
        'item_status': '/{id}/item_status',
        'create_list': '',
        'add_item': '/{id}/add_item',
        'remove_item': '/{id}/remove_item',
        'clear': '/{id}/clear',
    }

    def __init__(self, id=0, session_id=0):
        super(Lists, self).__init__()
        self.id = id
        self.session_id = session_id

    def info(self, **kwargs):
        """
        Get the details of a list.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def item_status(self, **kwargs):
        """
        You can use this method to check if a movie has already been added to
        the list.

        Args:
            movie_id: The id of the movie.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('item_status')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def create_list(self, **kwargs):
        """
        Create a list.

        Args:
            name: Name of the list.
            description: Description of the list.
            language: (optional) ISO 639-1 code.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('create_list')
        kwargs.update({'session_id': self.session_id})

        payload = {
            'name': kwargs.pop('name', None),
            'description': kwargs.pop('description', None),
        }
        if 'language' in kwargs:
            payload['language'] = kwargs['language']

        response = self._POST(path, kwargs, payload)
        self._set_attrs_to_values(response)
        return response

    def add_item(self, **kwargs):
        """
        Add a movie to a list.

        Args:
            media_id: A movie id.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('add_item')
        kwargs.update({'session_id': self.session_id})

        payload = {
            'media_id': kwargs.pop('media_id', None),
        }

        response = self._POST(path, kwargs, payload)
        self._set_attrs_to_values(response)
        return response

    def remove_item(self, **kwargs):
        """
        Remove a movie from a list.

        Args:
            media_id: A movie id.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('remove_item')
        kwargs.update({'session_id': self.session_id})

        payload = {
            'media_id': kwargs.pop('media_id', None),
        }

        response = self._POST(path, kwargs, payload)
        self._set_attrs_to_values(response)
        return response

    def clear_list(self, **kwargs):
        """
        Clear all of the items from a list.

        Args:
            confirm: True (do it) | False (don't do it)

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('clear')
        kwargs.update({'session_id': self.session_id})

        payload = {}

        response = self._POST(path, kwargs, payload)
        self._set_attrs_to_values(response)
        return response

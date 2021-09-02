# -*- coding: utf-8 -*-

"""
tmdbsimple.find
~~~~~~~~~~~~~~~
This module implements the Find functionality of tmdbsimple.

Created by Celia Oakley on 2013-10-31.

:copyright: (c) 2013-2020 by Celia Oakley
:license: GPLv3, see LICENSE for more details
"""

from .base import TMDB


class Find(TMDB):
    """
    Find functionality.

    See: https://developers.themoviedb.org/3/find
    """
    BASE_PATH = 'find'
    URLS = {
        'info': '/{id}',
    }

    def __init__(self, id=0):
        super(Find, self).__init__()
        self.id = id

    def info(self, **kwargs):
        """
        The find method makes it easy to search for objects in our database by
        an external id. For example, an IMDB ID.

        This method will search all objects (movies, TV shows and people) and
        return the results in a single response.

        The supported external sources for each object are as follows.
            Media Databases: IMDb ID, TVDB ID, Freebase MID*, Freebase ID*,
                             TVRage ID*
            Social IDs: Facebook, Insagram, Twitter

        Args:
            external_source: See lists above.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class Trending(TMDB):
    """
    Trending functionality.

    See: https://developers.themoviedb.org/3/trending
    """
    BASE_PATH = 'trending'
    URLS = {
        'info': '/{media_type}/{time_window}',
    }

    def __init__(self, media_type='all', time_window='day'):
        super(Trending, self).__init__()
        self.media_type = media_type
        self.time_window = time_window

    def info(self, **kwargs):
        """
        Get the daily or weekly trending items. The daily trending list tracks
        items over the period of a day while items have a 24 hour half life.
        The weekly list tracks items over a 7 day period, with a 7 day half
        life.

        Valid Media Types
            'all': Include all movies, TV shows and people in the results as a
                   global trending list.
            'movie': Show the trending movies in the results.
            'tv': Show the trending TV shows in the results.
            'people': Show the trending people in the results.

        Valid Time Windows
            'day': View the trending list for the day.
            'week': View the trending list for the week.

        Args:

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_media_type_time_window_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

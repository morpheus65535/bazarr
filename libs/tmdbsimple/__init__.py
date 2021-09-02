# -*- coding: utf-8 -*-

"""
tmdbsimple
~~~~~~~~~~

*tmdbsimple* is a wrapper, written in Python, for The Movie Database (TMDb)
API v3.  By calling the functions available in *tmdbsimple* you can simplify
your code and easily access a vast amount of movie, tv, and cast data.  To find
out more about The Movie Database API, check out the overview page
http://www.themoviedb.org/documentation/api and documentation page
https://developers.themoviedb.org/3/getting-started
https://www.themoviedb.org/documentation/api/status-codes

:copyright: (c) 2013-2020 by Celia Oakley.
:license: GPLv3, see LICENSE for more details
"""

__title__ = 'tmdbsimple'
__version__ = '2.4.2'
__author__ = 'Celia Oakley'
__copyright__ = 'Copyright (c) 2013-2020 Celia Oakley'
__license__ = 'GPLv3'

import os

from .account import Account, Authentication, GuestSessions, Lists
from .base import APIKeyError
from .changes import Changes
from .configuration import Configuration, Certifications, Timezones
from .discover import Discover
from .find import Find, Trending
from .genres import Genres
from .movies import Movies, Collections, Companies, Keywords, Reviews
from .people import People, Credits, Jobs
from .search import Search
from .tv import TV, TV_Seasons, TV_Episodes, TV_Episode_Groups, TV_Changes, Networks

__all__ = ['Account', 'Authentication', 'GuestSessions', 'Lists',
           'APIKeyError',
           'Changes',
           'Configuration', 'Certifications', 'Timezones',
           'Discover',
           'Find', 'Trending',
           'Genres',
           'Movies', 'Collections', 'Companies', 'Keywords', 'Reviews',
           'People', 'Credits', 'Jobs',
           'Search',
           'TV', 'TV_Seasons', 'TV_Episodes', 'TV_Episode_Groups', 'TV_Changes', 'Networks'
           ]

API_KEY = os.environ.get('TMDB_API_KEY', None)
API_VERSION = '3'

# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from functools import wraps
import logging
import re

import requests

from .. import __short_version__
from ..cache import REFINER_EXPIRATION_TIME, region
from ..utils import sanitize
from ..video import Episode

logger = logging.getLogger(__name__)

series_re = re.compile(r'^(?P<series>.*?)(?: \((?:(?P<year>\d{4})|(?P<country>[A-Z]{2}))\))?$')


def requires_auth(func):
    """Decorator for :class:`TVDBClient` methods that require authentication"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.token is None or self.token_expired:
            self.login()
        elif self.token_needs_refresh:
            self.refresh_token()
        return func(self, *args, **kwargs)
    return wrapper


class TVDBClient(object):
    """TVDB REST API Client

    :param str apikey: API key to use.
    :param str username: username to use.
    :param str password: password to use.
    :param str language: language of the responses.
    :param session: session object to use.
    :type session: :class:`requests.sessions.Session` or compatible.
    :param dict headers: additional headers.
    :param int timeout: timeout for the requests.

    """
    #: Base URL of the API
    base_url = 'https://api.thetvdb.com'

    #: Token lifespan
    token_lifespan = timedelta(hours=1)

    #: Minimum token age before a :meth:`refresh_token` is triggered
    refresh_token_every = timedelta(minutes=30)

    def __init__(self, apikey=None, username=None, password=None, language='en', session=None, headers=None,
                 timeout=10):
        #: API key
        self.apikey = apikey

        #: Username
        self.username = username

        #: Password
        self.password = password

        #: Last token acquisition date
        self.token_date = datetime.utcnow() - self.token_lifespan

        #: Session for the requests
        self.session = session or requests.Session()
        self.session.timeout = timeout
        self.session.headers.update(headers or {})
        self.session.headers['Content-Type'] = 'application/json'
        self.session.headers['Accept-Language'] = language

    @property
    def language(self):
        return self.session.headers['Accept-Language']

    @language.setter
    def language(self, value):
        self.session.headers['Accept-Language'] = value

    @property
    def token(self):
        if 'Authorization' not in self.session.headers:
            return None
        return self.session.headers['Authorization'][7:]

    @property
    def token_expired(self):
        return datetime.utcnow() - self.token_date > self.token_lifespan

    @property
    def token_needs_refresh(self):
        return datetime.utcnow() - self.token_date > self.refresh_token_every

    def login(self):
        """Login"""
        # perform the request
        data = {'apikey': self.apikey, 'username': self.username, 'password': self.password}
        r = self.session.post(self.base_url + '/login', json=data)
        r.raise_for_status()

        # set the Authorization header
        self.session.headers['Authorization'] = 'Bearer ' + r.json()['token']

        # update token_date
        self.token_date = datetime.utcnow()

    def refresh_token(self):
        """Refresh token"""
        # perform the request
        r = self.session.get(self.base_url + '/refresh_token')
        r.raise_for_status()

        # set the Authorization header
        self.session.headers['Authorization'] = 'Bearer ' + r.json()['token']

        # update token_date
        self.token_date = datetime.utcnow()

    @requires_auth
    def search_series(self, name=None, imdb_id=None, zap2it_id=None):
        """Search series"""
        # perform the request
        params = {'name': name, 'imdbId': imdb_id, 'zap2itId': zap2it_id}
        r = self.session.get(self.base_url + '/search/series', params=params)
        if r.status_code == 404:
            return None
        r.raise_for_status()

        return r.json()['data']

    @requires_auth
    def get_series(self, id):
        """Get series"""
        # perform the request
        r = self.session.get(self.base_url + '/series/{}'.format(id))
        if r.status_code == 404:
            return None
        r.raise_for_status()

        return r.json()['data']

    @requires_auth
    def get_series_actors(self, id):
        """Get series actors"""
        # perform the request
        r = self.session.get(self.base_url + '/series/{}/actors'.format(id))
        if r.status_code == 404:
            return None
        r.raise_for_status()

        return r.json()['data']

    @requires_auth
    def get_series_episodes(self, id, page=1):
        """Get series episodes"""
        # perform the request
        params = {'page': page}
        r = self.session.get(self.base_url + '/series/{}/episodes'.format(id), params=params)
        if r.status_code == 404:
            return None
        r.raise_for_status()

        return r.json()

    @requires_auth
    def query_series_episodes(self, id, absolute_number=None, aired_season=None, aired_episode=None, dvd_season=None,
                              dvd_episode=None, imdb_id=None, page=1):
        """Query series episodes"""
        # perform the request
        params = {'absoluteNumber': absolute_number, 'airedSeason': aired_season, 'airedEpisode': aired_episode,
                  'dvdSeason': dvd_season, 'dvdEpisode': dvd_episode, 'imdbId': imdb_id, 'page': page}
        r = self.session.get(self.base_url + '/series/{}/episodes/query'.format(id), params=params)
        if r.status_code == 404:
            return None
        r.raise_for_status()

        return r.json()

    @requires_auth
    def get_episode(self, id):
        """Get episode"""
        # perform the request
        r = self.session.get(self.base_url + '/episodes/{}'.format(id))
        if r.status_code == 404:
            return None
        r.raise_for_status()

        return r.json()['data']


#: Configured instance of :class:`TVDBClient`
tvdb_client = TVDBClient('5EC930FB90DA1ADA', headers={'User-Agent': 'Subliminal/%s' % __short_version__})


@region.cache_on_arguments(expiration_time=REFINER_EXPIRATION_TIME)
def search_series(name):
    """Search series.

    :param str name: name of the series.
    :return: the search results.
    :rtype: list

    """
    return tvdb_client.search_series(name)


@region.cache_on_arguments(expiration_time=REFINER_EXPIRATION_TIME)
def get_series(id):
    """Get series.

    :param int id: id of the series.
    :return: the series data.
    :rtype: dict

    """
    return tvdb_client.get_series(id)


@region.cache_on_arguments(expiration_time=REFINER_EXPIRATION_TIME)
def get_series_episode(series_id, season, episode):
    """Get an episode of a series.

    :param int series_id: id of the series.
    :param int season: season number of the episode.
    :param int episode: episode number of the episode.
    :return: the episode data.
    :rtype: dict

    """
    result = tvdb_client.query_series_episodes(series_id, aired_season=season, aired_episode=episode)
    if result:
        return tvdb_client.get_episode(result['data'][0]['id'])


def refine(video, **kwargs):
    """Refine a video by searching `TheTVDB <http://thetvdb.com/>`_.

    .. note::

        This refiner only work for instances of :class:`~subliminal.video.Episode`.

    Several attributes can be found:

      * :attr:`~subliminal.video.Episode.series`
      * :attr:`~subliminal.video.Episode.year`
      * :attr:`~subliminal.video.Episode.series_imdb_id`
      * :attr:`~subliminal.video.Episode.series_tvdb_id`
      * :attr:`~subliminal.video.Episode.title`
      * :attr:`~subliminal.video.Video.imdb_id`
      * :attr:`~subliminal.video.Episode.tvdb_id`

    """
    # only deal with Episode videos
    if not isinstance(video, Episode):
        logger.error('Cannot refine episodes')
        return

    # exit if the information is complete
    if video.series_tvdb_id and video.tvdb_id:
        logger.debug('No need to search')
        return

    # search the series
    logger.info('Searching series %r', video.series)
    results = search_series(video.series.lower())
    if not results:
        logger.warning('No results for series')
        return
    logger.debug('Found %d results', len(results))

    # search for exact matches
    matching_results = []
    for result in results:
        matching_result = {}

        # use seriesName and aliases
        series_names = [result['seriesName']]
        series_names.extend(result['aliases'])

        # parse the original series as series + year or country
        original_match = series_re.match(result['seriesName']).groupdict()

        # parse series year
        series_year = None
        if result['firstAired']:
            series_year = datetime.strptime(result['firstAired'], '%Y-%m-%d').year

        # discard mismatches on year
        if video.year and series_year and video.year != series_year:
            logger.debug('Discarding series %r mismatch on year %d', result['seriesName'], series_year)
            continue

        # iterate over series names
        for series_name in series_names:
            # parse as series and year
            series, year, country = series_re.match(series_name).groups()
            if year:
                year = int(year)

            # discard mismatches on year
            if year and (video.original_series or video.year != year):
                logger.debug('Discarding series name %r mismatch on year %d', series, year)
                continue

            # match on sanitized series name
            if sanitize(series) == sanitize(video.series):
                logger.debug('Found exact match on series %r', series_name)
                matching_result['match'] = {'series': original_match['series'], 'year': series_year,
                                            'original_series': original_match['year'] is None}
                break

        # add the result on match
        if matching_result:
            matching_result['data'] = result
            matching_results.append(matching_result)

    # exit if we don't have exactly 1 matching result
    if not matching_results:
        logger.error('No matching series found')
        return
    if len(matching_results) > 1:
        logger.error('Multiple matches found')
        return

    # get the series
    matching_result = matching_results[0]
    series = get_series(matching_result['data']['id'])

    # add series information
    logger.debug('Found series %r', series)
    video.series = matching_result['match']['series']
    video.year = matching_result['match']['year']
    video.original_series = matching_result['match']['original_series']
    video.series_tvdb_id = series['id']
    video.series_imdb_id = series['imdbId'] or None

    # get the episode
    logger.info('Getting series episode %dx%d', video.season, video.episode)
    episode = get_series_episode(video.series_tvdb_id, video.season, video.episode)
    if not episode:
        logger.warning('No results for episode')
        return

    # add episode information
    logger.debug('Found episode %r', episode)
    video.tvdb_id = episode['id']
    video.title = episode['episodeName'] or None
    video.imdb_id = episode['imdbId'] or None

# -*- coding: utf-8 -*-
import logging
import operator

import requests

from .. import __short_version__
from ..cache import REFINER_EXPIRATION_TIME, region
from ..video import Episode, Movie
from ..utils import sanitize

logger = logging.getLogger(__name__)


class OMDBClient(object):
    base_url = 'http://www.omdbapi.com'

    def __init__(self, version=1, session=None, headers=None, timeout=10):
        #: Session for the requests
        self.session = session or requests.Session()
        self.session.timeout = timeout
        self.session.headers.update(headers or {})
        self.session.params['r'] = 'json'
        self.session.params['v'] = version

    def get(self, id=None, title=None, type=None, year=None, plot='short', tomatoes=False):
        # build the params
        params = {}
        if id:
            params['i'] = id
        if title:
            params['t'] = title
        if not params:
            raise ValueError('At least id or title is required')
        params['type'] = type
        params['y'] = year
        params['plot'] = plot
        params['tomatoes'] = tomatoes

        # perform the request
        r = self.session.get(self.base_url, params=params)
        r.raise_for_status()

        # get the response as json
        j = r.json()

        # check response status
        if j['Response'] == 'False':
            return None

        return j

    def search(self, title, type=None, year=None, page=1):
        # build the params
        params = {'s': title, 'type': type, 'y': year, 'page': page}

        # perform the request
        r = self.session.get(self.base_url, params=params)
        r.raise_for_status()

        # get the response as json
        j = r.json()

        # check response status
        if j['Response'] == 'False':
            return None

        return j


omdb_client = OMDBClient(headers={'User-Agent': 'Subliminal/%s' % __short_version__})


@region.cache_on_arguments(expiration_time=REFINER_EXPIRATION_TIME)
def search(title, type, year):
    results = omdb_client.search(title, type, year)
    if not results:
        return None

    # fetch all paginated results
    all_results = results['Search']
    total_results = int(results['totalResults'])
    page = 1
    while total_results > page * 10:
        page += 1
        results = omdb_client.search(title, type, year, page=page)
        all_results.extend(results['Search'])

    return all_results


def refine(video, **kwargs):
    """Refine a video by searching `OMDb API <http://omdbapi.com/>`_.

    Several :class:`~subliminal.video.Episode` attributes can be found:

      * :attr:`~subliminal.video.Episode.series`
      * :attr:`~subliminal.video.Episode.year`
      * :attr:`~subliminal.video.Episode.series_imdb_id`

    Similarly, for a :class:`~subliminal.video.Movie`:

      * :attr:`~subliminal.video.Movie.title`
      * :attr:`~subliminal.video.Movie.year`
      * :attr:`~subliminal.video.Video.imdb_id`

    """
    if isinstance(video, Episode):
        # exit if the information is complete
        if video.series_imdb_id:
            logger.debug('No need to search')
            return

        # search the series
        results = search(video.series, 'series', video.year)
        if not results:
            logger.warning('No results for series')
            return
        logger.debug('Found %d results', len(results))

        # filter the results
        results = [r for r in results if sanitize(r['Title']) == sanitize(video.series)]
        if not results:
            logger.warning('No matching series found')
            return

        # process the results
        found = False
        for result in sorted(results, key=operator.itemgetter('Year')):
            if video.original_series and video.year is None:
                logger.debug('Found result for original series without year')
                found = True
                break
            if video.year == int(result['Year'].split(u'\u2013')[0]):
                logger.debug('Found result with matching year')
                found = True
                break

        if not found:
            logger.warning('No matching series found')
            return

        # add series information
        logger.debug('Found series %r', result)
        video.series = result['Title']
        video.year = int(result['Year'].split(u'\u2013')[0])
        video.series_imdb_id = result['imdbID']

    elif isinstance(video, Movie):
        # exit if the information is complete
        if video.imdb_id:
            return

        # search the movie
        results = search(video.title, 'movie', video.year)
        if not results:
            logger.warning('No results')
            return
        logger.debug('Found %d results', len(results))

        # filter the results
        results = [r for r in results if sanitize(r['Title']) == sanitize(video.title)]
        if not results:
            logger.warning('No matching movie found')
            return

        # process the results
        found = False
        for result in results:
            if video.year is None:
                logger.debug('Found result for movie without year')
                found = True
                break
            if video.year == int(result['Year']):
                logger.debug('Found result with matching year')
                found = True
                break

        if not found:
            logger.warning('No matching movie found')
            return

        # add movie information
        logger.debug('Found movie %r', result)
        video.title = result['Title']
        video.year = int(result['Year'].split(u'\u2013')[0])
        video.imdb_id = result['imdbID']

# coding=utf-8

from __future__ import absolute_import
import logging
import re

from random import randint
from requests import Session

from subzero.language import Language
from subliminal.providers import ParserBeautifulSoup
from subliminal.cache import SHOW_EXPIRATION_TIME, region, EPISODE_EXPIRATION_TIME
from subliminal.exceptions import ProviderError
from subliminal.providers.tvsubtitles import TVsubtitlesProvider as _TVsubtitlesProvider, \
    TVsubtitlesSubtitle as _TVsubtitlesSubtitle, episode_id_re
from subliminal.utils import sanitize
from subliminal.video import Episode

from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

logger = logging.getLogger(__name__)


class TVsubtitlesSubtitle(_TVsubtitlesSubtitle):
    def __init__(self, language, page_link, subtitle_id, series, season, episode, year, rip, release):
        super(TVsubtitlesSubtitle, self).__init__(language, page_link, subtitle_id, series, season, episode,
                                                  year, rip, release)
        self.release_info = u"%s, %s" % (rip, release)
        self.matches = set()


class TVsubtitlesProvider(_TVsubtitlesProvider):
    languages = {Language('por', 'BR')} | {Language(l) for l in [
        'ara', 'bul', 'ces', 'dan', 'deu', 'ell', 'eng', 'fin', 'fra', 'hun', 'ita', 'jpn', 'kor', 'nld', 'pol', 'por',
        'ron', 'rus', 'spa', 'swe', 'tur', 'ukr', 'zho'
    ]}
    video_types = (Episode,)
    subtitle_class = TVsubtitlesSubtitle

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME)
    def _show_list(self):
        """
        Retrieve the complete list of TV shows available on the provider server.

        The method requests the ``tvshows.html`` page from the server, parses
        the HTML content and extracts every link pointing to a show page. For
        each matching link, the show title, its numeric identifier (taken from
        the link target) and the year of first airing (taken from the last cell
        of the same table row, when present) are collected. The result is
        cached on the method arguments for the duration defined by the show
        expiration time, so repeated calls within that period do not trigger
        new HTTP requests.

        :raises ProviderError: If the page contains no shows. Raising keeps the
            empty result out of the cache.
        :raises requests.exceptions.HTTPError: If the server responds with an
            unsuccessful HTTP status code.
        :raises requests.exceptions.Timeout: If the request does not complete
            within the configured timeout.
        :raises requests.exceptions.RequestException: If any other network
            related error occurs while fetching the page.
        :return: A list of tuples, each containing the show title as a string,
            the show identifier as an integer and the year of first airing as an
            integer or ``None`` when the year could not be determined.
        :rtype: list[tuple[str, int, int | None]]
        """
        r = self.session.get(self.server_url + 'tvshows.html', timeout=20)
        r.raise_for_status()
        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])
        shows = []
        for a in soup.select('a[href^="tvshow-"]'):
            m = re.match(r'tvshow-(\d+)-\d+\.html$', a.get('href', ''))
            td = a.find_parent('td')
            if not m or td is None:
                continue
            cells = td.find_next_siblings('td')
            ym = re.match(r'\s*(\d{4})', cells[-1].text) if cells else None
            shows.append((a.text.strip(), int(m.group(1)), int(ym.group(1)) if ym else None))
        soup.decompose()
        if not shows:
            raise ProviderError('No shows found in tvshows.html')
        return shows

    def search_show_id(self, series, year=None):
        """
        Search the show list for the identifier of a series matching the given
        name and, optionally, the given year.

        The series name is sanitized and lower-cased before comparison. Each
        entry of the show list is parsed to separate the base series name from
        an optional trailing year or country suffix (such as "(US)" or "(UK)").
        An entry is considered a candidate when either its base name or its
        full name matches the wanted series name. When a year is provided, an
        exact match on the year is preferred; if no exact match exists, the
        first candidate whose year differs by at most one year is returned as a
        fallback. When no year is provided, the first candidate found is
        returned.

        :param series: Name of the series to search for.
        :type series: str
        :param year: Year of the series used to disambiguate between shows
            sharing the same name. If omitted, the first matching show is
            returned.
        :type year: int or None
        :return: The identifier of the matching show, or ``None`` if no show
            matches the given series name and year.
        :rtype: int or str or None
        """
        logger.info('Searching show id for %r', series)
        wanted = sanitize(series).lower()
        exact, close = None, None
        for name, show_id, first_year in self._show_list():
            m = re.match(r'^(?P<series>.+?)(?: \(?(?P<year>\d{4})\)?| \((?:US|UK)\))?$', name)
            base = sanitize(m.group('series')).lower() if m else sanitize(name).lower()
            if base != wanted and sanitize(name).lower() != wanted:
                continue
            show_year = int(m.group('year')) if m and m.group('year') else first_year
            if year is None or show_year == year:
                exact = show_id
                break
            if close is None and show_year is not None and abs(show_year - year) <= 1:
                close = show_id
        return exact or close

    @region.cache_on_arguments(expiration_time=EPISODE_EXPIRATION_TIME)
    def get_episode_ids(self, show_id, season):
        """Get episode ids from the show id and the season.

        :param int show_id: show id.
        :param int season: season of the episode.
        :return: episode ids per episode number.
        :rtype: dict

        """
        # get the page of the season of the show
        logger.info('Getting the page of show id %d, season %d', show_id, season)
        r = self.session.get(self.server_url + 'tvshow-%d-%d.html' % (show_id, season), timeout=10)
        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])

        # loop over episode rows
        episode_ids = {}
        for row in soup.select('table#table5 tr'):
            # skip rows that do not have a link to the episode page
            if not row('a', href=episode_id_re):
                continue

            # extract data from the cells
            cells = row('td')
            episode = int(cells[0].text.split('x')[1])
            episode_id = int(cells[1].a['href'][8:-5])
            episode_ids[episode] = episode_id

        if episode_ids:
            logger.debug('Found episode ids %r', episode_ids)
        else:
            logger.warning('No episode ids found')

        soup.decompose()
        soup = None

        return episode_ids

    def query(self, show_id, series, season, episode, year=None):
        # get the episode ids
        episode_ids = self.get_episode_ids(show_id, season)
        # Provider doesn't store multi episode information
        episode = min(episode) if episode and isinstance(episode, list) else episode

        if episode not in episode_ids:
            logger.error('Episode %d not found', episode)
            return []

        # get the episode page
        logger.info('Getting the page for episode %d', episode_ids[episode])
        r = self.session.get(self.server_url + 'episode-%d.html' % episode_ids[episode], timeout=10)
        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])

        # loop over subtitles rows
        subtitles = []
        for row in soup.select('.subtitlen'):
            # read the item
            language = Language.fromtvsubtitles(row.h5.img['src'][13:-4])
            subtitle_id = int(row.parent['href'][10:-5])
            page_link = self.server_url + 'subtitle-%d.html' % subtitle_id
            rip = row.find('p', title='rip').text.strip() or None
            release = row.find('h5').text.strip() or None

            subtitle = self.subtitle_class(language, page_link, subtitle_id, series, season, episode, year, rip,
                                           release)
            logger.info('Found subtitle %s', subtitle)
            subtitles.append(subtitle)

        soup.decompose()
        soup = None

        return subtitles

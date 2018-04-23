# -*- coding: utf-8 -*-
import logging
import re

from babelfish import Language, language_converters
from guessit import guessit
from requests import Session

from . import ParserBeautifulSoup, Provider
from .. import __short_version__
from ..cache import SHOW_EXPIRATION_TIME, region
from ..exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded
from ..score import get_equivalent_release_groups
from ..subtitle import Subtitle, fix_line_ending, guess_matches
from ..utils import sanitize, sanitize_release_group
from ..video import Episode

logger = logging.getLogger(__name__)

language_converters.register('addic7ed = subliminal.converters.addic7ed:Addic7edConverter')

# Series cell matching regex
show_cells_re = re.compile(b'<td class="version">.*?</td>', re.DOTALL)

#: Series header parsing regex
series_year_re = re.compile(r'^(?P<series>[ \w\'.:(),*&!?-]+?)(?: \((?P<year>\d{4})\))?$')


class Addic7edSubtitle(Subtitle):
    """Addic7ed Subtitle."""
    provider_name = 'addic7ed'

    def __init__(self, language, hearing_impaired, page_link, series, season, episode, title, year, version,
                 download_link):
        super(Addic7edSubtitle, self).__init__(language, hearing_impaired=hearing_impaired, page_link=page_link)
        self.series = series
        self.season = season
        self.episode = episode
        self.title = title
        self.year = year
        self.version = version
        self.download_link = download_link

    @property
    def id(self):
        return self.download_link

    def get_matches(self, video):
        matches = set()

        # series name
        if video.series and sanitize(self.series) in (
                sanitize(name) for name in [video.series] + video.alternative_series):
            matches.add('series')
        # season
        if video.season and self.season == video.season:
            matches.add('season')
        # episode
        if video.episode and self.episode == video.episode:
            matches.add('episode')
        # title of the episode
        if video.title and sanitize(self.title) == sanitize(video.title):
            matches.add('title')
        # year
        if video.original_series and self.year is None or video.year and video.year == self.year:
            matches.add('year')
        # release_group
        if (video.release_group and self.version and
                any(r in sanitize_release_group(self.version)
                    for r in get_equivalent_release_groups(sanitize_release_group(video.release_group)))):
            matches.add('release_group')
        # resolution
        if video.resolution and self.version and video.resolution in self.version.lower():
            matches.add('resolution')
        # format
        if video.format and self.version and video.format.lower() in self.version.lower():
            matches.add('format')
        # other properties
        matches |= guess_matches(video, guessit(self.version), partial=True)

        return matches


class Addic7edProvider(Provider):
    """Addic7ed Provider."""
    languages = {Language('por', 'BR')} | {Language(l) for l in [
        'ara', 'aze', 'ben', 'bos', 'bul', 'cat', 'ces', 'dan', 'deu', 'ell', 'eng', 'eus', 'fas', 'fin', 'fra', 'glg',
        'heb', 'hrv', 'hun', 'hye', 'ind', 'ita', 'jpn', 'kor', 'mkd', 'msa', 'nld', 'nor', 'pol', 'por', 'ron', 'rus',
        'slk', 'slv', 'spa', 'sqi', 'srp', 'swe', 'tha', 'tur', 'ukr', 'vie', 'zho'
    ]}
    video_types = (Episode,)
    server_url = 'http://www.addic7ed.com/'
    subtitle_class = Addic7edSubtitle

    def __init__(self, username=None, password=None):
        if any((username, password)) and not all((username, password)):
            raise ConfigurationError('Username and password must be specified')

        self.username = username
        self.password = password
        self.logged_in = False
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/%s' % __short_version__

        # login
        if self.username and self.password:
            logger.info('Logging in')
            data = {'username': self.username, 'password': self.password, 'Submit': 'Log in'}
            r = self.session.post(self.server_url + 'dologin.php', data, allow_redirects=False, timeout=10)

            if r.status_code != 302:
                raise AuthenticationError(self.username)

            logger.debug('Logged in')
            self.logged_in = True

    def terminate(self):
        # logout
        if self.logged_in:
            logger.info('Logging out')
            r = self.session.get(self.server_url + 'logout.php', timeout=10)
            r.raise_for_status()
            logger.debug('Logged out')
            self.logged_in = False

        self.session.close()

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME)
    def _get_show_ids(self):
        """Get the ``dict`` of show ids per series by querying the `shows.php` page.

        :return: show id per series, lower case and without quotes.
        :rtype: dict

        """
        # get the show page
        logger.info('Getting show ids')
        r = self.session.get(self.server_url + 'shows.php', timeout=10)
        r.raise_for_status()

        # LXML parser seems to fail when parsing Addic7ed.com HTML markup.
        # Last known version to work properly is 3.6.4 (next version, 3.7.0, fails)
        # Assuming the site's markup is bad, and stripping it down to only contain what's needed.
        show_cells = re.findall(show_cells_re, r.content)
        if show_cells:
            soup = ParserBeautifulSoup(b''.join(show_cells), ['lxml', 'html.parser'])
        else:
            # If RegEx fails, fall back to original r.content and use 'html.parser'
            soup = ParserBeautifulSoup(r.content, ['html.parser'])

        # populate the show ids
        show_ids = {}
        for show in soup.select('td.version > h3 > a[href^="/show/"]'):
            show_ids[sanitize(show.text)] = int(show['href'][6:])
        logger.debug('Found %d show ids', len(show_ids))

        return show_ids

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME)
    def _search_show_id(self, series, year=None):
        """Search the show id from the `series` and `year`.

        :param str series: series of the episode.
        :param year: year of the series, if any.
        :type year: int
        :return: the show id, if found.
        :rtype: int

        """
        # addic7ed doesn't support search with quotes
        series = series.replace('\'', ' ')

        # build the params
        series_year = '%s %d' % (series, year) if year is not None else series
        params = {'search': series_year, 'Submit': 'Search'}

        # make the search
        logger.info('Searching show ids with %r', params)
        r = self.session.get(self.server_url + 'srch.php', params=params, timeout=10)
        r.raise_for_status()
        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])

        # get the suggestion
        suggestion = soup.select('span.titulo > a[href^="/show/"]')
        if not suggestion:
            logger.warning('Show id not found: no suggestion')
            return None
        if not sanitize(suggestion[0].i.text.replace('\'', ' ')) == sanitize(series_year):
            logger.warning('Show id not found: suggestion does not match')
            return None
        show_id = int(suggestion[0]['href'][6:])
        logger.debug('Found show id %d', show_id)

        return show_id

    def get_show_id(self, series, year=None, country_code=None):
        """Get the best matching show id for `series`, `year` and `country_code`.

        First search in the result of :meth:`_get_show_ids` and fallback on a search with :meth:`_search_show_id`.

        :param str series: series of the episode.
        :param year: year of the series, if any.
        :type year: int
        :param country_code: country code of the series, if any.
        :type country_code: str
        :return: the show id, if found.
        :rtype: int

        """
        series_sanitized = sanitize(series).lower()
        show_ids = self._get_show_ids()
        show_id = None

        # attempt with country
        if not show_id and country_code:
            logger.debug('Getting show id with country')
            show_id = show_ids.get('%s %s' % (series_sanitized, country_code.lower()))

        # attempt with year
        if not show_id and year:
            logger.debug('Getting show id with year')
            show_id = show_ids.get('%s %d' % (series_sanitized, year))

        # attempt clean
        if not show_id:
            logger.debug('Getting show id')
            show_id = show_ids.get(series_sanitized)

        # search as last resort
        if not show_id:
            logger.warning('Series %s not found in show ids', series)
            show_id = self._search_show_id(series)

        return show_id

    def query(self, show_id, series, season, year=None, country=None):
        # get the page of the season of the show
        logger.info('Getting the page of show id %d, season %d', show_id, season)
        r = self.session.get(self.server_url + 'show/%d' % show_id, params={'season': season}, timeout=10)
        r.raise_for_status()

        if not r.content:
            # Provider returns a status of 304 Not Modified with an empty content
            # raise_for_status won't raise exception for that status code
            logger.debug('No data returned from provider')
            return []

        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])

        # loop over subtitle rows
        match = series_year_re.match(soup.select('#header font')[0].text.strip()[:-10])
        series = match.group('series')
        year = int(match.group('year')) if match.group('year') else None
        subtitles = []
        for row in soup.select('tr.epeven'):
            cells = row('td')

            # ignore incomplete subtitles
            status = cells[5].text
            if status != 'Completed':
                logger.debug('Ignoring subtitle with status %s', status)
                continue

            # read the item
            language = Language.fromaddic7ed(cells[3].text)
            hearing_impaired = bool(cells[6].text)
            page_link = self.server_url + cells[2].a['href'][1:]
            season = int(cells[0].text)
            episode = int(cells[1].text)
            title = cells[2].text
            version = cells[4].text
            download_link = cells[9].a['href'][1:]

            subtitle = self.subtitle_class(language, hearing_impaired, page_link, series, season, episode, title, year,
                                           version, download_link)
            logger.debug('Found subtitle %r', subtitle)
            subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        # lookup show_id
        titles = [video.series] + video.alternative_series
        show_id = None
        for title in titles:
            show_id = self.get_show_id(title, video.year)
            if show_id is not None:
                break

        # query for subtitles with the show_id
        if show_id is not None:
            subtitles = [s for s in self.query(show_id, title, video.season, video.year)
                         if s.language in languages and s.episode == video.episode]
            if subtitles:
                return subtitles
        else:
            logger.error('No show id found for %r (%r)', video.series, {'year': video.year})

        return []

    def download_subtitle(self, subtitle):
        # download the subtitle
        logger.info('Downloading subtitle %r', subtitle)
        r = self.session.get(self.server_url + subtitle.download_link, headers={'Referer': subtitle.page_link},
                             timeout=10)
        r.raise_for_status()

        if not r.content:
            # Provider returns a status of 304 Not Modified with an empty content
            # raise_for_status won't raise exception for that status code
            logger.debug('Unable to download subtitle. No data returned from provider')
            return

        # detect download limit exceeded
        if r.headers['Content-Type'] == 'text/html':
            raise DownloadLimitExceeded

        subtitle.content = fix_line_ending(r.content)

# -*- coding: utf-8 -*-
import bisect
from collections import defaultdict
import io
import json
import logging
import zipfile

from babelfish import Language
from guessit import guessit
from requests import Session

from . import ParserBeautifulSoup, Provider
from .. import __short_version__
from ..cache import SHOW_EXPIRATION_TIME, region
from ..exceptions import AuthenticationError, ConfigurationError, ProviderError
from ..subtitle import Subtitle, fix_line_ending, guess_matches
from ..utils import sanitize
from ..video import Episode, Movie

logger = logging.getLogger(__name__)


class SubsCenterSubtitle(Subtitle):
    """SubsCenter Subtitle."""
    provider_name = 'subscenter'

    def __init__(self, language, hearing_impaired, page_link, series, season, episode, title, subtitle_id, subtitle_key,
                 downloaded, releases):
        super(SubsCenterSubtitle, self).__init__(language, hearing_impaired, page_link)
        self.series = series
        self.season = season
        self.episode = episode
        self.title = title
        self.subtitle_id = subtitle_id
        self.subtitle_key = subtitle_key
        self.downloaded = downloaded
        self.releases = releases

    @property
    def id(self):
        return str(self.subtitle_id)

    def get_matches(self, video):
        matches = set()

        # episode
        if isinstance(video, Episode):
            # series
            if video.series and sanitize(self.series) == sanitize(video.series):
                matches.add('series')
            # season
            if video.season and self.season == video.season:
                matches.add('season')
            # episode
            if video.episode and self.episode == video.episode:
                matches.add('episode')
            # guess
            for release in self.releases:
                matches |= guess_matches(video, guessit(release, {'type': 'episode'}))
        # movie
        elif isinstance(video, Movie):
            # guess
            for release in self.releases:
                matches |= guess_matches(video, guessit(release, {'type': 'movie'}))

        # title
        if video.title and sanitize(self.title) == sanitize(video.title):
            matches.add('title')

        return matches


class SubsCenterProvider(Provider):
    """SubsCenter Provider."""
    languages = {Language.fromalpha2(l) for l in ['he']}
    server_url = 'http://www.subscenter.co/he/'

    def __init__(self, username=None, password=None):
        if username is not None and password is None or username is None and password is not None:
            raise ConfigurationError('Username and password must be specified')

        self.session = None
        self.username = username
        self.password = password
        self.logged_in = False

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/{}'.format(__short_version__)

        # login
        if self.username is not None and self.password is not None:
            logger.debug('Logging in')
            url = self.server_url + 'subscenter/accounts/login/'

            # retrieve CSRF token
            self.session.get(url)
            csrf_token = self.session.cookies['csrftoken']

            # actual login
            data = {'username': self.username, 'password': self.password, 'csrfmiddlewaretoken': csrf_token}
            r = self.session.post(url, data, allow_redirects=False, timeout=10)

            if r.status_code != 302:
                raise AuthenticationError(self.username)

            logger.info('Logged in')
            self.logged_in = True

    def terminate(self):
        # logout
        if self.logged_in:
            logger.info('Logging out')
            r = self.session.get(self.server_url + 'subscenter/accounts/logout/', timeout=10)
            r.raise_for_status()
            logger.info('Logged out')
            self.logged_in = False

        self.session.close()

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME)
    def _search_url_titles(self, title):
        """Search the URL titles by kind for the given `title`.

        :param str title: title to search for.
        :return: the URL titles by kind.
        :rtype: collections.defaultdict

        """
        # make the search
        logger.info('Searching title name for %r', title)
        r = self.session.get(self.server_url + 'subtitle/search/', params={'q': title}, timeout=10)
        r.raise_for_status()

        # check for redirections
        if r.history and all([h.status_code == 302 for h in r.history]):
            logger.debug('Redirected to the subtitles page')
            links = [r.url]
        else:
            # get the suggestions (if needed)
            soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])
            links = [link.attrs['href'] for link in soup.select('#processes div.generalWindowTop a')]
            logger.debug('Found %d suggestions', len(links))

        url_titles = defaultdict(list)
        for link in links:
            parts = link.split('/')
            url_titles[parts[-3]].append(parts[-2])

        return url_titles

    def query(self, title, season=None, episode=None):
        # search for the url title
        url_titles = self._search_url_titles(title)

        # episode
        if season and episode:
            if 'series' not in url_titles:
                logger.error('No URL title found for series %r', title)
                return []
            url_title = url_titles['series'][0]
            logger.debug('Using series title %r', url_title)
            url = self.server_url + 'cst/data/series/sb/{}/{}/{}/'.format(url_title, season, episode)
            page_link = self.server_url + 'subtitle/series/{}/{}/{}/'.format(url_title, season, episode)
        else:
            if 'movie' not in url_titles:
                logger.error('No URL title found for movie %r', title)
                return []
            url_title = url_titles['movie'][0]
            logger.debug('Using movie title %r', url_title)
            url = self.server_url + 'cst/data/movie/sb/{}/'.format(url_title)
            page_link = self.server_url + 'subtitle/movie/{}/'.format(url_title)

        # get the list of subtitles
        logger.debug('Getting the list of subtitles')
        r = self.session.get(url)
        r.raise_for_status()
        results = json.loads(r.text)

        # loop over results
        subtitles = {}
        for language_code, language_data in results.items():
            for quality_data in language_data.values():
                for quality, subtitles_data in quality_data.items():
                    for subtitle_item in subtitles_data.values():
                        # read the item
                        language = Language.fromalpha2(language_code)
                        hearing_impaired = bool(subtitle_item['hearing_impaired'])
                        subtitle_id = subtitle_item['id']
                        subtitle_key = subtitle_item['key']
                        downloaded = subtitle_item['downloaded']
                        release = subtitle_item['subtitle_version']

                        # add the release and increment downloaded count if we already have the subtitle
                        if subtitle_id in subtitles:
                            logger.debug('Found additional release %r for subtitle %d', release, subtitle_id)
                            bisect.insort_left(subtitles[subtitle_id].releases, release)  # deterministic order
                            subtitles[subtitle_id].downloaded += downloaded
                            continue

                        # otherwise create it
                        subtitle = SubsCenterSubtitle(language, hearing_impaired, page_link, title, season, episode,
                                                      title, subtitle_id, subtitle_key, downloaded, [release])
                        logger.debug('Found subtitle %r', subtitle)
                        subtitles[subtitle_id] = subtitle

        return subtitles.values()

    def list_subtitles(self, video, languages):
        season = episode = None
        title = video.title

        if isinstance(video, Episode):
            title = video.series
            season = video.season
            episode = video.episode

        return [s for s in self.query(title, season, episode) if s.language in languages]

    def download_subtitle(self, subtitle):
        # download
        url = self.server_url + 'subtitle/download/{}/{}/'.format(subtitle.language.alpha2, subtitle.subtitle_id)
        params = {'v': subtitle.releases[0], 'key': subtitle.subtitle_key}
        r = self.session.get(url, params=params, headers={'Referer': subtitle.page_link}, timeout=10)
        r.raise_for_status()

        # open the zip
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            # remove some filenames from the namelist
            namelist = [n for n in zf.namelist() if not n.endswith('.txt')]
            if len(namelist) > 1:
                raise ProviderError('More than one file to unzip')

            subtitle.content = fix_line_ending(zf.read(namelist[0]))

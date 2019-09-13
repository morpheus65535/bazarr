# -*- coding: utf-8 -*-
import io
import logging
import re
from zipfile import ZipFile

from babelfish import Language, language_converters
from guessit import guessit
from requests import Session

from . import ParserBeautifulSoup, Provider
from .. import __short_version__
from ..cache import EPISODE_EXPIRATION_TIME, SHOW_EXPIRATION_TIME, region
from ..exceptions import ProviderError
from ..score import get_equivalent_release_groups
from ..subtitle import Subtitle, fix_line_ending, guess_matches
from ..utils import sanitize, sanitize_release_group
from ..video import Episode

logger = logging.getLogger(__name__)

language_converters.register('tvsubtitles = subliminal.converters.tvsubtitles:TVsubtitlesConverter')

link_re = re.compile(r'^(?P<series>.+?)(?: \(?\d{4}\)?| \((?:US|UK)\))? \((?P<first_year>\d{4})-\d{4}\)$')
episode_id_re = re.compile(r'^episode-\d+\.html$')


class TVsubtitlesSubtitle(Subtitle):
    """TVsubtitles Subtitle."""
    provider_name = 'tvsubtitles'

    def __init__(self, language, page_link, subtitle_id, series, season, episode, year, rip, release):
        super(TVsubtitlesSubtitle, self).__init__(language, page_link=page_link)
        self.subtitle_id = subtitle_id
        self.series = series
        self.season = season
        self.episode = episode
        self.year = year
        self.rip = rip
        self.release = release

    @property
    def id(self):
        return str(self.subtitle_id)

    def get_matches(self, video):
        matches = set()

        # series
        if video.series and sanitize(self.series) == sanitize(video.series):
            matches.add('series')
        # season
        if video.season and self.season == video.season:
            matches.add('season')
        # episode
        if video.episode and self.episode == video.episode:
            matches.add('episode')
        # year
        if video.original_series and self.year is None or video.year and video.year == self.year:
            matches.add('year')
        # release_group
        if (video.release_group and self.release and
                any(r in sanitize_release_group(self.release)
                    for r in get_equivalent_release_groups(sanitize_release_group(video.release_group)))):
            matches.add('release_group')
        # other properties
        if self.release:
            matches |= guess_matches(video, guessit(self.release, {'type': 'episode'}), partial=True)
        if self.rip:
            matches |= guess_matches(video, guessit(self.rip), partial=True)

        return matches


class TVsubtitlesProvider(Provider):
    """TVsubtitles Provider."""
    languages = {Language('por', 'BR')} | {Language(l) for l in [
        'ara', 'bul', 'ces', 'dan', 'deu', 'ell', 'eng', 'fin', 'fra', 'hun', 'ita', 'jpn', 'kor', 'nld', 'pol', 'por',
        'ron', 'rus', 'spa', 'swe', 'tur', 'ukr', 'zho'
    ]}
    video_types = (Episode,)
    server_url = 'http://www.tvsubtitles.net/'

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/%s' % __short_version__

    def terminate(self):
        self.session.close()

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME)
    def search_show_id(self, series, year=None):
        """Search the show id from the `series` and `year`.

        :param str series: series of the episode.
        :param year: year of the series, if any.
        :type year: int
        :return: the show id, if any.
        :rtype: int

        """
        # make the search
        logger.info('Searching show id for %r', series)
        r = self.session.post(self.server_url + 'search.php', data={'q': series}, timeout=10)
        r.raise_for_status()

        # get the series out of the suggestions
        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])
        show_id = None
        for suggestion in soup.select('div.left li div a[href^="/tvshow-"]'):
            match = link_re.match(suggestion.text)
            if not match:
                logger.error('Failed to match %s', suggestion.text)
                continue

            if match.group('series').lower() == series.lower():
                if year is not None and int(match.group('first_year')) != year:
                    logger.debug('Year does not match')
                    continue
                show_id = int(suggestion['href'][8:-5])
                logger.debug('Found show id %d', show_id)
                break

        return show_id

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

        return episode_ids

    def query(self, series, season, episode, year=None):
        # search the show id
        show_id = self.search_show_id(series, year)
        if show_id is None:
            logger.error('No show id found for %r (%r)', series, {'year': year})
            return []

        # get the episode ids
        episode_ids = self.get_episode_ids(show_id, season)
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
            release = row.find('p', title='release').text.strip() or None

            subtitle = TVsubtitlesSubtitle(language, page_link, subtitle_id, series, season, episode, year, rip,
                                           release)
            logger.debug('Found subtitle %s', subtitle)
            subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        return [s for s in self.query(video.series, video.season, video.episode, video.year) if s.language in languages]

    def download_subtitle(self, subtitle):
        # download as a zip
        logger.info('Downloading subtitle %r', subtitle)
        r = self.session.get(self.server_url + 'download-%d.html' % subtitle.subtitle_id, timeout=10)
        r.raise_for_status()

        # open the zip
        with ZipFile(io.BytesIO(r.content)) as zf:
            if len(zf.namelist()) > 1:
                raise ProviderError('More than one file to unzip')

            subtitle.content = fix_line_ending(zf.read(zf.namelist()[0]))

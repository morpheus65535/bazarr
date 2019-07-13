# -*- coding: utf-8 -*-
import logging
import re

from subzero.language import Language
from guessit import guessit
from requests import Session

from subliminal.providers import ParserBeautifulSoup, Provider
from subliminal import __short_version__
from subliminal.cache import SHOW_EXPIRATION_TIME, region
from subliminal.exceptions import AuthenticationError, ConfigurationError
from subliminal.score import get_equivalent_release_groups
from subliminal.subtitle import Subtitle, fix_line_ending, guess_matches
from subliminal.utils import sanitize, sanitize_release_group
from subliminal.video import Episode

logger = logging.getLogger(__name__)
article_re = re.compile(r'^([A-Za-z]{1,3}) (.*)$')
episode_re = re.compile(r'^(\d+)(-(\d+))*$')


class XSubsSubtitle(Subtitle):
    """XSubs Subtitle."""
    provider_name = 'xsubs'

    def __init__(self, language, page_link, series, season, episode, year, title, version, download_link):
        super(XSubsSubtitle, self).__init__(language, page_link=page_link)
        self.series = series
        self.season = season
        self.episode = episode
        self.year = year
        self.title = title
        self.version = version
        self.download_link = download_link
        self.hearing_impaired = None
        self.encoding = 'windows-1253'

    @property
    def id(self):
        return self.download_link

    def get_matches(self, video):
        matches = set()

        if isinstance(video, Episode):
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
            # other properties
            matches |= guess_matches(video, guessit(self.version, {'type': 'episode'}), partial=True)

        return matches


class XSubsProvider(Provider):
    """XSubs Provider."""
    languages = {Language(l) for l in ['ell']}
    video_types = (Episode,)
    server_url = 'http://xsubs.tv'
    sign_in_url = '/xforum/account/signin/'
    sign_out_url = '/xforum/account/signout/'
    all_series_url = '/series/all.xml'
    series_url = '/series/{:d}/main.xml'
    season_url = '/series/{show_id:d}/{season:d}.xml'
    page_link = '/ice/xsw.xml?srsid={show_id:d}#{season_id:d};{season:d};{episode:d}'
    download_link = '/xthru/getsub/{:d}'
    subtitle_class = XSubsSubtitle

    def __init__(self, username=None, password=None):
        if any((username, password)) and not all((username, password)):
            raise ConfigurationError('Username and password must be specified')

        self.username = username
        self.password = password
        self.logged_in = False
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/{}'.format(__short_version__)

        # login
        if self.username and self.password:
            logger.info('Logging in')
            self.session.get(self.server_url + self.sign_in_url)
            data = {'username': self.username,
                    'password': self.password,
                    'csrfmiddlewaretoken': self.session.cookies['csrftoken']}
            r = self.session.post(self.server_url + self.sign_in_url, data, allow_redirects=False, timeout=10)

            if r.status_code != 302:
                raise AuthenticationError(self.username)

            logger.debug('Logged in')
            self.logged_in = True

    def terminate(self):
        # logout
        if self.logged_in:
            logger.info('Logging out')
            r = self.session.get(self.server_url + self.sign_out_url, timeout=10)
            r.raise_for_status()
            logger.debug('Logged out')
            self.logged_in = False

        self.session.close()

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME, should_cache_fn=lambda value: value)
    def _get_show_ids(self):
        # get the shows page
        logger.info('Getting show ids')
        r = self.session.get(self.server_url + self.all_series_url, timeout=10)
        r.raise_for_status()

        if not r.content:
            logger.debug('No data returned from provider')
            return []

        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])

        # populate the show ids
        show_ids = {}
        for show_category in soup.findAll('seriesl'):
            if show_category.attrs['category'] == u'Σειρές':
                for show in show_category.findAll('series'):
                    show_ids[sanitize(show.text)] = int(show['srsid'])
                break
        logger.debug('Found %d show ids', len(show_ids))

        return show_ids

    def get_show_id(self, series_names, year=None):
        series_sanitized_names = []
        for name in series_names:
            sanitized_name = sanitize(name)
            series_sanitized_names.append(sanitized_name)
            alternative_name = _get_alternative_name(sanitized_name)
            if alternative_name:
                series_sanitized_names.append(alternative_name)

        show_ids = self._get_show_ids()
        show_id = None

        for series_sanitized in series_sanitized_names:
            # attempt with year
            if year:
                logger.debug('Getting show id with year')
                show_id = show_ids.get('{series} {year:d}'.format(series=series_sanitized, year=year))

            # attempt with article at the end
            if not show_id and year:
                logger.debug('Getting show id with year in brackets')
                show_id = show_ids.get('{series} [{year:d}]'.format(series=series_sanitized, year=year))

            # attempt clean
            if not show_id:
                logger.debug('Getting show id')
                show_id = show_ids.get(series_sanitized)

            if show_id:
                break

        return int(show_id) if show_id else None

    def query(self, show_id, series, season, year=None, country=None):
        # get the season list of the show
        logger.info('Getting the season list of show id %d', show_id)
        r = self.session.get(self.server_url + self.series_url.format(show_id), timeout=10)
        r.raise_for_status()

        if not r.content:
            logger.debug('No data returned from provider')
            return []

        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])

        series = soup.find('name').text

        # loop over season rows
        seasons = soup.findAll('series_group')
        season_id = None

        for season_row in seasons:
            try:
                parsed_season = int(season_row['ssnnum'])
                if parsed_season == season:
                    season_id = int(season_row['ssnid'])
                    break
            except (ValueError, TypeError):
                continue

        if season_id is None:
            logger.debug('Season not found in provider')
            return []

        # get the subtitle list of the season
        logger.info('Getting the subtitle list of season %d', season)
        r = self.session.get(self.server_url + self.season_url.format(show_id=show_id, season=season_id), timeout=10)
        r.raise_for_status()

        if not r.content:
            logger.debug('No data returned from provider')
            return []

        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])

        subtitles = []
        # loop over episode rows
        for subtitle_group in soup.findAll('subg'):
            # read the episode info
            episode_info = subtitle_group.find('etitle')
            if episode_info is None:
                continue

            episodes = []
            episode_match = episode_re.match(episode_info['number'])
            if episode_match:
                episodes = [int(e) for e in [episode_match.group(1), episode_match.group(3)] if e]

            subtitle_info = subtitle_group.find('sgt')
            if subtitle_info is None:
                continue

            season = int(subtitle_info['ssnnum'])
            episode_id = int(subtitle_info['epsid'])

            # filter out unreleased subtitles
            for subs_tag in subtitle_group.findAll('sr'):
                if subs_tag['published_on'] == '':
                    continue

                page_link = self.server_url + self.page_link.format(show_id=show_id, season_id=season_id,
                                                                    season=season, episode=episode_id)
                title = episode_info['title']
                version = subs_tag.fmt.text + ' ' + subs_tag.team.text
                download_link = self.server_url + self.download_link.format(int(subs_tag['rlsid']))

                for episode in episodes:
                    subtitle = self.subtitle_class(Language.fromalpha2('el'), page_link, series, season, episode, year,
                                                   title, version, download_link)
                    logger.debug('Found subtitle %r', subtitle)
                    subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        if isinstance(video, Episode):
            # lookup show_id
            titles = [video.series] + video.alternative_series
            show_id = self.get_show_id(titles, video.year)

            # query for subtitles with the show_id
            if show_id:
                subtitles = [s for s in self.query(show_id, video.series, video.season, video.year)
                             if s.language in languages and s.season == video.season and s.episode == video.episode]
                if subtitles:
                    return subtitles
            else:
                logger.error('No show id found for %r (%r)', video.series, {'year': video.year})

        return []

    def download_subtitle(self, subtitle):
        if isinstance(subtitle, XSubsSubtitle):
            # download the subtitle
            logger.info('Downloading subtitle %r', subtitle)
            r = self.session.get(subtitle.download_link, headers={'Referer': subtitle.page_link},
                                 timeout=10)
            r.raise_for_status()

            if not r.content:
                logger.debug('Unable to download subtitle. No data returned from provider')
                return

            subtitle.content = fix_line_ending(r.content)


def _get_alternative_name(series):
    article_match = article_re.match(series)
    if article_match:
        return '{series} {article}'.format(series=article_match.group(2), article=article_match.group(1))

    return None

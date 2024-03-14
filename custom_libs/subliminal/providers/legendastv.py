# -*- coding: utf-8 -*-
import io
import json
import logging
import os
import re

from babelfish import Language, language_converters
from datetime import datetime, timedelta
from dogpile.cache.api import NO_VALUE
from guessit import guessit
import pytz
import rarfile
from rarfile import RarFile, is_rarfile
from rebulk.loose import ensure_list
from requests import Session
from zipfile import ZipFile, is_zipfile

from . import ParserBeautifulSoup, Provider
from ..cache import SHOW_EXPIRATION_TIME, region
from ..exceptions import AuthenticationError, ConfigurationError, ProviderError, ServiceUnavailable
from ..matches import guess_matches
from ..subtitle import SUBTITLE_EXTENSIONS, Subtitle, fix_line_ending
from ..utils import sanitize
from ..video import Episode, Movie

logger = logging.getLogger(__name__)

language_converters.register('legendastv = subliminal.converters.legendastv:LegendasTVConverter')

# Configure :mod:`rarfile` to use the same path separator as :mod:`zipfile`
rarfile.PATH_SEP = '/'

#: Conversion map for types
type_map = {'M': 'movie', 'S': 'episode', 'C': 'episode'}

#: BR title season parsing regex
season_re = re.compile(r' - (?P<season>\d+)(\xaa|a|st|nd|rd|th) (temporada|season)', re.IGNORECASE)

#: Downloads parsing regex
downloads_re = re.compile(r'(?P<downloads>\d+) downloads')

#: Rating parsing regex
rating_re = re.compile(r'nota (?P<rating>\d+)')

#: Timestamp parsing regex
timestamp_re = re.compile(r'(?P<day>\d+)/(?P<month>\d+)/(?P<year>\d+) - (?P<hour>\d+):(?P<minute>\d+)')

#: Title with year/country regex
title_re = re.compile(r'^(?P<series>.*?)(?: \((?:(?P<year>\d{4})|(?P<country>[A-Z]{2}))\))?$')

#: Cache key for releases
releases_key = __name__ + ':releases|{archive_id}|{archive_name}'


class LegendasTVArchive(object):
    """LegendasTV Archive.

    :param str id: identifier.
    :param str name: name.
    :param bool pack: contains subtitles for multiple episodes.
    :param bool pack: featured.
    :param str link: link.
    :param int downloads: download count.
    :param int rating: rating (0-10).
    :param timestamp: timestamp.
    :type timestamp: datetime.datetime
    """

    def __init__(self, id, name, pack, featured, link, downloads=0, rating=0, timestamp=None):
        #: Identifier
        self.id = id

        #: Name
        self.name = name

        #: Pack
        self.pack = pack

        #: Featured
        self.featured = featured

        #: Link
        self.link = link

        #: Download count
        self.downloads = downloads

        #: Rating (0-10)
        self.rating = rating

        #: Timestamp
        self.timestamp = timestamp

        #: Compressed content as :class:`rarfile.RarFile` or :class:`zipfile.ZipFile`
        self.content = None

    def __repr__(self):
        return '<%s [%s] %r>' % (self.__class__.__name__, self.id, self.name)


class LegendasTVSubtitle(Subtitle):
    """LegendasTV Subtitle."""

    provider_name = 'legendastv'

    def __init__(self, language, type, title, year, imdb_id, season, archive, name):
        super(LegendasTVSubtitle, self).__init__(language, page_link=archive.link)
        self.type = type
        self.title = title
        self.year = year
        self.imdb_id = imdb_id
        self.season = season
        self.archive = archive
        self.name = name

    @property
    def id(self):
        return '%s-%s' % (self.archive.id, self.name.lower())

    @property
    def info(self):
        return self.name

    def get_matches(self, video, hearing_impaired=False):
        matches = guess_matches(video, {
            'title': self.title,
            'year': self.year
        })

        # episode
        if isinstance(video, Episode) and self.type == 'episode':
            # imdb_id
            if video.series_imdb_id and self.imdb_id == video.series_imdb_id:
                matches.add('series_imdb_id')

        # movie
        elif isinstance(video, Movie) and self.type == 'movie':
            # imdb_id
            if video.imdb_id and self.imdb_id == video.imdb_id:
                matches.add('imdb_id')

        # name
        matches |= guess_matches(video, guessit(self.name, {'type': self.type}))

        return matches


class LegendasTVProvider(Provider):
    """LegendasTV Provider.

    :param str username: username.
    :param str password: password.
    """

    languages = {Language.fromlegendastv(l) for l in language_converters['legendastv'].codes}
    server_url = 'http://legendas.tv/'
    subtitle_class = LegendasTVSubtitle

    def __init__(self, username=None, password=None):

        # Provider needs UNRAR installed. If not available raise ConfigurationError
        try:
            rarfile.custom_check([rarfile.UNRAR_TOOL], True)
        except rarfile.RarExecError:
            raise ConfigurationError('UNRAR tool not available')

        if any((username, password)) and not all((username, password)):
            raise ConfigurationError('Username and password must be specified')

        self.username = username
        self.password = password
        self.logged_in = False
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = self.user_agent

        # login
        if self.username and self.password:
            logger.info('Logging in')
            data = {'_method': 'POST', 'data[User][username]': self.username, 'data[User][password]': self.password}
            r = self.session.post(self.server_url + 'login', data, allow_redirects=False, timeout=10)
            raise_for_status(r)

            soup = ParserBeautifulSoup(r.content, ['html.parser'])
            if soup.find('div', {'class': 'alert-error'}, string=re.compile(u'Usuário ou senha inválidos')):
                raise AuthenticationError(self.username)

            logger.debug('Logged in')
            self.logged_in = True

    def terminate(self):
        # logout
        if self.logged_in:
            logger.info('Logging out')
            r = self.session.get(self.server_url + 'users/logout', allow_redirects=False, timeout=10)
            raise_for_status(r)
            logger.debug('Logged out')
            self.logged_in = False

        self.session.close()

    @staticmethod
    def is_valid_title(title, title_id, sanitized_title, season, year):
        """Check if is a valid title."""
        sanitized_result = sanitize(title['title'])
        if sanitized_result != sanitized_title:
            logger.debug("Mismatched title, discarding title %d (%s)",
                         title_id, sanitized_result)
            return

        # episode type
        if season:
            # discard mismatches on type
            if title['type'] != 'episode':
                logger.debug("Mismatched 'episode' type, discarding title %d (%s)", title_id, sanitized_result)
                return

            # discard mismatches on season
            if 'season' not in title or title['season'] != season:
                logger.debug('Mismatched season %s, discarding title %d (%s)',
                             title.get('season'), title_id, sanitized_result)
                return
        # movie type
        else:
            # discard mismatches on type
            if title['type'] != 'movie':
                logger.debug("Mismatched 'movie' type, discarding title %d (%s)", title_id, sanitized_result)
                return

            # discard mismatches on year
            if year is not None and 'year' in title and title['year'] != year:
                logger.debug("Mismatched movie year, discarding title %d (%s)", title_id, sanitized_result)
                return
        return True

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME, should_cache_fn=lambda value: value)
    def search_titles(self, title, season, title_year):
        """Search for titles matching the `title`.

        For episodes, each season has it own title
        :param str title: the title to search for.
        :param int season: season of the title
        :param int title_year: year of the title
        :return: found titles.
        :rtype: dict
        """
        titles = {}
        sanitized_titles = [sanitize(title)]
        ignore_characters = {'\'', '.'}
        if any(c in title for c in ignore_characters):
            sanitized_titles.append(sanitize(title, ignore_characters=ignore_characters))

        for sanitized_title in sanitized_titles:
            # make the query
            if season:
                logger.info('Searching episode title %r for season %r', sanitized_title, season)
            else:
                logger.info('Searching movie title %r', sanitized_title)

            r = self.session.get(self.server_url + 'legenda/sugestao/{}'.format(sanitized_title), timeout=10)
            raise_for_status(r)
            results = json.loads(r.text)

            # loop over results
            for result in results:
                source = result['_source']

                # extract id
                title_id = int(source['id_filme'])

                # extract type
                title = {'type': type_map[source['tipo']]}

                # extract title, year and country
                name, year, country = title_re.match(source['dsc_nome']).groups()
                title['title'] = name

                # extract imdb_id
                if source['id_imdb'] != '0':
                    if not source['id_imdb'].startswith('tt'):
                        title['imdb_id'] = 'tt' + source['id_imdb'].zfill(7)
                    else:
                        title['imdb_id'] = source['id_imdb']

                # extract season
                if title['type'] == 'episode':
                    if source['temporada'] and source['temporada'].isdigit():
                        title['season'] = int(source['temporada'])
                    else:
                        match = season_re.search(source['dsc_nome_br'])
                        if match:
                            title['season'] = int(match.group('season'))
                        else:
                            logger.debug('No season detected for title %d (%s)', title_id, name)

                # extract year
                if year:
                    title['year'] = int(year)
                elif source['dsc_data_lancamento'] and source['dsc_data_lancamento'].isdigit():
                    # year is based on season air date hence the adjustment
                    title['year'] = int(source['dsc_data_lancamento']) - title.get('season', 1) + 1

                # add title only if is valid
                # Check against title without ignored chars
                if self.is_valid_title(title, title_id, sanitized_titles[0], season, title_year):
                    titles[title_id] = title

            logger.debug('Found %d titles', len(titles))

        return titles

    @region.cache_on_arguments(expiration_time=timedelta(minutes=15).total_seconds())
    def get_archives(self, title_id, language_code, title_type, season, episodes):
        """Get the archive list from a given `title_id`, `language_code`, `title_type`, `season` and `episode`.

        :param int title_id: title id.
        :param int language_code: language code.
        :param str title_type: episode or movie
        :param int season: season
        :param list episodes: episodes
        :return: the archives.
        :rtype: list of :class:`LegendasTVArchive`

        """
        archives = []
        page = 0
        while True:
            # get the archive page
            url = self.server_url + 'legenda/busca/-/{language}/-/{page}/{title}'.format(
                language=language_code, page=page, title=title_id)
            r = self.session.get(url)
            raise_for_status(r)

            # parse the results
            soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])
            for archive_soup in soup.select('div.list_element > article > div > div.f_left'):
                # create archive
                archive = LegendasTVArchive(archive_soup.a['href'].split('/')[2],
                                            archive_soup.a.text,
                                            'pack' in archive_soup.parent['class'],
                                            'destaque' in archive_soup.parent['class'],
                                            self.server_url + archive_soup.a['href'][1:])
                # clean name of path separators and pack flags
                clean_name = archive.name.replace('/', '-')
                if archive.pack and clean_name.startswith('(p)'):
                    clean_name = clean_name[3:]

                # guess from name
                guess = guessit(clean_name, {'type': title_type})

                # episode
                if season and episodes:
                    # discard mismatches on episode in non-pack archives

                    # Guessit may return int for single episode or list for multi-episode
                    # Check if archive name has multiple episodes releases on it
                    if not archive.pack and 'episode' in guess:
                        wanted_episode = set(episodes)
                        archive_episode = set(ensure_list(guess['episode']))

                        if not wanted_episode.intersection(archive_episode):
                            logger.debug('Mismatched episode %s, discarding archive: %s', guess['episode'], clean_name)
                            continue

                # extract text containing downloads, rating and timestamp
                data_text = archive_soup.find('p', class_='data').text

                # match downloads
                archive.downloads = int(downloads_re.search(data_text).group('downloads'))

                # match rating
                match = rating_re.search(data_text)
                if match:
                    archive.rating = int(match.group('rating'))

                # match timestamp and validate it
                time_data = {k: int(v) for k, v in timestamp_re.search(data_text).groupdict().items()}
                archive.timestamp = pytz.timezone('America/Sao_Paulo').localize(datetime(**time_data))
                if archive.timestamp > datetime.utcnow().replace(tzinfo=pytz.utc):
                    raise ProviderError('Archive timestamp is in the future')

                # add archive
                logger.info('Found archive for title %d and language %d at page %s: %s',
                            title_id, language_code, page, archive)
                archives.append(archive)

            # stop on last page
            if soup.find('a', attrs={'class': 'load_more'}, string='carregar mais') is None:
                break

            # increment page count
            page += 1

        logger.debug('Found %d archives', len(archives))

        return archives

    def download_archive(self, archive):
        """Download an archive's :attr:`~LegendasTVArchive.content`.

        :param archive: the archive to download :attr:`~LegendasTVArchive.content` of.
        :type archive: :class:`LegendasTVArchive`

        """
        logger.info('Downloading archive %s', archive.id)
        r = self.session.get(self.server_url + 'downloadarquivo/{}'.format(archive.id))
        raise_for_status(r)

        # open the archive
        archive_stream = io.BytesIO(r.content)
        if is_rarfile(archive_stream):
            logger.debug('Identified rar archive')
            archive.content = RarFile(archive_stream)
        elif is_zipfile(archive_stream):
            logger.debug('Identified zip archive')
            archive.content = ZipFile(archive_stream)
        else:
            raise ValueError('Not a valid archive')

    def query(self, language, title, season=None, episodes=None, year=None):
        # search for titles
        titles = self.search_titles(title, season, year)

        subtitles = []
        # iterate over titles
        for title_id, t in titles.items():

            logger.info('Getting archives for title %d and language %d', title_id, language.legendastv)
            archives = self.get_archives(title_id, language.legendastv, t['type'], season, episodes or [])
            if not archives:
                logger.info('No archives found for title %d and language %d', title_id, language.legendastv)

            # iterate over title's archives
            for a in archives:

                # compute an expiration time based on the archive timestamp
                expiration_time = (datetime.utcnow().replace(tzinfo=pytz.utc) - a.timestamp).total_seconds()

                # attempt to get the releases from the cache
                cache_key = releases_key.format(archive_id=a.id, archive_name=a.name)
                releases = region.get(cache_key, expiration_time=expiration_time)

                # the releases are not in cache or cache is expired
                if releases == NO_VALUE:
                    logger.info('Releases not found in cache')

                    # download archive
                    self.download_archive(a)

                    # extract the releases
                    releases = []
                    for name in a.content.namelist():
                        # discard the legendastv file
                        if name.startswith('Legendas.tv'):
                            continue

                        # discard hidden files
                        if os.path.split(name)[-1].startswith('.'):
                            continue

                        # discard non-subtitle files
                        if not name.lower().endswith(SUBTITLE_EXTENSIONS):
                            continue

                        releases.append(name)

                    # cache the releases
                    region.set(cache_key, releases)

                # iterate over releases
                for r in releases:
                    subtitle = self.subtitle_class(language, t['type'], t['title'], t.get('year'), t.get('imdb_id'),
                                                   t.get('season'), a, r)
                    logger.debug('Found subtitle %r', subtitle)
                    subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        season = None
        episodes = []
        if isinstance(video, Episode):
            titles = [video.series] + video.alternative_series
            season = video.season
            episodes = video.episodes
        else:
            titles = [video.title] + video.alternative_titles

        for title in titles:
            subtitles = [s for l in languages for s in
                         self.query(l, title, season=season, episodes=episodes, year=video.year)]
            if subtitles:
                return subtitles

        return []

    def download_subtitle(self, subtitle):
        # download archive in case we previously hit the releases cache and didn't download it
        if subtitle.archive.content is None:
            self.download_archive(subtitle.archive)

        # extract subtitle's content
        subtitle.content = fix_line_ending(subtitle.archive.content.read(subtitle.name))


def raise_for_status(r):
    # When site is under maintaince and http status code 200.
    if 'Em breve estaremos de volta' in r.text:
        raise ServiceUnavailable
    else:
        r.raise_for_status()

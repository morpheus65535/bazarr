# coding=utf-8

import io
import logging
import re
from datetime import datetime
import dateutil.parser

import rarfile

from zipfile import ZipFile, is_zipfile
from rarfile import RarFile, is_rarfile
from babelfish import language_converters, Script
from requests import RequestException, codes as request_codes
from guessit import guessit
from subliminal_patch.http import RetryingCFSession
from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.utils import sanitize, fix_inconsistent_naming as _fix_inconsistent_naming
from subliminal.exceptions import ProviderError, AuthenticationError, ConfigurationError
from subliminal.score import get_equivalent_release_groups
from subliminal.utils import sanitize_release_group
from subliminal.subtitle import guess_matches
from subliminal.video import Episode, Movie
from subliminal.subtitle import fix_line_ending

from subzero.language import Language
from dogpile.cache.api import NO_VALUE
from subliminal.cache import region

# parsing regex definitions
title_re = re.compile(r'(?P<title>(?:.+(?= [Aa][Kk][Aa] ))|.+)(?:(?:.+)(?P<altitle>(?<= [Aa][Kk][Aa] ).+))?')


def fix_inconsistent_naming(title):
    """Fix titles with inconsistent naming using dictionary and sanitize them.

    :param str title: original title.
    :return: new title.
    :rtype: str

    """
    return _fix_inconsistent_naming(title, {"DC's Legends of Tomorrow": "Legends of Tomorrow",
                                            "Marvel's Jessica Jones": "Jessica Jones"})


logger = logging.getLogger(__name__)

# Configure :mod:`rarfile` to use the same path separator as :mod:`zipfile`
rarfile.PATH_SEP = '/'

language_converters.register('titlovi = subliminal_patch.converters.titlovi:TitloviConverter')


class TitloviSubtitle(Subtitle):
    provider_name = 'titlovi'

    def __init__(self, language, download_link, sid, releases, title, alt_title=None, season=None,
                 episode=None, year=None, rating=None, download_count=None, asked_for_release_group=None, asked_for_episode=None):
        super(TitloviSubtitle, self).__init__(language)
        self.sid = sid
        self.releases = self.release_info = releases
        self.title = title
        self.alt_title = alt_title
        self.season = season
        self.episode = episode
        self.year = year
        self.download_link = download_link
        self.rating = rating
        self.download_count = download_count
        self.matches = None
        self.asked_for_release_group = asked_for_release_group
        self.asked_for_episode = asked_for_episode

    def __repr__(self):
        if self.season and self.episode:
            return '<%s "%s (%r)" s%.2de%.2d [%s:%s] ID:%r R:%.2f D:%r>' % (
                self.__class__.__name__, self.title, self.year, self.season, self.episode, self.language, self._guessed_encoding, self.sid,
                self.rating, self.download_count)
        else:
            return '<%s "%s (%r)" [%s:%s] ID:%r R:%.2f D:%r>' % (
                self.__class__.__name__, self.title, self.year,  self.language, self._guessed_encoding, self.sid, self.rating, self.download_count)

    @property
    def id(self):
        return self.sid

    def get_matches(self, video):
        matches = set()

        # handle movies and series separately
        if isinstance(video, Episode):
            # series
            if video.series and sanitize(self.title) == fix_inconsistent_naming(video.series) or sanitize(
                    self.alt_title) == fix_inconsistent_naming(video.series):
                matches.add('series')
            # year
            if video.original_series and self.year is None or video.year and video.year == self.year:
                matches.add('year')
            # season
            if video.season and self.season == video.season:
                matches.add('season')
            # episode
            if video.episode and self.episode == video.episode:
                matches.add('episode')
        # movie
        elif isinstance(video, Movie):
            # title
            if video.title and sanitize(self.title) == fix_inconsistent_naming(video.title) or sanitize(
                    self.alt_title) == fix_inconsistent_naming(video.title):
                matches.add('title')
            # year
            if video.year and self.year == video.year:
                matches.add('year')

        # rest is same for both groups

        # release_group
        if (video.release_group and self.releases and
                any(r in sanitize_release_group(self.releases)
                    for r in get_equivalent_release_groups(sanitize_release_group(video.release_group)))):
            matches.add('release_group')
        # resolution
        if video.resolution and self.releases and video.resolution in self.releases.lower():
            matches.add('resolution')
        # format
        if video.format and self.releases and video.format.lower() in self.releases.lower():
            matches.add('format')
        # other properties
        matches |= guess_matches(video, guessit(self.releases))

        self.matches = matches

        return matches


class TitloviProvider(Provider, ProviderSubtitleArchiveMixin):
    subtitle_class = TitloviSubtitle
    languages = {Language.fromtitlovi(l) for l in language_converters['titlovi'].codes} | {Language.fromietf('sr-Latn')}
    api_url = 'https://kodi.titlovi.com/api/subtitles'
    api_gettoken_url = api_url + '/gettoken'
    api_search_url = api_url + '/search'

    def __init__(self, username=None, password=None):
        if not all((username, password)):
            raise ConfigurationError('Username and password must be specified')

        self.username = username
        self.password = password

        self.session = None

        self.user_id = None
        self.login_token = None
        self.token_exp = None

    def initialize(self):
        self.session = RetryingCFSession()
        #load_verification("titlovi", self.session)

        token = region.get("titlovi_token")
        if token is not NO_VALUE:
            self.user_id, self.login_token, self.token_exp = token
            if datetime.now() > self.token_exp:
                logger.debug('Token expired')
                self.log_in()
            else:
                logger.debug('Use cached token')
        else:
            logger.debug('Token not found in cache')
            self.log_in()

    def log_in(self):
        login_params = dict(username=self.username, password=self.password, json=True)
        try:
            response = self.session.post(self.api_gettoken_url, params=login_params)
            if response.status_code == request_codes.ok:
                resp_json = response.json()
                self.login_token = resp_json.get('Token')
                self.user_id = resp_json.get('UserId')
                self.token_exp = dateutil.parser.parse(resp_json.get('ExpirationDate'))

                region.set("titlovi_token", [self.user_id, self.login_token, self.token_exp])
                logger.debug('New token obtained')

            elif response.status_code == request_codes.unauthorized:
                raise AuthenticationError('Login failed')

        except RequestException as e:
            logger.error(e)
    def terminate(self):
        self.session.close()

    def query(self, languages, title, season=None, episode=None, year=None, imdb_id=None, video=None):
        search_params = dict()

        used_languages = languages
        lang_strings = [str(lang) for lang in used_languages]

        # handle possible duplicate use of Serbian Latin
        if "sr" in lang_strings and "sr-Latn" in lang_strings:
            logger.info('Duplicate entries <Language [sr]> and <Language [sr-Latn]> found, filtering languages')
            used_languages = filter(lambda l: l != Language.fromietf('sr-Latn'), used_languages)
            logger.info('Filtered language list %r', used_languages)

        # convert list of languages into search string
        langs = '|'.join(map(str, [l.titlovi for l in used_languages]))

        # set query params
        search_params['query'] = title
        search_params['lang'] = langs
        is_episode = False
        if season and episode:
            is_episode = True
            search_params['season'] = season
            search_params['episode'] = episode
        #if year:
        #    search_params['year'] = year
        if imdb_id:
            search_params['imdbID'] = imdb_id

        # loop through paginated results
        logger.info('Searching subtitles %r', search_params)
        subtitles = []
        query_results = []

        try:
            search_params['token'] = self.login_token
            search_params['userid'] = self.user_id
            search_params['json'] = True

            response = self.session.get(self.api_search_url, params=search_params)
            resp_json = response.json()
            if resp_json['SubtitleResults']:
                query_results.extend(resp_json['SubtitleResults'])


        except Exception as e:
            logger.error(e)

        for sub in query_results:

            # title and alternate title
            match = title_re.search(sub.get('Title'))
            if match:
                _title = match.group('title')
                alt_title = match.group('altitle')
            else:
                continue

            # handle movies and series separately
            if is_episode:
                subtitle = self.subtitle_class(Language.fromtitlovi(sub.get('Lang')), sub.get('Link'), sub.get('Id'), sub.get('Release'), _title,
                                               alt_title=alt_title, season=sub.get('Season'), episode=sub.get('Episode'),
                                               year=sub.get('Year'), rating=sub.get('Rating'),
                                               download_count=sub.get('DownloadCount'),
                                               asked_for_release_group=video.release_group,
                                               asked_for_episode=episode)
            else:
                subtitle = self.subtitle_class(Language.fromtitlovi(sub.get('Lang')), sub.get('Link'), sub.get('Id'), sub.get('Release'), _title,
                                               alt_title=alt_title, year=sub.get('Year'), rating=sub.get('Rating'),
                                               download_count=sub.get('DownloadCount'),
                                               asked_for_release_group=video.release_group)
            logger.debug('Found subtitle %r', subtitle)

            # prime our matches so we can use the values later
            subtitle.get_matches(video)

            # add found subtitles
            subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        season = episode = None

        if isinstance(video, Episode):
            title = video.series
            season = video.season
            episode = video.episode
        else:
            title = video.title

        return [s for s in
                self.query(languages, fix_inconsistent_naming(title), season=season, episode=episode, year=video.year,
                           imdb_id=video.imdb_id,
                           video=video)]

    def download_subtitle(self, subtitle):
        r = self.session.get(subtitle.download_link, timeout=10)
        r.raise_for_status()

        # open the archive
        archive_stream = io.BytesIO(r.content)
        if is_rarfile(archive_stream):
            logger.debug('Archive identified as rar')
            archive = RarFile(archive_stream)
        elif is_zipfile(archive_stream):
            logger.debug('Archive identified as zip')
            archive = ZipFile(archive_stream)
        else:
            subtitle.content = r.content
            if subtitle.is_valid():
                return
            subtitle.content = None

            raise ProviderError('Unidentified archive type')

        subs_in_archive = archive.namelist()

        # if Serbian lat and cyr versions are packed together, try to find right version
        if len(subs_in_archive) > 1 and (subtitle.language == 'sr' or subtitle.language == 'sr-Cyrl'):
            self.get_subtitle_from_bundled_archive(subtitle, subs_in_archive, archive)
        else:
            # use default method for everything else
            subtitle.content = self.get_subtitle_from_archive(subtitle, archive)

    def get_subtitle_from_bundled_archive(self, subtitle, subs_in_archive, archive):
        sr_lat_subs = []
        sr_cyr_subs = []
        sub_to_extract = None

        for sub_name in subs_in_archive:
            _sub_name = sub_name.lower()

            if not ('.cyr' in _sub_name or '.cir' in _sub_name or 'cyr)' in _sub_name):
                sr_lat_subs.append(sub_name)

            if ('.cyr' in sub_name or '.cir' in _sub_name) and not '.lat' in _sub_name.lower():
                sr_cyr_subs.append(sub_name)

        if subtitle.language == 'sr':
            if len(sr_lat_subs) > 0:
                sub_to_extract = sr_lat_subs[0]

        if subtitle.language == 'sr-Cyrl':
            if len(sr_cyr_subs) > 0:
                sub_to_extract = sr_cyr_subs[0]

        logger.info(u'Using %s from the archive', sub_to_extract)
        subtitle.content = fix_line_ending(archive.read(sub_to_extract))

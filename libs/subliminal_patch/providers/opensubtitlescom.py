# -*- coding: utf-8 -*-
import logging
import os
import datetime

from requests import Session, ConnectionError, Timeout, ReadTimeout
from subzero.language import Language

from babelfish import language_converters
from subliminal import Episode, Movie
from subliminal.score import get_equivalent_release_groups
from subliminal.utils import sanitize_release_group, sanitize
from subliminal_patch.exceptions import TooManyRequests
from subliminal.exceptions import DownloadLimitExceeded, AuthenticationError, ConfigurationError, ServiceUnavailable, \
    ProviderError
from .mixins import ProviderRetryMixin
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.subtitle import fix_line_ending, SUBTITLE_EXTENSIONS
from subliminal_patch.providers import Provider
from subliminal_patch.utils import fix_inconsistent_naming
from subliminal.cache import region
from dogpile.cache.api import NO_VALUE
from guessit import guessit

logger = logging.getLogger(__name__)

SHOW_EXPIRATION_TIME = datetime.timedelta(weeks=1).total_seconds()
TOKEN_EXPIRATION_TIME = datetime.timedelta(hours=12).total_seconds()


def fix_tv_naming(title):
    """Fix TV show titles with inconsistent naming using dictionary, but do not sanitize them.

    :param str title: original title.
    :return: new title.
    :rtype: str

    """
    return fix_inconsistent_naming(title, {"Superman & Lois": "Superman and Lois",
                                           }, True)


def fix_movie_naming(title):
    return fix_inconsistent_naming(title, {
                                           }, True)


class OpenSubtitlesComSubtitle(Subtitle):
    provider_name = 'opensubtitlescom'
    hash_verifiable = False

    def __init__(self, language, hearing_impaired, page_link, file_id, releases, uploader, title, year,
                 hash_matched, hash=None, season=None, episode=None):
        self.title = title
        self.year = year
        self.season = season
        self.episode = episode
        self.releases = releases
        self.release_info = releases
        self.language = language
        self.hearing_impaired = hearing_impaired
        self.file_id = file_id
        self.page_link = page_link
        self.download_link = None
        self.uploader = uploader
        self.matches = None
        self.hash = hash
        self.encoding = 'utf-8'
        self.hash_matched = hash_matched

    @property
    def id(self):
        return self.file_id

    def get_matches(self, video):
        matches = set()

        # handle movies and series separately
        if isinstance(video, Episode):
            # series
            matches.add('series')
            # year
            if video.year == self.year:
                matches.add('year')
            # season
            if video.season == self.season:
                matches.add('season')
            # episode
            if video.episode == self.episode:
                matches.add('episode')
        # movie
        elif isinstance(video, Movie):
            # title
            matches.add('title')
            # year
            if video.year == self.year:
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
        # source
        if video.source and self.releases and video.source.lower() in self.releases.lower():
            matches.add('source')
        # hash
        if self.hash_matched:
            matches.add('hash')
        # other properties
        matches |= guess_matches(video, guessit(self.releases))

        self.matches = matches

        return matches


class OpenSubtitlesComProvider(ProviderRetryMixin, Provider):
    """OpenSubtitlesCom Provider"""
    server_url = 'https://api.opensubtitles.com/api/v1/'

    languages = {Language.fromopensubtitles(l) for l in language_converters['szopensubtitles'].codes}
    languages.update(set(Language.rebuild(l, forced=True) for l in languages))

    def __init__(self, username=None, password=None, use_hash=True, api_key=None):
        if not api_key:
            raise ConfigurationError('Api_key must be specified')

        if not all((username, password)):
            raise ConfigurationError('Username and password must be specified')

        self.session = Session()
        self.session.headers = {'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2"),
                                'Api-Key': api_key,
                                'Content-Type': 'application/json'}
        self.token = None
        self.username = username
        self.password = password
        self.video = None
        self.use_hash = use_hash

    def initialize(self):
        self.token = region.get("oscom_token", expiration_time=TOKEN_EXPIRATION_TIME)
        if self.token is NO_VALUE:
            self.login()

    def terminate(self):
        self.session.close()

    def login(self):
        try:
            r = self.session.post(self.server_url + 'login',
                                  json={"username": self.username, "password": self.password},
                                  allow_redirects=False,
                                  timeout=30)
        except (ConnectionError, Timeout, ReadTimeout):
            raise ServiceUnavailable('Unknown Error, empty response: %s: %r' % (r.status_code, r))
        else:
            if r.status_code == 200:
                try:
                    self.token = r.json()['token']
                except ValueError:
                    raise ProviderError('Invalid JSON returned by provider')
                else:
                    region.set("oscom_token", self.token)
                    return True
            elif r.status_code == 401:
                raise AuthenticationError('Login failed: {}'.format(r.reason))
            elif r.status_code == 429:
                raise TooManyRequests()
            elif r.status_code == 503:
                raise ProviderError(r.reason)
            else:
                raise ProviderError('Bad status code: {}'.format(r.status_code))
        finally:
            return False

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME)
    def search_titles(self, title):
        title_id = None
        imdb_id = None

        if isinstance(self.video, Episode) and self.video.series_imdb_id:
            imdb_id = self.video.series_imdb_id
        elif isinstance(self.video, Movie) and self.video.imdb_id:
            imdb_id = self.video.imdb_id

        if imdb_id:
            parameters = {'imdb_id': imdb_id}
            logging.debug('Searching using this IMDB id: {}'.format(imdb_id))
        else:
            parameters = {'query': title}
            logging.debug('Searching using this title: {}'.format(title))

        results = self.session.get(self.server_url + 'features', params=parameters, timeout=30)

        if results.status_code == 401:
            logging.debug('Authentification failed: clearing cache and attempting to login.')
            region.delete("oscom_token")
            self.login()

            results = self.session.get(self.server_url + 'features', params=parameters, timeout=30)

            if results.status_code == 429:
                raise TooManyRequests()
            elif results.status_code == 503:
                raise ProviderError(results.reason)
        elif results.status_code == 429:
            raise TooManyRequests()
        elif results.status_code == 503:
            raise ProviderError(results.reason)

        # deserialize results
        try:
            results_dict = results.json()['data']
        except ValueError:
            raise ProviderError('Invalid JSON returned by provider')
        else:
            # loop over results
            for result in results_dict:
                if fix_tv_naming(title).lower() == result['attributes']['title'].lower() and \
                        (not self.video.year or self.video.year == int(result['attributes']['year'])):
                    title_id = result['id']
                    break

            if title_id:
                logging.debug('Found this title ID: {}'.format(title_id))
                return title_id
        finally:
            if not title_id:
                logger.debug('No match found for {}'.format(title))

    def query(self, languages, video):
        self.video = video
        if self.use_hash:
            hash = self.video.hashes.get('opensubtitlescom')
            logging.debug('Searching using this hash: {}'.format(hash))
        else:
            hash = None

        if isinstance(self.video, Episode):
            title = self.video.series
        else:
            title = self.video.title

        title_id = self.search_titles(title)
        if not title_id:
            return []
        lang_strings = [str(lang) for lang in languages]
        langs = ','.join(lang_strings)
        logging.debug('Searching for this languages: {}'.format(lang_strings))

        # query the server
        if isinstance(self.video, Episode):
            res = self.session.get(self.server_url + 'subtitles',
                                   params={'parent_feature_id': title_id,
                                           'languages': langs,
                                           'episode_number': self.video.episode,
                                           'season_number': self.video.season,
                                           'moviehash': hash},
                                   timeout=30)
        else:
            res = self.session.get(self.server_url + 'subtitles',
                                   params={'id': title_id,
                                           'languages': langs,
                                           'moviehash': hash},
                                   timeout=30)

        if res.status_code == 429:
            raise TooManyRequests()

        elif res.status_code == 503:
            raise ProviderError(res.reason)

        subtitles = []

        try:
            result = res.json()
        except ValueError:
            raise ProviderError('Invalid JSON returned by provider')
        else:
            logging.debug('Query returned {} subtitles'.format(len(result['data'])))

            if len(result['data']):
                for item in result['data']:
                    if 'season_number' in item['attributes']['feature_details']:
                        season_number = item['attributes']['feature_details']['season_number']
                    else:
                        season_number = None

                    if 'episode_number' in item['attributes']['feature_details']:
                        episode_number = item['attributes']['feature_details']['episode_number']
                    else:
                        episode_number = None

                    if 'moviehash_match' in item['attributes']:
                        moviehash_match = item['attributes']['moviehash_match']
                    else:
                        moviehash_match = False

                    if len(item['attributes']['files']):
                        subtitle = OpenSubtitlesComSubtitle(
                                language=Language.fromietf(item['attributes']['language']),
                                hearing_impaired=item['attributes']['hearing_impaired'],
                                page_link=item['attributes']['url'],
                                file_id=item['attributes']['files'][0]['file_id'],
                                releases=item['attributes']['release'],
                                uploader=item['attributes']['uploader']['name'],
                                title=item['attributes']['feature_details']['movie_name'],
                                year=item['attributes']['feature_details']['year'],
                                season=season_number,
                                episode=episode_number,
                                hash_matched=moviehash_match
                            )
                        subtitle.get_matches(self.video)
                        subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def download_subtitle(self, subtitle):
        logger.info('Downloading subtitle %r', subtitle)

        headers = {'Accept': 'application/json', 'Content-Type': 'application/json',
                   'Authorization': 'Beaker ' + self.token}
        res = self.session.post(self.server_url + 'download',
                                json={'file_id': subtitle.file_id, 'sub_format': 'srt'},
                                headers=headers,
                                timeout=30)
        if res.status_code == 429:
            raise TooManyRequests()
        elif res.status_code == 406:
            raise DownloadLimitExceeded("Daily download limit reached")
        elif res.status_code == 503:
            raise ProviderError(res.reason)
        else:
            try:
                subtitle.download_link = res.json()['link']
            except ValueError:
                raise ProviderError('Invalid JSON returned by provider')
            else:
                r = self.session.get(subtitle.download_link, timeout=30)

                if res.status_code == 429:
                    raise TooManyRequests()
                elif res.status_code == 406:
                    raise DownloadLimitExceeded("Daily download limit reached")
                elif res.status_code == 503:
                    raise ProviderError(res.reason)

                subtitle_content = r.content

                if subtitle_content:
                    subtitle.content = fix_line_ending(subtitle_content)
                else:
                    logger.debug('Could not download subtitle from {}'.format(subtitle.download_link))

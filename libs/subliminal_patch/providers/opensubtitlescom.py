# -*- coding: utf-8 -*-
import logging
import os
import time
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
from subliminal_patch.subtitle import Subtitle
from subliminal.subtitle import fix_line_ending, SUBTITLE_EXTENSIONS
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import guess_matches
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

    def __init__(self, language, forced, hearing_impaired, page_link, file_id, releases, uploader, title, year,
                 hash_matched, file_hash=None, season=None, episode=None):
        language = Language.rebuild(language, hi=hearing_impaired, forced=forced)

        self.title = title
        self.year = year
        self.season = season
        self.episode = episode
        self.releases = releases
        self.release_info = releases
        self.language = language
        self.hearing_impaired = hearing_impaired
        self.forced = forced
        self.file_id = file_id
        self.page_link = page_link
        self.download_link = None
        self.uploader = uploader
        self.matches = None
        self.hash = file_hash
        self.encoding = 'utf-8'
        self.hash_matched = hash_matched

    @property
    def id(self):
        return self.file_id

    def get_matches(self, video):
        matches = set()
        type_ = "movie" if isinstance(video, Movie) else "episode"

        # handle movies and series separately
        if type_ == "episode":
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
        else:
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

        if self.hash_matched:
            matches.add('hash')

        # other properties
        matches |= guess_matches(video, guessit(self.releases, {"type": type_}))

        self.matches = matches

        return matches


class OpenSubtitlesComProvider(ProviderRetryMixin, Provider):
    """OpenSubtitlesCom Provider"""
    server_url = 'https://api.opensubtitles.com/api/v1/'

    languages = {Language.fromopensubtitles(lang) for lang in language_converters['szopensubtitles'].codes}
    languages.update(set(Language.rebuild(lang, forced=True) for lang in languages))

    video_types = (Episode, Movie)

    def __init__(self, username=None, password=None, use_hash=True, api_key=None):
        if not all((username, password)):
            raise ConfigurationError('Username and password must be specified')

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
        self._started = None

    def initialize(self):
        self._started = time.time()
        self.login()

    def terminate(self):
        self.session.close()

    def ping(self):
        return self._started and (time.time() - self._started) < TOKEN_EXPIRATION_TIME

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
                    return
            elif r.status_code == 401:
                raise AuthenticationError('Login failed: {}'.format(r.reason))
            elif r.status_code == 429:
                raise TooManyRequests()
            elif 500 <= r.status_code <= 599:
                raise ProviderError(r.reason)
            else:
                raise ProviderError('Bad status code: {}'.format(r.status_code))

    @staticmethod
    def sanitize_external_ids(external_id):
        if isinstance(external_id, str):
            external_id = external_id.lower().lstrip('tt').lstrip('0')
        sanitized_id = external_id[:-1].lstrip('0') + external_id[-1]
        return int(sanitized_id)

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME)
    def search_titles(self, title):
        title_id = None

        parameters = {'query': title.lower()}
        logging.debug('Searching using this title: {}'.format(title))

        results = self.session.get(self.server_url + 'features', params=parameters, timeout=30)

        if results.status_code == 401:
            logging.debug('Authentification failed: clearing cache and attempting to login.')
            region.delete("oscom_token")
            self.login()

            results = self.session.get(self.server_url + 'features', params=parameters, timeout=30)

            if results.status_code == 429:
                raise TooManyRequests()
            elif 500 <= results.status_code <= 599:
                raise ProviderError(results.reason)
        elif results.status_code == 429:
            raise TooManyRequests()
        elif 500 <= results.status_code <= 599:
            raise ProviderError(results.reason)

        # deserialize results
        try:
            results_dict = results.json()['data']
        except ValueError:
            raise ProviderError('Invalid JSON returned by provider')
        else:
            # loop over results
            for result in results_dict:
                if 'title' in result['attributes']:
                    if isinstance(self.video, Episode):
                        if fix_tv_naming(title).lower() == result['attributes']['title'].lower() and \
                                (not self.video.year or self.video.year == int(result['attributes']['year'])):
                            title_id = result['id']
                            break
                    else:
                        if fix_movie_naming(title).lower() == result['attributes']['title'].lower() and \
                                (not self.video.year or self.video.year == int(result['attributes']['year'])):
                            title_id = result['id']
                            break
                else:
                    continue

            if title_id:
                logging.debug('Found this title ID: {}'.format(title_id))
                return self.sanitize_external_ids(title_id)
        finally:
            if not title_id:
                logger.debug('No match found for {}'.format(title))

    def query(self, languages, video):
        self.video = video
        if self.use_hash:
            file_hash = self.video.hashes.get('opensubtitlescom')
            logging.debug('Searching using this hash: {}'.format(hash))
        else:
            file_hash = None

        if isinstance(self.video, Episode):
            title = self.video.series
        else:
            title = self.video.title

        imdb_id = None
        if isinstance(self.video, Episode) and self.video.series_imdb_id:
            imdb_id = self.sanitize_external_ids(self.video.series_imdb_id)
        elif isinstance(self.video, Movie) and self.video.imdb_id:
            imdb_id = self.sanitize_external_ids(self.video.imdb_id)

        title_id = None
        if not imdb_id:
            title_id = self.search_titles(title)
            if not title_id:
                return []

        lang_strings = [str(lang.basename) for lang in languages]
        only_foreign = all([lang.forced for lang in languages])
        also_foreign = any([lang.forced for lang in languages])
        if only_foreign:
            forced = 'only'
        elif also_foreign:
            forced = 'include'
        else:
            forced = 'exclude'

        langs = ','.join(lang_strings)
        logging.debug('Searching for this languages: {}'.format(lang_strings))

        # query the server
        if isinstance(self.video, Episode):
            res = self.session.get(self.server_url + 'subtitles',
                                   params=(('episode_number', self.video.episode),
                                           ('foreign_parts_only', forced),
                                           ('languages', langs.lower()),
                                           ('moviehash', file_hash),
                                           ('parent_feature_id', title_id) if title_id else ('imdb_id', imdb_id),
                                           ('season_number', self.video.season),
                                           ('query', os.path.basename(self.video.name))),
                                   timeout=30)
        else:
            res = self.session.get(self.server_url + 'subtitles',
                                   params=(('foreign_parts_only', forced),
                                           ('id', title_id) if title_id else ('imdb_id', imdb_id),
                                           ('languages', langs.lower()),
                                           ('moviehash', file_hash),
                                           ('query', os.path.basename(self.video.name))),
                                   timeout=30)

        if res.status_code == 429:
            raise TooManyRequests()

        elif 500 <= res.status_code <= 599:
            raise ProviderError(res.reason)

        subtitles = []

        try:
            result = res.json()
            if 'data' not in result:
                raise ValueError
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
                            forced=item['attributes']['foreign_parts_only'],
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
        if self.token is NO_VALUE:
            logger.debug("No cached token, we'll try to login again.")
            self.login()
        if self.token is NO_VALUE:
            logger.debug("Unable to obtain an authentication token right now, we'll try again later.")
            raise ProviderError("Unable to obtain an authentication token")

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
        elif 500 <= res.status_code <= 599:
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
                elif 500 <= res.status_code <= 599:
                    raise ProviderError(res.reason)

                subtitle_content = r.content

                if subtitle_content:
                    subtitle.content = fix_line_ending(subtitle_content)
                else:
                    logger.debug('Could not download subtitle from {}'.format(subtitle.download_link))

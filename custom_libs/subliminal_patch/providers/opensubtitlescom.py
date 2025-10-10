# -*- coding: utf-8 -*-
import logging
import os
import time
import datetime
import json

from requests import Session, ConnectionError, Timeout, ReadTimeout, RequestException
from requests.exceptions import JSONDecodeError
from subzero.language import Language

from babelfish import language_converters
from subliminal import Episode, Movie
from subliminal.score import get_equivalent_release_groups
from subliminal.utils import sanitize_release_group, sanitize
from subliminal_patch.exceptions import TooManyRequests, APIThrottled
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

retry_amount = 3


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


custom_languages = {
    'pt': 'pt-PT',
    'zh': 'zh-CN',
    'es-MX': 'ea',
}


def to_opensubtitlescom(lang):
    if lang in custom_languages.keys():
        return custom_languages[lang]
    else:
        return lang


def from_opensubtitlescom(lang):
    from_custom_languages = {v: k for k, v in custom_languages.items()}
    if lang in from_custom_languages.keys():
        return from_custom_languages[lang]
    else:
        return lang


class OpenSubtitlesComSubtitle(Subtitle):
    provider_name = 'opensubtitlescom'
    hash_verifiable = True
    hearing_impaired_verifiable = True

    def __init__(self, language, forced, hearing_impaired, page_link, file_id, releases, uploader, title, year,
                 hash_matched, file_hash=None, season=None, episode=None, imdb_match=False):
        super().__init__(language, hearing_impaired, page_link)
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
        self.imdb_match = imdb_match

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
            # season
            if video.season == self.season:
                matches.add('season')
            # episode
            if video.episode == self.episode:
                matches.add('episode')
            # imdb
            if self.imdb_match:
                matches.add('series_imdb_id')
        else:
            # title
            matches.add('title')
            # imdb
            if self.imdb_match:
                matches.add('imdb_id')

        # rest is same for both groups

        # year
        if video.year == self.year:
            matches.add('year')

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
    server_hostname = 'api.opensubtitles.com'

    languages = ({Language.fromietf("es-MX")} |
                 {Language.fromopensubtitles(lang) for lang in language_converters['szopensubtitles'].codes})
    languages.update(set(Language.rebuild(lang, forced=True) for lang in languages))
    languages.update(set(Language.rebuild(lang, hi=True) for lang in languages))

    video_types = (Episode, Movie)

    def __init__(self, username=None, password=None, use_hash=True, include_ai_translated=False, api_key=None):
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
        self.include_ai_translated = include_ai_translated
        self._started = None

    def initialize(self):
        self._started = time.time()

        if region.get("oscom_token", expiration_time=TOKEN_EXPIRATION_TIME) is NO_VALUE:
            logger.debug("No cached token, we'll try to login again.")
            self.login()
        else:
            self.token = region.get("oscom_token", expiration_time=TOKEN_EXPIRATION_TIME)

        if region.get("oscom_server", expiration_time=TOKEN_EXPIRATION_TIME) is NO_VALUE:
            logger.debug("No cached server, we'll try to login again.")
            self.login()
        else:
            self.server_hostname = region.get("oscom_server", expiration_time=TOKEN_EXPIRATION_TIME)

    def terminate(self):
        self.session.close()

    def ping(self):
        return self._started and (time.time() - self._started) < TOKEN_EXPIRATION_TIME

    def server_url(self):
        return f'https://{self.server_hostname}/api/v1/'

    def login(self, is_retry=False):
        r = self.checked(
            lambda: self.session.post(self.server_url() + 'login',
                                      json={"username": self.username, "password": self.password},
                                      allow_redirects=False,
                                      timeout=30),
            is_retry=is_retry)

        try:
            self.token = r.json()['token']
        except (ValueError, JSONDecodeError, AttributeError):
            log_request_response(r)
            raise ProviderError("Cannot get token from provider login response")
        else:
            log_request_response(r, non_standard=False)
            region.set("oscom_token", self.token)

        try:
            self.server_hostname = r.json()['base_url']
        except (ValueError, JSONDecodeError):
            log_request_response(r)
            raise ProviderError("Cannot get server from provider login response")
        else:
            log_request_response(r, non_standard=False)
            region.set("oscom_server", self.server_hostname)
        finally:
            if self.server_hostname.startswith('vip'):
                self.session.headers.update({'Authorization': 'Bearer ' + self.token})
            else:
                self.session.headers.pop('Authorization', None)

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
        logger.debug(f'Searching using this title: {title}')

        results = self.retry(
            lambda: self.checked(
                lambda: self.session.get(self.server_url() + 'features', params=parameters, timeout=30),
                validate_json=True,
                json_key_name='data'
            ),
            amount=retry_amount
        )

        # deserialize results
        results_dict = results.json()['data']

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
            logger.debug(f'Found this title ID: {title_id}')
            return self.sanitize_external_ids(title_id)

        if not title_id:
            logger.debug(f'No match found for {title}')

    @staticmethod
    def is_real_forced(attributes):
        return attributes['foreign_parts_only'] and not attributes['hearing_impaired']

    def query(self, languages, video):
        self.video = video
        if self.use_hash:
            file_hash = self.video.hashes.get('opensubtitlescom')
            logger.debug(f'Searching using this hash: {file_hash}')
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

        # be sure to remove duplicates using list(set())
        langs_list = sorted(list(set([to_opensubtitlescom(lang.basename).lower() for lang in languages])))

        langs = ','.join(langs_list)
        logger.debug(f'Searching for those languages: {langs}')

        # define the proper query parameters based on the video type
        # query parameters must be alphabetically ordered to prevent redirect
        if isinstance(self.video, Episode):
            params = [('episode_number', self.video.episode),
                      ('imdb_id', imdb_id if not title_id else None),
                      ('languages', langs),
                      ('moviehash', file_hash),
                      ('parent_feature_id', title_id if title_id else None),
                      ('season_number', self.video.season)]
        else:
            params = [('id', title_id if title_id else None),
                      ('imdb_id', imdb_id if not title_id else None),
                      ('languages', langs),
                      ('moviehash', file_hash)]

        # prepend the 'exclude' parameter to the list of query parameters if we don't want AI translated subtitles'
        if not self.include_ai_translated:
            params.insert(0, ('ai_translated', 'exclude'))

        # query the server
        res = self.retry(
            lambda: self.checked(
                lambda: self.session.get(self.server_url() + 'subtitles', params=params, timeout=30),
                validate_json=True,
                json_key_name='data'
            ),
            amount=retry_amount
        )

        subtitles = []

        result = res.json()

        # filter out forced subtitles or not depending on the required languages
        if all([lang.forced for lang in languages]):  # only forced
            result['data'] = [x for x in result['data'] if self.is_real_forced(x['attributes'])]
        elif any([lang.forced for lang in languages]):  # also forced
            pass
        else:  # not forced
            result['data'] = [x for x in result['data'] if not self.is_real_forced(x['attributes'])]

        logger.debug(f"Query returned {len(result['data'])} subtitles")

        if len(result['data']):
            for item in result['data']:
                # ignore AI translated subtitles
                if not self.include_ai_translated:
                    if 'ai_translated' in item['attributes'] and item['attributes']['ai_translated']:
                        logger.debug("Skipping AI translated subtitles")
                        continue

                # ignore machine translated subtitles
                if 'machine_translated' in item['attributes'] and item['attributes']['machine_translated']:
                    logger.debug("Skipping machine translated subtitles")
                    continue

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

                try:
                    year = int(item['attributes']['feature_details']['year'])
                except TypeError:
                    year = item['attributes']['feature_details']['year']

                if len(item['attributes']['files']):
                    subtitle = OpenSubtitlesComSubtitle(
                        language=Language.fromietf(from_opensubtitlescom(item['attributes']['language'])),
                        forced=self.is_real_forced(item['attributes']),
                        hearing_impaired=item['attributes']['hearing_impaired'],
                        page_link=item['attributes']['url'],
                        file_id=item['attributes']['files'][0]['file_id'],
                        releases=item['attributes']['release'],
                        uploader=item['attributes']['uploader']['name'],
                        title=item['attributes']['feature_details']['movie_name'],
                        year=year,
                        season=season_number,
                        episode=episode_number,
                        hash_matched=moviehash_match,
                        imdb_match=True if imdb_id else False
                    )
                    subtitle.get_matches(self.video)
                    subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def download_subtitle(self, subtitle):
        logger.info('Downloading subtitle %r', subtitle)

        headers = {'Accept': 'application/json', 'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + self.token}
        res = self.retry(
            lambda: self.checked(
                lambda: self.session.post(self.server_url() + 'download',
                                          json={'file_id': subtitle.file_id, 'sub_format': 'srt'},
                                          headers=headers,
                                          timeout=30),
                validate_json=True,
                json_key_name='link'
            ),
            amount=retry_amount
        )

        logger.debug(f'params sent to the download endpoint: {res.request.body}')
        download_data = res.json()
        subtitle.download_link = download_data['link']

        r = self.retry(
            lambda: self.checked(
                lambda: self.session.get(subtitle.download_link, timeout=30),
                validate_content=True
            ),
            amount=retry_amount
        )

        if not r:
            logger.debug(f'Could not download subtitle from {subtitle.download_link}')
            subtitle.content = None
            return
        else:
            subtitle_content = r.content
            subtitle.content = fix_line_ending(subtitle_content)

    @staticmethod
    def reset_token():
        logger.debug('Authentication failed: clearing cache and attempting to login.')
        region.delete("oscom_token")
        region.delete("oscom_server")
        return

    def checked(self, fn, raise_api_limit=False, validate_json=False, json_key_name=None, validate_content=False,
                is_retry=False):
        """Run :fn: and check the response status before returning it.

        :param fn: the function to make an API call to OpenSubtitles.com.
        :param raise_api_limit: if True we wait a little bit longer before running the call again.
        :param validate_json: test if response is valid json.
        :param json_key_name: test if returned json contain a specific key.
        :param validate_content: test if response have a content (used with download).
        :param is_retry: prevent additional retries with login endpoint.
        :return: the response.

        """
        response = None
        try:
            try:
                response = fn()
            except APIThrottled:
                if not raise_api_limit:
                    logger.info("API request limit hit, waiting and trying again once.")
                    time.sleep(15)
                    return self.checked(fn, raise_api_limit=True)
                raise
            except (ConnectionError, Timeout, ReadTimeout):
                raise ServiceUnavailable(f'Unknown Error, empty response: {response.status_code}: {response}')
            except Exception:
                logger.exception('Unhandled exception raised.')
                raise ProviderError('Unhandled exception raised. Check log.')
            else:
                status_code = response.status_code
        except Exception:
            status_code = None
        else:
            if status_code == 400:
                try:
                    json_response = response.json()
                    message = json_response['message']
                except JSONDecodeError:
                    raise ProviderError('Invalid JSON returned by provider')
                else:
                    log_request_response(response)
                    raise ConfigurationError(message)
            elif status_code == 401:
                log_request_response(response)
                self.reset_token()
                if is_retry:
                    raise AuthenticationError('Login failed')
                else:
                    time.sleep(1)
                    self.login(is_retry=True)
                    self.checked(fn, raise_api_limit=raise_api_limit, validate_json=validate_json,
                                 json_key_name=json_key_name, validate_content=validate_content, is_retry=True)
            elif status_code == 403:
                log_request_response(response)
                raise ProviderError("Bazarr API key seems to be in problem")
            elif status_code == 406:
                try:
                    json_response = response.json()
                    download_count = json_response['requests']
                    remaining_download = json_response['remaining']
                    quota_reset_time = json_response['reset_time']
                except JSONDecodeError:
                    raise ProviderError('Invalid JSON returned by provider')
                else:
                    log_request_response(response)
                    raise DownloadLimitExceeded(f"Daily download limit reached. {download_count} subtitles have been "
                                                f"downloaded and {remaining_download} remaining subtitles can be "
                                                f"downloaded. Quota will be reset in {quota_reset_time}.")
            elif status_code == 410:
                log_request_response(response)
                raise ProviderError("Download as expired")
            elif status_code == 429:
                log_request_response(response)
                raise TooManyRequests()
            elif status_code == 502:
                # this one should deal with Bad Gateway issue on their side.
                raise APIThrottled()
            elif 500 <= status_code <= 599:
                raise ProviderError(response.reason)

            if status_code != 200:
                log_request_response(response)
                raise ProviderError(f'Bad status code: {response.status_code}')

            if validate_json:
                try:
                    json_test = response.json()
                except JSONDecodeError:
                    raise ProviderError('Invalid JSON returned by provider')
                else:
                    if json_key_name not in json_test:
                        raise ProviderError(f'Invalid JSON returned by provider: no {json_key_name} key in returned json.')

            if validate_content:
                if not hasattr(response, 'content'):
                    logger.error('Download link returned no content attribute.')
                    return False
                elif not response.content:
                    logger.error(f'This download link returned empty content: {response.url}')
                    return False

        return response


def log_request_response(response, non_standard=True):
    redacted_request_headers = response.request.headers
    if 'Authorization' in redacted_request_headers and isinstance(redacted_request_headers['Authorization'], str):
        redacted_request_headers['Authorization'] = redacted_request_headers['Authorization'][:-8]+8*'x'

    if response.request.body:
        redacted_request_body = json.loads(response.request.body)
        if 'password' in redacted_request_body:
            redacted_request_body['password'] = 'redacted'
    else:
        redacted_request_body = None

    redacted_response_body = json.loads(response.text)
    if 'token' in redacted_response_body and isinstance(redacted_response_body['token'], str):
        redacted_response_body['token'] = redacted_response_body['token'][:-8] + 8 * 'x'

    if non_standard:
        logger.debug("opensubtitlescom returned a non standard response. Logging request/response for debugging "
                      "purpose.")
    else:
        logger.debug("opensubtitlescom returned a standard response. Logging request/response for debugging purpose.")
    logger.debug(f"Request URL: {response.request.url}")
    logger.debug(f"Request Headers: {redacted_request_headers}")
    logger.debug(f"Request Body: {json.dumps(redacted_request_body)}")
    logger.debug(f"Response Status Code: {response.status_code}")
    logger.debug(f"Response Headers: {response.headers}")
    logger.debug(f"Response Body: {json.dumps(redacted_response_body)}")

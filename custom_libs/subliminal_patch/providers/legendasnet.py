# -*- coding: utf-8 -*-
import logging
import os
import time
import io
import json
from typing import Callable

from zipfile import ZipFile, is_zipfile
from urllib.parse import urljoin
from requests import Session, Response

from subzero.language import Language
from subliminal import Episode, Movie
from subliminal.exceptions import ConfigurationError, ProviderError, DownloadLimitExceeded
from subliminal_patch.exceptions import APIThrottled
from .mixins import ProviderRetryMixin
from subliminal_patch.subtitle import Subtitle
from subliminal.subtitle import fix_line_ending
from subliminal_patch.providers import Provider
from subliminal_patch.providers import utils

logger = logging.getLogger(__name__)

retry_amount = 3
retry_timeout = 5


class LegendasNetSubtitle(Subtitle):
    provider_name = 'legendasnet'
    hash_verifiable = False

    def __init__(self, language, forced, page_link, download_link, file_id, release_names, uploader,
                 season=None, episode=None):
        super().__init__(language)
        language = Language.rebuild(language, forced=forced)

        self.season = season
        self.episode = episode
        self.releases = release_names
        self.release_info = ', '.join(release_names)
        self.language = language
        self.forced = forced
        self.file_id = file_id
        self.page_link = page_link
        self.download_link = download_link
        self.uploader = uploader
        self.matches = set()

    @property
    def id(self):
        return self.file_id

    def get_matches(self, video):
        matches = set()

        # handle movies and series separately
        if isinstance(video, Episode):
            # series
            matches.add('series')
            # season
            if video.season == self.season:
                matches.add('season')
            # episode
            if video.episode == self.episode:
                matches.add('episode')
            # imdb
            matches.add('series_imdb_id')
        else:
            # title
            matches.add('title')
            # imdb
            matches.add('imdb_id')

        utils.update_matches(matches, video, self.release_info)

        self.matches = matches

        return matches


class LegendasNetProvider(ProviderRetryMixin, Provider):
    """Legendas.Net Provider"""
    server_hostname = 'legendas.net/api'

    languages = {Language('por', 'BR')}
    video_types = (Episode, Movie)

    def __init__(self, username, password):
        self.session = Session()
        self.session.headers = {'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")}
        self.username = username
        self.password = password
        self.access_token = None
        self.video = None
        self._started = None
        self.login()

    def login(self):
        headersList = {
            "Accept": "*/*",
            "User-Agent": self.session.headers['User-Agent'],
            "Content-Type": "application/json"
        }

        payload = json.dumps({
            "email": self.username,
            "password": self.password
        })

        response = self.retry(
            lambda: self.checked(
                lambda: self.session.request("POST", self.server_url() + 'login', data=payload, headers=headersList,
                                             timeout=30),
                is_login=True,
            ),
            amount=retry_amount,
            retry_timeout=retry_timeout
        )

        self.access_token = response.json().get('access_token')
        if not self.access_token:
            raise ConfigurationError('Access token not found in login response')
        self.session.headers.update({'Authorization': f'Bearer {self.access_token}'})

    def initialize(self):
        self._started = time.time()

    def terminate(self):
        self.session.close()

    def server_url(self):
        return f'https://{self.server_hostname}/v1/'

    def query(self, languages, video):
        self.video = video

        # query the server
        if isinstance(self.video, Episode):
            res = self.retry(
                lambda: self.checked(
                    lambda: self.session.get(self.server_url() + 'search/tv',
                                             json={
                                                 'name': video.series,
                                                 'page': 1,
                                                 'per_page': 25,
                                                 'tv_episode': video.episode,
                                                 'tv_season': video.season,
                                                 'imdb_id': video.series_imdb_id
                                             },
                                             headers={'Content-Type': 'application/json'},
                                             timeout=30)),
                amount=retry_amount,
                retry_timeout=retry_timeout
            )
        else:
            res = self.retry(
                lambda: self.checked(
                    lambda: self.session.get(self.server_url() + 'search/movie',
                                             json={
                                                 'name': video.title,
                                                 'page': 1,
                                                 'per_page': 25,
                                                 'imdb_id': video.imdb_id
                                             },
                                             headers={'Content-Type': 'application/json'},
                                             timeout=30)),
                amount=retry_amount,
                retry_timeout=retry_timeout
            )

        subtitles = []

        result = res.json()

        if ('success' in result and not result['success']) or ('status' in result and not result['status']):
            logger.debug(result["error"])
            return []

        if isinstance(self.video, Episode):
            if len(result['tv_shows']):
                for item in result['tv_shows']:
                    subtitle = LegendasNetSubtitle(
                        language=Language('por', 'BR'),
                        forced=self._is_forced(item),
                        page_link=f"https://legendas.net/tv_legenda?movie_id={result['tv_shows'][0]['tmdb_id']}&"
                                  f"legenda_id={item['id']}",
                        download_link=item['path'],
                        file_id=item['id'],
                        release_names=[item.get('release_name', '')],
                        uploader=item['uploader'],
                        season=item.get('season', ''),
                        episode=item.get('episode', '')
                    )
                    subtitle.get_matches(self.video)
                    if subtitle.language in languages:
                        subtitles.append(subtitle)
        else:
            if len(result['movies']):
                for item in result['movies']:
                    subtitle = LegendasNetSubtitle(
                        language=Language('por', 'BR'),
                        forced=self._is_forced(item),
                        page_link=f"https://legendas.net/legenda?movie_id={result['movies'][0]['tmdb_id']}&"
                                  f"legenda_id={item['id']}",
                        download_link=item['path'],
                        file_id=item['id'],
                        release_names=[item.get('release_name', '')],
                        uploader=item['uploader'],
                        season=None,
                        episode=None
                    )
                    subtitle.get_matches(self.video)
                    if subtitle.language in languages:
                        subtitles.append(subtitle)

        return subtitles

    @staticmethod
    def _is_forced(item):
        forced_tags = ['forced', 'foreign']
        for tag in forced_tags:
            if tag in item.get('comment', '').lower():
                return True

        # nothing match so we consider it as normal subtitles
        return False

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def download_subtitle(self, subtitle):
        logger.debug('Downloading subtitle %r', subtitle)
        download_link = urljoin("https://legendas.net", subtitle.download_link)

        r = self.retry(
            lambda: self.checked(
                lambda: self.session.get(download_link, timeout=30),
                is_download=True
            ),
            amount=retry_amount,
            retry_timeout=retry_timeout
        )

        if not r:
            logger.error(f'Could not download subtitle from {download_link}')
            subtitle.content = None
            return
        else:
            archive_stream = io.BytesIO(r.content)
            if is_zipfile(archive_stream):
                archive = ZipFile(archive_stream)
                for name in archive.namelist():
                    subtitle_content = archive.read(name)
                    subtitle.content = fix_line_ending(subtitle_content)
                    return
            else:
                subtitle_content = r.content
                subtitle.content = fix_line_ending(subtitle_content)
                return

    def checked(self, fn: Callable, is_retry: bool = False, is_download: bool = False, is_login: bool = False) -> Response:
        """
        Executes the provided function and performs error handling and response validation for API calls.

        The method handles various HTTP status codes such as 401, 403, 404, and 429, and retries
        login if access tokens are invalid. Additionally, it ensures unhandled exceptions are logged
        and raises appropriate custom exceptions when needed.

        :param fn: The callable function that makes the HTTP request.
        :type fn: Callable
        :param is_retry: Indicates if the function is being retried due to a previous failed attempt.
        :type is_retry: bool
        :param is_download: Specifies if the function call is related to downloading subtitles. Helps in defining
            behavior in case of API throttling or limiting conditions.
        :type is_download: bool
        :param is_login: Specifies if the function call is for a login operation. Used to handle cases
            of invalid credentials.
        :type is_login: bool
        :return: The HTTP response object returned by the provided function if the status code is valid.
        :rtype: Response
        :raises ProviderError: If an unhandled exception occurs or the endpoint is not found.
        :raises DownloadLimitExceeded: If the daily download limit is exceeded.
        :raises APIThrottled: If too many requests are sent in a short period.
        :raises ConfigurationError: If login credentials or access tokens are invalid.
        """
        response = None
        try:
            response = fn()
        except Exception:
            logger.exception('Unhandled exception raised.')
            raise ProviderError('Unhandled exception raised. Check log.')
        else:
            status_code = response.status_code
            if status_code == 404:
                logger.error(f"Endpoint not found: {response.url}")
                raise ProviderError("Endpoint not found")
            elif status_code == 429:
                if is_download:
                    raise DownloadLimitExceeded("Daily download limit exceeded")
                else:
                    raise APIThrottled("Too many requests")
            elif status_code in (401, 403):
                self.session.headers.pop('Authorization', None)
                if is_login:
                    raise ConfigurationError('Invalid username or password')
                else:
                    if is_retry:
                        logger.debug("Access token is still invalid, giving up")
                        raise ConfigurationError("Invalid access token")
                    else:
                        logger.debug("Access token invalid, retrying login")
                        time.sleep(1)
                        self.login()
                        time.sleep(1)
                        return self.checked(fn, is_retry=True, is_download=is_download)
            elif status_code != 200:
                response.raise_for_status()

        return response

# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
import os
import time
import io
import datetime

from typing import Set
from typing import Optional, TYPE_CHECKING

from babelfish import language_converters
from zipfile import ZipFile, is_zipfile
from requests import Session, Response
from guessit import guessit

from subzero.language import Language
from subliminal import Episode, Movie
from subliminal.cache import region
from subliminal.exceptions import AuthenticationError, ConfigurationError
from subliminal_patch.exceptions import APIThrottled, ForbiddenError, TooManyRequests
from .mixins import ProviderRetryMixin
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.providers import Provider, utils
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin

if TYPE_CHECKING:
    from subliminal_patch import Video

logger = logging.getLogger(__name__)

TITLES_EXPIRATION_TIME = datetime.timedelta(hours=6).total_seconds()
QUERIES_EXPIRATION_TIME = datetime.timedelta(hours=1).total_seconds()
ARCHIVES_EXPIRATION_TIME = datetime.timedelta(minutes=15).total_seconds()

retry_amount = 3
retry_timeout = 5

language_converters.register('subsource = subliminal_patch.converters.subsource:SubsourceConverter')
supported_languages = list(language_converters['subsource'].to_subsource.keys())


class SubsourceSubtitle(Subtitle):
    provider_name = 'subsource'
    hash_verifiable = False
    hearing_impaired_verifiable = True

    def __init__(self, language, forced, hearing_impaired, page_link, subtitles_id, release_names, uploader,
                 season=None, episode=None, asked_for_episode=None, is_pack=False):
        super().__init__(language)
        language = Language.rebuild(language, hi=hearing_impaired, forced=forced)

        self.releases = release_names
        self.release_info = ', '.join(release_names)
        self.language = language
        self.forced = forced
        self.hearing_impaired = hearing_impaired
        self.subtitles_id = subtitles_id
        self.page_link = page_link
        self.download_link = None
        self.uploader = uploader
        self.matches = None
        self.season = season
        self.episode = episode
        self.asked_for_episode = asked_for_episode
        self.is_pack = is_pack

    @property
    def id(self) -> int:
        return self.subtitles_id

    def get_matches(self, video: Video) -> Set[str]:
        """
        Analyzes the given subtitles and identifies relevant attributes or associations
        by updating the matches set. Handles movies and series differently to
        match relevant attributes like title, IMDb identifiers, and pack type.

        :param video: A video instance, typically a movie or a series episode, to
                      analyze for matches.
        :return: A set of strings representing identified attributes or matches
                 relevant to the given video.
        """
        matches = set()

        utils.update_matches(matches, video, self.release_info)

        # handle movies and series separately
        if isinstance(video, Episode):
            # series
            matches.add('series')
            # imdb
            matches.add('series_imdb_id')
            # season pack
            if self.is_pack:
                matches.add('episode')
        else:
            # title
            matches.add('title')
            # imdb
            matches.add('imdb_id')

        self.matches = matches

        return matches


class SubsourceProvider(ProviderRetryMixin, Provider, ProviderSubtitleArchiveMixin):
    """Subsource Provider"""
    server_hostname = 'api.subsource.net'

    languages = {Language(*lang) for lang in supported_languages}
    languages.update(set(Language.rebuild(lang, forced=True) for lang in languages))
    languages.update(set(Language.rebuild(lang, hi=True) for lang in languages))

    video_types = (Episode, Movie)

    def __init__(self, api_key=None):
        if not api_key:
            raise ConfigurationError('Api_key must be specified')

        self.session = Session()
        self.session.headers = {'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")}
        self.api_key = api_key
        self.video = None
        self._started = None

    def initialize(self):
        self._started = time.time()

    def terminate(self):
        self.session.close()

    def _server_url(self) -> str:
        return f'https://{self.server_hostname}/api/v1/'

    @region.cache_on_arguments(expiration_time=TITLES_EXPIRATION_TIME)
    def search_titles(self, title: str, imdb_id: str, season: int = None) -> Optional[int]:
        """
        Searches for the ID of a movie or TV show title on an external database using either title, IMDb ID,
        and optionally the season number. The method sends a request to the provider's API server, deserializes
        the response, and attempts to find a matching title based on the provided parameters.

        :param title: The name of the title to search for, provided as a string.
        :type title: str
        :param imdb_id: The IMDb ID of the title to search for.
        :type imdb_id: str
        :param season: (Optional) The season number if the search is for a TV show. Defaults to None.
        :type season: int, optional
        :return: The ID of the movie or show if found, otherwise None.
        :rtype: Optional[int]
        """
        title_id = None

        if imdb_id:
            parameters = {
                'api_key': self.api_key,
                'searchType': 'imdb',
                'imdb': imdb_id,
            }
            logger.debug(f'Searching using this imdb ID: {imdb_id}')
        else:
            parameters = {
                'api_key': self.api_key,
                'searchType': 'text',
                'q': title.lower(),
            }
            logger.debug(f'Searching using this title: {title}')

        if season:
            parameters['season'] = season

        results = self.retry(
            lambda: self.session.get(self._server_url() + 'movies/search', params=parameters, timeout=30),
            amount=retry_amount,
            retry_timeout=retry_timeout
        )

        self._status_raiser(results)

        # deserialize results
        results_dict = results.json()['data']
        def get_alternative_titles(video):
            titles = set()
            if isinstance(video, Episode):
                if video.series:
                    titles.add(video.series)
                for alt in video.alternative_series or []:
                    titles.add(alt)
            else:
                if video.title:
                    titles.add(video.title)
            return {t.lower() for t in titles if t}


        alternative_titles = get_alternative_titles(self.video)
        logger.debug(f"alternative titles: {alternative_titles}")
        
        # loop over results
        for result in results_dict:
            if 'title' not in result or 'releaseYear' not in result:
                continue
            
            sub_titles = {result['title'].lower()}
            logger.debug(f"Subsource titles: {sub_titles}")

            if result.get('alternateTitle'):
                sub_titles.add(result['alternateTitle'].lower())
            matched = False
            for alternative_title in alternative_titles:
                for sub in sub_titles:
                    if alternative_title in sub:
                        matched = True
                if matched:
                    break
            if matched:
                if not self.video.year or self.video.year == int(result['releaseYear']):
                    title_id = result['movieId']
                    break
            else:
                continue

        if title_id:
            logger.debug(f'Found this title ID: {title_id}')
        else:
            logger.debug(f'No match found for {title}')

        return title_id

    @region.cache_on_arguments(expiration_time=QUERIES_EXPIRATION_TIME)
    def query(self, languages: Set[Language], video) -> list:
        """
        Queries subtitles for the given video in the specified languages. The method takes into account whether
        the video is an episode or a movie, searches using the appropriate parameters, and processes the results
        to return a list of subtitles matching the search criteria.

        :param languages: A set of `Language` objects specifying the languages for which subtitles are required.
        :param video: A `Video` object (either a `Movie` or `Episode`) containing information about the video
            for which subtitles are being searched.
        :return: A list of `SubsourceSubtitle` objects representing the found subtitles that match
            the provided criteria.
        """
        self.video = video
        if isinstance(self.video, Episode):
            title = self.video.series
        else:
            title = self.video.title

        if isinstance(self.video, Episode) and self.video.series_imdb_id:
            imdb_id = self.video.series_imdb_id
            title_id = self.search_titles(title, imdb_id, season=self.video.season)
        elif isinstance(self.video, Movie) and self.video.imdb_id:
            imdb_id = self.video.imdb_id
            title_id = self.search_titles(title, imdb_id)
        else:
            title_id = None

        if not title_id:
            logger.debug('No title id found for this video')
            return []

        # we make sure to get only one language to search for
        if len(languages):
            language = list(languages)[0]
        else:
            return []

        language_name = language_converters['subsource'].convert(language.alpha3, language.country, language.script)

        logger.debug(f'Searching for this language: {language}')

        parameters = (
            ('api_key', self.api_key),
            ('language', language_name.lower()),
            ('limit', 100),
            ('movieId', title_id)
        )

        # query the server
        if isinstance(self.video, Episode):
            parameters += (('seasonNumber', self.video.season), ('episodeNumber', self.video.episode))
            res = self.retry(
                lambda: self.session.get(self._server_url() + 'subtitles',
                                         params=parameters,
                                         timeout=30),
                amount=retry_amount,
                retry_timeout=retry_timeout
            )
        else:
            res = self.retry(
                lambda: self.session.get(self._server_url() + 'subtitles',
                                         params=parameters,
                                         timeout=30),
                amount=retry_amount,
                retry_timeout=retry_timeout
            )

        self._status_raiser(res)

        subtitles = []

        result = res.json()

        if 'success' in result and not result['success']:
            return []

        logger.debug(f"Query returned {len(result['data'])} subtitles")

        if len(result['data']):
            for item in result['data']:
                page_link = f"https://subsource.net{item['link']}"
                is_forced = self._is_forced(item)
                if is_forced and not language.forced:
                    continue

                is_hi = self._is_hi(item)
                if not is_hi and language.hi:
                    continue

                if isinstance(video, Episode):
                    season, episode = self._get_season_episode_from_release_info(item['releaseInfo'])
                    if season == video.season and (not episode or episode == video.episode):
                        subtitle = SubsourceSubtitle(
                            language=Language.fromalpha3b(language_converters['subsource'].reverse(item['language']
                                                                                                   .capitalize())[0]),
                            forced=is_forced,
                            hearing_impaired=is_hi,
                            page_link=page_link,
                            subtitles_id=item['subtitleId'],
                            release_names=item['releaseInfo'],
                            uploader=self._get_uploader_name(item),
                            season=season,
                            episode=episode,
                            asked_for_episode=video.episode,
                            is_pack=not episode,
                        )
                    else:
                        continue
                else:

                    subtitle = SubsourceSubtitle(
                        language=Language.fromalpha3b(language_converters['subsource'].reverse(item['language']
                                                                                               .capitalize())[0]),
                        forced=is_forced,
                        hearing_impaired=is_hi,
                        page_link=page_link,
                        subtitles_id=item['subtitleId'],
                        release_names=item['releaseInfo'],
                        uploader=self._get_uploader_name(item),
                    )

                subtitles.append(subtitle)

        return subtitles

    @staticmethod
    def _is_hi(item: dict) -> bool:
        """
        Checks if a given subtitle item uses hearing impairment captioning.

        This static method evaluates the provided subtitle item dictionary to determine
        if it satisfies conditions indicating it is related to hearing-impaired
        captioning. The function checks against specific attributes and tags
        within the item to tell whether it relates to hearing-impaired captioning.

        :param item: A dictionary containing details about the subtitle item (tags
            or commentary).

        :return: A boolean value indicating whether the subtitle item is hearing-impaired.
        :rtype: bool
        """
        if 'hearingImpaired' in item and item['hearingImpaired']:
            return True

        # Comments include specific mention of removed or non HI
        non_hi_tag = ['hi remove', 'non hi', 'nonhi', 'non-hi', 'non-sdh', 'non sdh', 'nonsdh', 'sdh remove']
        if isinstance(item.get('commentary'), str) and any(x in item.get('commentary', '').lower() for x in non_hi_tag):
            return False

        # Commentaries include some specific strings
        hi_tag = ['_hi_', ' hi ', '.hi.', 'hi ', ' hi', 'sdh', '𝓢𝓓𝓗', '_cc_', ' cc ', '.cc.', 'closed caption']
        if isinstance(item.get('commentary'), str) and any(x in item.get('commentary', '').lower() for x in hi_tag):
            return True

        # nothing match so we consider it as non-HI
        return False

    @staticmethod
    def _is_forced(item: dict) -> bool:
        """
        Determines whether the given subtitle item is marked as "forced".

        This utility method checks if the subtitle item contains specific identifiers
        that indicate it is forced, such as the presence of "foreignParts" or predefined
        keywords in its commentary.

        :param item: Dictionary representing the subtitle item to be checked.
                     The dictionary may include keys such as `'foreignParts'`
                     and `'commentary'`.
        :type item: dict
        :return: True if the subtitle item is determined to be forced, otherwise False.
        :rtype: bool
        """
        if 'foreignParts' in item and item['foreignParts']:
            return True

        # Comments include specific mention of forced subtitles
        forced_tags = ['forced', 'foreign']
        if isinstance(item.get('commentary'), str) and any(x in item.get('commentary', '').lower() for x in forced_tags):
            return True

        # nothing match so we consider it as normal subtitles
        return False

    @staticmethod
    def _get_uploader_name(item: dict) -> str:
        """
        Returns the display name of the uploader based on the given subtitle item
        dictionary.

        This method identifies the uploader by matching the contributor ID with the
        uploader ID from the provided item. If a match is found, the display name of
        the uploader is returned. If there is no match, an empty string is returned.

        :param item: Dictionary containing contributor details and uploader ID.
        :type item: dict
        :return: The display name of the uploader if found; otherwise, an empty string.
        :rtype: str
        """
        for contributor in item['contributors']:
            if contributor['id'] == item['uploaderId']:
                return contributor['displayname']
        return ''

    @staticmethod
    def _status_raiser(response: Response):
        """
        Raises exceptions based on the HTTP response status code received.

        Intercepts the response and raises specific exceptions for various HTTP
        status codes to indicate the type of error condition encountered.
        If the response status code is neither explicitly handled nor 200
        (OK), it will invoke the `raise_for_status` method on the `Response`
        object.

        :param response: A `Response` object from an HTTP request.
        :type response: Response
        :raises APIThrottled: If the status code is 400, indicating invalid
                              request parameters.
        :raises AuthenticationError: If the status code is 401, indicating
                                      authentication is required.
        :raises ForbiddenError: If the status code is 403, indicating access
                                is denied to a resource.
        :raises TooManyRequests: If the status code is 429, indicating a rate
                                 limit has been exceeded.
        :raises HTTPError: If the status code is not 200 and is not explicitly
                           handled by any of the listed exceptions.
        """
        if response.status_code == 400:
            raise APIThrottled("Invalid request parameters")
        elif response.status_code == 401:
            raise AuthenticationError("Authentication required")
        elif response.status_code == 403:
            raise ForbiddenError("Access denied")
        elif response.status_code == 429:
            raise TooManyRequests("Rate limit exceeded")
        elif response.status_code != 200:
            response.raise_for_status()

    @staticmethod
    def _get_season_episode_from_release_info(releases_info: list) -> tuple:
        """
        Extracts season and episode details from a list of release information strings.

        This static method takes a list of release information strings and uses the `guessit`
        library to extract season and episode numbers. If season and episode numbers are
        found in the release information, they are returned as a tuple. The method stops
        processing once both season and episode values are identified.

        :param releases_info: A list of strings containing release information from which
            season and episode numbers are to be extracted.
        :type releases_info: list
        :return: A tuple containing the extracted season and episode numbers, or (None, None)
            if they could not be determined.
        :rtype: tuple
        """
        season = None
        episode = None
        if isinstance(releases_info, list):
            for release_info in releases_info:
                if season and episode:
                    break

                guessed = guessit(release_info, {"type": "episode", "includes": ["season", "episode"]})

                if not season and 'season' in guessed and guessed['season']:
                    season = guessed['season']
                if not episode and 'episode' in guessed and guessed['episode']:
                    episode = guessed['episode']
        return season, episode

    def list_subtitles(self, video: Video, languages: Set[Language]) -> list:
        """
        List all subtitles available for a given video in specified languages.

        This function queries available subtitles for the provided video and returns
        them in a list. It supports filtering by a set of specified languages.

        :param video: The video object for which subtitles need to be listed.
        :type video: Video
        :param languages: The set of languages to filter the list of subtitles.
        :type languages: Set[Language]
        :return: A list of subtitles filtered by the specified languages.
        :rtype: list
        """
        return self.query(languages, video)

    def download_subtitle(self, subtitle: SubsourceSubtitle) -> SubsourceSubtitle:
        """
        Downloads a subtitle file from the provider's API server. This function
        constructs a download URL for the given subtitle, retrieves the
        archive content, and extracts the subtitle data if it is a valid zip
        file.

        If the subtitle cannot be downloaded or extracted, the content of the
        subtitle will be set to None.

        :param subtitle: The subtitle object to download.
        :type subtitle: SubsourceSubtitle
        :return: The subtitle object after attempting to download its content.
        :rtype: SubsourceSubtitle
        """
        logger.debug('Downloading subtitle %r', subtitle)
        download_link = self._server_url() + f"subtitles/{subtitle.id}/download"

        r = self._get_subtitles_archive(download_link)

        self._status_raiser(r)

        if not r:
            logger.error(f'Could not download subtitle from {download_link}')
            subtitle.content = None
        else:
            archive_stream = io.BytesIO(r.content)
            if is_zipfile(archive_stream):
                archive = ZipFile(archive_stream)
                subtitle.content = self.get_subtitle_from_archive(subtitle, archive)
            else:
                logger.error(f'Could not unzip subtitle from {download_link}')
                subtitle.content = None

        return subtitle

    @region.cache_on_arguments(expiration_time=ARCHIVES_EXPIRATION_TIME)
    def _get_subtitles_archive(self, download_link: str) -> Response:
        """
        Fetches a subtitle archive from the given download link. The method uses caching
        to store the result for a defined expiration period and retries the network
        request upon failure due to transient issues.

        :param download_link: The URL for the subtitles archive to download.
        :type download_link: str
        :return: The HTTP response object containing the subtitle archive.
        :rtype: Response
        """
        return self.retry(
            lambda: self.session.get(download_link, params={'api_key': self.api_key}, timeout=30),
            amount=retry_amount,
            retry_timeout=retry_timeout
        )

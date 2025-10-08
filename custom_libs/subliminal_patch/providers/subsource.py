# -*- coding: utf-8 -*-
import logging
import os
import time
import io

from babelfish import language_converters
from zipfile import ZipFile, is_zipfile
from requests import Session

from subzero.language import Language
from subliminal import Episode, Movie
from subliminal.exceptions import ConfigurationError, AuthenticationError
from subliminal_patch.exceptions import APIThrottled, ForbiddenError, TooManyRequests
from .mixins import ProviderRetryMixin
from subliminal_patch.subtitle import Subtitle
from subliminal.subtitle import fix_line_ending
from subliminal_patch.providers import Provider
from subliminal_patch.providers import utils

logger = logging.getLogger(__name__)

retry_amount = 3
retry_timeout = 5

language_converters.register('subsource = subliminal_patch.converters.subsource:SubsourceConverter')
supported_languages = list(language_converters['subsource'].to_subsource.keys())


class SubsourceSubtitle(Subtitle):
    provider_name = 'subsource'
    hash_verifiable = False
    hearing_impaired_verifiable = True

    def __init__(self, language, forced, hearing_impaired, page_link, subtitles_id, release_names, uploader):
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

    @property
    def id(self):
        return self.subtitles_id

    def get_matches(self, video):
        matches = set()

        # handle movies and series separately
        if isinstance(video, Episode):
            # series
            matches.add('series')
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


class SubsourceProvider(ProviderRetryMixin, Provider):
    """Subsource Provider"""
    server_hostname = 'api.subsource.net'

    languages = {Language(*lang) for lang in supported_languages}
    languages.update(set(Language.rebuild(lang, forced=True) for lang in languages))
    languages.update(set(Language.rebuild(l, hi=True) for l in languages))

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

    def server_url(self):
        return f'https://{self.server_hostname}/api/v1/'

    def search_titles(self, title, imdb_id, season=None):
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
            lambda: self.session.get(self.server_url() + 'movies/search', params=parameters, timeout=30),
            amount=retry_amount,
            retry_timeout=retry_timeout
        )

        self._status_raiser(results)

        # deserialize results
        results_dict = results.json()['data']

        # loop over results
        for result in results_dict:
            if 'title' in result and 'releaseYear' in result:
                if title.lower() == result['title'].lower() and \
                        (not self.video.year or self.video.year == int(result['releaseYear'])):
                    title_id = result['movieId']
                    break
            else:
                continue

        if title_id:
            logger.debug(f'Found this title ID: {title_id}')
        else:
            logger.debug(f'No match found for {title}')

        return title_id

    def query(self, languages, video):
        self.video = video
        if isinstance(self.video, Episode):
            title = self.video.series
        else:
            title = self.video.title

        imdb_id = None
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

        # be sure to remove duplicates using list(set())
        language = [language_converters['subsource'].convert(lang.alpha3, lang.country, lang.script) for lang in
                    languages]
        only_hi = all([lang.hi for lang in languages])
        only_forced = all([lang.forced for lang in languages])
        if len(language):
            language = language[0]
        else:
            return []

        logger.debug(f'Searching for those languages: {language}')

        parameters = (
            ('api_key', self.api_key),
            ('language', language.lower()),
            ('limit', 100),
            ('movieId', title_id)
        )

        if only_hi:
            parameters += (('hearingImpaired', True),)
        elif only_forced:
            parameters += (('foreignParts', True),)

        # query the server
        if isinstance(self.video, Episode):
            parameters += (('seasonNumber', self.video.season), ('episodeNumber', self.video.episode))
            res = self.retry(
                lambda: self.session.get(self.server_url() + 'subtitles',
                                         params=parameters,
                                         timeout=30),
                amount=retry_amount,
                retry_timeout=retry_timeout
            )
        else:
            res = self.retry(
                lambda: self.session.get(self.server_url() + 'subtitles',
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

                subtitle = SubsourceSubtitle(
                    language=Language.fromalpha3b(language_converters['subsource'].reverse(item['language'].capitalize())[0]),
                    forced=self._is_forced(item),
                    hearing_impaired=self._is_hi(item),
                    page_link=page_link,
                    subtitles_id=item['subtitleId'],
                    release_names=item['releaseInfo'],
                    uploader=self._get_uploader_name(item),
                )
                subtitle.get_matches(self.video)
                subtitles.append(subtitle)

        return subtitles

    @staticmethod
    def _is_hi(item):
        if 'hearingImpaired' in item and item['hearingImpaired']:
            return True

        # Comments include specific mention of removed or non HI
        non_hi_tag = ['hi remove', 'non hi', 'nonhi', 'non-hi', 'non-sdh', 'non sdh', 'nonsdh', 'sdh remove']
        for tag in non_hi_tag:
            if tag in item.get('commentary', '').lower():
                return False

        # Archive filename include _HI_
        if '_hi_' in item.get('link', '').lower():
            return True

        # Comments or release names include some specific strings
        hi_keys = [item.get('commentary', '').lower(), [x.lower() for x in item.get('releaseInfo', [])]]
        hi_tag = ['_hi_', ' hi ', '.hi.', 'hi ', ' hi', 'sdh', '𝓢𝓓𝓗']
        for key in hi_keys:
            if any(x in key for x in hi_tag):
                return True

        # nothing match so we consider it as non-HI
        return False

    @staticmethod
    def _is_forced(item):
        if 'foreignParts' in item and item['foreignParts']:
            return True

        # Comments include specific mention of forced subtitles
        forced_tags = ['forced', 'foreign']
        for tag in forced_tags:
            if tag in item.get('commentary', '').lower():
                return True

        # nothing match so we consider it as normal subtitles
        return False

    @staticmethod
    def _get_uploader_name(item):
        for contributor in item['contributors']:
            if contributor['id'] == item['uploaderId']:
                return contributor['displayname']
        return ''

    @staticmethod
    def _status_raiser(response):
        if response.status_code == 400:
            raise APIThrottled("Bad Request")
        elif response.status_code == 401:
            raise AuthenticationError("Authentication required")
        elif response.status_code == 403:
            raise ForbiddenError("Access denied")
        elif response.status_code == 429:
            raise TooManyRequests("Rate limit exceeded")
        elif response.status_code != 200:
            response.raise_for_status()

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def download_subtitle(self, subtitle):
        logger.debug('Downloading subtitle %r', subtitle)
        download_link = self.server_url() + f"subtitles/{subtitle.id}/download"

        r = self.retry(
            lambda: self.session.get(download_link, params={'api_key': self.api_key}, timeout=30),
            amount=retry_amount,
            retry_timeout=retry_timeout
        )

        self._status_raiser(r)

        if not r:
            logger.error(f'Could not download subtitle from {download_link}')
            subtitle.content = None
            return
        else:
            archive_stream = io.BytesIO(r.content)
            if is_zipfile(archive_stream):
                archive = ZipFile(archive_stream)
                for name in archive.namelist():
                    # TODO when possible, deal with season pack / multiple files archive
                    subtitle_content = archive.read(name)
                    subtitle.content = fix_line_ending(subtitle_content)
                    return
            else:
                logger.error(f'Could not unzip subtitle from {download_link}')
                subtitle.content = None
                return

# -*- coding: utf-8 -*-
import logging
import os
import time
import io

from zipfile import ZipFile, is_zipfile
from urllib.parse import urljoin
from requests import Session

from babelfish import language_converters
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

language_converters.register('subdl = subliminal_patch.converters.subdl:SubdlConverter')


class SubdlSubtitle(Subtitle):
    provider_name = 'subdl'
    hash_verifiable = False
    hearing_impaired_verifiable = True

    def __init__(self, language, forced, hearing_impaired, page_link, download_link, file_id, release_names, uploader,
                 season=None, episode=None):
        super().__init__(language)
        language = Language.rebuild(language, hi=hearing_impaired, forced=forced)

        self.season = season
        self.episode = episode
        self.releases = release_names
        self.release_info = ', '.join(release_names)
        self.language = language
        self.forced = forced
        self.hearing_impaired = hearing_impaired
        self.file_id = file_id
        self.page_link = page_link
        self.download_link = download_link
        self.uploader = uploader
        self.matches = None

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
            # tmdb 
            matches.add('tmdb_id')

        utils.update_matches(matches, video, self.release_info)

        self.matches = matches

        return matches


class SubdlProvider(ProviderRetryMixin, Provider):
    """Subdl Provider"""
    server_hostname = 'api.subdl.com'

    languages = {Language(*lang) for lang in list(language_converters['subdl'].to_subdl.keys())}
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

    def query(self, languages, video):
        self.video = video
        if isinstance(self.video, Episode):
            title = self.video.series
        else:
            title = self.video.title

        imdb_id = None
        tmdb_id = None
        if isinstance(self.video, Episode) and self.video.series_imdb_id:
            imdb_id = self.video.series_imdb_id
        elif isinstance(self.video, Movie):
            if self.video.imdb_id:
               imdb_id = self.video.imdb_id
            if self.video.tmdb_id:
               tmdb_id = self.video.tmdb_id

        # be sure to remove duplicates using list(set())
        langs_list = sorted(list(set([language_converters['subdl'].convert(lang.alpha3, lang.country, lang.script) for
                                      lang in languages])))

        langs = ','.join(langs_list)
        logger.debug(f'Searching for those languages: {langs}')

        # query the server
        if isinstance(self.video, Episode):
            res = self.retry(
                lambda: self.session.get(self.server_url() + 'subtitles',
                                         params=(('api_key', self.api_key),
                                                 ('episode_number', self.video.episode),
                                                 ('film_name', title if not imdb_id else None),
                                                 ('imdb_id', imdb_id if imdb_id else None),
                                                 ('languages', langs),
                                                 ('season_number', self.video.season),
                                                 ('subs_per_page', 30),
                                                 ('type', 'tv'),
                                                 ('comment', 1),
                                                 ('releases', 1),
                                                 ('bazarr', 1)),  # this argument filter incompatible image based or
                                         # txt subtitles
                                         timeout=30),
                amount=retry_amount,
                retry_timeout=retry_timeout
            )
        else:
            params = {
                       'api_key': self.api_key,
                       'film_name': title if not imdb_id else None,
                       'imdb_id': imdb_id,
                       'languages': langs,
                       'subs_per_page': 30,
                       'type': 'movie',
                       'comment': 1,
                       'releases': 1,
                       'bazarr': 1
            }
            res = self.retry(
                lambda: self.session.get(self.server_url() + 'subtitles',
                                         params=params, # this argument filter incompatible image based or
                                         # txt subtitles
                                         timeout=30),
                amount=retry_amount,
                retry_timeout=retry_timeout
            )

            # subdl also allows searching by TMDB ID, and some movies don't always
            # have the correct IMDB ID, or may not have it at all. We also search by TMDB ID
            # if it's available for the movie.
            if res.status_code == 200:
                # if the previous request with IMDb ID reported errors
                res_data=res.json()

                if 'status' in res_data and not res_data['status']:
                    if not tmdb_id:
                        logger.debug("No subtitles found via IMDb id or film name. TMDB ID unavailable for fallback")

                    # If the movie also has the TMDB ID code, we try to search
                    # for subtitles using only the TMDB ID code
                    else:
                        logger.debug("No subtitles found via IMDb id or film name. Search instead with TMDB id")

                        params.pop('film_name', None)
                        params.pop('imdb_id', None)
                        params['tmdb_id']=tmdb_id

                        res = self.retry(
                            lambda: self.session.get(self.server_url() + 'subtitles',
                                                     params=params,
                                                     timeout=30),
                            amount=retry_amount,
                            retry_timeout=retry_timeout
                        )

        if res.status_code == 429:
            raise APIThrottled("Too many requests")
        elif res.status_code == 403:
            raise ConfigurationError("Invalid API key")
        elif res.status_code != 200:
            res.raise_for_status()

        subtitles = []

        result = res.json()

        if ('success' in result and not result['success']) or ('status' in result and not result['status']):
            logger.debug(result)
            if 'error' in result:
                raise ProviderError(result['error'])

        logger.debug(f"Query returned {len(result['subtitles'])} subtitles")

        if len(result['subtitles']):
            for item in result['subtitles']:
                if (isinstance(self.video, Episode) and
                        item.get('episode_from', False) != item.get('episode_end', False)):
                    # ignore season packs
                    continue
                else:
                    subtitle = SubdlSubtitle(
                        language=Language.fromsubdl(item['language']),
                        forced=self._is_forced(item),
                        hearing_impaired=item.get('hi', False) or self._is_hi(item),
                        page_link=urljoin("https://subdl.com", item.get('subtitlePage', '')),
                        download_link=item['url'],
                        file_id=item['name'],
                        release_names=item.get('releases', []),
                        uploader=item.get('author', ''),
                        season=item.get('season', None),
                        episode=item.get('episode', None),
                    )
                    subtitle.get_matches(self.video)
                    if subtitle.language in languages:  # make sure only desired subtitles variants are returned
                        subtitles.append(subtitle)

        return subtitles

    @staticmethod
    def _is_hi(item):
        # Comments include specific mention of removed or non HI
        non_hi_tag = ['hi remove', 'non hi', 'nonhi', 'non-hi', 'non-sdh', 'non sdh', 'nonsdh', 'sdh remove']
        for tag in non_hi_tag:
            if tag in item.get('comment', '').lower():
                return False

        # Archive filename include _HI_
        if '_hi_' in item.get('name', '').lower():
            return True

        # Comments or release names include some specific strings
        hi_keys = [item.get('comment', '').lower(), [x.lower() for x in item.get('releases', [])]]
        hi_tag = ['_hi_', ' hi ', '.hi.', 'hi ', ' hi', 'sdh', '𝓢𝓓𝓗']
        for key in hi_keys:
            if any(x in key for x in hi_tag):
                return True

        # nothing match so we consider it as non-HI
        return False

    @staticmethod
    def _is_forced(item):
        # Comments include specific mention of forced subtitles
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
        download_link = urljoin("https://dl.subdl.com", subtitle.download_link)

        r = self.retry(
            lambda: self.session.get(download_link, timeout=30),
            amount=retry_amount,
            retry_timeout=retry_timeout
        )

        if r.status_code == 429 or (r.status_code == 500 and r.text == 'Download limit exceeded'):
            raise DownloadLimitExceeded("Daily download limit exceeded")
        elif r.status_code == 403:
            raise ConfigurationError("Invalid API key")
        elif r.status_code != 200:
            r.raise_for_status()

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

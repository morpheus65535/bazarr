# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime
import logging
import lzma
import os
import tempfile

from dogpile.cache import make_region
from guessit import guessit
from requests import Session
from subzero.language import Language


from subliminal.exceptions import ConfigurationError, ProviderError
from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.video import Episode

try:
    from lxml import etree
except ImportError:
    try:
        import xml.etree.cElementTree as etree
    except ImportError:
        import xml.etree.ElementTree as etree

logger = logging.getLogger(__name__)

# TODO: Test and Support Other Languages
supported_languages = [
    "eng",  # English
    "ita",  # Italian
]


class AnimeToshoSubtitle(Subtitle):
    """AnimeTosho.org Subtitle."""
    provider_name = 'animetosho'

    def __init__(self, language, download_link, meta):
        super(AnimeToshoSubtitle, self).__init__(language, page_link=download_link)
        self.meta = meta
        self.download_link = download_link

    @property
    def id(self):
        return self.download_link

    def get_matches(self, video):
        matches = set()
        matches |= guess_matches(video, guessit(self.meta['filename']))

        # Add these data are explicit extracted from the API and they always have to match otherwise they wouldn't
        # arrive at this point and would stop on list_subtitles.
        matches.update(['title', 'series', 'tvdb_id', 'season', 'episode'])

        return matches


class AnimeToshoProvider(Provider, ProviderSubtitleArchiveMixin):
    """AnimeTosho.org Provider."""
    subtitle_class = AnimeToshoSubtitle
    languages = {Language('por', 'BR')} | {Language(sl) for sl in supported_languages}
    video_types = Episode

    def __init__(self, search_threshold=None, anidb_api_client=None, anidb_api_client_ver=None, cache_dir=None):
        self.session = None

        if not all([search_threshold, anidb_api_client, anidb_api_client_ver]):
            raise ConfigurationError("Search threshold, Api Client and Version must be specified!")

        cache_dir = os.path.join(
            cache_dir or tempfile.gettempdir(), self.__class__.__name__.lower()
        )

        self.search_threshold = search_threshold
        self.anidb_api_client = anidb_api_client
        self.anidb_api_client_ver = anidb_api_client_ver
        self.cache = make_region().configure(
            'dogpile.cache.dbm', expiration_time=datetime.timedelta(days=1).total_seconds(), arguments={
                "filename": os.path.join(cache_dir)
            }
        )

    def initialize(self):
        self.session = Session()

    def terminate(self):
        self.session.close()

    def list_subtitles(self, video, languages):
        anidb_episode_id = self._get_episode_id(video)

        if not anidb_episode_id:
            raise ProviderError('Unable to retrieve anidb episode id')

        return [s for s in self._get_series(anidb_episode_id) if s.language in languages]

    def download_subtitle(self, subtitle):
        logger.info('Downloading subtitle %r', subtitle)

        r = self.session.get(subtitle.page_link, timeout=10)
        r.raise_for_status()

        # Check if the bytes content starts with the xz magic number of the xz archives
        if not self._is_xz_file(r.content):
            raise ProviderError('Unidentified archive type')

        subtitle.content = lzma.decompress(r.content)

        return subtitle

    @staticmethod
    def _is_xz_file(content):
        return content.startswith(b'\xFD\x37\x7A\x58\x5A\x00')

    def _get_episode_id(self, video):
        api_url = 'http://api.anidb.net:9001/httpapi'

        series_id = self._get_series_id(video)

        if not series_id:
            return None

        cache_key = 'animetosho_series:{}.episodes'.format(series_id)

        cached_episodes = self.cache.get(cache_key)

        if cached_episodes:
            logger.debug('Using cached episodes for series %r', series_id)

            episode_elements = etree.fromstring(cached_episodes)

            cached_episode = int(episode_elements.find(f".//episode[epno='{video.episode}']").attrib.get('id'))

            if cached_episode:
                return cached_episode

        logger.debug('Cached episodes not found. Retrieving from API %r', series_id)

        r = self.session.get(
            api_url,
            params={
                'request': 'anime',
                'client': self.anidb_api_client,
                'clientver': self.anidb_api_client_ver,
                'protover': 1,
                'aid': series_id
            },
            timeout=10)
        r.raise_for_status()

        xml_root = etree.fromstring(r.content)

        if xml_root.attrib.get('code') == '500':
            raise ProviderError('AniDb API Abuse detected. Banned status.')

        episode_elements = xml_root.find('episodes')

        # Cache the episodes
        self.cache.set(cache_key, etree.tostring(episode_elements, encoding='utf-8', method='xml'))

        logger.debug('Cache written for series %r', series_id)

        return int(episode_elements.find(f".//episode[epno='{video.episode}']").attrib.get('id'))

    def _get_series_id(self, video):
        cache_key_anidb_id = 'animetosho_tvdbid:{}.anidb_id'.format(video.series_tvdb_id)
        cache_key_id_mappings = 'animetosho_id_mappings'

        cached_series_id = self.cache.get(cache_key_anidb_id)

        if cached_series_id:
            logger.debug('Using cached value for series tvdb id %r', video.series_tvdb_id)

            return cached_series_id

        id_mappings = self.cache.get(cache_key_id_mappings)

        if not id_mappings:
            logger.debug('Id mappings not cached, retrieving fresh mappings')

            r = self.session.get(
                'https://raw.githubusercontent.com/Anime-Lists/anime-lists/master/anime-list.xml',
                timeout=10
            )

            r.raise_for_status()

            id_mappings = r.content

            self.cache.set(cache_key_id_mappings, id_mappings)

        xml_root = etree.fromstring(id_mappings)

        season = video.season if video.season else 0

        anime = xml_root.find(f".//anime[@tvdbid='{video.series_tvdb_id}'][@defaulttvdbseason='{season}']")

        if not anime:
            return None

        anidb_id = int(anime.attrib.get('anidbid'))

        self.cache.set(cache_key_anidb_id, anidb_id)

        logger.debug('Cache written for anidb %r', anidb_id)

        return anidb_id

    def _get_series(self, episode_id):
        storage_download_url = 'https://animetosho.org/storage/attach/'
        feed_api_url = 'https://feed.animetosho.org/json'

        subtitles = []

        entries = self._get_series_entries(episode_id)

        for entry in entries:
            r = self.session.get(
                feed_api_url,
                params={
                    'show': 'torrent',
                    'id': entry['id'],
                },
                timeout=10
            )
            r.raise_for_status()

            for file in r.json()['files']:
                if 'attachments' not in file:
                    continue

                subtitle_files = list(filter(lambda f: f['type'] == 'subtitle', file['attachments']))

                for subtitle_file in subtitle_files:
                    hex_id = format(subtitle_file['id'], '08x')

                    subtitle = self.subtitle_class(
                        Language.fromalpha3b(subtitle_file['info']['lang']),
                        storage_download_url + '{}/{}.xz'.format(hex_id, subtitle_file['id']),
                        meta=file,
                    )

                    logger.debug('Found subtitle %r', subtitle)

                    subtitles.append(subtitle)

        return subtitles

    def _get_series_entries(self, episode_id):
        api_url = 'https://feed.animetosho.org/json'

        r = self.session.get(
            api_url,
            params={
                'eid': episode_id,
            },
            timeout=10
        )

        r.raise_for_status()

        j = r.json()

        # Ignore records that are not yet ready or has been abandoned by AnimeTosho.
        entries = list(filter(lambda t: t['status'] == 'complete', j))[:self.search_threshold]

        # Return the latest entries that have been added as it is used to cutoff via the user configuration threshold
        entries.sort(key=lambda t: t['timestamp'], reverse=True)

        return entries

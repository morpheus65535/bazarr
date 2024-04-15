# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import lzma

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

supported_languages = [
    "ara",  # Arabic
    "eng",  # English
    "fin",  # Finnish
    "fra",  # French
    "ita",  # Italian
    "jpn",  # Japanese
    "pol",  # Polish
    "spa",  # Spanish
    "tur",  # Turkish
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

    def __init__(self, search_threshold=None):
        self.session = None

        if not all([search_threshold]):
            raise ConfigurationError("Search threshold, Api Client and Version must be specified!")

        self.search_threshold = search_threshold

    def initialize(self):
        self.session = Session()

    def terminate(self):
        self.session.close()

    def list_subtitles(self, video, languages):
        if not video.series_anidb_episode_id:
            raise ProviderError("Video does not have an AnimeTosho Episode ID!")

        return [s for s in self._get_series(video.series_anidb_episode_id) if s.language in languages]

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

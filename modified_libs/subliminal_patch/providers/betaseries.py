# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import logging
import os
import re
import io
import rarfile
import zipfile

from babelfish import language_converters
from guessit import guessit
from requests import Session
from subzero.language import Language

from subliminal import Movie, Episode, ProviderError, __short_version__
from subliminal.exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded, ProviderError
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.subtitle import fix_line_ending, SUBTITLE_EXTENSIONS
from subliminal_patch.providers import Provider
from subzero.language import Language

logger = logging.getLogger(__name__)

server_url = 'https://api.betaseries.com/'


class BetaSeriesSubtitle(Subtitle):
    provider_name = 'betaseries'

    def __init__(self, subtitle_id, language, video_name, url, matches, source):
        super(BetaSeriesSubtitle, self).__init__(language, page_link=url)
        self.subtitle_id = subtitle_id
        self.video_name = video_name
        self.download_url = url
        self.matches = matches
        self.source = source

    @property
    def id(self):
        return self.subtitle_id

    @property
    def download_link(self):
        return self.download_url

    @property
    def release_info(self):
        return self.video_name

    def get_matches(self, video):
        matches = self.matches

        if isinstance(video, Episode):
            matches |= guess_matches(video, guessit(
                self.video_name, {'type': 'episode'}), partial=True)

        return matches


class BetaSeriesProvider(Provider):
    """BetaSeries Provider"""
    languages = {Language(l) for l in ['fra', 'eng']}
    video_types = (Episode,)

    def __init__(self, token=None):
        if not token:
            raise ConfigurationError('Token must be specified')
        self.token = token

    def initialize(self):
        self.session = Session()
        self.session.headers = {
            'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")}

    def terminate(self):
        self.session.close()

    def query(self, languages, video):
        # query the server
        result = None
        self.video = video
        matches = set()
        if video.tvdb_id:
            params = {'key': self.token,
                      'thetvdb_id': video.tvdb_id,
                      'v': 3.0,
                      'subtitles': 1}
            logger.debug('Searching subtitles %r', params)
            res = self.session.get(
                server_url + 'episodes/display', params=params, timeout=10)
            res.raise_for_status()
            result = res.json()
            matches.add('tvdb_id')
        elif video.series_tvdb_id:
            params = {'key': self.token,
                      'thetvdb_id': video.series_tvdb_id,
                      'season': video.season,
                      'episode': video.episode,
                      'subtitles': 1,
                      'v': 3.0}
            logger.debug('Searching subtitles %r', params)
            res = self.session.get(
                server_url + 'shows/episodes', params=params, timeout=10)
            res.raise_for_status()
            result = res.json()
            matches.add('series_tvdb_id')
        else:
            logger.debug(
                'The show has no tvdb_id and series_tvdb_id: the search can\'t be done')
            return []

        if result['errors'] != []:
            logger.debug('Status error: %r', result['errors'])
            return []

        # parse the subtitles
        subtitles = []
        if 'episode' in result:
            subs = result['episode']['subtitles']
        elif 'episodes' in result:
            subs = result['episodes'][0]['subtitles']
        else:
            return []

        for sub in subs:
            language = _translateLanguageCodeToLanguage(sub['language'])
            if language in languages:
                # Filter seriessub source because it shut down so the links are all 404
                if str(sub['source']) != 'seriessub':
                    subtitles.append(BetaSeriesSubtitle(
                        sub['id'], language, sub['file'], sub['url'], matches, str(sub['source'])))

        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def download_subtitle(self, subtitle):
        logger.info('Downloading subtitle %r', subtitle)
        r = self.session.get(subtitle.download_link, timeout=10)
        if r.status_code == 404:
            logger.error('Error 404 downloading %r', subtitle)
            return
        else:
            r.raise_for_status()

        archive = _get_archive(r.content)
        if archive:
            subtitle_names = _get_subtitle_names_from_archive(archive)
            subtitle_to_download = _choose_subtitle_with_release_group(subtitle_names, self.video.release_group)
            logger.debug('Subtitle to download: ' + subtitle_to_download)
            subtitle_content = archive.read(subtitle_to_download)
        else:
            subtitle_content = r.content

        if subtitle_content:
            subtitle.content = fix_line_ending(subtitle_content)
        else:
            logger.error('Could not extract subtitle from %r', archive)


def _get_archive(content):
    # open the archive
    archive_stream = io.BytesIO(content)
    archive = None
    if rarfile.is_rarfile(archive_stream):
        logger.debug('Identified rar archive')
        archive = rarfile.RarFile(archive_stream)
    elif zipfile.is_zipfile(archive_stream):
        logger.debug('Identified zip archive')
        archive = zipfile.ZipFile(archive_stream)

    return archive


def _get_subtitle_names_from_archive(archive):
    subtitlesToConsider = []
    for name in archive.namelist():
        # discard hidden files
        if os.path.split(name)[-1].startswith('.'):
            continue

        # discard non-subtitle files
        if not name.lower().endswith(SUBTITLE_EXTENSIONS):
            continue

        subtitlesToConsider.append(name)

    if len(subtitlesToConsider)>0:
        logger.debug('Subtitles in archive: ' + ' '.join(subtitlesToConsider))
        return subtitlesToConsider
    else:
        return None


def _translateLanguageCodeToLanguage(languageCode):
    if languageCode.lower() == 'vo':
        return Language.fromalpha2('en')
    elif languageCode.lower() == 'vf':
        return Language.fromalpha2('fr')


def _choose_subtitle_with_release_group(subtitle_names, release_group):
    if release_group:
        for subtitle in subtitle_names:
            if release_group in subtitle:
                return subtitle
    return subtitle_names[0]

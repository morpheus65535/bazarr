# -*- coding: utf-8 -*-
import io
import logging
import os
import zipfile

import rarfile
from subzero.language import Language
from guessit import guessit
from requests import Session

from subliminal import __short_version__
from subliminal.providers import ParserBeautifulSoup, Provider
from subliminal.subtitle import SUBTITLE_EXTENSIONS, Subtitle, fix_line_ending, guess_matches
from subliminal.video import Episode, Movie

logger = logging.getLogger(__name__)


class GreekSubtitlesSubtitle(Subtitle):
    """GreekSubtitles Subtitle."""
    provider_name = 'greeksubtitles'

    def __init__(self, language, page_link, version, download_link):
        super(GreekSubtitlesSubtitle, self).__init__(language, page_link=page_link)
        self.version = version
        self.download_link = download_link
        self.hearing_impaired = None
        self.encoding = 'windows-1253'

    @property
    def id(self):
        return self.download_link

    def get_matches(self, video):
        matches = set()

        # episode
        if isinstance(video, Episode):
            # other properties
            matches |= guess_matches(video, guessit(self.version, {'type': 'episode'}), partial=True)
        # movie
        elif isinstance(video, Movie):
            # other properties
            matches |= guess_matches(video, guessit(self.version, {'type': 'movie'}), partial=True)

        return matches


class GreekSubtitlesProvider(Provider):
    """GreekSubtitles Provider."""
    languages = {Language(l) for l in ['ell', 'eng']}
    server_url = 'http://gr.greek-subtitles.com/'
    search_url = 'search.php?name={}'
    download_url = 'http://www.greeksubtitles.info/getp.php?id={:d}'
    subtitle_class = GreekSubtitlesSubtitle

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/{}'.format(__short_version__)

    def terminate(self):
        self.session.close()

    def query(self, keyword, season=None, episode=None, year=None):
        params = keyword
        if season and episode:
            params += ' S{season:02d}E{episode:02d}'.format(season=season, episode=episode)
        elif year:
            params += ' {:4d}'.format(year)

        logger.debug('Searching subtitles %r', params)
        subtitles = []
        search_link = self.server_url + self.search_url.format(params)
        while True:
            r = self.session.get(search_link, timeout=30)
            r.raise_for_status()

            if not r.content:
                logger.debug('No data returned from provider')
                return []

            soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['lxml', 'html.parser'])

            # loop over subtitles cells
            for cell in soup.select('td.latest_name > a:nth-of-type(1)'):
                # read the item
                subtitle_id = int(cell['href'].rsplit('/', 2)[1])
                page_link = cell['href']
                language = Language.fromalpha2(cell.parent.find('img')['src'].split('/')[-1].split('.')[0])
                version = cell.text.strip() or None
                if version is None:
                    version = ""

                subtitle = self.subtitle_class(language, page_link, version, self.download_url.format(subtitle_id))

                logger.debug('Found subtitle %r', subtitle)
                subtitles.append(subtitle)

            anchors = soup.select('td a')
            next_page_available = False
            for anchor in anchors:
                if 'Next' in anchor.text and 'search.php' in anchor['href']:
                    search_link = self.server_url + anchor['href']
                    next_page_available = True
                    break
            if not next_page_available:
                break

        return subtitles

    def list_subtitles(self, video, languages):
        if isinstance(video, Episode):
            titles = [video.series] + video.alternative_series
        elif isinstance(video, Movie):
            titles = [video.title] + video.alternative_titles
        else:
            titles = []

        subtitles = []
        # query for subtitles with the show_id
        for title in titles:
            if isinstance(video, Episode):
                subtitles += [s for s in self.query(title, season=video.season, episode=video.episode,
                                                    year=video.year)
                              if s.language in languages]
            elif isinstance(video, Movie):
                subtitles += [s for s in self.query(title, year=video.year)
                              if s.language in languages]

        return subtitles

    def download_subtitle(self, subtitle):
        if isinstance(subtitle, GreekSubtitlesSubtitle):
            # download the subtitle
            logger.info('Downloading subtitle %r', subtitle)
            r = self.session.get(subtitle.download_link, headers={'Referer': subtitle.page_link},
                                 timeout=30)
            r.raise_for_status()

            if not r.content:
                logger.debug('Unable to download subtitle. No data returned from provider')
                return

            archive = _get_archive(r.content)

            subtitle_content = _get_subtitle_from_archive(archive)
            if subtitle_content:
                subtitle.content = fix_line_ending(subtitle_content)
            else:
                logger.debug('Could not extract subtitle from %r', archive)


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


def _get_subtitle_from_archive(archive):
    for name in archive.namelist():
        # discard hidden files
        if os.path.split(name)[-1].startswith('.'):
            continue

        # discard non-subtitle files
        if not name.lower().endswith(SUBTITLE_EXTENSIONS):
            continue

        return archive.read(name)

    return None

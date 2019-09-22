# -*- coding: utf-8 -*-
import io
import logging
import os
import time
import zipfile

import rarfile
from subzero.language import Language
from requests import Session

from subliminal import __short_version__
from subliminal.exceptions import ServiceUnavailable
from subliminal.providers import ParserBeautifulSoup, Provider
from subliminal.subtitle import SUBTITLE_EXTENSIONS, Subtitle, fix_line_ending,guess_matches
from subliminal.video import Episode, Movie
from subliminal_patch.exceptions import ParseResponseError

logger = logging.getLogger(__name__)


class SubdivxSubtitle(Subtitle):
    provider_name = 'subdivx'
    hash_verifiable = False

    def __init__(self, language, page_link, description, title):
        super(SubdivxSubtitle, self).__init__(language, hearing_impaired=False,
                                              page_link=page_link)
        self.description = description.lower()
        self.title = title

    @property
    def id(self):
        return self.page_link

    def get_matches(self, video):
        matches = set()

        # episode
        if isinstance(video, Episode):
            # already matched in search query
            matches.update(['title', 'series', 'season', 'episode', 'year'])

        # movie
        elif isinstance(video, Movie):
            # already matched in search query
            matches.update(['title', 'year'])

        # release_group
        if video.release_group and video.release_group.lower() in self.description:
            matches.add('release_group')

        # resolution
        if video.resolution and video.resolution.lower() in self.description:
            matches.add('resolution')

        # format
        if video.format:
            formats = [video.format.lower()]
            if formats[0] == "web-dl":
                formats.append("webdl")
                formats.append("webrip")
                formats.append("web ")
            for frmt in formats:
                if frmt.lower() in self.description:
                    matches.add('format')
                    break

        # video_codec
        if video.video_codec:
            video_codecs = [video.video_codec.lower()]
            if video_codecs[0] == "h264":
                formats.append("x264")
            elif video_codecs[0] == "h265":
                formats.append("x265")
            for vc in formats:
                if vc.lower() in self.description:
                    matches.add('video_codec')
                    break

        return matches


class SubdivxSubtitlesProvider(Provider):
    provider_name = 'subdivx'
    hash_verifiable = False
    languages = {Language.fromalpha2(l) for l in ['es']}
    subtitle_class = SubdivxSubtitle

    server_url = 'https://www.subdivx.com/'
    multi_result_throttle = 2
    language_list = list(languages)

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/{}'.format(__short_version__)

    def terminate(self):
        self.session.close()

    def query(self, keyword, season=None, episode=None, year=None):
        query = keyword
        if season and episode:
            query += ' S{season:02d}E{episode:02d}'.format(season=season, episode=episode)
        elif year:
            query += ' {:4d}'.format(year)

        params = {
            'buscar': query,  # search string
            'accion': 5,  # action search
            'oxdown': 1,  # order by downloads descending
            'pg': 1  # page 1
        }

        logger.debug('Searching subtitles %r', query)
        subtitles = []
        language = self.language_list[0]
        search_link = self.server_url + 'index.php'
        while True:
            response = self.session.get(search_link, params=params, timeout=10)
            self._check_response(response)

            try:
                page_subtitles = self._parse_subtitles_page(response, language)
            except Exception as e:
                raise ParseResponseError('Error parsing subtitles list: ' + str(e))

            subtitles += page_subtitles

            if len(page_subtitles) >= 20:
                params['pg'] += 1  # search next page
                time.sleep(self.multi_result_throttle)
            else:
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
        for title in titles:
            if isinstance(video, Episode):
                subtitles += [s for s in self.query(title, season=video.season,
                                                    episode=video.episode, year=video.year)
                              if s.language in languages]
            elif isinstance(video, Movie):
                subtitles += [s for s in self.query(title, year=video.year)
                              if s.language in languages]

        return subtitles

    def download_subtitle(self, subtitle):
        if isinstance(subtitle, SubdivxSubtitle):
            # download the subtitle
            logger.info('Downloading subtitle %r', subtitle)

            # get download link
            download_link = self._get_download_link(subtitle)

            # download zip / rar file with the subtitle
            response = self.session.get(download_link, headers={'Referer': subtitle.page_link}, timeout=30)
            self._check_response(response)

            # open the compressed archive
            archive = self._get_archive(response.content)

            # extract the subtitle
            subtitle_content = self._get_subtitle_from_archive(archive)
            subtitle.content = fix_line_ending(subtitle_content)

    def _check_response(self, response):
        if response.status_code != 200:
            raise ServiceUnavailable('Bad status code: ' + str(response.status_code))

    def _parse_subtitles_page(self, response, language):
        subtitles = []

        page_soup = ParserBeautifulSoup(response.content.decode('iso-8859-1', 'ignore'), ['lxml', 'html.parser'])
        title_soups = page_soup.find_all("div", {'id': 'menu_detalle_buscador'})
        body_soups = page_soup.find_all("div", {'id': 'buscador_detalle'})

        for subtitle in range(0, len(title_soups)):
            title_soup, body_soup = title_soups[subtitle], body_soups[subtitle]

            # title
            title = title_soup.find("a").text.replace("Subtitulo de ", "")
            page_link = title_soup.find("a")["href"].replace('http://', 'https://')

            # body
            description = body_soup.find("div", {'id': 'buscador_detalle_sub'}).text

            subtitle = self.subtitle_class(language, page_link, description, title)

            logger.debug('Found subtitle %r', subtitle)
            subtitles.append(subtitle)

        return subtitles

    def _get_download_link(self, subtitle):
        response = self.session.get(subtitle.page_link, timeout=10)
        self._check_response(response)
        try:
            page_soup = ParserBeautifulSoup(response.content.decode('iso-8859-1', 'ignore'), ['lxml', 'html.parser'])
            links_soup = page_soup.find_all("a", {'class': 'detalle_link'})
            for link_soup in links_soup:
                if link_soup['href'].startswith('bajar'):
                    return self.server_url + link_soup['href']
        except Exception as e:
            raise ParseResponseError('Error parsing download link: ' + str(e))

        raise ParseResponseError('Download link not found')

    def _get_archive(self, content):
        # open the archive
        archive_stream = io.BytesIO(content)
        if rarfile.is_rarfile(archive_stream):
            logger.debug('Identified rar archive')
            archive = rarfile.RarFile(archive_stream)
        elif zipfile.is_zipfile(archive_stream):
            logger.debug('Identified zip archive')
            archive = zipfile.ZipFile(archive_stream)
        else:
            raise ParseResponseError('Unsupported compressed format')

        return archive

    def _get_subtitle_from_archive(self, archive):
        for name in archive.namelist():
            # discard hidden files
            if os.path.split(name)[-1].startswith('.'):
                continue

            # discard non-subtitle files
            if not name.lower().endswith(SUBTITLE_EXTENSIONS):
                continue

            return archive.read(name)

        raise ParseResponseError('Can not find the subtitle in the compressed file')

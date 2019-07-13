# -*- coding: utf-8 -*-
import io
import logging
import os
import zipfile

import rarfile
from subzero.language import Language
from guessit import guessit
from requests import Session
from six import text_type

from subliminal import __short_version__
from subliminal.providers import ParserBeautifulSoup, Provider
from subliminal.subtitle import SUBTITLE_EXTENSIONS, Subtitle, fix_line_ending, guess_matches
from subliminal.video import Episode, Movie

logger = logging.getLogger(__name__)


class ZimukuSubtitle(Subtitle):
    """Zimuku Subtitle."""
    provider_name = 'zimuku'

    def __init__(self, language, page_link, version, download_link):
        super(ZimukuSubtitle, self).__init__(language, page_link=page_link)
        self.version = version
        self.download_link = download_link
        self.hearing_impaired = None
        self.encoding = 'utf-8'

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


class ZimukuProvider(Provider):
    """Zimuku Provider."""
    languages = {Language(l) for l in ['zho', 'eng']}

    server_url = 'http://www.zimuku.la'
    search_url = '/search?q={}'
    download_url = 'http://www.zimuku.la/'
    
    UserAgent  = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'

    subtitle_class = ZimukuSubtitle

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
        search_link = self.server_url + text_type(self.search_url).format(params)

        r = self.session.get(search_link, timeout=30)
        r.raise_for_status()

        if not r.content:
            logger.debug('No data returned from provider')
            return []

        soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['lxml', 'html.parser'])

        for entity in soup.select('div.item.prel.clearfix a:nth-of-type(2)'):
            moviename = entity.text
            entity_url = self.server_url + entity['href']
            logger.debug(entity_url)
            r = self.session.get(entity_url, timeout=30)
            r.raise_for_status()
            logger.debug('looking into ' + entity_url)

            soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['lxml', 'html.parser']).find("div", class_="subs box clearfix")
            # loop over subtitles cells

            subs = soup.tbody.find_all("tr")
            for sub in subs:
                page_link = '%s%s' % (self.server_url, sub.a.get('href').encode('utf-8'))
                version = sub.a.text.encode('utf-8') or None
                if version is None:
                    version = ""
                try:
                    td = sub.find("td", class_="tac lang")
                    r2 = td.find_all("img")
                    langs = [x.get('title').encode('utf-8') for x in r2]
                except:
                    langs = '未知' 
                name = '%s (%s)' % (version, ",".join(langs))

                if ('English' in langs) and not(('简体中文' in langs) or ('繁體中文' in langs)):
                    language = Language('eng')
                else:
                    language = Language('zho')
                # read the item
                subtitle = self.subtitle_class(language, page_link, version, page_link.replace("detail","dld"))

                logger.debug('Found subtitle %r', subtitle)
                subtitles.append(subtitle)

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
        if isinstance(subtitle, ZimukuSubtitle):
            # download the subtitle
            logger.info('Downloading subtitle %r', subtitle)
            r = self.session.get(subtitle.download_link, headers={'Referer': subtitle.page_link},
                                 timeout=30)
            r.raise_for_status()

            if not r.content:
                logger.debug('Unable to download subtitle. No data returned from provider')
                return

            soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['lxml', 'html.parser'])
            links = soup.find("div", {"class":"clearfix"}).find_all('a')
            # TODO: add settings for choice

            for down_link in links:
                url = down_link.get('href').encode('utf-8')
                url = self.server_url + url
                r = self.session.get(url, headers={'Referer': subtitle.download_link},
                                 timeout=30)
                r.raise_for_status()

                if len(r.content) > 1024:
                    break

            archive_stream = io.BytesIO(r.content)
            archive = None
            if rarfile.is_rarfile(archive_stream):
                logger.debug('Identified rar archive')
                archive = rarfile.RarFile(archive_stream)
                subtitle_content = _get_subtitle_from_archive(archive)
            elif zipfile.is_zipfile(archive_stream):
                logger.debug('Identified zip archive')
                archive = zipfile.ZipFile(archive_stream)
                subtitle_content = _get_subtitle_from_archive(archive)
            else:
                subtitle_content = r.content
            
            if subtitle_content:
                subtitle.content = fix_line_ending(subtitle_content)
            else:
                logger.debug('Could not extract subtitle from %r', archive)


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

# -*- coding: utf-8 -*-
import io
import logging
from random import randint

from zipfile import ZipFile, is_zipfile
from rarfile import RarFile, is_rarfile

from requests import Session
import chardet
from bs4 import UnicodeDammit
from subzero.language import Language

from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.subtitle import Subtitle
from subliminal.exceptions import ProviderError
from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitle import sanitize
from subliminal.video import Movie
from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

logger = logging.getLogger(__name__)


class SubtitriIdSubtitle(Subtitle):
    """subtitri.id.lv Subtitle."""
    provider_name = 'subtitriid'

    def __init__(self, language, page_link, download_link, title, year, imdb_id):
        super(SubtitriIdSubtitle, self).__init__(language, page_link=page_link)
        self.download_link = download_link
        self.title = title
        self.year = year
        self.imdb_id = imdb_id
        self.matches = None

    @property
    def id(self):
        return self.download_link

    def get_matches(self, video):
        matches = set()
        if isinstance(video, Movie):
            # title
            if video.title and sanitize(self.title) == sanitize(video.title):
                matches.add('title')
            # year
            if video.year and self.year == video.year:
                matches.add('year')
            # imdb id
            if video.imdb_id and self.imdb_id == video.imdb_id:
                matches.add('imdb_id')
        
        self.matches = matches
        return matches

    def guess_encoding(self):
        # override default subtitle guess_encoding method to not include language-specific encodings guessing
        # chardet encoding detection seem to yield better results
        """Guess encoding using chardet.

        :return: the guessed encoding.
        :rtype: str

        """
        if self._guessed_encoding:
            return self._guessed_encoding

        logger.info('Guessing encoding for language %s', self.language)

        # guess/detect encoding using chardet
        encoding = chardet.detect(self.content)['encoding']
        logger.info('Chardet found encoding %s', encoding)

        if not encoding:
            # fallback on bs4
            logger.info('Falling back to bs4 detection')
            a = UnicodeDammit(self.content)

            logger.info("bs4 detected encoding: %s", a.original_encoding)

            if a.original_encoding:
                self._guessed_encoding = a.original_encoding
                return a.original_encoding
            raise ValueError(u"Couldn't guess the proper encoding for %s", self)

        self._guessed_encoding = encoding
        return encoding


class SubtitriIdProvider(Provider, ProviderSubtitleArchiveMixin):
    """subtitri.id.lv Provider."""
    subtitle_class = SubtitriIdSubtitle
    languages = {Language('lva', 'LV')} | {Language.fromalpha2(l) for l in ['lv']}
    server_url = 'http://subtitri.id.lv'
    search_url =  server_url + '/search/'

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]
        self.session.headers['Referer'] = self.server_url

    def terminate(self):
        self.session.close()

    def query(self, title):
        subtitles = []

        r = self.session.get(self.search_url, params = {'q': title}, timeout=10)
        r.raise_for_status()

        if not r.content:
            logger.debug('No data returned from provider')
            return []

        soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['lxml', 'html.parser'])

        # loop over subtitle cells
        rows = soup.select('.eBlock')
        for row in rows:
            result_anchor_el = row.select_one('.eTitle > a')
            
            # page link
            page_link = result_anchor_el.get('href')

            # fetch/parse additional info
            r = self.session.get(page_link, timeout=10)
            soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['lxml', 'html.parser'])

            # title
            movie_titles_string = soup.select_one('.main-header').text.strip()
            movie_titles_list = movie_titles_string.split(' / ')
            title = movie_titles_list[-1]

            # year
            year = soup.select_one('#film-page-year').text.strip()

            # imdb id
            imdb_link = soup.select_one('#actors-page > a').get('href')
            imdb_id = imdb_link.split('/')[-2]

            # download link
            href = soup.select_one('.hvr').get('href')
            download_link = self.server_url + href

            # create/add the subitle
            subtitle = self.subtitle_class(Language.fromalpha2('lv'), page_link, download_link, title, year, imdb_id)
            logger.debug('subtitri.id.lv: Found subtitle %r', subtitle)
            subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        if isinstance(video, Movie):
            titles = [video.title] + video.alternative_titles
        else:
            titles = []

        subtitles = []
        # query for subtitles
        for title in titles:
            if isinstance(video, Movie):
                subtitles += [s for s in self.query(title) if s.language in languages]

        return subtitles

    def download_subtitle(self, subtitle):
        if isinstance(subtitle, SubtitriIdSubtitle):
            # download the subtitle
            r = self.session.get(subtitle.download_link, timeout=10)
            r.raise_for_status()

            # open the archive
            archive_stream = io.BytesIO(r.content)
            if is_rarfile(archive_stream):
                archive = RarFile(archive_stream)
            elif is_zipfile(archive_stream):
                archive = ZipFile(archive_stream)
            else:
                subtitle.content = r.content
                if subtitle.is_valid():
                    return
                subtitle.content = None

                raise ProviderError('Unidentified archive type')

            subtitle.content = self.get_subtitle_from_archive(subtitle, archive)

# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import re
import io
import codecs
from hashlib import sha1
from random import randint
from zipfile import ZipFile, is_zipfile
from bs4 import BeautifulSoup
from requests import Session
from guessit import guessit
from dogpile.cache.api import NO_VALUE
from subliminal import Movie, region
from subliminal.subtitle import fix_line_ending
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches
from subzero.language import Language
from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

logger = logging.getLogger(__name__)


class YifySubtitle(Subtitle):
    """YIFY Subtitles"""
    provider_name = 'yifysubtitles'

    def __init__(self, language, page_link, release, uploader, sub_link, rating, hi):
        super(YifySubtitle, self).__init__(language)
        self.page_link = page_link
        self.hearing_impaired = hi
        self.release_info = release
        self.uploader = uploader
        self.sub_link = sub_link
        self.rating = rating

    @property
    def id(self):
        return self.page_link

    def make_picklable(self):
        self.content = None
        self._is_valid = False
        return self

    def get_matches(self, video):
        matches = set()
        matches.add('imdb_id')
        matches |= guess_matches(video, guessit(self.release_info, video.hints))
        return matches


class YifySubtitlesProvider(Provider):
    """YIFY Subtitles Provider."""

    YifyLanguages = [
        ('Albanian', 'sqi', None),
        ('Arabic', 'ara', None),
        ('Bengali', 'ben', None),
        ('Brazilian Portuguese', 'por', 'BR'),
        ('Bulgarian', 'bul', None),
        ('Chinese', 'zho', None),
        ('Croatian', 'hrv', None),
        ('Czech', 'ces', None),
        ('Danish', 'dan', None),
        ('Dutch', 'nld', None),
        ('English', 'eng', None),
        ('Farsi/Persian', 'fas', None),
        ('Finnish', 'fin', None),
        ('French', 'fra', None),
        ('German', 'deu', None),
        ('Greek', 'ell', None),
        ('Hebrew', 'heb', None),
        ('Hungarian', 'hun', None),
        ('Indonesian', 'ind', None),
        ('Italian', 'ita', None),
        ('Japanese', 'jpn', None),
        ('Korean', 'kor', None),
        ('Lithuanian', 'lit', None),
        ('Macedonian', 'mkd', None),
        ('Malay', 'msa', None),
        ('Norwegian', 'nor', None),
        ('Polish', 'pol', None),
        ('Portuguese', 'por', None),
        ('Romanian', 'ron', None),
        ('Russian', 'rus', None),
        ('Serbian', 'srp', None),
        ('Slovenian', 'slv', None),
        ('Spanish', 'spa', None),
        ('Swedish', 'swe', None),
        ('Thai', 'tha', None),
        ('Turkish', 'tur', None),
        ('Urdu', 'urd', None),
        ('Vietnamese', 'vie', None)
    ]

    languages = {Language(l, c) for (_, l, c) in YifyLanguages}
    server_url = 'https://www.yifysubtitles.com'

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]
        self.session.headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        self.session.headers["Accept-Language"] = "en-US,en;q=0.5"
        self.session.headers["Accept-Encoding"] = "gzip, deflate"
        self.session.headers["DNT"] = "1"
        self.session.headers["Connection"] = "keep-alive"
        self.session.headers["Upgrade-Insecure-Requests"] = "1"
        self.session.headers["Cache-Control"] = "max-age=0"

    def terminate(self):
        self.session.close()

    def _parse_row(self, row, languages):
        td = row.findAll('td')
        rating = int(td[0].text)
        sub_lang = td[1].text
        release = re.sub(r'^subtitle ', '', td[2].text)
        sub_link = td[2].find('a').get('href')
        sub_link = re.sub(r'^/subtitles/', self.server_url + '/subtitle/', sub_link) + '.zip'
        hi = True if td[3].find('span', {'class': 'hi-subtitle'}) else False
        uploader = td[4].text
        page_link = self.server_url + td[5].find('a').get('href')

        _, l, c = next(x for x in self.YifyLanguages if x[0] == sub_lang)
        lang = Language(l, c)
        if languages & set([lang]):
            return [YifySubtitle(lang, page_link, release, uploader, sub_link, rating, hi)]

        return []

    def _query(self, languages, video):
        subtitles = []

        logger.info('Searching subtitle %r', video.imdb_id)
        response = self.session.get(self.server_url + '/movie-imdb/' + video.imdb_id,
                                    allow_redirects=False, timeout=10,
                                    headers={'Referer': self.server_url})
        response.raise_for_status()

        if response.status_code != 200:
            logger.debug('No subtitles found')
            return subtitles

        soup = BeautifulSoup(response.content, 'lxml')
        tbl = soup.find('table', {'class': 'other-subs'})
        tbl_body = tbl.find('tbody') if tbl else None
        rows = tbl_body.findAll('tr') if tbl_body else []

        for row in rows:
            try:
                subtitles = subtitles + self._parse_row(row, languages)
            except Exception as e:
                pass

        subtitles.sort(key=lambda x: x.rating, reverse=True)
        return subtitles

    def list_subtitles(self, video, languages):
        return self._query(languages, video) if isinstance(video, Movie) and video.imdb_id else []

    def download_subtitle(self, subtitle):
        logger.info('Downloading subtitle %r', subtitle.sub_link)
        cache_key = sha1(subtitle.sub_link.encode("utf-8")).digest()
        request = region.get(cache_key)
        if request is NO_VALUE:
            request = self.session.get(subtitle.sub_link, headers={
                'Referer': subtitle.page_link
                })
            request.raise_for_status()
            region.set(cache_key, request)
        else:
            logger.info('Cache file: %s', codecs.encode(cache_key, 'hex_codec').decode('utf-8'))

        archive_stream = io.BytesIO(request.content)
        if is_zipfile(archive_stream):
            self._process_archive(ZipFile(archive_stream), subtitle)
        else:
            logger.error('Ignore unsupported archive %r', request.headers)

    def _process_archive(self, archive_stream, subtitle):
        for file_name in archive_stream.namelist():
            if file_name.lower().endswith(('.srt', '.sub')):
                logger.info('Found subtitle file %r', file_name)
                subtitle.content = fix_line_ending(archive_stream.read(file_name))
                if subtitle.is_valid():
                    return


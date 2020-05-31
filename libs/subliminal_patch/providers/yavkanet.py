# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import re
import io
import os
import codecs
from hashlib import sha1
from random import randint
from bs4 import BeautifulSoup
from zipfile import ZipFile, is_zipfile
from rarfile import RarFile, is_rarfile
from requests import Session
from guessit import guessit
from dogpile.cache.api import NO_VALUE
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.utils import sanitize
from subliminal.subtitle import guess_matches
from subliminal.video import Episode, Movie
from subliminal.subtitle import fix_line_ending
from subliminal.cache import region
from subzero.language import Language
from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

logger = logging.getLogger(__name__)


class YavkaNetSubtitle(Subtitle):
    """YavkaNet Subtitle."""
    provider_name = 'yavkanet'

    def __init__(self, language, filename, type, video, link, fps):
        super(YavkaNetSubtitle, self).__init__(language)
        self.filename = filename
        self.page_link = link
        self.type = type
        self.video = video
        self.fps = fps
        self.release_info = os.path.splitext(filename)[0]

    @property
    def id(self):
        return self.page_link + self.filename

    def get_fps(self):
        return self.fps

    def make_picklable(self):
        self.content = None
        self._is_valid = False
        return self

    def get_matches(self, video):
        matches = set()

        video_filename = video.name
        video_filename = os.path.basename(video_filename)
        video_filename, _ = os.path.splitext(video_filename)
        video_filename = re.sub(r'\[\w+\]$', '', video_filename).strip().upper()

        subtitle_filename = self.filename
        subtitle_filename = os.path.basename(subtitle_filename)
        subtitle_filename, _ = os.path.splitext(subtitle_filename)
        subtitle_filename = re.sub(r'\[\w+\]$', '', subtitle_filename).strip().upper()

        if ((video_filename == subtitle_filename) or
            (self.single_file is True and video_filename in self.notes.upper())):
            matches.add('hash')

        if video.year and self.year == video.year:
            matches.add('year')

        matches |= guess_matches(video, guessit(self.title, {'type': self.type}))
        matches |= guess_matches(video, guessit(self.filename, {'type': self.type}))
        return matches


class YavkaNetProvider(Provider):
    """YavkaNet Provider."""
    languages = {Language(l) for l in [
        'bul', 'eng', 'rus', 'spa', 'ita'
    ]}

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]
        self.session.headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        self.session.headers["Accept-Language"] = "en-US,en;q=0.5"
        self.session.headers["Accept-Encoding"] = "gzip, deflate, br"
        self.session.headers["DNT"] = "1"
        self.session.headers["Connection"] = "keep-alive"
        self.session.headers["Upgrade-Insecure-Requests"] = "1"
        self.session.headers["Cache-Control"] = "max-age=0"

    def terminate(self):
        self.session.close()

    def query(self, language, video):
        subtitles = []
        isEpisode = isinstance(video, Episode)
        params = {
            's': '',
            'y': '',
            'u': '',
            'l': 'BG',
            'i': ''
        }

        if isEpisode:
            params['s'] = "%s s%02de%02d" % (sanitize(video.series, {'\''}), video.season, video.episode)
        else:
            params['y'] = video.year
            params['s'] = sanitize(video.title, {'\''})

        if   language == 'en' or language == 'eng':
            params['l'] = 'EN'
        elif language == 'ru' or language == 'rus':
            params['l'] = 'RU'
        elif language == 'es' or language == 'spa':
            params['l'] = 'ES'
        elif language == 'it' or language == 'ita':
            params['l'] = 'IT'

        logger.info('Searching subtitle %r', params)
        response = self.session.get('http://yavka.net/subtitles.php', params=params, allow_redirects=False, timeout=10, headers={
            'Referer': 'http://yavka.net/',
            })

        response.raise_for_status()

        if response.status_code != 200:
            logger.debug('No subtitles found')
            return subtitles

        soup = BeautifulSoup(response.content, 'lxml')
        rows = soup.findAll('tr')
        
        # Search on first 25 rows only
        for row in rows[:25]:
            element = row.find('a', {'class': 'selector'})
            if element:
                link = element.get('href')
                notes = element.get('content')
                title = element.get_text()

                try:
                    year = int(element.find_next_sibling('span').text.strip('()'))
                except:
                    year = None

                try:
                    fps = float(row.find('span', {'title': 'Кадри в секунда'}).text.strip())
                except:
                    fps = None

                element = row.find('a', {'class': 'click'})
                uploader = element.get_text() if element else None
                logger.info('Found subtitle link %r', link)
                sub = self.download_archive_and_add_subtitle_files('http://yavka.net/' + link, language, video, fps)
                for s in sub:
                    s.title = title
                    s.notes = notes
                    s.year = year
                    s.uploader = uploader
                    s.single_file = True if len(sub) == 1 else False
                subtitles = subtitles + sub
        return subtitles
        
    def list_subtitles(self, video, languages):
        return [s for l in languages for s in self.query(l, video)]

    def download_subtitle(self, subtitle):
        if subtitle.content:
            pass
        else:
            seeking_subtitle_file = subtitle.filename
            arch = self.download_archive_and_add_subtitle_files(subtitle.page_link, subtitle.language, subtitle.video,
                                                                subtitle.fps)
            for s in arch:
                if s.filename == seeking_subtitle_file:
                    subtitle.content = s.content

    def process_archive_subtitle_files(self, archiveStream, language, video, link, fps):
        subtitles = []
        type = 'episode' if isinstance(video, Episode) else 'movie'
        for file_name in archiveStream.namelist():
            if file_name.lower().endswith(('.srt', '.sub')):
                logger.info('Found subtitle file %r', file_name)
                subtitle = YavkaNetSubtitle(language, file_name, type, video, link, fps)
                subtitle.content = fix_line_ending(archiveStream.read(file_name))
                subtitles.append(subtitle)
        return subtitles

    def download_archive_and_add_subtitle_files(self, link, language, video, fps):
        logger.info('Downloading subtitle %r', link)
        cache_key = sha1(link.encode("utf-8")).digest()
        request = region.get(cache_key)
        if request is NO_VALUE:
            request = self.session.get(link, headers={
                'Referer': 'http://yavka.net/subtitles.php'
                })
            request.raise_for_status()
            region.set(cache_key, request)
        else:
            logger.info('Cache file: %s', codecs.encode(cache_key, 'hex_codec').decode('utf-8'))

        archive_stream = io.BytesIO(request.content)
        if is_rarfile(archive_stream):
            return self.process_archive_subtitle_files(RarFile(archive_stream), language, video, link, fps)
        elif is_zipfile(archive_stream):
            return self.process_archive_subtitle_files(ZipFile(archive_stream), language, video, link, fps)
        else:
            logger.error('Ignore unsupported archive %r', request.headers)
            region.delete(cache_key)
            return []        

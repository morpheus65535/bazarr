# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import re
import io
import os
import codecs
import time
from hashlib import sha1
from random import randint
from bs4 import BeautifulSoup
from zipfile import ZipFile, is_zipfile
from rarfile import RarFile, is_rarfile
from requests import Session
from guessit import guessit
from dogpile.cache.api import NO_VALUE
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal_patch.utils import sanitize, fix_inconsistent_naming
from subliminal.video import Episode, Movie
from subliminal.subtitle import fix_line_ending
from subliminal.cache import region
from subzero.language import Language
from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

logger = logging.getLogger(__name__)


def fix_tv_naming(title):
    """Fix TV show titles with inconsistent naming using dictionary, but do not sanitize them.
    :param str title: original title.
    :return: new title.
    :rtype: str
    """
    return fix_inconsistent_naming(title, {"Superman & Lois": "Superman and Lois",
                                           }, True)


def fix_movie_naming(title):
    return fix_inconsistent_naming(title, {
    }, True)


class YavkaNetSubtitle(Subtitle):
    """YavkaNet Subtitle."""
    provider_name = 'yavkanet'

    def __init__(self, language, filename, type, video, link, fps, subs_form_data):
        super(YavkaNetSubtitle, self).__init__(language)
        self.filename = filename
        self.page_link = link
        self.type = type
        self.video = video
        self.fps = fps
        self.release_info = filename
        self.subs_form_data = subs_form_data
        self.content = None
        self._is_valid = False
        self.matches = set()
        if fps:
            if video.fps and float(video.fps) == fps:
                self.release_info += " [{:.3f}]".format(fps)
            else:
                self.release_info += " [{:.3f}]".format(fps)

    @property
    def id(self):
        return self.page_link + self.filename

    def get_fps(self):
        return self.fps

    def make_picklable(self):
        return self

    def get_matches(self, video):
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
            self.matches.add('hash')

        if video.year and self.year == video.year:
            self.matches.add('year')

        self.matches |= guess_matches(video, guessit(self.title, {'type': self.type}))
        self.matches |= guess_matches(video, guessit(self.filename, {'type': self.type}))
        return self.matches


class YavkaNetProvider(Provider):
    """YavkaNet Provider."""
    languages = {Language(l) for l in [
        'bul', 'eng', 'rus', 'spa', 'ita'
    ]}
    video_types = (Episode, Movie)

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

    def query(self, language, video):
        subtitles = []
        isEpisode = isinstance(video, Episode)

        if isEpisode:
            imdb_id = video.series_imdb_id
        else:
            imdb_id = video.imdb_id

        logger.info(f'Searching subtitle for {imdb_id}')
        response = self.retry(self.session.get(f'https://yavka.net/imdb/{imdb_id}', timeout=10,
                                               headers={'Referer': 'https://yavka.net/'}))
        if not response:
            return subtitles
        response.raise_for_status()

        if response.status_code != 200:
            logger.debug('No subtitles found')
            return subtitles

        soup = BeautifulSoup(response.content, 'html.parser')
        rows = soup.findAll('tr')

        # Search on first 25 rows only
        for row in rows[-50:]:
            element = row.select_one('a.balon, a.selector')
            if element:
                link = element.get('href')
                notes = re.sub(r'(?s)<p.*><img [A-z0-9=\'/\. :;#]*>(.*)</p>', r"\1", element.get('content'))
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
                
                cache_link = 'https://yavka.net' + link + '/'
                cache_key = sha1(cache_link.encode("utf-8")).digest()
                request = region.get(cache_key)
                if request is NO_VALUE:
                    # slow down to prevent being throttled
                    time.sleep(randint(0, 1))
                    response = self.retry(self.session.get('https://yavka.net' + link))
                    if not response:
                        logger.info('Subtitle page did not load: %s', link)
                        continue

                    soup = BeautifulSoup(response.content, 'html.parser')
                    post_form = soup.find('form', attrs={'method': 'POST'})
                    if post_form:
                        input_fields = post_form.find_all('input')
                        subs_form_data = {}
                        for input_field in input_fields:
                            input_name = input_field.get('name')
                            if input_name:  # Only add to dictionary if the input has a name
                                subs_form_data[input_name] = input_field.get('value', '')
                        logger.info('Found subtitle form data "%s" for %s', subs_form_data, link)
                    else:
                        logger.info('Could not find subtitle form data: %s', link)
                        continue
                else:
                    # will fetch from cache
                    subs_form_data = {}
                    logger.info('Skipping routines. Will use cache: %s', link)

                sub = self.download_archive_and_add_subtitle_files('https://yavka.net' + link + '/', language, video,
                                                                   fps, subs_form_data)
                for s in sub:
                    s.title = title
                    s.notes = notes
                    s.year = year
                    s.uploader = uploader
                    s.single_file = True if len(sub) == 1 else False
                subtitles = subtitles + sub
        return subtitles

    def list_subtitles(self, video, languages):
        return [s for lang in languages for s in self.query(lang, video)]

    def download_subtitle(self, subtitle):
        if subtitle.content:
            pass
        else:
            seeking_subtitle_file = subtitle.filename
            arch = self.download_archive_and_add_subtitle_files(subtitle.page_link, subtitle.language, subtitle.video,
                                                                subtitle.fps, subtitle.subs_form_data)
            for s in arch:
                if s.filename == seeking_subtitle_file:
                    subtitle.content = s.content

    @staticmethod
    def process_archive_subtitle_files(archive_stream, language, video, link, fps, subs_form_data):
        subtitles = []
        media_type = 'episode' if isinstance(video, Episode) else 'movie'
        for file_name in archive_stream.namelist():
            if file_name.lower().endswith(('.srt', '.sub')):
                logger.info('Found subtitle file %r', file_name)
                subtitle = YavkaNetSubtitle(language, file_name, media_type, video, link, fps, subs_form_data)
                subtitle.content = fix_line_ending(archive_stream.read(file_name))
                subtitles.append(subtitle)
        return subtitles

    def download_archive_and_add_subtitle_files(self, link, language, video, fps, subs_form_data):
        logger.info('Downloading subtitle %r', link)
        cache_key = sha1(link.encode("utf-8")).digest()
        request = region.get(cache_key)
        if request is NO_VALUE:
            time.sleep(1)
            request = self.retry(self.session.post(link, data=subs_form_data, headers={
                'referer': link
            }, allow_redirects=False))
            if not request:
                return []
            request.raise_for_status()
            region.set(cache_key, request)
            logger.info('Writing caching file %s for %s', codecs.encode(cache_key, 'hex_codec').decode('utf-8'), link)
        else:
            logger.info('Using cache file %s for %s', codecs.encode(cache_key, 'hex_codec').decode('utf-8'), link)

        try:
            archive_stream = io.BytesIO(request.content)
            if is_rarfile(archive_stream):
                return self.process_archive_subtitle_files(RarFile(archive_stream), language, video, link, fps,
                                                           subs_form_data)
            elif is_zipfile(archive_stream):
                return self.process_archive_subtitle_files(ZipFile(archive_stream), language, video, link, fps,
                                                           subs_form_data)
        except:
            pass

        logger.error('Ignore unsupported archive %r', request.headers)
        region.delete(cache_key)
        return []

    @staticmethod
    def retry(func, limit=5, delay=5):
        for i in range(limit):
            response = func
            if response.content:
                return response
            else:
                logging.debug('Slowing down because we are getting throttled. Iteration {0} of {1}.Waiting {2} seconds '
                              'to retry...'.format(i + 1, limit, delay))
                time.sleep(delay)

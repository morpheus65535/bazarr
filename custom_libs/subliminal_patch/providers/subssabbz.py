# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import re
import io
import os
import codecs
import unicodedata
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
    return fix_inconsistent_naming(title, {"Marvel's Daredevil": "Daredevil",
                                           "Marvel's Luke Cage": "Luke Cage",
                                           "Marvel's Iron Fist": "Iron Fist",
                                           "Marvel's Jessica Jones": "Jessica Jones",
                                           "DC's Legends of Tomorrow": "Legends of Tomorrow",
                                           "Doctor Who (2005)": "Doctor Who",
                                           "Star Trek: Deep Space Nine": "Star Trek DS9",
                                           "Star Trek: The Next Generation": "Star Trek TNG",
                                           "Superman & Lois": "Superman and Lois",
                                           }, True)


def fix_movie_naming(title):
    return fix_inconsistent_naming(title, {"Back to the Future Part": "Back to the Future",
                                           }, True)


class SubsSabBzSubtitle(Subtitle):
    """SubsSabBz Subtitle."""
    provider_name = 'subssabbz'

    def __init__(self, language, filename, type, video, link, fps, num_cds):
        super(SubsSabBzSubtitle, self).__init__(language)
        self.filename = filename
        self.page_link = link
        self.type = type
        self.video = video
        self.fps = fps
        self.num_cds = num_cds
        self.release_info = filename
        self.matches = set()
        if fps:
            if video.fps and float(video.fps) == fps:
                self.release_info += " <b>[{:.3f}]</b>".format(fps)
            else:
                self.release_info += " [{:.3f}]".format(fps)

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

        if isinstance(video, Movie):
            if video.imdb_id and self.imdb_id == video.imdb_id:
                self.matches.add('imdb_id')

        self.matches |= guess_matches(video, guessit(self.title, {'type': self.type}))

        guess_filename = guessit(self.filename, video.hints)
        self.matches |= guess_matches(video, guess_filename)

        if isinstance(video, Movie) and ((isinstance(self.num_cds, int) and self.num_cds > 1) or 'cd' in guess_filename):
            # reduce score of subtitles for multi-disc movie releases
            return set()

        return self.matches


class SubsSabBzProvider(Provider):
    """SubsSabBz Provider."""
    languages = {Language(l) for l in [
        'bul', 'eng'
    ]}
    languages.update(set(Language.rebuild(l, hi=True) for l in languages))
    languages.update(set(Language.rebuild(l, forced=True) for l in languages))
    video_types = (Episode, Movie)

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
            'act': 'search',
            'movie': '',
            'select-language': '2',
            'upldr': '',
            'yr': '',
            'release': ''
        }

        if isEpisode:
            title = sanitize(fix_tv_naming(video.series), {'\''})
        else:
            params['yr'] = video.year
            title = sanitize(fix_movie_naming(video.title), {'\''})

        # Strip diacritics/accents (e.g. Shōgun -> Shogun) for search compatibility
        params['movie'] = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')

        if language.alpha3 == 'eng':
            params['select-language'] = 1

        logger.info('Searching subtitle %r', params)
        response = self.session.post('http://subs.sab.bz/index.php?', params=params, allow_redirects=False, timeout=30, headers={
            'Referer': 'http://subs.sab.bz/',
            })

        response.raise_for_status()

        if response.status_code != 200:
            logger.debug('No subtitles found')
            return subtitles

        soup = BeautifulSoup(response.content, 'lxml')
        rows = soup.findAll('tr', {'class': 'subs-row'})

        # Search on first 25 rows only
        for row in rows[:25]:
            a_element_wrapper = row.find('td', { 'class': 'c2field' })
            if a_element_wrapper:
                element = a_element_wrapper.find('a')
                if element:
                    link = element.get('href')
                    notes = re.sub(r'ddrivetip\(\'<div.*/></div>(.*)\',\'#[0-9]+\'\)', r'\1', element.get('onmouseover'))
                    title = element.get_text()

                    try:
                        year = int(str(element.next_sibling).strip(' ()'))
                    except:
                        year = None

                    td = row.findAll('td')

                    try:
                        num_cds = int(td[6].get_text())
                    except:
                        num_cds = None

                    try:
                        fps = float(td[7].get_text())
                    except:
                        fps = None

                    try:
                        uploader = td[8].get_text()
                    except:
                        uploader = None

                    try:
                        imdb_id = re.findall(r'imdb.com/title/(tt\d+)/?$', td[9].find('a').get('href'))[0]
                    except:
                        imdb_id = None

                    logger.info('Found subtitle link %r', link)
                    try:
                        sub = self.download_archive_and_add_subtitle_files(link, language, video, fps, num_cds)
                    except Exception as e:
                        logger.warning('Failed to download %s: %s', link, e)
                        continue
                    for s in sub:
                        s.title = title
                        s.notes = notes
                        s.year = year
                        s.uploader = uploader
                        s.imdb_id = imdb_id
                        s.single_file = True if len(sub) == 1 and num_cds == 1 else False
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
                                                                subtitle.fps, subtitle.num_cds)
            for s in arch:
                if s.filename == seeking_subtitle_file:
                    subtitle.content = s.content

    def process_archive_subtitle_files(self, archiveStream, language, video, link, fps, num_cds):
        subtitles = []
        type = 'episode' if isinstance(video, Episode) else 'movie'
        for file_name in sorted(archiveStream.namelist()):
            if file_name.lower().endswith(('.srt', '.sub')):
                logger.info('Found subtitle file %r', file_name)
                subtitle = SubsSabBzSubtitle(language, file_name, type, video, link, fps, num_cds)
                subtitle.content = fix_line_ending(archiveStream.read(file_name))
                subtitles.append(subtitle)
        return subtitles

    def download_archive_and_add_subtitle_files(self, link, language, video, fps, num_cds):
        logger.info('Downloading subtitle %r', link)
        cache_key = sha1(link.encode("utf-8")).digest()
        request = region.get(cache_key)
        if request is NO_VALUE:
            request = self.session.get(link, headers={
                'Referer': 'http://subs.sab.bz/index.php?'
                })
            request.raise_for_status()
            region.set(cache_key, request)
        else:
            logger.info('Cache file: %s', codecs.encode(cache_key, 'hex_codec').decode('utf-8'))

        try:
            archive_stream = io.BytesIO(request.content)
            if is_rarfile(archive_stream):
                return self.process_archive_subtitle_files(RarFile(archive_stream), language, video, link, fps, num_cds)
            elif is_zipfile(archive_stream):
                return self.process_archive_subtitle_files(ZipFile(archive_stream), language, video, link, fps, num_cds)
        except:
            pass

        logger.error('Ignore unsupported archive %r', request.headers)
        region.delete(cache_key)
        return []

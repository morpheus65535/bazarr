# coding=utf-8

from __future__ import absolute_import
import os
import io
import logging
import re
import rarfile
from random import randint

from zipfile import ZipFile, is_zipfile
from rarfile import RarFile, is_rarfile
from guessit import guessit
from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal_patch.utils import sanitize, fix_inconsistent_naming as _fix_inconsistent_naming
from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST
from subliminal.exceptions import ProviderError
from subliminal.providers import ParserBeautifulSoup
from subliminal.video import Episode, Movie
from subliminal.subtitle import SUBTITLE_EXTENSIONS
from subzero.language import Language

# parsing regex definitions
title_re = re.compile(r'(?P<title>(?:.+(?= [Aa][Kk][Aa] ))|.+)(?:(?:.+)(?P<altitle>(?<= [Aa][Kk][Aa] ).+))?')


def fix_inconsistent_naming(title):
    """Fix titles with inconsistent naming using dictionary and sanitize them.

    :param str title: original title.
    :return: new title.
    :rtype: str

    """
    return _fix_inconsistent_naming(title, {"DC's Legends of Tomorrow": "Legends of Tomorrow",
                                            "Marvel's Jessica Jones": "Jessica Jones"})


logger = logging.getLogger(__name__)


class TitrariSubtitle(Subtitle):

    provider_name = 'titrari'

    def __init__(self, language, download_link, sid, comments, title, imdb_id, page_link, uploader, year=None,
            download_count=None, is_episode=False, desired_episode=None):
        super(TitrariSubtitle, self).__init__(language)
        self.sid = sid
        self.title = title
        self.imdb_id = imdb_id
        self.download_link = download_link
        self.page_link = page_link
        self.uploader = uploader
        self.year = year
        self.download_count = download_count
        self.comments = self.releases = self.release_info = comments
        self.matches = None
        self.is_episode = is_episode
        self.desired_episode = desired_episode

    @property
    def id(self):
        return self.sid

    def __str__(self):
        return self.title + "(" + str(self.year) + ")" + " -> " + self.download_link

    def __repr__(self):
        return self.title + "(" + str(self.year) + ")"

    def get_matches(self, video):
        matches = set()

        if video.year and self.year == video.year:
            matches.add('year')

        if video.release_group and video.release_group in self.comments:
            matches.add('release_group')

        if isinstance(video, Movie):
            # title
            if video.title and sanitize(self.title) == fix_inconsistent_naming(video.title):
                matches.add('title')

            # imdb
            if video.imdb_id and self.imdb_id == video.imdb_id:
                matches.add('imdb_id')

            # guess match others
            matches |= guess_matches(video, guessit(self.comments, {"type": "movie"}))

        else:
            # title
            seasonless_title = re.sub(r'\s-\sSezonul\s\d+$', '', self.title.rstrip())
            if video.series and fix_inconsistent_naming(video.series) == sanitize(seasonless_title):
                matches.add('series')

            # imdb
            if video.series_imdb_id and self.imdb_id == video.series_imdb_id:
                matches.add('imdb_id')

            # season
            if f"Sezonul {video.season}" in self.title:
                matches.add('season')

            # episode
            if {"imdb_id", "season"}.issubset(matches):
                matches.add('episode')

            # guess match others
            matches |= guess_matches(video, guessit(self.comments, {"type": "episode"}))

        self.matches = matches

        return matches


class TitrariProvider(Provider, ProviderSubtitleArchiveMixin):
    subtitle_class = TitrariSubtitle
    languages = {Language(lang) for lang in ['ron', 'eng']}
    languages.update(set(Language.rebuild(lang, forced=True) for lang in languages))
    languages.update(set(Language.rebuild(lang, hi=True) for lang in languages))
    video_types = (Episode, Movie)
    api_url = 'https://www.titrari.ro/'
    # query_advanced_search = 'cautarepreaavansata'
    query_advanced_search = "maicauta"

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        # Hardcoding the UA to bypass the 30s throttle that titrari.ro uses for IP/UA pair
        self.session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, ' \
                                             'like Gecko) Chrome/93.0.4535.2 Safari/537.36'
        # self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]

    def terminate(self):
        self.session.close()

    def query(self, language=None, title=None, imdb_id=None, video=None):
        subtitles = []

        params = self.getQueryParams(imdb_id, title, language)

        search_response = self.session.get(self.api_url, params=params, timeout=15)
        search_response.raise_for_status()

        if not search_response.content:
            logger.debug('No data returned from provider')
            return []

        soup = ParserBeautifulSoup(search_response.content.decode('utf-8', 'ignore'), ['lxml', 'html.parser'])

        # loop over subtitle cells
        rows = soup.select('td[rowspan="5"]')
        for index, row in enumerate(rows):
            result_anchor_el = row.select_one('a')

            # Download link
            href = result_anchor_el.get('href')
            download_link = self.api_url + href

            fullTitle = row.parent.select('h1 a')[0].text

            # Get title
            try:
                title = fullTitle.split("(")[0]
            except:
                logger.error("Error parsing title")

            # Get downloads count
            downloads = 0
            try:
                downloads = int(row.parent.parent.select('span')[index].text[12:])
            except:
                logger.error("Error parsing downloads")

            # Get year
            try:
                year = int(fullTitle.split("(")[1].split(")")[0])
            except:
                year = None
                logger.error("Error parsing year")

            # Get imdbId
            sub_imdb_id = self.getImdbIdFromSubtitle(row)

            comments = ''
            try:
                comments = row.parent.parent.select('.comment')[1].text
            except:
                logger.error("Error parsing comments")

            # Get page_link
            try:
                page_link = self.api_url + row.parent.select('h1 a')[0].get('href')
            except:
                logger.error("Error parsing page_link")

            # Get uploader
            try:
                uploader = row.parent.select('td.row1.stanga a')[-1].text
            except:
                logger.error("Error parsing uploader")

            episode_number = video.episode if isinstance(video, Episode) else None
            subtitle = self.subtitle_class(language, download_link, index, comments, title, sub_imdb_id, page_link, uploader,
                                           year, downloads, isinstance(video, Episode), episode_number)
            logger.debug('Found subtitle %r', str(subtitle))
            subtitles.append(subtitle)

        ordered_subs = self.order(subtitles)

        return ordered_subs

    @staticmethod
    def order(subtitles):
        logger.debug("Sorting by download count...")
        sorted_subs = sorted(subtitles, key=lambda s: s.download_count, reverse=True)
        return sorted_subs

    @staticmethod
    def getImdbIdFromSubtitle(row):
        imdbId = None
        try:
            imdbId = row.parent.parent.find_all(src=re.compile("imdb"))[0].parent.get('href').split("tt")[-1]
        except:
            logger.error("Error parsing imdb id")
        if imdbId is not None:
            return "tt" + imdbId
        else:
            return None

    # titrari.ro seems to require all parameters now
    #  z2 = comment (empty)
    #  z3 = fps (-1: any, 0: N/A, 1: 23.97 FPS etc.)
    #  z4 = CD count (-1: any)
    #  z5 = imdb_id (empty or integer)
    #  z6 = sort order (0: unsorted, 1: by date, 2: by name)
    #  z7 = title (empty or string)
    #  z8 = language (-1: all, 1: ron, 2: eng)
    #  z9 = genre (All: all, Action: action etc.)
    # z11 = type (0: any, 1: movie, 2: series)
    def getQueryParams(self, imdb_id, title, language):
        queryParams = {
            'page': self.query_advanced_search,
            'z7': '',
            'z2': '',
            'z5': '',
            'z3': '-1',
            'z4': '-1',
            'z8': '-1',
            'z9': 'All',
            'z11': '0',
            'z6': '0'
        }
        if imdb_id is not None:
            queryParams["z5"] = imdb_id
        elif title is not None:
            queryParams["z7"] = title

        if language == 'ro':
            queryParams["z8"] = '1'
        elif language == 'en':
            queryParams["z8"] = '2'

        return queryParams

    def list_subtitles(self, video, languages):
        title = fix_inconsistent_naming(video.title)
        imdb_id = None
        try:
            if isinstance(video, Episode):
                imdb_id = video.series_imdb_id[2:]
            else:
                imdb_id = video.imdb_id[2:]
        except:
            logger.error('Error parsing imdb_id from video object {}'.format(str(video)))

        subtitles = [s for lang in languages for s in
                     self.query(lang, title, imdb_id, video)]
        return subtitles

    def download_subtitle(self, subtitle):
        r = self.session.get(subtitle.download_link, headers={'Referer': self.api_url}, timeout=10)
        r.raise_for_status()

        # open the archive
        archive_stream = io.BytesIO(r.content)
        if is_rarfile(archive_stream):
            logger.debug('Archive identified as RAR')
            archive = RarFile(archive_stream)
        elif is_zipfile(archive_stream):
            logger.debug('Archive identified as ZIP')
            archive = ZipFile(archive_stream)
        else:
            subtitle.content = r.content
            if subtitle.is_valid():
                return
            subtitle.content = None

            raise ProviderError('Unidentified archive type')

        if subtitle.is_episode:
            subtitle.content = self._get_subtitle_from_archive(subtitle, archive)
        else:
            subtitle.content = self.get_subtitle_from_archive(subtitle, archive)

    @staticmethod
    def _get_subtitle_from_archive(subtitle, archive):
        for name in archive.namelist():
            # discard hidden files
            if os.path.split(name)[-1].startswith('.'):
                continue

            # discard non-subtitle files
            if not name.lower().endswith(SUBTITLE_EXTENSIONS):
                continue

            _guess = guessit(name)
            if subtitle.desired_episode == _guess['episode']:
                return archive.read(name)

        return None

# vim: set expandtab ts=4 sw=4:

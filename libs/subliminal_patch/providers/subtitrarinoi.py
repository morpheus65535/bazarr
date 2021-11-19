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

# Configure :mod:`rarfile` to use the same path separator as :mod:`zipfile`
rarfile.PATH_SEP = '/'


class SubtitrarinoiSubtitle(Subtitle):

    provider_name = 'subtitrarinoi'

    def __init__(self, language, download_link, sid, comments, title, imdb_id, uploader, page_link, year=None,
            download_count=None, is_episode=False, desired_episode=False):
        super(SubtitrarinoiSubtitle, self).__init__(language)
        self.sid = sid
        self.title = title
        self.imdb_id = imdb_id
        self.download_link = download_link
        self.year = year
        self.download_count = download_count
        self.comments = self.releases = self.release_info = ",".join(comments.split(";"))
        self.matches = None
        self.uploader = uploader
        self.page_link = page_link
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
            if f"Sezonul {video.season}" in self.comments:
                matches.add('season')

            # episode
            if {"imdb_id", "season"}.issubset(matches):
                matches.add('episode')

            # guess match others
            matches |= guess_matches(video, guessit(self.comments, {"type": "episode"}))

        self.matches = matches

        return matches

class SubtitrarinoiProvider(Provider, ProviderSubtitleArchiveMixin):
    subtitle_class = SubtitrarinoiSubtitle
    languages = {Language(lang) for lang in ['ron']}
    languages.update(set(Language.rebuild(lang, forced=True) for lang in languages))
    video_types = (Episode, Movie)
    server_url = 'https://www.subtitrari-noi.ro/'
    api_url = server_url + 'paginare_filme.php'

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4535.2 Safari/537.36'
        self.session.headers['X-Requested-With'] = 'XMLHttpRequest'
        self.session.headers['Referer'] = self.server_url

    def terminate(self):
        self.session.close()

    def query(self, languages=None, title=None, imdb_id=None, video=None):
        subtitles = []

        params = self.getQueryParams(imdb_id, title)
        search_response = self.session.post(self.api_url, data=params, timeout=15)
        search_response.raise_for_status()

        soup = ParserBeautifulSoup(search_response.content.decode('utf-8', 'ignore'), ['lxml', 'html.parser'])

        # loop over subtitle cells
        rows = soup.select('div[id="round"]')

        if len(rows) == 0:
            logger.debug('No data returned from provider')
            return []

        # release comments are outside of the parent for the sub details itself, so we just map it to another list
        comment_rows = soup.findAll('div', attrs={'class': None, 'id': None, 'align': None})

        for index, row in enumerate(rows):
            result_anchor_el = row.select_one('.buton').select('a')

            # Download link
            href = result_anchor_el[0]['href']
            download_link = self.server_url + href

            fullTitle = row.select_one('#content-main a').text

            # Get title
            try:
                title = fullTitle.split("(")[0]
            except:
                logger.error("Error parsing title")

            # Get Uploader
            try:
                uploader = row.select('#content-main p')[4].text[10:]
            except:
                logger.error("Error parsing uploader")

            # Get downloads count
            downloads = 0
            try:
                downloads = int(row.select_one('#content-right p').text[12:])
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
                comments = comment_rows[index].text
                logger.debug('Comments: {}'.format(comments))
            except:
                logger.error("Error parsing comments")

            # Get Page Link
            try:
                page_link = row.select_one('#content-main a')['href']
            except:
                logger.error("Error parsing page_link")

            episode_number = video.episode if isinstance(video, Episode) else None
            subtitle = self.subtitle_class(next(iter(languages)), download_link, index, comments, title, sub_imdb_id, uploader, page_link, year, downloads, isinstance(video, Episode), episode_number)
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
            imdbId = row.select('div[id=content-right] a')[-1].find_all(src=re.compile("imdb"))[0].parent.get('href').split("tt")[-1]
        except:
            logger.error("Error parsing imdb id")
        if imdbId is not None:
            return "tt" + imdbId
        else:
            return None

    # subtitrari-noi.ro params
    # info: there seems to be no way to do an advanced search by imdb_id or title
    # the page seems to populate both "search_q" and "cautare" with the same value
    # search_q = ?
    # cautare = search string
    # tip = type of search (0: premiere - doesn't return anything, 1: series only, 2: both, I think, not sure on that)
    # an = year
    # gen = genre

    def getQueryParams(self, imdb_id, title):
        queryParams = {
        'search_q': '1',
            'tip': '2',
            'an': 'Toti anii',
            'gen': 'Toate',
        }   
        if imdb_id is not None:
            queryParams["cautare"] = imdb_id
        elif title is not None:
            queryParams["cautare"] = title
        
        queryParams["query_q"] = queryParams["cautare"]

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

        subtitles = [s for s in
                self.query(languages, title, imdb_id, video)]
        return subtitles

    def download_subtitle(self, subtitle):
        r = self.session.get(subtitle.download_link, headers={'Referer': self.api_url}, timeout=10)
        r.raise_for_status()

        # open the archive
        archive_stream = io.BytesIO(r.content)
        if is_rarfile(archive_stream):
            logger.debug('Archive identified as rar')
            archive = RarFile(archive_stream)
        elif is_zipfile(archive_stream):
            logger.debug('Archive identified as zip')
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

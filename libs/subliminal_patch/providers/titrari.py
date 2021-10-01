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

class TitrariSubtitle(Subtitle):

    provider_name = 'titrari'

    def __init__(self, language, download_link, sid, releases, title, imdb_id, year=None, download_count=None, comments=None):
        super(TitrariSubtitle, self).__init__(language)
        self.sid = sid
        self.title = title
        self.imdb_id = imdb_id
        self.download_link = download_link
        self.year = year
        self.download_count = download_count
        self.releases = self.release_info = releases
        self.comments = comments

    @property
    def id(self):
        return self.sid

    def __str__(self):
        return self.title + "(" + str(self.year) + ")" + " -> " + self.download_link

    def __repr__(self):
        return self.title + "(" + str(self.year) + ")"

    def get_matches(self, video):
        matches = set()

        if isinstance(video, Movie):
            # title
            if video.title and sanitize(self.title) == fix_inconsistent_naming(video.title):
                matches.add('title')

            if video.year and self.year == video.year:
                matches.add('year')

            if video.imdb_id and self.imdb_id == video.imdb_id:
                matches.add('imdb_id')

            if video.release_group and video.release_group in self.comments:
                matches.add('release_group')

            matches |= guess_matches(video, guessit(self.comments, {"type": "movie"}))

        self.matches = matches

        return matches


class TitrariProvider(Provider, ProviderSubtitleArchiveMixin):
    subtitle_class = TitrariSubtitle
    languages = {Language(l) for l in ['ron', 'eng']}
    languages.update(set(Language.rebuild(l, forced=True) for l in languages))
    api_url = 'https://www.titrari.ro/'
    query_advanced_search = 'cautarepreaavansata'

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]

    def terminate(self):
        self.session.close()

    def query(self, languages=None, title=None, imdb_id=None, video=None):
        subtitles = []

        params = self.getQueryParams(imdb_id, title)

        search_response = self.session.get(self.api_url, params=params, timeout=15)
        search_response.raise_for_status()

        if not search_response.content:
            logger.debug('[#### Provider: titrari.ro] No data returned from provider')
            return []

        soup = ParserBeautifulSoup(search_response.content.decode('utf-8', 'ignore'), ['lxml', 'html.parser'])

        # loop over subtitle cells
        rows = soup.select('td[rowspan=\'5\']')
        for index, row in enumerate(rows):
            result_anchor_el = row.select_one('a')

            # Download link
            href = result_anchor_el.get('href')
            download_link = self.api_url + href

            fullTitle = row.parent.find("h1").find("a").text

            #Get title
            try:
                title = fullTitle.split("(")[0]
            except:
                logger.error("[#### Provider: titrari.ro] Error parsing title.")

            # Get downloads count
            try:
                downloads = int(row.parent.parent.select("span")[index].text[12:])
            except:
                logger.error("[#### Provider: titrari.ro] Error parsing downloads.")

            # Get year
            try:
                year = int(fullTitle.split("(")[1].split(")")[0])
            except:
                year = None
                logger.error("[#### Provider: titrari.ro] Error parsing year.")

            # Get imdbId
            sub_imdb_id = self.getImdbIdFromSubtitle(row)

            try:
                comments = row.parent.parent.find_all("td", class_=re.compile("comment"))[index*2+1].text
            except:
                logger.error("Error parsing comments.")

            subtitle = self.subtitle_class(next(iter(languages)), download_link, index, None, title, sub_imdb_id, year, downloads, comments)
            logger.debug('[#### Provider: titrari.ro] Found subtitle %r', str(subtitle))
            subtitles.append(subtitle)

        ordered_subs = self.order(subtitles, video)

        return ordered_subs

    def order(self, subtitles, video):
        logger.debug("[#### Provider: titrari.ro] Sorting by download count...")
        sorted_subs = sorted(subtitles, key=lambda s: s.download_count, reverse=True)
        return sorted_subs

    def getImdbIdFromSubtitle(self, row):
        try:
            imdbId = row.parent.parent.find_all(src=re.compile("imdb"))[0].parent.get('href').split("tt")[-1]
        except:
            logger.error("[#### Provider: titrari.ro] Error parsing imdbId.")
        if imdbId is not None:
            return "tt" + imdbId
        else:
            return None


    def getQueryParams(self, imdb_id, title):
        queryParams = {
            'page': self.query_advanced_search,
            'z8': '1'
        }
        if imdb_id is not None:
            queryParams["z5"] = imdb_id
        elif title is not None:
            queryParams["z7"] = title

        return queryParams

    def list_subtitles(self, video, languages):
        title = fix_inconsistent_naming(video.title)
        imdb_id = None
        try:
            imdb_id = video.imdb_id[2:]
        except:
            logger.error("[#### Provider: titrari.ro] Error parsing video.imdb_id.")

        return [s for s in
                self.query(languages, title, imdb_id, video)]

    def download_subtitle(self, subtitle):
        r = self.session.get(subtitle.download_link, headers={'Referer': self.api_url}, timeout=10)
        r.raise_for_status()

        # open the archive
        archive_stream = io.BytesIO(r.content)
        if is_rarfile(archive_stream):
            logger.debug('[#### Provider: titrari.ro] Archive identified as rar')
            archive = RarFile(archive_stream)
        elif is_zipfile(archive_stream):
            logger.debug('[#### Provider: titrari.ro] Archive identified as zip')
            archive = ZipFile(archive_stream)
        else:
            subtitle.content = r.content
            if subtitle.is_valid():
                return
            subtitle.content = None

            raise ProviderError('[#### Provider: titrari.ro] Unidentified archive type')

        subtitle.releases = _get_releases_from_archive(archive)
        subtitle.content = self.get_subtitle_from_archive(subtitle, archive)


def _get_releases_from_archive(archive):
    releases = []
    for name in archive.namelist():
        # discard hidden files
        if os.path.split(name)[-1].startswith('.'):
            continue

        # discard non-subtitle files
        if not name.lower().endswith(SUBTITLE_EXTENSIONS):
            continue

        releases.append(os.path.splitext(os.path.split(name)[1])[0])

    return releases

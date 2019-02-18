# -*- coding: utf-8 -*-
# encoding=utf8
import io
import logging
import os
import random

import rarfile
import re
import zipfile

from subzero.language import Language
from guessit import guessit
from requests import Session
from six import text_type

from subliminal.providers import ParserBeautifulSoup, Provider
from subliminal import __short_version__
from subliminal.cache import SHOW_EXPIRATION_TIME, region
from subliminal.score import get_equivalent_release_groups
from subliminal.subtitle import SUBTITLE_EXTENSIONS, Subtitle, fix_line_ending, guess_matches
from subliminal.utils import sanitize, sanitize_release_group
from subliminal.video import Movie

logger = logging.getLogger(__name__)

year_re = re.compile(r'^\((\d{4})\)$')
alpha2_to_alpha3 = {'el': ('ell',), 'en': ('eng',)}


class Subs4FreeSubtitle(Subtitle):
    """Subs4Free Subtitle."""
    provider_name = 'subs4free'

    def __init__(self, language, page_link, title, year, version, download_link):
        super(Subs4FreeSubtitle, self).__init__(language, page_link=page_link)
        self.title = title
        self.year = year
        self.version = version
        self.download_link = download_link
        self.hearing_impaired = False
        self.encoding = 'utf8'

    @property
    def id(self):
        return self.download_link

    def get_matches(self, video):
        matches = set()

        # movie
        if isinstance(video, Movie):
            # title
            if video.title and (sanitize(self.title) in (
                    sanitize(name) for name in [video.title] + video.alternative_titles)):
                matches.add('title')
            # year
            if video.year and self.year == video.year:
                matches.add('year')

        # release_group
        if (video.release_group and self.version and
                any(r in sanitize_release_group(self.version)
                    for r in get_equivalent_release_groups(sanitize_release_group(video.release_group)))):
            matches.add('release_group')
        # resolution
        if video.resolution and self.version and video.resolution in self.version.lower():
            matches.add('resolution')
        # format
        if video.format and self.version and sanitize(video.format) in sanitize(self.version):
            matches.add('format')
        # other properties
        matches |= guess_matches(video, guessit(self.version, {'type': 'movie'}), partial=True)

        return matches


class Subs4FreeProvider(Provider):
    """Subs4Free Provider."""
    languages = {Language(l) for l in ['ell', 'eng']}
    server_url = 'https://www.sf4-industry.com'
    download_url = '/getSub.html'
    search_url = '/search_report.php?search=%s&searchType=1'
    subtitle_class = Subs4FreeSubtitle

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/%s' % __short_version__

    def terminate(self):
        self.session.close()

    def get_show_ids(self, title, year=None):
        """Get the best matching show id for `series` and `year``.

        First search in the result of :meth:`_get_show_suggestions`.

        :param title: show title.
        :param year: year of the show, if any.
        :type year: int
        :return: the show id, if found.
        :rtype: str

        """
        title_sanitized = sanitize(title).lower()
        show_ids = self._get_suggestions(title)

        matched_show_ids = []
        for show in show_ids:
            show_id = None
            show_title = sanitize(show['title'])
            # attempt with year
            if not show_id and year:
                logger.debug('Getting show id with year')
                show_id = show['link'].split('?p=')[-1] if show_title == '%s %d' % (
                    title_sanitized, year) else None

            # attempt clean
            if not show_id:
                logger.debug('Getting show id')
                show_id = show['link'].split('?p=')[-1] if show_title == title_sanitized else None

            if show_id:
                matched_show_ids.append(show_id)

        return matched_show_ids

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME, to_str=text_type)
    def _get_suggestions(self, title):
        """Search the show or movie id from the `title` and `year`.

        :param str title: title of the show.
        :return: the show suggestions found.
        :rtype: dict

        """
        # make the search
        logger.info('Searching show ids with %r', title)
        r = self.session.get(self.server_url + self.search_url % title, headers={'Referer': self.server_url},
                             timeout=10)
        r.raise_for_status()

        if not r.content:
            logger.debug('No data returned from provider')
            return {}

        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])
        suggestions = [{'link': l.attrs['value'], 'title': l.text}
                       for l in soup.select('select[name="Mov_sel"] > option[value]')]
        logger.debug('Found suggestions: %r', suggestions)

        return suggestions

    def query(self, movie_id, title, year):
        # get the season list of the show
        logger.info('Getting the subtitle list of show id %s', movie_id)
        if movie_id:
            page_link = self.server_url + '/' + movie_id
        else:
            page_link = self.server_url + self.search_url % ' '.join([title, str(year)])

        r = self.session.get(page_link, timeout=10)
        r.raise_for_status()

        if not r.content:
            logger.debug('No data returned from provider')
            return []

        soup = ParserBeautifulSoup(r.content, ['html.parser'])

        year_num = None
        year_element = soup.select_one('td#dates_header > table div')
        matches = False
        if year_element:
            matches = year_re.match(str(year_element.contents[2]).strip())
        if matches:
            year_num = int(matches.group(1))

        title_element = soup.select_one('td#dates_header > table u')
        show_title = str(title_element.contents[0]).strip() if title_element else None

        subtitles = []
        # loop over episode rows
        for subtitle in soup.select('table.table_border div[align="center"] > div'):
            # read common info
            version = subtitle.find('b').text
            download_link = self.server_url + subtitle.find('a')['href']
            language = Language.fromalpha2(subtitle.find('img')['src'].split('/')[-1].split('.')[0])

            subtitle = self.subtitle_class(language, page_link, show_title, year_num, version, download_link)

            logger.debug('Found subtitle %r', subtitle)
            subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        # lookup show_id
        titles = [video.title] + video.alternative_titles if isinstance(video, Movie) else []

        show_ids = None
        for title in titles:
            show_ids = self.get_show_ids(title, video.year)
            if show_ids is not None:
                break

        subtitles = []
        # query for subtitles with the show_id
        if show_ids and len(show_ids) > 0:
            for show_id in show_ids:
                subtitles += [s for s in self.query(show_id, video.title, video.year) if s.language in languages]
        else:
            subtitles += [s for s in self.query(None, video.title, video.year) if s.language in languages]

        return subtitles

    def download_subtitle(self, subtitle):
        if isinstance(subtitle, Subs4FreeSubtitle):
            # download the subtitle
            logger.info('Downloading subtitle %r', subtitle)
            r = self.session.get(subtitle.download_link, headers={'Referer': subtitle.page_link}, timeout=10)
            r.raise_for_status()

            if not r.content:
                logger.debug('Unable to download subtitle. No data returned from provider')
                return

            soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])
            download_element = soup.select_one('input[name="id"]')
            image_element = soup.select_one('input[type="image"]')
            subtitle_id = download_element['value'] if download_element else None
            width = int(str(image_element['width']).strip('px')) if image_element else 0
            height = int(str(image_element['height']).strip('px')) if image_element else 0

            if not subtitle_id:
                logger.debug('Unable to download subtitle. No download link found')
                return

            download_url = self.server_url + self.download_url
            r = self.session.post(download_url, data={'utf8': 1, 'id': subtitle_id, 'x': random.randint(0, width),
                                                      'y': random.randint(0, height)},
                                  headers={'Referer': subtitle.download_link}, timeout=10)
            r.raise_for_status()

            if not r.content:
                logger.debug('Unable to download subtitle. No data returned from provider')
                return

            archive = _get_archive(r.content)

            subtitle_content = _get_subtitle_from_archive(archive) if archive else r.content

            if subtitle_content:
                subtitle.content = fix_line_ending(subtitle_content)
            else:
                logger.debug('Could not extract subtitle from %r', archive)


def _get_archive(content):
    # open the archive
    archive_stream = io.BytesIO(content)
    archive = None
    if rarfile.is_rarfile(archive_stream):
        logger.debug('Identified rar archive')
        archive = rarfile.RarFile(archive_stream)
    elif zipfile.is_zipfile(archive_stream):
        logger.debug('Identified zip archive')
        archive = zipfile.ZipFile(archive_stream)

    return archive


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

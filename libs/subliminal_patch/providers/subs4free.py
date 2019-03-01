# -*- coding: utf-8 -*-
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

from subliminal.providers import ParserBeautifulSoup, Provider
from subliminal import __short_version__
from subliminal.cache import SHOW_EXPIRATION_TIME, region
from subliminal.score import get_equivalent_release_groups
from subliminal.subtitle import SUBTITLE_EXTENSIONS, Subtitle, fix_line_ending, guess_matches
from subliminal.utils import sanitize, sanitize_release_group
from subliminal.video import Movie

logger = logging.getLogger(__name__)

year_re = re.compile(r'^\((\d{4})\)$')


class Subs4FreeSubtitle(Subtitle):
    """Subs4Free Subtitle."""
    provider_name = 'subs4free'

    def __init__(self, language, page_link, title, year, version, download_link):
        super(Subs4FreeSubtitle, self).__init__(language, page_link=page_link)
        self.title = title
        self.year = year
        self.version = version
        self.download_link = download_link
        self.hearing_impaired = None
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
        # other properties
        matches |= guess_matches(video, guessit(self.version, {'type': 'movie'}), partial=True)

        return matches


class Subs4FreeProvider(Provider):
    """Subs4Free Provider."""
    languages = {Language(l) for l in ['ell', 'eng']}
    video_types = (Movie,)
    server_url = 'https://www.sf4-industry.com'
    download_url = '/getSub.html'
    search_url = '/search_report.php?search={}&searchType=1'
    anti_block_1 = 'https://images.subs4free.info/favicon.ico'
    anti_block_2 = 'https://www.subs4series.com/includes/anti-block-layover.php?launch=1'
    anti_block_3 = 'https://www.subs4series.com/includes/anti-block.php'
    subtitle_class = Subs4FreeSubtitle

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/{}'.format(__short_version__)

    def terminate(self):
        self.session.close()

    def get_show_links(self, title, year=None):
        """Get the matching show links for `title` and `year`.

        First search in the result of :meth:`_get_show_suggestions`.

        :param title: show title.
        :param year: year of the show, if any.
        :type year: int
        :return: the show links, if found.
        :rtype: list of str

        """
        title = sanitize(title)
        suggestions = self._get_suggestions(title)

        show_links = []
        for suggestion in suggestions:
            show_title = sanitize(suggestion['title'])

            if show_title == title or (year and show_title == '{title} {year:d}'.format(title=title, year=year)):
                logger.debug('Getting show id')
                show_links.append(suggestion['link'].split('?p=')[-1])

        return show_links

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME, should_cache_fn=lambda value: value)
    def _get_suggestions(self, title):
        """Search the show or movie id from the `title` and `year`.

        :param str title: title of the show.
        :return: the show suggestions found.
        :rtype: list of dict

        """
        # make the search
        logger.info('Searching show ids with %r', title)
        r = self.session.get(self.server_url + self.search_url.format(title),
                             headers={'Referer': self.server_url}, timeout=10)
        r.raise_for_status()

        if not r.content:
            logger.debug('No data returned from provider')
            return []

        soup = ParserBeautifulSoup(r.content, ['html.parser'])
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
            page_link = self.server_url + self.search_url.format(' '.join([title, str(year)]))

        r = self.session.get(page_link, timeout=10)
        r.raise_for_status()

        if not r.content:
            logger.debug('No data returned from provider')
            return []

        soup = ParserBeautifulSoup(r.content, ['html.parser'])

        year = None
        year_element = soup.select_one('td#dates_header > table div')
        matches = False
        if year_element:
            matches = year_re.match(str(year_element.contents[2]).strip())
        if matches:
            year = int(matches.group(1))

        title_tag = soup.select_one('td#dates_header > table u')
        show_title = str(title_tag.contents[0]).strip() if title_tag else None

        subtitles = []
        # loop over episode rows
        for subs_tag in soup.select('table .seeDark,.seeMedium'):
            # read common info
            version = subs_tag.find('b').text
            download_link = self.server_url + subs_tag.find('a')['href']
            language = Language.fromalpha2(subs_tag.find('img')['src'].split('/')[-1].split('.')[0])

            subtitle = self.subtitle_class(language, page_link, show_title, year, version, download_link)

            logger.debug('Found subtitle {!r}'.format(subtitle))
            subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        # lookup show_id
        titles = [video.title] + video.alternative_titles if isinstance(video, Movie) else []

        show_links = None
        for title in titles:
            show_links = self.get_show_links(title, video.year)
            if show_links:
                break

        subtitles = []
        # query for subtitles with the show_id
        if show_links:
            for show_link in show_links:
                subtitles += [s for s in self.query(show_link, video.title, video.year) if s.language in languages]
        else:
            subtitles += [s for s in self.query(None, sanitize(video.title), video.year) if s.language in languages]

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

            self.apply_anti_block(subtitle)

            download_url = self.server_url + self.download_url
            r = self.session.post(download_url, data={'id': subtitle_id, 'x': random.randint(0, width),
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

    def apply_anti_block(self, subtitle):
        self.session.get(self.anti_block_1, headers={'Referer': subtitle.download_link}, timeout=10)
        self.session.get(self.anti_block_2, headers={'Referer': subtitle.download_link}, timeout=10)
        self.session.get(self.anti_block_3, headers={'Referer': subtitle.download_link}, timeout=10)


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

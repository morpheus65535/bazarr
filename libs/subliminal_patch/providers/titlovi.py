# coding=utf-8

import io
import logging
import math
import re
import time

import rarfile

from bs4 import BeautifulSoup
from zipfile import ZipFile, is_zipfile
from rarfile import RarFile, is_rarfile
from babelfish import language_converters, Script
from requests import RequestException
from guessit import guessit
from subliminal_patch.http import RetryingCFSession
from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.utils import sanitize, fix_inconsistent_naming as _fix_inconsistent_naming
from subliminal.exceptions import ProviderError
from subliminal.score import get_equivalent_release_groups
from subliminal.utils import sanitize_release_group
from subliminal.subtitle import guess_matches
from subliminal.video import Episode, Movie
from subliminal.subtitle import fix_line_ending
from subliminal_patch.pitcher import pitchers, load_verification, store_verification
from subzero.language import Language

from random import randint
from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

# parsing regex definitions
title_re = re.compile(r'(?P<title>(?:.+(?= [Aa][Kk][Aa] ))|.+)(?:(?:.+)(?P<altitle>(?<= [Aa][Kk][Aa] ).+))?')
lang_re = re.compile(r'(?<=flags/)(?P<lang>.{2})(?:.)(?P<script>c?)(?:.+)')
season_re = re.compile(r'Sezona (?P<season>\d+)')
episode_re = re.compile(r'Epizoda (?P<episode>\d+)')
year_re = re.compile(r'(?P<year>\d+)')
fps_re = re.compile(r'fps: (?P<fps>.+)')


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

language_converters.register('titlovi = subliminal_patch.converters.titlovi:TitloviConverter')


class TitloviSubtitle(Subtitle):
    provider_name = 'titlovi'

    def __init__(self, language, page_link, download_link, sid, releases, title, alt_title=None, season=None,
                 episode=None, year=None, fps=None, asked_for_release_group=None, asked_for_episode=None):
        super(TitloviSubtitle, self).__init__(language, page_link=page_link)
        self.sid = sid
        self.releases = self.release_info = releases
        self.title = title
        self.alt_title = alt_title
        self.season = season
        self.episode = episode
        self.year = year
        self.download_link = download_link
        self.fps = fps
        self.matches = None
        self.asked_for_release_group = asked_for_release_group
        self.asked_for_episode = asked_for_episode

    @property
    def id(self):
        return self.sid

    def get_matches(self, video):
        matches = set()

        # handle movies and series separately
        if isinstance(video, Episode):
            # series
            if video.series and sanitize(self.title) == fix_inconsistent_naming(video.series) or sanitize(
                    self.alt_title) == fix_inconsistent_naming(video.series):
                matches.add('series')
            # year
            if video.original_series and self.year is None or video.year and video.year == self.year:
                matches.add('year')
            # season
            if video.season and self.season == video.season:
                matches.add('season')
            # episode
            if video.episode and self.episode == video.episode:
                matches.add('episode')
        # movie
        elif isinstance(video, Movie):
            # title
            if video.title and sanitize(self.title) == fix_inconsistent_naming(video.title) or sanitize(
                    self.alt_title) == fix_inconsistent_naming(video.title):
                matches.add('title')
            # year
            if video.year and self.year == video.year:
                matches.add('year')

        # rest is same for both groups

        # release_group
        if (video.release_group and self.releases and
                any(r in sanitize_release_group(self.releases)
                    for r in get_equivalent_release_groups(sanitize_release_group(video.release_group)))):
            matches.add('release_group')
        # resolution
        if video.resolution and self.releases and video.resolution in self.releases.lower():
            matches.add('resolution')
        # format
        if video.format and self.releases and video.format.lower() in self.releases.lower():
            matches.add('format')
        # other properties
        matches |= guess_matches(video, guessit(self.releases))

        self.matches = matches

        return matches


class TitloviProvider(Provider, ProviderSubtitleArchiveMixin):
    subtitle_class = TitloviSubtitle
    languages = {Language.fromtitlovi(l) for l in language_converters['titlovi'].codes} | {Language.fromietf('sr-Latn')}
    server_url = 'https://titlovi.com'
    search_url = server_url + '/titlovi/?'
    download_url = server_url + '/download/?type=1&mediaid='

    def initialize(self):
        self.session = RetryingCFSession()
        #load_verification("titlovi", self.session)

    def terminate(self):
        self.session.close()

    def query(self, languages, title, season=None, episode=None, year=None, video=None):
        items_per_page = 10
        current_page = 1

        used_languages = languages
        lang_strings = [str(lang) for lang in used_languages]

        # handle possible duplicate use of Serbian Latin
        if "sr" in lang_strings and "sr-Latn" in lang_strings:
            logger.info('Duplicate entries <Language [sr]> and <Language [sr-Latn]> found, filtering languages')
            used_languages = filter(lambda l: l != Language.fromietf('sr-Latn'), used_languages)
            logger.info('Filtered language list %r', used_languages)

        # convert list of languages into search string
        langs = '|'.join(map(str, [l.titlovi for l in used_languages]))

        # set query params
        params = {'prijevod': title, 'jezik': langs}
        is_episode = False
        if season and episode:
            is_episode = True
            params['s'] = season
            params['e'] = episode
        if year:
            params['g'] = year

        # loop through paginated results
        logger.info('Searching subtitles %r', params)
        subtitles = []

        while True:
            # query the server
            try:
                r = self.session.get(self.search_url, params=params, timeout=10)
                r.raise_for_status()
            except RequestException as e:
                logger.exception('RequestException %s', e)
                break
            else:
                try:
                    soup = BeautifulSoup(r.content, 'lxml')

                    # number of results
                    result_count = int(soup.select_one('.results_count b').string)
                except:
                    result_count = None

                # exit if no results
                if not result_count:
                    if not subtitles:
                        logger.debug('No subtitles found')
                    else:
                        logger.debug("No more subtitles found")
                    break

                # number of pages with results
                pages = int(math.ceil(result_count / float(items_per_page)))

                # get current page
                if 'pg' in params:
                    current_page = int(params['pg'])

                try:
                    sublist = soup.select('section.titlovi > ul.titlovi > li.subtitleContainer.canEdit')
                    for sub in sublist:
                        # subtitle id
                        sid = sub.find(attrs={'data-id': True}).attrs['data-id']
                        # get download link
                        download_link = self.download_url + sid
                        # title and alternate title
                        match = title_re.search(sub.a.string)
                        if match:
                            _title = match.group('title')
                            alt_title = match.group('altitle')
                        else:
                            continue

                        # page link
                        page_link = self.server_url + sub.a.attrs['href']
                        # subtitle language
                        _lang = sub.select_one('.lang')
                        match = lang_re.search(_lang.attrs.get('src', _lang.attrs.get('data-cfsrc', '')))
                        if match:
                            try:
                                # decode language
                                lang = Language.fromtitlovi(match.group('lang')+match.group('script'))
                            except ValueError:
                                continue

                        # relase year or series start year
                        match = year_re.search(sub.find(attrs={'data-id': True}).parent.i.string)
                        if match:
                            r_year = int(match.group('year'))
                        # fps
                        match = fps_re.search(sub.select_one('.fps').string)
                        if match:
                            fps = match.group('fps')
                        # releases
                        releases = str(sub.select_one('.fps').parent.contents[0].string)

                        # handle movies and series separately
                        if is_episode:
                            # season and episode info
                            sxe = sub.select_one('.s0xe0y').string
                            r_season = None
                            r_episode = None
                            if sxe:
                                match = season_re.search(sxe)
                                if match:
                                    r_season = int(match.group('season'))
                                match = episode_re.search(sxe)
                                if match:
                                    r_episode = int(match.group('episode'))

                            subtitle = self.subtitle_class(lang, page_link, download_link, sid, releases, _title,
                                                           alt_title=alt_title, season=r_season, episode=r_episode,
                                                           year=r_year, fps=fps,
                                                           asked_for_release_group=video.release_group,
                                                           asked_for_episode=episode)
                        else:
                            subtitle = self.subtitle_class(lang, page_link, download_link, sid, releases, _title,
                                                           alt_title=alt_title, year=r_year, fps=fps,
                                                           asked_for_release_group=video.release_group)
                        logger.debug('Found subtitle %r', subtitle)

                        # prime our matches so we can use the values later
                        subtitle.get_matches(video)

                        # add found subtitles
                        subtitles.append(subtitle)

                finally:
                    soup.decompose()

                # stop on last page
                if current_page >= pages:
                    break

                # increment current page
                params['pg'] = current_page + 1
                logger.debug('Getting page %d', params['pg'])

        return subtitles

    def list_subtitles(self, video, languages):
        season = episode = None
        if isinstance(video, Episode):
            title = video.series
            season = video.season
            episode = video.episode
        else:
            title = video.title

        return [s for s in
                self.query(languages, fix_inconsistent_naming(title), season=season, episode=episode, year=video.year,
                           video=video)]

    def download_subtitle(self, subtitle):
        r = self.session.get(subtitle.download_link, timeout=10)
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

        subs_in_archive = archive.namelist()

        # if Serbian lat and cyr versions are packed together, try to find right version
        if len(subs_in_archive) > 1 and (subtitle.language == 'sr' or subtitle.language == 'sr-Cyrl'):
            self.get_subtitle_from_bundled_archive(subtitle, subs_in_archive, archive)
        else:
            # use default method for everything else
            subtitle.content = self.get_subtitle_from_archive(subtitle, archive)

    def get_subtitle_from_bundled_archive(self, subtitle, subs_in_archive, archive):
        sr_lat_subs = []
        sr_cyr_subs = []
        sub_to_extract = None

        for sub_name in subs_in_archive:
            if not ('.cyr' in sub_name or '.cir' in sub_name):
                sr_lat_subs.append(sub_name)

            if ('.cyr' in sub_name or '.cir' in sub_name) and not '.lat' in sub_name:
                sr_cyr_subs.append(sub_name)

        if subtitle.language == 'sr':
            if len(sr_lat_subs) > 0:
                sub_to_extract = sr_lat_subs[0]

        if subtitle.language == 'sr-Cyrl':
            if len(sr_cyr_subs) > 0:
                sub_to_extract = sr_cyr_subs[0]

        logger.info(u'Using %s from the archive', sub_to_extract)
        subtitle.content = fix_line_ending(archive.read(sub_to_extract))

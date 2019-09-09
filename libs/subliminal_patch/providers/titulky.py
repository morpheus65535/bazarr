# -*- coding: utf-8 -*-
import io
import logging
import os
import zipfile
import time

import rarfile
from subzero.language import Language
from guessit import guessit
from requests import Session
from six import text_type

from subliminal import __short_version__
from subliminal.exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded
from subliminal.providers import ParserBeautifulSoup, Provider
from subliminal.subtitle import SUBTITLE_EXTENSIONS, fix_line_ending, Subtitle
from subliminal_patch.subtitle import guess_matches
from subliminal.video import Episode, Movie
from subliminal.utils import sanitize_release_group
from subliminal.score import get_equivalent_release_groups
from subliminal_patch.utils import sanitize

logger = logging.getLogger(__name__)


# class TitulkySubtitle(Subtitle):
#     """Titulky Subtitle."""
#     provider_name = 'Titulky'
#
#     def __init__(self, language, page_link, year, version, download_link):
#         super(TitulkySubtitle, self).__init__(language, page_link=page_link)
#         self.year = year
#         self.version = version
#         self.download_link = download_link
#         self.hearing_impaired = None
#         self.encoding = 'UTF-8'
#
#     @property
#     def id(self):
#         return self.download_link
#
#     def get_matches(self, video):
#         matches = set()
#
#         # episode
#         if isinstance(video, Episode):
#             # other properties
#             matches |= guess_matches(video, guessit(self.version, {'type': 'episode'}), partial=True)
#         # movie
#         elif isinstance(video, Movie):
#             # other properties
#             matches |= guess_matches(video, guessit(self.version, {'type': 'movie'}), partial=True)
#
#         return matches

class TitulkySubtitle(Subtitle):
    provider_name = 'titulky'
    
    def __init__(self, language, page_link, season, episode, version, download_link, year, title, asked_for_release_group=None,
                 asked_for_episode=None):
        super(TitulkySubtitle, self).__init__(language, page_link=page_link)
        self.season = season
        self.episode = episode
        self.version = version
        self.year = year
        self.download_link = download_link
        self.encoding = 'UTF-8'
        for t in title:
            self.title = t
        if year:
            self.year = int(year)
        
        self.page_link = page_link
        self.asked_for_release_group = asked_for_release_group
        self.asked_for_episode = asked_for_episode
    
    @property
    def id(self):
        return self.download_link
    
    def get_matches(self, video):
        """
        patch: set guessit to single_value
        :param video:
        :return:
        """
        matches = set()

        # episode
        if isinstance(video, Episode):
            # series
            if video.series:
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
            # guess
            matches |= guess_matches(video, guessit(self.version, {'type': 'episode', "single_value": True}))
            pass
        # movie
        elif isinstance(video, Movie):
            # title
            if video.title and (sanitize(self.title) in (
                    sanitize(name) for name in [video.title] + video.alternative_titles)):
                matches.add('title')
            # year
            if video.year and self.year == video.year:
                matches.add('year')
            # guess
            matches |= guess_matches(video, guessit(self.version, {'type': 'movie', "single_value": True}))

        self.matches = matches

        return matches
    
    # def get_matches(self, video):
    #     matches = set()
    #
    #     # episode
    #     if isinstance(video, Episode):
    #         # series
    #         if video.series and (sanitize(self.series_name) in (
    #                 sanitize(name) for name in [video.series] + video.alternative_series)):
    #             matches.add('series')
    #     # movie
    #     elif isinstance(video, Movie):
    #         # title
    #         if video.title and (sanitize(self.movie_name) in (
    #                 sanitize(name) for name in [video.title] + video.alternative_titles)):
    #             matches.add('title')
    #
    #     # # episode
    #     # if isinstance(video, Episode):
    #     #     # other properties
    #     #     matches |= guess_matches(video, guessit(self.version, {'type': 'episode'}), partial=True)
    #     # # movie
    #     # elif isinstance(video, Movie):
    #     #     # other properties
    #     #     matches |= guess_matches(video, guessit(self.version, {'type': 'movie'}), partial=True)
    #
    #     return matches


class TitulkyProvider(Provider):
    """Titulky Provider."""
    languages = {Language(l) for l in ['ces', 'slk']}
    
    server_url = 'https://premium.titulky.com'
    sign_out_url = '?Logoff=true'
    search_url_series = '?Fulltext={}'
    search_url_movies = '?Searching=AdvancedResult&ARelease={}'
    dn_url = 'https://premium.titulky.com'
    download_url = 'https://premium.titulky.com/idown.php?titulky='
    
    UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'
    
    subtitle_class = TitulkySubtitle
    
    def __init__(self, username=None, password=None):
        if any((username, password)) and not all((username, password)):
            raise ConfigurationError('Username and password must be specified')
        
        self.username = username
        self.password = password
        self.logged_in = False
        self.session = None
    
    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/{}'.format(__short_version__)
        
        # login
        if self.username and self.password:
            logger.info('Logging in')
            self.session.get(self.server_url)
            data = {'Login': self.username,
                    'Password': self.password}
            r = self.session.post(self.server_url, data, allow_redirects=False, timeout=10)
            
            if 'BadLogin' in r.content:
                raise AuthenticationError(self.username)
            
            logger.debug('Logged in')
            self.logged_in = True
    
    def terminate(self):
        # logout
        if self.logged_in:
            logger.info('Logging out')
            r = self.session.get(self.server_url + self.sign_out_url, timeout=10)
            r.raise_for_status()
            logger.debug('Logged out')
            self.logged_in = False
        
        self.session.close()
    
    def query(self, keyword, season=None, episode=None, year=None, video=None):
        params = keyword
        if season and episode:
            params += ' S{season:02d}E{episode:02d}'.format(season=season, episode=episode)
        elif year:
            params += '&ARok={:4d}'.format(year)
        
        logger.debug('Searching subtitles %r', params)
        subtitles = []
        if season and episode:
            search_link = self.server_url + text_type(self.search_url_series).format(params)
        elif year:
            search_link = self.server_url + text_type(self.search_url_movies).format(params)
        
        
        r = self.session.get(search_link, timeout=30)
        r.raise_for_status()
        
        if not r.content:
            logger.debug('No data returned from provider')
            return []
        
        # soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['lxml', 'html.parser'])
        
        # for entity in soup.select('table .main_table > tbody > tr'):
        # for entity in soup.find_all("table", class_="main_table"):
        #     moviename = entity.text
        # entity_url = self.server_url + entity['href']
        # logger.debug(entity_url)
        # r = self.session.get(entity_url, timeout=30)
        # r.raise_for_status()
        # logger.debug('looking into ' + entity_url)
        
        soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['lxml', 'html.parser']).find("table",
                                                                                                      class_="main_table")
        # loop over subtitles cells
        if soup:
            subs = soup.find_all("tr", class_="row1")
            subs += soup.find_all("tr", class_="row2")
            for sub in subs:
                page_link = '%s%s' % (self.server_url, sub.a.get('href').encode('utf-8'))
                title = sub.find_all('td')[0:1]
                title = [x.text.encode('utf-8') for x in title]
                version = sub.find(class_="fixedTip")
                if version is None:
                    version = ""
                else:
                    version = version['title']
                try:
                    r = sub.find_all('td')[6:7]
                    # r2 = td.find("td", "img")
                    langs = [x.text.encode('utf-8') for x in r]
                    pass
                except:
                    langs = 'CZ'
                name = '%s (%s)' % (version, langs)
                
                if ('CZ' in langs):
                    language = Language('ces')
                elif ('SK' in langs):
                    language = Language('slk')
                # read the item
                # subtitle = self.subtitle_class(language, page_link, year, version, page_link.replace("detail", "dld"))
                download_link = sub.find('a', class_='titulkydownloadajax')
                download_link = self.download_url + download_link.get('href')
                
                subtitle = self.subtitle_class(language, page_link,
                                               season, episode, version, download_link, year, title,
                                               asked_for_release_group=video.release_group,
                                               asked_for_episode=episode)
                
                logger.debug('Found subtitle %r', subtitle)
                subtitles.append(subtitle)
            
            soup.decompose()
            soup = None
        
        return subtitles
    
    def list_subtitles(self, video, languages):
        if isinstance(video, Episode):
            titles = [video.series] + video.alternative_series
        elif isinstance(video, Movie):
            titles = [video.title] + video.alternative_titles
        else:
            titles = []
        
        subtitles = []
        # query for subtitles with the show_id
        for title in titles:
            if isinstance(video, Episode):
                subtitles += [s for s in self.query(title, season=video.season, episode=video.episode,
                                                    year=video.year, video=video)
                              if s.language in languages]
            elif isinstance(video, Movie):
                subtitles += [s for s in self.query(title, year=video.year, video=video)
                              if s.language in languages]
        
        return subtitles
    
    def download_subtitle(self, subtitle):
        if isinstance(subtitle, TitulkySubtitle):
            # download the subtitle
            logger.info('Downloading subtitle %r', subtitle)
            r = self.session.get(subtitle.download_link, headers={'Referer': subtitle.page_link},
                                 timeout=30)
            r.raise_for_status()
            
            if not r.content:
                logger.debug('Unable to download subtitle. No data returned from provider')
                return
            elif 'Limit vyčerpán' in r.content:
                raise DownloadLimitExceeded
            
            soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['lxml', 'html.parser'])
            # links = soup.find("a", {"id": "downlink"}).find_all('a')
            link = soup.find(id="downlink")
            # TODO: add settings for choice
            
            url = link.get('href')
            url = self.dn_url + url
            time.sleep(0.5)
            r = self.session.get(url, headers={'Referer': subtitle.download_link},
                                 timeout=30)
            r.raise_for_status()
            
        
        archive_stream = io.BytesIO(r.content)
        archive = None
        if rarfile.is_rarfile(archive_stream):
            logger.debug('Identified rar archive')
            archive = rarfile.RarFile(archive_stream)
            subtitle_content = _get_subtitle_from_archive(archive)
        elif zipfile.is_zipfile(archive_stream):
            logger.debug('Identified zip archive')
            archive = zipfile.ZipFile(archive_stream)
            subtitle_content = _get_subtitle_from_archive(archive)
        else:
            subtitle_content = r.content
        
        if subtitle_content:
            subtitle.content = fix_line_ending(subtitle_content)
        else:
            logger.debug('Could not extract subtitle from %r', archive)


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

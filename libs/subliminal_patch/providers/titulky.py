# -*- coding: utf-8 -*-
from __future__ import absolute_import

import io
import logging
import math
import os
import re
import zipfile
from random import randint
from threading import Thread

import chardet
import rarfile
from guessit import guessit
from requests import Session
from requests.adapters import HTTPAdapter
from subliminal import __short_version__
from subliminal.exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded, Error, ProviderError
from subliminal.providers import ParserBeautifulSoup, Provider
from subliminal.subtitle import SUBTITLE_EXTENSIONS, Subtitle, fix_line_ending
from subliminal.video import Episode, Movie
from subliminal_patch.score import framerate_equal
from subliminal_patch.subtitle import guess_matches, sanitize
from subzero.language import Language

from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

logger = logging.getLogger(__name__)


class TitulkySubtitle(Subtitle):
    """Titulky.com subtitle"""
    provider_name = 'titulky'
    
    hash_verifiable = False
    hearing_impaired_verifiable = False

    def __init__(self, sub_id, language, names, season, episode, year, release_info, fps, uploader, approved, page_link, download_link, skip_wrong_fps=False):
        super().__init__(language, page_link=page_link)

        self.names = names
        self.year = year
        self.sub_id = sub_id
        self.fps = fps
        self.season = season
        self.episode = episode
        self.release_info = release_info
        self.language = language
        self.approved = approved
        self.page_link = page_link
        self.uploader = uploader
        self.download_link = download_link
        self.skip_wrong_fps = skip_wrong_fps
        self.matches = None

    @property
    def id(self):
        return self.sub_id
    
    def get_fps(self):
        return self.fps
    

    def get_matches(self, video):
        matches = set()
        _type = 'movie' if isinstance(video, Movie) else 'episode'
       
        if _type == 'episode':
            ## EPISODE
            if self.season and self.season == video.season:
                matches.add('season')
            if self.episode and self.episode == video.episode:
                matches.add('episode')
            
            name_matches = [video.series and sanitize(name) in sanitize(video.series) for name in self.names]
            if any(name_matches):
                matches.add('series')

        elif _type == 'movie':
            ## MOVIE
            name_matches = [video.title and sanitize(name) in sanitize(video.title) for name in self.names]
            if any(name_matches):
                matches.add('title')
        
        ## MOVIE OR EPISODE
        if video.year and video.year == self.year:
            matches.add('year')


        matches |= guess_matches(video, guessit(self.release_info, {"type": _type}))
        
        
        if self.skip_wrong_fps and video.fps and self.fps and not framerate_equal(video.fps, self.fps):
            logger.info(f"Titulky.com: Skipping subtitle {self}: wrong FPS")
            matches.clear()
        
        self.matches = matches
        return matches


class TitulkyProvider(Provider):
    """Titulky.com provider"""
    
    languages = {Language(l) for l in ['ces', 'slk']}
    hash_verifiable = False
    hearing_impaired_verifiable = False

    
    server_url = 'https://premium.titulky.com'
    login_url = server_url
    logout_url = f"{server_url}?action=logout"
    download_url = f"{server_url}/download.php?id="

    timeout = 30
    max_threads = 5
    
    subtitle_class = TitulkySubtitle
    
    def __init__(self, username=None, password=None, skip_wrong_fps=None, approved_only=None, multithreading=None):
        if not all([username, password]):
            raise ConfigurationError("Username and password must be specified!")
        
        if type(skip_wrong_fps) is not bool:
            raise ConfigurationError(f"Skip_wrong_fps {skip_wrong_fps} must be a boolean!")
        
        if type(approved_only) is not bool:
            raise ConfigurationError(f"Approved_only {approved_only} must be a boolean!")
        
        if type(multithreading) is not bool:
            raise ConfigurationError(f"Multithreading {multithreading} must be a boolean!")
                
        
        self.username = username
        self.password = password
        self.skip_wrong_fps = skip_wrong_fps
        self.approved_only = approved_only
        self.multithreading = multithreading
        
        self.session = None
    
    def initialize(self):
        self.session = Session()
        # Set max pool size to the max number of threads we will use (i .e. the max number of search result rows)
        # or set it to the default value if multithreading is disabled.
        pool_maxsize = self.max_threads + 3 if self.max_threads > 10 else 10
        self.session.mount('https://', HTTPAdapter(pool_maxsize=pool_maxsize))
        self.session.mount('http://', HTTPAdapter(pool_maxsize=pool_maxsize))
        
        # Set headers
        self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]
        self.session.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        self.session.headers['Accept-Language'] = 'sk,cz,en;q=0.5'
        self.session.headers['Accept-Encoding'] = 'gzip, deflate'
        self.session.headers['DNT'] = '1'
        self.session.headers['Connection'] = 'keep-alive'
        self.session.headers['Upgrade-Insecure-Requests'] = '1'
        self.session.headers['Cache-Control'] = 'max-age=0'
        
        self.login()
    
    def terminate(self):
        self.logout()
        self.session.close()
    
    def login(self):
        logger.info("Titulky.com: Logging in")
        
        self.session.get(self.server_url)
        
        data = {
            'LoginName': self.username,
            'LoginPassword': self.password
        }
        res = self.session.post(self.server_url, data, allow_redirects=False, timeout=self.timeout)
        
        # If the response is a redirect and doesnt point to an error message page, then we are logged in
        if res.status_code == 302 and 'msg_type=i' in res.headers['Location']:
            return True
        else:
            raise AuthenticationError("Login failed")
    
    def logout(self):
        logger.info("Titulky.com: Logging out")
        
        res = self.session.get(self.logout_url, allow_redirects=False, timeout=self.timeout)
        
        # If the response is a redirect and doesnt point to an error message page, then we are logged out
        if res.status_code == 302 and 'msg_type=i' in res.headers['Location']:
            return True
        else:
            raise AuthenticationError("Logout failed.")

    def fetch_page(self, url):
        logger.debug(f"Titulky.com: Fetching url: {url}")
        res = self.session.get(url, timeout=self.timeout)
        
        if res.status_code != 200:
            raise ProviderError(f"Fetch failed with status code {res.status_code}")
        if not res.text:
            raise ProviderError("No response returned from the provider")
        
        return res.text

    def build_search_url(self, params):
        result = f"{self.server_url}/?"
        
        params['action'] = 'search'
        params['fsf'] = 1 # Requires subtitle names to match full search keyword
        
        for key, value in params.items():
            result += f'{key}={value}&'
        
        # Remove last &
        result = result[:-1]
        
        # Remove spaces
        result = result.replace(' ', '+')
        
        return result
    
    # Parse details of an individual subtitle: release, language, uploader, fps and year
    def parse_details(self, url):
        html_src = self.fetch_page(url)
        details_page_soup = ParserBeautifulSoup(html_src, ['lxml', 'html.parser'])
        
        details_container = details_page_soup.find('div', class_='detail')
        if not details_container:
            # The subtitles were removed and got redirected to a different page. Better treat this silently.
            logger.debug("Titulky.com: Could not find details div container. Skipping.")
            return False
        
        ### RELEASE
        release = None
        release_tag = details_container.find('div', class_='releas')
        
        if not release_tag:
            raise Error("Could not find release tag. Did the HTML source change?")
        
        release = release_tag.get_text(strip=True)
        
        if not release:
            logger.info("Titulky.com: No release information supplied on details page.")

        ### LANGUAGE
        language = None
        czech_flag = details_container.select('img[src*=\'flag-CZ\']')
        slovak_flag = details_container.select('img[src*=\'flag-SK\']')
        
        if czech_flag and not slovak_flag:
            language = Language('ces')
        elif slovak_flag and not czech_flag: 
            language = Language('slk')
        
        if not language:
            logger.debug("Titulky.com: No language information supplied on details page.")

        ### UPLOADER
        uploader = None
        uploader_tag = details_container.find('div', class_='ulozil')
        
        if not uploader_tag:
            raise Error("Could not find uploader tag. Did the HTML source change?")
        
        uploader_anchor_tag = uploader_tag.find('a')
        
        if not uploader_anchor_tag:
            raise Error("Could not find uploader anchor tag. Did the HTML source change?")
        
        uploader = uploader_anchor_tag.string.strip() if uploader_anchor_tag else None
        
        if not uploader:
            logger.debug("Titulky.com: No uploader name supplied on details page.")

        ### FPS
        fps = None
        fps_icon_tag_selection = details_container.select('img[src*=\'Movieroll\']')
        
        if not fps_icon_tag_selection and not hasattr(fps_icon_tag_selection[0], 'parent'):
            raise Error("Could not find parent of the fps icon tag. Did the HTML source change?")
        
        fps_icon_tag = fps_icon_tag_selection[0]
        parent_text = fps_icon_tag.parent.get_text(strip=True)
        match = re.findall('(\d+,\d+) fps', parent_text)
            
         # If the match is found, change the decimal separator to a dot and convert to float
        fps = float(match[0].replace(',', '.')) if len(match) > 0 else None

        if not fps:
            logger.debug("Titulky.com: No fps supplied on details page.")
        
        ### YEAR
        year = None
        h1_tag = details_container.find('h1', id='titulky')
        
        if not h1_tag:
            raise Error("Could not find h1 tag. Did the HTML source change?")
        
        # The h1 tag contains the name of the subtitle and a year
        h1_texts = [text for text in h1_tag.stripped_strings]
        year = int(h1_texts[1]) if len(h1_texts) > 1 else None
        
        if not year:
            logger.debug("Titulky.com: No year supplied on details page.")
        
        
        # Clean up
        details_page_soup.decompose()
        details_page_soup = None
        
        # Return the subtitle details
        return {
            'release': release, 
            'language': language, 
            'uploader': uploader, 
            'fps': fps,
            'year': year
        }
    
    def process_row(self, row, keyword, thread_id=None, threads_data=None):
        try:
            # The first anchor tag is an image preview, the second is the name
            anchor_tag = row.find_all('a')[1]
            # The details link is relative, so we need to remove the dot at the beginning
            details_link = f"{self.server_url}{anchor_tag.get('href')[1:]}"
            id_match = re.findall('id=(\d+)', details_link)
            sub_id = id_match[0] if len(id_match) > 0 else None
            download_link = f"{self.download_url}{sub_id}"

            # Approved subtitles have a pbl1 class for their row, others have a pbl0 class
            approved = True if 'pbl1' in row.get('class') else False
            
            # Name + alternative names
            table_columns = row.findAll("td")
            main_name = anchor_tag.get_text(strip=True)
            alt_names = [alt_name.strip() for alt_name in table_columns[2].get_text(strip=True).split("/")]
            names = [main_name] + alt_names


            # Loop over all subtitle names and check if the keyword contains them
            name_matches = [keyword and sanitize(keyword) not in sanitize(name) for name in names]

            # Skip subtitles that do not contain the keyword in their name(s)
            if keyword and all(name_matches) is False:
                logger.debug(f"Titulky.com: Skipping subtitle with names: '{names}', because it does not not contain the keyword: '{keyword}'")
                if type(threads_data) is list and type(thread_id) is int:
                    threads_data[thread_id] = {
                        'sub_info': None,
                        'exception': None
                    }
                    
                return None
            
            details = self.parse_details(details_link)
            if not details:
                # Details parsing was NOT successful, skipping
                if type(threads_data) is list and type(thread_id) is int:
                    threads_data[thread_id] = {
                        'sub_info': None,
                        'exception': None
                    }
                    
                return None
            
            # Combine all subtitle data into one dict
            result = {
                'names': names,
                'id': sub_id,
                'approved': approved,
                'details_link': details_link,
                'download_link': download_link
            }
            
            result.update(details)
            
            if type(threads_data) is list and type(thread_id) is int:
                threads_data[thread_id] = {
                    'sub_info': result,
                    'exception': None
                }
                
            return details
        except Exception as e:
            if type(threads_data) is list and type(thread_id) is int:
                threads_data[thread_id] = {
                    'sub_info': None,
                    'exception': e
                }
                
            raise e
    
    # There are multiple ways to find subs from this provider:
    # 1. SEARCH by sub title
    #    - parameter: .................. Fulltext=<SUB NAME> 
    # 2. SEARCH by imdb id
    #    - parameter: .................. IMDB=<IMDB ID>
    # 3. SEARCH by season/episode
    #    - parameter: .................. Sezona=<SEASON>
    #    - parameter: .................. Epizoda=<EPISODE>
    # 4. SEARCH by year
    #    - parameter: .................. Rok=<YEAR>
    # 5. SEARCH by video type
    #    - parameter: .................. Serial=<('S' for series | 'F' for movies | '' for all)>
    # 6. SEARCH by language
    #    - parameter: .................. Jazyk=<('CZ' for czech | 'SK' for slovak | '' for all)>
    # 7. SEARCH by status
    #    - parameter: .................. ASchvalene=<('1' for approved only | '-0' for subs awaiting approval | '' for all)>
    # - redirects should NOT be allowed here
    #
    # 8. BROWSE subtitles by IMDB ID
    #   - Subtitles are here categorised by seasons and episodes
    #   - URL: https://premium.titulky.com/?action=serial&step=<SEASON>&id=<IMDB ID>
    #   - it seems that the url redirects to a page with their own internal ID, redirects should be allowed here
    def query(self, language, type, keyword=None, year=None, season=None, episode=None, imdb_id=None):
        ## Build the search URL
        params = {}
        
        # Keyword
        if keyword:
            params['Fulltext'] = keyword
        # Video type
        if type == 'episode':
            params['Serial'] = 'S'
        else:
            params['Serial'] = 'F'
        # Season / Episode
        if season:
            params['Sezona'] = season
        if episode:
            params['Epizoda'] = episode
        # IMDB ID
        if imdb_id:
            params['IMDB'] = imdb_id[2:] # Remove the tt from the imdb id
        # Year
        if year:
            params['Rok'] = year
        # Language
        if language == Language('ces'):
            params['Jazyk'] = 'CZ'
        elif language == Language('slk'):
            params['Jazyk'] = 'SK'
        elif language == None:
            params['Jazyk'] = ''
        else:
            return []
        # Status
        if self.approved_only:
            params['ASchvalene'] = '1'
        else:
            params['ASchvalene'] = ''
            
        
        search_url = self.build_search_url(params)
        
        ## Search results page parsing
        html_src = self.fetch_page(search_url)
        search_page_soup = ParserBeautifulSoup(html_src, ['lxml', 'html.parser'])
        
        # If there is a message containing "Žádny odpovídající záznam", it means that there are no results
        # If that's the case, return an empty list
        error_message = search_page_soup.select('.panel-body > strong')
        if len(error_message) > 0 and 'Žádný odpovídající záznam' in error_message[0].get_text(strip=True):
            logger.info("Titulky.com: No results found")
            return []
        
        # Get the table containing the search results
        table = search_page_soup.find('table', class_='table')
        if not table:
            logger.debug("Titulky.com: Could not find table")
            raise Error("Could not find table. Did the HTML source change?")
        
        # Get table body containing rows of subtitles
        table_body = table.find('tbody')
        if not table_body:
            logger.debug("Titulky.com: Could not find table body")
            raise Error("Could not find table body. Did the HTML source change?")
        
        ## Loop over all subtitles on the first page and put them in a list
        subtitles = []
        rows = table_body.find_all('tr')
        
        if not self.multithreading:
            # Process the rows sequentially
            logger.info("Titulky.com: processing results in sequence")
            for i, row in enumerate(rows):
                sub_info = self.process_row(row, keyword)
                
                # If subtitle info was returned, then everything was okay 
                # and we can instationate it and add it to the list
                if sub_info:
                    logger.debug(f"Titulky.com: Sucessfully retrieved subtitle info, row: {i}")

                    # Try to parse S00E00 string from the main subtitle name
                    sub_season = None
                    sub_episode = None
                    season_episode_string = re.findall('S(\d+)E(\d+)', sub_info['names'][0], re.IGNORECASE)
                    if season_episode_string:
                        sub_season = season_episode_string[0][0]
                        sub_episode = season_episode_string[0][1]


                    subtitle_instance = self.subtitle_class(sub_info['id'], sub_info['language'], sub_info['names'], sub_season, sub_episode, sub_info['year'], sub_info['release'], sub_info['fps'],
                                                            sub_info['uploader'], sub_info['approved'], sub_info['details_link'], sub_info['download_link'], skip_wrong_fps=self.skip_wrong_fps)
                    subtitles.append(subtitle_instance)
                else:
                    # No subtitle info was returned, i. e. something unexpected
                    # happend during subtitle details page fetching and processing.
                    logger.debug(f"Titulky.com: No subtitle info retrieved, row: {i}")
        else:
            # Process the rows in paralell
            logger.info(f"Titulky.com: processing results in parelell, {self.max_threads} rows at a time.")

            threads = [None] * len(rows)
            threads_data = [None] * len(rows)

            # Process rows in parallel, self.max_threads at a time.
            cycles = math.ceil(len(rows)/self.max_threads)
            for i in range(cycles):
                # Batch number i
                starting_index = i * self.max_threads # Inclusive
                ending_index = starting_index + self.max_threads # Non-inclusive

                # Create threads for all rows in this batch
                for j in range(starting_index, ending_index):
                    # Check if j-th row exists
                    if j < len(rows):
                        # Row number j
                        logger.debug(f"Titulky.com: Creating thread {j} (batch: {i})")
                        # Create a thread for row j and start it
                        threads[j] = Thread(target=self.process_row, args=[rows[j], keyword], kwargs={'thread_id': j, 'threads_data': threads_data})
                        threads[j].start()

                # Wait for all created threads to finish before moving to another batch of rows
                for j in range(starting_index, ending_index):
                    # Check if j-th row exists
                    if j < len(rows):
                        threads[j].join()

            # Process the resulting data from all threads
            for i in range(len(threads_data)):
                thread_data = threads_data[i]

                # If the thread returned didn't return anything, but expected a dict object
                if not thread_data:
                    raise Error(f"No data returned from thread ID: {i}")
                
                # If an exception was raised in a thread, raise it again here
                if 'exception' in thread_data and thread_data['exception']:
                    logger.debug(f"Titulky.com: An error occured while processing a row in the thread ID {i}")
                    raise thread_data['exception']

                # If the thread returned a subtitle info, great, instantiate it and add it to the list
                if 'sub_info' in thread_data and thread_data['sub_info']:
                    # Instantiate the subtitle object
                    logger.debug(f"Titulky.com: Sucessfully retrieved subtitle info, thread ID: {i}")
                    sub_info = thread_data['sub_info']

                    # Try to parse S00E00 string from the main subtitle name
                    sub_season = None
                    sub_episode = None
                    season_episode_string = re.findall('S(\d+)E(\d+)', sub_info['names'][0], re.IGNORECASE)
                    if season_episode_string:
                        sub_season = season_episode_string[0][0]
                        sub_episode = season_episode_string[0][1]

                    subtitle_instance = self.subtitle_class(sub_info['id'], sub_info['language'], sub_info['names'], sub_season, sub_episode, sub_info['year'], sub_info['release'], sub_info['fps'],
                                                            sub_info['uploader'], sub_info['approved'], sub_info['details_link'], sub_info['download_link'], skip_wrong_fps=self.skip_wrong_fps)
                    subtitles.append(subtitle_instance)
                else:
                    # The thread returned data, but it didn't contain a subtitle info, i. e. something unexpected
                    # happend during subtitle details page fetching and processing.
                    logger.debug(f"Titulky.com: No subtitle info retrieved, thread ID: {i}")
                
        # Clean up
        search_page_soup.decompose()
        search_page_soup = None
        
        logger.debug(f"Titulky.com: Found subtitles: {subtitles}")
        
        return subtitles
    
    def list_subtitles(self, video, languages):        
        subtitles = []
        
        # Possible paths:
        # (1) Search by IMDB ID [and season/episode for tv series]
        # (2) Search by keyword: video (title|series) [and season/episode for tv series]
        # (3) Search by keyword: video series + S00E00 (tv series only)
        
        for language in languages:
            if isinstance(video, Episode):
                # (1)
                logger.debug("Titulky.com: Finding subtitles by IMDB ID (1)")
                if video.series_imdb_id:
                    partial_subs = self.query(language, 'episode', imdb_id=video.series_imdb_id, season=video.season, episode=video.episode)
                    if(len(partial_subs) > 0):
                        subtitles += partial_subs
                        continue
                
                # (2)
                logger.debug("Titulky.com: Finding subtitles by keyword (2)")
                keyword = video.series
                partial_subs = self.query(language, 'episode', keyword=keyword, season=video.season, episode=video.episode)
                if(len(partial_subs) > 0):
                    subtitles += partial_subs
                    continue
                
                # (3)
                logger.debug("Titulky.com: Finding subtitles by keyword (3)")
                keyword = f"{video.series} S{video.season:02d}E{video.episode:02d}"
                partial_subs = self.query(language, 'episode', keyword=keyword)
                subtitles += partial_subs
            elif isinstance(video, Movie):
                # (1)
                logger.debug("Titulky.com: Finding subtitles by IMDB ID (1)")
                if video.imdb_id:
                    partial_subs = self.query(language, 'movie', imdb_id=video.imdb_id)
                    if(len(partial_subs) > 0):
                        subtitles += partial_subs
                        continue
                
                # (2)
                logger.debug("Titulky.com: Finding subtitles by keyword (2)")
                keyword = video.title
                partial_subs = self.query(language, 'movie', keyword=keyword)
                subtitles += partial_subs
                
        return subtitles
    
# The rest is mostly old code from original implementation. Might want to redo it.
    def download_subtitle(self, subtitle):
        res = self.session.get(subtitle.download_link, headers={'Referer': subtitle.page_link},
                             timeout=self.timeout)
        res.raise_for_status()
            
        archive_stream = io.BytesIO(res.content)
        archive = None
        if rarfile.is_rarfile(archive_stream):
            logger.debug("Titulky.com: Identified rar archive")
            archive = rarfile.RarFile(archive_stream)
            subtitle_content = _get_subtitle_from_archive(archive)
        elif zipfile.is_zipfile(archive_stream):
            logger.debug("Titulky.com: Identified zip archive")
            archive = zipfile.ZipFile(archive_stream)
            subtitle_content = _get_subtitle_from_archive(archive)
        else:
            subtitle_content = res.content
            
        if subtitle_content:
            subtitle.content = fix_line_ending(subtitle_content)
            return subtitle_content
        else:
            logger.debug(f"Titulky.com: Could not extract subtitle from {archive}")

def _get_subtitle_from_archive(archive):
    if '_info.txt' in archive.namelist():
        info_content_binary = archive.read('_info.txt')
        info_content = info_content_binary.decode(chardet.detect(info_content_binary)['encoding'])
        if "nestaženo - překročen limit" in info_content:
            raise DownloadLimitExceeded("The download limit has been exceeded")

    for name in archive.namelist():
        # discard hidden files
        if os.path.split(name)[-1].startswith('.'):
            continue
        
        # discard non-subtitle files
        if not name.lower().endswith(SUBTITLE_EXTENSIONS):
            continue
        
        return archive.read(name)
    
    return None

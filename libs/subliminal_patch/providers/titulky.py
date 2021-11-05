# -*- coding: utf-8 -*-
from __future__ import absolute_import

import io
import logging
import math
import re
import zipfile
from random import randint
from threading import Thread

import rarfile
from guessit import guessit
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError

from subliminal.exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded, Error, ProviderError
from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitle import fix_line_ending
from subliminal.video import Episode, Movie

from subliminal_patch.exceptions import ParseResponseError
from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.score import framerate_equal
from subliminal_patch.subtitle import Subtitle, guess_matches, sanitize

from subzero.language import Language

from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

logger = logging.getLogger(__name__)


class TitulkySubtitle(Subtitle):
    """Titulky.com subtitle"""
    provider_name = 'titulky'

    hash_verifiable = False
    hearing_impaired_verifiable = False

    def __init__(self,
                 sub_id,
                 imdb_id,
                 language,
                 names,
                 season,
                 episode,
                 year,
                 releases,
                 fps,
                 uploader,
                 approved,
                 page_link,
                 download_link,
                 skip_wrong_fps=False,
                 asked_for_episode=None):
        super().__init__(language, page_link=page_link)

        self.names = names
        self.year = year
        self.sub_id = sub_id
        self.imdb_id = imdb_id
        self.fps = fps
        self.season = season
        self.episode = episode
        self.releases = releases
        self.release_info = ', '.join(releases)
        self.language = language
        self.approved = approved
        self.page_link = page_link
        self.uploader = uploader
        self.download_link = download_link
        self.skip_wrong_fps = skip_wrong_fps
        self.asked_for_episode = asked_for_episode
        self.matches = None

        # Try to parse S00E00 string from the main subtitle name
        season_episode_string = re.findall(r'S(\d+)E(\d+)', self.names[0],
                                           re.IGNORECASE)

        # If we did not search for subtitles with season and episode numbers in search query,
        # try to parse it from the main subtitle name that most likely contains it
        if season_episode_string:
            if self.season is None:
                self.season = int(season_episode_string[0][0])
            if self.episode is None:
                self.episode = int(season_episode_string[0][1])

    @property
    def id(self):
        return self.sub_id

    def get_fps(self):
        return self.fps

    def get_matches(self, video):
        matches = set()
        _type = 'movie' if isinstance(video, Movie) else 'episode'

        sub_names = self._remove_season_episode_string(self.names)

        if _type == 'episode':
            ## EPISODE

            # match imdb_id of a series
            if video.series_imdb_id and video.series_imdb_id == self.imdb_id:
                matches.add('series_imdb_id')

            # match season/episode
            if self.season and self.season == video.season:
                matches.add('season')
            if self.episode and self.episode == video.episode:
                matches.add('episode')

            # match series name
            series_names = [video.series] + video.alternative_series
            logger.debug(
                f"Titulky.com: Finding exact match between subtitle names {sub_names} and series names {series_names}"
            )
            if _contains_element(_from=series_names,
                                 _in=sub_names,
                                 exactly=True):
                matches.add('series')

            # match episode title
            episode_titles = [video.title]
            logger.debug(
                f"Titulky.com: Finding exact match between subtitle names {sub_names} and episode titles {episode_titles}"
            )
            if _contains_element(_from=episode_titles,
                                 _in=sub_names,
                                 exactly=True):
                matches.add('episode_title')

        elif _type == 'movie':
            ## MOVIE

            # match imdb_id of a movie
            if video.imdb_id and video.imdb_id == self.imdb_id:
                matches.add('imdb_id')

            # match movie title
            video_titles = [video.title] + video.alternative_titles
            logger.debug(
                f"Titulky.com: Finding exact match between subtitle names {sub_names} and video titles {video_titles}"
            )
            if _contains_element(_from=video_titles,
                                 _in=sub_names,
                                 exactly=True):
                matches.add('title')

        ## MOVIE OR EPISODE

        # match year
        if video.year and video.year == self.year:
            matches.add('year')

        # match other properties based on release infos
        for release in self.releases:
            matches |= guess_matches(video, guessit(release, {"type": _type}))

        # If turned on in settings, then do not match if video FPS is not equal to subtitle FPS
        if self.skip_wrong_fps and video.fps and self.fps and not framerate_equal(
                video.fps, self.fps):
            logger.info(f"Titulky.com: Skipping subtitle {self}: wrong FPS")
            matches.clear()

        self.matches = matches

        return matches

    # Remove the S00E00 from elements of names array
    def _remove_season_episode_string(self, names):
        result = names.copy()

        for i, name in enumerate(result):
            cleaned_name = re.sub(r'S\d+E\d+', '', name, flags=re.IGNORECASE)
            cleaned_name = cleaned_name.strip()

            result[i] = cleaned_name

        return result


class TitulkyProvider(Provider, ProviderSubtitleArchiveMixin):
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

    def __init__(self,
                 username=None,
                 password=None,
                 skip_wrong_fps=None,
                 approved_only=None,
                 multithreading=None):
        if not all([username, password]):
            raise ConfigurationError("Username and password must be specified!")

        if type(skip_wrong_fps) is not bool:
            raise ConfigurationError(
                f"Skip_wrong_fps {skip_wrong_fps} must be a boolean!")

        if type(approved_only) is not bool:
            raise ConfigurationError(
                f"Approved_only {approved_only} must be a boolean!")

        if type(multithreading) is not bool:
            raise ConfigurationError(
                f"Multithreading {multithreading} must be a boolean!")

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
        self.session.headers['User-Agent'] = AGENT_LIST[randint(
            0,
            len(AGENT_LIST) - 1)]
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

        data = {'LoginName': self.username, 'LoginPassword': self.password}
        res = self.session.post(self.server_url,
                                data,
                                allow_redirects=False,
                                timeout=self.timeout)

        # If the response is a redirect and doesnt point to an error message page, then we are logged in
        if res.status_code == 302 and 'msg_type=i' in res.headers['Location']:
            return True
        else:
            raise AuthenticationError("Login failed")

    def logout(self):
        logger.info("Titulky.com: Logging out")

        res = self.session.get(self.logout_url,
                               allow_redirects=False,
                               timeout=self.timeout)

        # If the response is a redirect and doesnt point to an error message page, then we are logged out
        if res.status_code == 302 and 'msg_type=i' in res.headers['Location']:
            return True
        else:
            raise AuthenticationError("Logout failed.")

    def fetch_page(self, url, ref=None):
        logger.debug(f"Titulky.com: Fetching url: {url}")

        res = self.session.get(
            url,
            timeout=self.timeout,
            headers={'Referer': ref if ref else self.server_url})

        if res.status_code != 200:
            raise HTTPError(f"Fetch failed with status code {res.status_code}")
        if not res.text:
            raise ProviderError("No response returned from the provider")

        return res.text

    def build_search_url(self, params):
        result = f"{self.server_url}/?"

        params['action'] = 'search'
        # Requires subtitle names to match full search keyword
        params['fsf'] = 1

        for key, value in params.items():
            result += f'{key}={value}&'

        # Remove the last &
        result = result[:-1]

        # Remove spaces
        result = result.replace(' ', '+')

        return result

    # Parse details of an individual subtitle: imdb_id, release, language, uploader, fps and year
    def parse_details(self, details_url, search_url):
        html_src = self.fetch_page(details_url, ref=search_url)
        details_page_soup = ParserBeautifulSoup(html_src,
                                                ['lxml', 'html.parser'])

        details_container = details_page_soup.find('div', class_='detail')
        if not details_container:
            # The subtitles could be removed and got redirected to a different page. Better treat this silently.
            logger.debug(
                "Titulky.com: Could not find details div container. Skipping.")
            return False

        ### IMDB ID
        imdb_id = None
        imdb_tag = details_container.find('a', attrs={'target': 'imdb'})

        if imdb_tag:
            imdb_url = imdb_tag.get('href')
            imdb_id = re.findall(r'tt(\d+)', imdb_url)[0]

        if not imdb_id:
            logger.debug("Titulky.com: No IMDB ID supplied on details page.")

        ### RELEASE
        release = None
        release_tag = details_container.find('div', class_='releas')

        if not release_tag:
            raise ParseResponseError(
                "Could not find release tag. Did the HTML source change?")

        release = release_tag.get_text(strip=True)

        if not release:
            logger.debug(
                "Titulky.com: No release information supplied on details page.")

        ### LANGUAGE
        language = None
        czech_flag = details_container.select('img[src*=\'flag-CZ\']')
        slovak_flag = details_container.select('img[src*=\'flag-SK\']')

        if czech_flag and not slovak_flag:
            language = Language('ces')
        elif slovak_flag and not czech_flag:
            language = Language('slk')

        if not language:
            logger.debug(
                "Titulky.com: No language information supplied on details page."
            )

        ### UPLOADER
        uploader = None
        uploader_tag = details_container.find('div', class_='ulozil')

        if not uploader_tag:
            raise ParseResponseError(
                "Could not find uploader tag. Did the HTML source change?")

        uploader_anchor_tag = uploader_tag.find('a')

        if not uploader_anchor_tag:
            raise ParseResponseError(
                "Could not find uploader anchor tag. Did the HTML source change?"
            )

        uploader = uploader_anchor_tag.string.strip(
        ) if uploader_anchor_tag else None

        if not uploader:
            logger.debug(
                "Titulky.com: No uploader name supplied on details page.")

        ### FPS
        fps = None
        fps_icon_tag_selection = details_container.select(
            'img[src*=\'Movieroll\']')

        if not fps_icon_tag_selection and not hasattr(fps_icon_tag_selection[0],
                                                      'parent'):
            raise ParseResponseError(
                "Could not find parent of the fps icon tag. Did the HTML source change?"
            )

        fps_icon_tag = fps_icon_tag_selection[0]
        parent_text = fps_icon_tag.parent.get_text(strip=True)
        match = re.findall(r'(\d+,\d+) fps', parent_text)

        # If the match is found, change the decimal separator to a dot and convert to float
        fps = float(match[0].replace(',', '.')) if len(match) > 0 else None

        if not fps:
            logger.debug("Titulky.com: No fps supplied on details page.")

        ### YEAR
        year = None
        h1_tag = details_container.find('h1', id='titulky')

        if not h1_tag:
            raise ParseResponseError(
                "Could not find h1 tag. Did the HTML source change?")

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
            'releases': [release],
            'language': language,
            'uploader': uploader,
            'fps': fps,
            'year': year,
            'imdb_id': imdb_id
        }

    def process_row(self,
                    row,
                    video_names,
                    search_url,
                    thread_id=None,
                    threads_data=None):
        try:
            # The first anchor tag is an image preview, the second is the name
            anchor_tag = row.find_all('a')[1]
            # The details link is relative, so we need to remove the dot at the beginning
            details_link = f"{self.server_url}{anchor_tag.get('href')[1:]}"
            id_match = re.findall(r'id=(\d+)', details_link)
            sub_id = id_match[0] if len(id_match) > 0 else None
            download_link = f"{self.download_url}{sub_id}"

            # Approved subtitles have a pbl1 class for their row, others have a pbl0 class
            approved = True if 'pbl1' in row.get('class') else False

            # Subtitle name + its alternative names
            table_columns = row.findAll('td')
            main_sub_name = anchor_tag.get_text(strip=True)

            alt_sub_names = [
                alt_sub_name.strip()
                for alt_sub_name in table_columns[2].string.split('/')
            ] if table_columns[2].string else []
            sub_names = [main_sub_name] + alt_sub_names

            # Does at least one subtitle name contain one of the video names?
            # Skip subtitles that do not match
            # Video names -> the main title and alternative titles of a movie or an episode and so on...
            # Subtitle names -> the main name and alternative names of a subtitle displayed in search results.
            # Could be handled in TitulkySubtitle class, however we want to keep the number of requests
            # as low as possible and this prevents the from requesting the details page unnecessarily
            if not _contains_element(_from=video_names, _in=sub_names):
                logger.debug(
                    f"Titulky.com: Skipping subtitle with names: {sub_names}, because there was no match with video names: {video_names}"
                )
                if type(threads_data) is list and type(thread_id) is int:
                    threads_data[thread_id] = {
                        'sub_info': None,
                        'exception': None
                    }

                return None

            details = self.parse_details(details_link, search_url)
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
                'names': sub_names,
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
                threads_data[thread_id] = {'sub_info': None, 'exception': e}

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
    def query(self,
              language,
              video_names,
              type,
              keyword=None,
              year=None,
              season=None,
              episode=None,
              imdb_id=None):
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
            params['IMDB'] = imdb_id[2:]  # Remove the tt from the imdb id
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
        search_page_soup = ParserBeautifulSoup(html_src,
                                               ['lxml', 'html.parser'])

        # If there is a message containing "Žádny odpovídající záznam", it means that there are no results
        # If that's the case, return an empty list
        error_message = search_page_soup.select('.panel-body > strong')
        if len(
                error_message
        ) > 0 and 'Žádný odpovídající záznam' in error_message[0].get_text(
                strip=True):
            logger.info("Titulky.com: No results found")
            return []

        # Get the table containing the search results
        table = search_page_soup.find('table', class_='table')
        if not table:
            logger.debug("Titulky.com: Could not find table")
            raise ParseResponseError(
                "Could not find table. Did the HTML source change?")

        # Get table body containing rows of subtitles
        table_body = table.find('tbody')
        if not table_body:
            logger.debug("Titulky.com: Could not find table body")
            raise ParseResponseError(
                "Could not find table body. Did the HTML source change?")

        ## Loop over all subtitles on the first page and put them in a list
        subtitles = []
        rows = table_body.find_all('tr')

        if not self.multithreading:
            # Process the rows sequentially
            logger.info("Titulky.com: processing results in sequence")
            for i, row in enumerate(rows):
                sub_info = self.process_row(row, video_names, search_url)

                # If subtitle info was returned, then everything was okay
                # and we can instationate it and add it to the list
                if sub_info:
                    logger.debug(
                        f"Titulky.com: Sucessfully retrieved subtitle info, row: {i}"
                    )

                    # If we found the subtitle by IMDB ID, no need to get it from details page
                    sub_imdb_id = imdb_id or sub_info['imdb_id']

                    subtitle_instance = self.subtitle_class(
                        sub_info['id'],
                        sub_imdb_id,
                        sub_info['language'],
                        sub_info['names'],
                        season,
                        episode,
                        sub_info['year'],
                        sub_info['releases'],
                        sub_info['fps'],
                        sub_info['uploader'],
                        sub_info['approved'],
                        sub_info['details_link'],
                        sub_info['download_link'],
                        skip_wrong_fps=self.skip_wrong_fps,
                        asked_for_episode=(type == 'episode'))
                    subtitles.append(subtitle_instance)
                else:
                    # No subtitle info was returned, i. e. something unexpected
                    # happend during subtitle details page fetching and processing.
                    logger.debug(
                        f"Titulky.com: No subtitle info retrieved, row: {i}")
        else:
            # Process the rows in paralell
            logger.info(
                f"Titulky.com: processing results in parelell, {self.max_threads} rows at a time."
            )

            threads = [None] * len(rows)
            threads_data = [None] * len(rows)

            # Process rows in parallel, self.max_threads at a time.
            cycles = math.ceil(len(rows) / self.max_threads)
            for i in range(cycles):
                # Batch number i
                starting_index = i * self.max_threads  # Inclusive
                ending_index = starting_index + self.max_threads  # Non-inclusive

                # Create threads for all rows in this batch
                for j in range(starting_index, ending_index):
                    # Check if j-th row exists
                    if j < len(rows):
                        # Row number j
                        logger.debug(
                            f"Titulky.com: Creating thread {j} (batch: {i})")
                        # Create a thread for row j and start it
                        threads[j] = Thread(
                            target=self.process_row,
                            args=[rows[j], video_names, search_url],
                            kwargs={
                                'thread_id': j,
                                'threads_data': threads_data
                            })
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
                    raise ProviderError(f"No data returned from thread ID: {i}")

                # If an exception was raised in a thread, raise it again here
                if 'exception' in thread_data and thread_data['exception']:
                    logger.debug(
                        f"Titulky.com: An error occured while processing a row in the thread ID {i}"
                    )
                    raise thread_data['exception']

                # If the thread returned a subtitle info, great, instantiate it and add it to the list
                if 'sub_info' in thread_data and thread_data['sub_info']:
                    # Instantiate the subtitle object
                    logger.debug(
                        f"Titulky.com: Sucessfully retrieved subtitle info, thread ID: {i}"
                    )
                    sub_info = thread_data['sub_info']

                    # If we found the subtitle by IMDB ID, no need to get it from details page
                    sub_imdb_id = imdb_id or sub_info['imdb_id']

                    subtitle_instance = self.subtitle_class(
                        sub_info['id'],
                        sub_imdb_id,
                        sub_info['language'],
                        sub_info['names'],
                        season,
                        episode,
                        sub_info['year'],
                        sub_info['releases'],
                        sub_info['fps'],
                        sub_info['uploader'],
                        sub_info['approved'],
                        sub_info['details_link'],
                        sub_info['download_link'],
                        skip_wrong_fps=self.skip_wrong_fps,
                        asked_for_episode=(type == 'episode'))
                    subtitles.append(subtitle_instance)
                else:
                    # The thread returned data, but it didn't contain a subtitle info, i. e. something unexpected
                    # happend during subtitle details page fetching and processing.
                    logger.debug(
                        f"Titulky.com: No subtitle info retrieved, thread ID: {i}"
                    )

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
                video_names = [video.series, video.title
                              ] + video.alternative_series

                # (1)
                logger.debug(
                    "Titulky.com: Finding subtitles by IMDB ID, Season and Episode (1)"
                )
                if video.series_imdb_id:
                    partial_subs = self.query(language,
                                              video_names,
                                              'episode',
                                              imdb_id=video.series_imdb_id,
                                              season=video.season,
                                              episode=video.episode)
                    if (len(partial_subs) > 0):
                        subtitles += partial_subs
                        continue

                # (2)
                logger.debug(
                    "Titulky.com: Finding subtitles by keyword, Season and Episode (2)"
                )
                keyword = video.series
                partial_subs = self.query(language,
                                          video_names,
                                          'episode',
                                          keyword=keyword,
                                          season=video.season,
                                          episode=video.episode)
                if (len(partial_subs) > 0):
                    subtitles += partial_subs
                    continue

                # (3)
                logger.debug(
                    "Titulky.com: Finding subtitles by keyword only (3)")
                keyword = f"{video.series} S{video.season:02d}E{video.episode:02d}"
                partial_subs = self.query(language,
                                          video_names,
                                          'episode',
                                          keyword=keyword)
                subtitles += partial_subs
            elif isinstance(video, Movie):
                video_names = [video.title] + video.alternative_titles

                # (1)
                logger.debug("Titulky.com: Finding subtitles by IMDB ID (1)")
                if video.imdb_id:
                    partial_subs = self.query(language,
                                              video_names,
                                              'movie',
                                              imdb_id=video.imdb_id)
                    if (len(partial_subs) > 0):
                        subtitles += partial_subs
                        continue

                # (2)
                logger.debug("Titulky.com: Finding subtitles by keyword (2)")
                keyword = video.title
                partial_subs = self.query(language,
                                          video_names,
                                          'movie',
                                          keyword=keyword)
                subtitles += partial_subs

        return subtitles

    def download_subtitle(self, subtitle):
        res = self.session.get(subtitle.download_link,
                               headers={'Referer': subtitle.page_link},
                               timeout=self.timeout)

        try:
            res.raise_for_status()
        except:
            raise HTTPError(
                f"An error occured during the download request to {subtitle.download_link}"
            )

        archive_stream = io.BytesIO(res.content)
        archive = None
        if rarfile.is_rarfile(archive_stream):
            logger.debug("Titulky.com: Identified rar archive")
            archive = rarfile.RarFile(archive_stream)
            subtitle_content = self.get_subtitle_from_archive(subtitle, archive)
        elif zipfile.is_zipfile(archive_stream):
            logger.debug("Titulky.com: Identified zip archive")
            archive = zipfile.ZipFile(archive_stream)
            subtitle_content = self.get_subtitle_from_archive(subtitle, archive)
        else:
            subtitle_content = fix_line_ending(res.content)

        if not subtitle_content:
            logger.debug(
                "Titulky.com: No subtitle content found. The downloading limit has been most likely exceeded."
            )
            raise DownloadLimitExceeded(
                "Subtitles download limit has been exceeded")

        subtitle.content = subtitle_content


# Check if any element from source array is contained partially or exactly in any element from target array
# Returns on the first match
def _contains_element(_from=None, _in=None, exactly=False):
    source_array = _from
    target_array = _in

    for source in source_array:
        for target in target_array:
            if exactly:
                if sanitize(source) == sanitize(target):
                    return True
            else:
                if sanitize(source) in sanitize(target):
                    return True

    return False

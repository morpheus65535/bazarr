# -*- coding: utf-8 -*-
import io
import logging
import math
import re
import zipfile
from random import randint
from urllib.parse import urlparse, parse_qs, quote
from threading import Thread

import rarfile
from guessit import guessit
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError

from subliminal.cache import region as cache
from subliminal.exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded, Error, ProviderError
from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitle import fix_line_ending
from subliminal.video import Episode, Movie

from subliminal_patch.exceptions import ParseResponseError
from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.score import framerate_equal
from subliminal_patch.subtitle import Subtitle, guess_matches, sanitize

from dogpile.cache.api import NO_VALUE
from subzero.language import Language

from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

logger = logging.getLogger(__name__)

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
        season_episode_string = None
        if len(self.names) > 0:
            season_episode_string = re.findall(r'S(\d+)E(\d+)', self.names[0], re.IGNORECASE)

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
        # Subtitle's names (could be series/episode/movie name) present in the subtitle details page
        # Consists of the main name and alternative names, stripped of the S00E00 substring
        sub_names = self._remove_season_episode_string(self.names)

        if _type == 'episode':
            # EPISODE

            # match imdb_id of a series
            if video.series_imdb_id and video.series_imdb_id == self.imdb_id:
                matches.add('series')
                matches.add('series_imdb_id')

            # match season/episode
            if self.season and self.season == video.season:
                matches.add('season')
            if self.episode and self.episode == video.episode:
                matches.add('episode')

            # match series name
            if len(sub_names) > 0:
                series_names = [video.series] + video.alternative_series
                logger.debug(
                    f"Titulky.com: Finding exact match between subtitle's names {sub_names} and series names {series_names}"
                )
                if _contains_element(_from=series_names,
                                     _in=sub_names,
                                     exactly=True):
                    matches.add('series')

                # match episode title
                episode_titles = [video.title]
                logger.debug(
                    f"Titulky.com: Finding exact match between subtitle's names {sub_names} and episode titles {episode_titles}"
                )
                if _contains_element(_from=episode_titles,
                                     _in=sub_names,
                                     exactly=True):
                    matches.add('episode_title')

        elif _type == 'movie':
            # MOVIE

            # match imdb_id of a movie
            if video.imdb_id and video.imdb_id == self.imdb_id:
                matches.add('imdb_id')

            # match movie title
            video_titles = [video.title] + video.alternative_titles
            logger.debug(
                f"Titulky.com: Finding exact match between subtitle's names {sub_names} and video titles {video_titles}"
            )
            if _contains_element(_from=video_titles,
                                 _in=sub_names,
                                 exactly=True):
                matches.add('title')

        # MOVIE OR EPISODE

        # match year
        if video.year and video.year == self.year:
            matches.add('year')

        # match other properties based on release infos
        for release in self.releases:
            matches |= guess_matches(video, guessit(release, {"type": _type}))

        # If turned on in settings, then do not match if video FPS is not equal to subtitle FPS
        if self.skip_wrong_fps and video.fps and self.fps and not framerate_equal(video.fps, self.fps):
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
    video_types = (Episode, Movie)
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
        cached_user_agent = cache.get('titulky_user_agent')
        if cached_user_agent == NO_VALUE:
            new_user_agent = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]
            cache.set('titulky_user_agent', new_user_agent)
            self.session.headers['User-Agent'] = new_user_agent
        else:
            self.session.headers['User-Agent'] = cached_user_agent

        self.session.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        self.session.headers['Accept-Language'] = 'sk,cz,en;q=0.5'
        self.session.headers['Accept-Encoding'] = 'gzip, deflate'
        self.session.headers['DNT'] = '1'
        self.session.headers['Connection'] = 'keep-alive'
        self.session.headers['Upgrade-Insecure-Requests'] = '1'
        self.session.headers['Cache-Control'] = 'max-age=0'

        self.login()

    def terminate(self):
        self.session.close()

    def login(self, bypass_cache=False):
        # Reuse all cookies if found in cache and skip login.
        cached_cookiejar = cache.get('titulky_cookiejar')
        if not bypass_cache and cached_cookiejar != NO_VALUE:
            logger.info("Titulky.com: Reusing cached cookies.")
            self.session.cookies.update(cached_cookiejar)
            return True

        logger.info("Titulky.com: Logging in...")

        data = {'LoginName': self.username, 'LoginPassword': self.password}
        res = self.session.post(self.server_url,
                                data,
                                allow_redirects=False,
                                timeout=self.timeout,
                                headers={'Referer': self.server_url})

        location_qs = parse_qs(urlparse(res.headers['Location']).query)

        # If the response is a redirect and doesnt point to an error message page, then we are logged in
        if res.status_code == 302 and location_qs['msg_type'][0] == 'i':
            if 'omezené' in location_qs['msg'][0]:
                raise AuthenticationError("V.I.P. account is required for this provider to work!")
            else:
                logger.info("Titulky.com: Successfully logged in, caching cookies for future connections...")
                cache.set('titulky_cookiejar', self.session.cookies.copy())
                return True
        else:
            raise AuthenticationError("Login failed")

    def logout(self):
        logger.info("Titulky.com: Logging out")

        res = self.session.get(self.logout_url,
                               allow_redirects=False,
                               timeout=self.timeout,
                               headers={'Referer': self.server_url})

        location_qs = parse_qs(urlparse(res.headers['Location']).query)

        logger.info("Titulky.com: Clearing cache...")
        cache.delete('titulky_cookiejar')
        cache.delete('titulky_user_agent')

        # If the response is a redirect and doesnt point to an error message page, then we are logged out
        if res.status_code == 302 and location_qs['msg_type'][0] == 'i':
            return True
        else:
            raise AuthenticationError("Logout failed.")

    # GET request a page. This functions acts as a requests.session.get proxy handling expired cached cookies
    # and subsequent relogging and sending the original request again. If all went well, returns the response.
    def get_request(self, url, ref=server_url, allow_redirects=False, _recursion=0):
        # That's deep... recursion... Stop. We don't have infinite memmory. And don't want to
        # spam titulky's server either. So we have to just accept the defeat. Let it throw!
        if _recursion >= 5:
            logger.debug(
                f"Titulky.com: Got into a loop while trying to send a request after relogging.")
            raise AuthenticationError(
                "Got into a loop and couldn't get authenticated!")

        logger.debug(f"Titulky.com: Fetching url: {url}")

        res = self.session.get(
            url,
            timeout=self.timeout,
            allow_redirects=allow_redirects,
            headers={'Referer': quote(ref) if ref else None})  # URL encode ref if it has value

        # Check if we got redirected because login cookies expired.
        # Note: microoptimization - don't bother parsing qs for non 302 responses.
        if res.status_code == 302:
            location_qs = parse_qs(urlparse(res.headers['Location']).query)
            if location_qs['msg_type'][0] == 'e' and "Přihlašte se" in location_qs['msg'][0]:
                logger.debug(f"Titulky.com: Login cookies expired.")
                self.login(True)
                return self.get_request(url, ref=ref, _recursion=(_recursion + 1))

        return res

    def fetch_page(self, url, ref=server_url, allow_redirects=False):
        res = self.get_request(url, ref=ref, allow_redirects=allow_redirects)

        if res.status_code != 200:
            raise HTTPError(f"Fetch failed with status code {res.status_code}")
        if not res.text:
            raise ProviderError("No response returned from the provider")

        return res.text

    def build_url(self, params):
        result = f"{self.server_url}/?"

        for key, value in params.items():
            result += f'{key}={value}&'

        # Remove the last &
        result = result[:-1]

        # Remove spaces
        result = result.replace(' ', '+')

        return result

    # Makes sure the function communicates with the caller as expected. For threads, do not return data, but
    # pass them via threads_data object. For synchronous calls, treat it normally, without any changes.
    def capable_of_multithreading(func):
        def outer_func(*args, **kwargs):
            if 'threads_data' in kwargs and 'thread_id' in kwargs:
                if type(kwargs['threads_data']) is list and type(kwargs['thread_id']) is int:
                    try:
                        func_kwargs = kwargs.copy()
                        func_kwargs.pop('threads_data', None)
                        func_kwargs.pop('thread_id', None)

                        returnValue = func(*args, **func_kwargs)
                        kwargs['threads_data'][kwargs['thread_id']] = {
                            'return_value': returnValue,
                            'exception': None
                        }

                    except BaseException as e:
                        kwargs['threads_data'][kwargs['thread_id']] = {
                            'return_value': None,
                            'exception': e
                        }
                        raise e
            else:
                return func(*args, **kwargs)

        return outer_func

    # Parse details of an individual subtitle: imdb_id, series/movie names, release, language, uploader, fps and year
    @capable_of_multithreading
    def parse_details(self, partial_info, ref_url=None):
        html_src = self.fetch_page(partial_info['details_link'], ref=ref_url)
        details_page_soup = ParserBeautifulSoup(html_src,
                                                ['lxml', 'html.parser'])

        details_container = details_page_soup.find('div', class_='detail')
        if not details_container:
            # The subtitles could be removed and got redirected to a different page. Better treat this silently.
            logger.info("Titulky.com: Could not find details div container. Skipping.")
            return False

        # IMDB ID
        imdb_id = None
        imdb_tag = details_page_soup.find('a', attrs={'target': re.compile(r"imdb", re.IGNORECASE)})

        if imdb_tag:
            imdb_url = imdb_tag.get('href')
            imdb_id = re.findall(r'tt(\d+)', imdb_url)[0]

        if not imdb_id:
            logger.debug("Titulky.com: No IMDB ID supplied on details page.")

        # SERIES/MOVIE NAMES
        names = []
        try:
            main_name = details_container.find('h1', id='titulky').contents[0].strip()
            alt_name = details_container.find('h2').contents[1].strip()
            if main_name:
                names.append(main_name)
            else:
                logger.debug("Titulky.com: Could not find main series/movie name on details page.")
            if alt_name:
                names.append(alt_name)
        except IndexError:
            raise ParseResponseError("Index out of range! This should not ever happen, but it just did. Oops.")

        if len(names) == 0:
            logger.debug("Titulky.com: No names found on details page.")

        # RELEASE
        release = None
        release_tag = details_container.find('div', class_='releas')

        if not release_tag:
            raise ParseResponseError("Could not find release tag. Did the HTML source change?")

        release = release_tag.get_text(strip=True)

        if not release:
            logger.debug("Titulky.com: No release information supplied on details page.")

        # LANGUAGE
        language = None
        czech_flag = details_container.select('img[src*=\'flag-CZ\']')
        slovak_flag = details_container.select('img[src*=\'flag-SK\']')

        if czech_flag and not slovak_flag:
            language = Language('ces')
        elif slovak_flag and not czech_flag:
            language = Language('slk')

        if not language:
            logger.debug("Titulky.com: No language information supplied on details page.")

        # UPLOADER
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
            logger.debug("Titulky.com: No uploader name supplied on details page.")

        # FPS
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

        # YEAR
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

        info = {
            'releases': [release],
            'names': names,
            'language': language,
            'uploader': uploader,
            'fps': fps,
            'year': year,
            'imdb_id': imdb_id
        }

        info.update(partial_info)

        return info

    # Process a single row of subtitles from a query method
    @capable_of_multithreading
    def process_row(self,
                    row,
                    video_names,
                    ref_url):
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
            logger.info(
                f"Titulky.com: Skipping subtitle with names: {sub_names}, because there was no match with video names: {video_names}"
            )
            return None

        partial_info = {
            'names': sub_names,
            'id': sub_id,
            'approved': approved,
            'details_link': details_link,
            'download_link': download_link
        }
        details = self.parse_details(partial_info, ref_url)

        return details

    #########
    # FIXME: After switching from Multithreaded to singlethreaded option, the provider does not return
    #        any data and requires bazarr to restart in order to work again with this setting. However,
    #        switching back to multithreaded does NOT require bazarr to be restarded.
    ####
    # Execute a func for each array member and return results. Handles async/sync side of things
    def execute_foreach(self, array, func, args=[], kwargs={}):
        if not self.multithreading:
            logger.info("Titulky.com: processing in sequence")

            result_array = []
            for i, obj in enumerate(array):
                passing_args = [obj] + args
                return_value = func(*passing_args, **kwargs)

                if return_value:
                    result_array.append(return_value)
                else:
                    logger.debug(f"Titulky.com: No data returned, element number: {i}")

            return result_array
        else:
            logger.info(f"Titulky.com: processing in parelell, {self.max_threads} elements at a time.")
            array_length = len(array)

            threads = [None] * array_length
            threads_data = [None] * array_length

            # Process in parallel, self.max_threads at a time.
            cycles = math.ceil(array_length / self.max_threads)
            for i in range(cycles):
                # Batch number i
                starting_index = i * self.max_threads  # Inclusive
                ending_index = starting_index + self.max_threads  # Non-inclusive

                # Create threads for all elements in this batch
                for j in range(starting_index, ending_index):
                    # Check if j-th element exists
                    if j < array_length:
                        # Element number j
                        logger.debug(f"Titulky.com: Creating thread {j} (batch: {i})")
                        # Merge supplied kwargs with our dict
                        kwargs.update({
                            'thread_id': j,
                            'threads_data': threads_data
                        })
                        # Create a thread for element j and start it
                        threads[j] = Thread(
                            target=func,
                            args=[array[j]] + args,
                            kwargs=kwargs
                        )
                        threads[j].start()

                # Wait for all created threads to finish before moving to another batch of data
                for j in range(starting_index, ending_index):
                    # Check if j-th data exists
                    if j < array_length:
                        threads[j].join()

            result_array = []
            # Process the resulting data from all threads
            for i in range(len(threads_data)):
                thread_data = threads_data[i]

                # If the thread returned didn't communicate at all
                if not thread_data:
                    raise ProviderError(f"No communication from thread ID: {i}")

                # If an exception was raised in a thread, raise it again here
                if 'exception' in thread_data and thread_data['exception']:
                    logger.debug(f"Titulky.com: An error occured while processing in the thread ID {i}")
                    raise thread_data['exception']

                if 'return_value' in thread_data:
                    result_array.append(thread_data['return_value'])

            return result_array

    # There are multiple ways to find subs from this provider:
    # \\ Using self.query function: "Universal search" //
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
    # \\ Using self.browse function: "Episode search" //
    # 8. BROWSE subtitles by IMDB ID (only episodes)
    #   - Subtitles are here categorised by seasons and episodes
    #   - URL: https://premium.titulky.com/?action=serial&step=<SEASON>&id=<IMDB ID>
    #   - it seems that the url redirects to a page with their own internal ID, redirects should be allowed here

    # Special search only for episodes. Complements the query method of searching.
    def browse_episodes(self,
                        language,
                        imdb_id=None,
                        season=None,
                        episode=None):

        params = {
            'action': 'serial',
            'step': season,
            # Remove the "tt" prefix
            'id': imdb_id[2:]
        }
        browse_url = self.build_url(params)
        html_src = self.fetch_page(browse_url, allow_redirects=True)

        browse_page_soup = ParserBeautifulSoup(
            html_src, ['lxml', 'html.parser'])
        # Container element containing subtitle div rows, None if the series was not found or similar
        container = browse_page_soup.find('form', class_='cloudForm')

        # No container with subtitles
        if not container:
            logger.debug("Titulky.com: Could not find container element. No subtitles found.")
            return []

        # All rows: subtitle rows, episode number rows, useless rows... Gotta filter this out.
        all_rows = container.find_all('div', class_='row')

        # Filtering and parsing rows
        episodes_dict = {}
        last_ep_num = None
        for row in all_rows:
            # This element holds the episode number of following row(s) of subtitles
            # E.g.: 1., 2., 3., 4.
            episode_num = row.find('h5')
            # Link to the sub details
            details_anchor = row.find('a') if 'pbl1' in row['class'] or 'pbl0' in row['class'] else None

            if episode_num:
                # The row is a div with episode number as its text content
                try:
                    # Remove period at the end and parse the string into a number
                    number = int(episode_num.string.replace('.', ''))
                    last_ep_num = number
                except:
                    logger.debug("Titulky.com: An error during parsing episode number!")
                    raise ProviderError("Could not parse episode number!")
            elif details_anchor:
                # The row is a subtitles row. Contains link to details page
                if not last_ep_num:
                    logger.debug("Titulky.com: No previous episode number!")
                    raise ProviderError("Previous episode number missing, can't parse.")

                details_link = f"{self.server_url}{details_anchor.get('href')[1:]}"
                id_match = re.findall(r'id=(\d+)', details_link)
                sub_id = id_match[0] if len(id_match) > 0 else None
                download_link = f"{self.download_url}{sub_id}"
                # Approved subtitles have a pbl1 class for their row, others have a pbl0 class
                approved = True if 'pbl1' in row.get('class') else False

                # Parse language to filter out subtitles that are not in the desired language
                sub_language = None
                czech_flag = row.select('img[src*=\'flag-CZ\']')
                slovak_flag = row.select('img[src*=\'flag-SK\']')

                if czech_flag and not slovak_flag:
                    sub_language = Language('ces')
                elif slovak_flag and not czech_flag:
                    sub_language = Language('slk')
                else:
                    logger.debug("Titulky.com: Unknown language while parsing subtitles!")
                
                # If the language is not the desired one, skip this row
                if sub_language and sub_language != language:
                    continue

                result = {
                    'id': sub_id,
                    'approved': approved,
                    'details_link': details_link,
                    'download_link': download_link
                }

                # If this row contains the first subtitles to an episode number,
                # add an empty array into the episodes dict at its place.
                if not last_ep_num in episodes_dict:
                    episodes_dict[last_ep_num] = []

                episodes_dict[last_ep_num].append(result)

        # Rows parsed into episodes_dict, now lets read what we got.
        if not episode in episodes_dict:
            # well, we got nothing, that happens!
            logger.debug("Titulky.com: No subtitles found")
            return []

        # Lets parse more details about subtitles that we actually care about
        subtitle_details = self.execute_foreach(episodes_dict[episode], self.parse_details)

        # After parsing, create new instances of Subtitle class
        subtitles = []
        for sub_info in subtitle_details:
            subtitle_instance = self.subtitle_class(
                sub_info['id'],
                imdb_id,
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
                asked_for_episode=True)
            subtitles.append(subtitle_instance)

        return subtitles

    # Universal search for subtitles. Searches both episodes and movies.
    def query(self,
              language,
              video_names,
              type,
              keyword=None,
              year=None,
              season=None,
              episode=None,
              imdb_id=None):
        # Build the search URL
        params = {
            'action': 'search',
            # Requires subtitle names to match full search keyword
            'fsf': 1
        }

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
            logger.debug(f"Titulky.com: Searching only for approved subtitles")
            params['ASchvalene'] = '1'
        else:
            params['ASchvalene'] = ''

        search_url = self.build_url(params)

        # Search results page parsing
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
            raise ParseResponseError("Could not find table body. Did the HTML source change?")

        # Loop over all subtitles on the first page and put them in a list
        subtitles = []
        rows = table_body.find_all('tr')
        for sub_info in self.execute_foreach(rows, self.process_row, args=[video_names, search_url]):
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

        # Clean up
        search_page_soup.decompose()
        search_page_soup = None

        logger.debug(f"Titulky.com: Found subtitles: {subtitles}")

        return subtitles

    def list_subtitles(self, video, languages):
        subtitles = []

        # Possible paths:
        # (0) Special for episodes: Browse TV Series page and search for subtitles
        # (1) Search by IMDB ID [and season/episode for tv series]
        # (2) Search by keyword: video (title|series) [and season/episode for tv series]
        # (3) Search by keyword: video series + S00E00 (tv series only)

        for language in languages:
            if isinstance(video, Episode):
                video_names = [video.series, video.title] + video.alternative_series

                # (0)
                if video.series_imdb_id:
                    logger.info("Titulky.com: Finding subtitles by browsing TV Series page (0)")
                    partial_subs = self.browse_episodes(language,
                                                        imdb_id=video.series_imdb_id,
                                                        season=video.season,
                                                        episode=video.episode)
                    if (len(partial_subs) > 0):
                        subtitles += partial_subs
                        continue

                # (1)
                if video.series_imdb_id:
                    logger.info("Titulky.com: Finding subtitles by IMDB ID, Season and Episode (1)")
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
                logger.info("Titulky.com: Finding subtitles by keyword, Season and Episode (2)")
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
                logger.info("Titulky.com: Finding subtitles by keyword only (3)")
                keyword = f"{video.series} S{video.season:02d}E{video.episode:02d}"
                partial_subs = self.query(language,
                                          video_names,
                                          'episode',
                                          keyword=keyword)
                subtitles += partial_subs
            elif isinstance(video, Movie):
                video_names = [video.title] + video.alternative_titles

                # (1)
                if video.imdb_id:
                    logger.info("Titulky.com: Finding subtitles by IMDB ID (1)")
                    partial_subs = self.query(language,
                                              video_names,
                                              'movie',
                                              imdb_id=video.imdb_id)
                    if (len(partial_subs) > 0):
                        subtitles += partial_subs
                        continue

                # (2)
                logger.info("Titulky.com: Finding subtitles by keyword (2)")
                keyword = video.title
                partial_subs = self.query(language,
                                          video_names,
                                          'movie',
                                          keyword=keyword)
                subtitles += partial_subs

        return subtitles

    def download_subtitle(self, subtitle):
        res = self.get_request(subtitle.download_link, ref=subtitle.page_link)

        try:
            res.raise_for_status()
        except:
            raise HTTPError(f"An error occured during the download request to {subtitle.download_link}")

        archive_stream = io.BytesIO(res.content)
        archive = None
        if rarfile.is_rarfile(archive_stream):
            logger.debug("Titulky.com: Identified rar archive")
            archive = rarfile.RarFile(archive_stream)
            subtitle_content = self.get_subtitle_from_archive(
                subtitle, archive)
        elif zipfile.is_zipfile(archive_stream):
            logger.debug("Titulky.com: Identified zip archive")
            archive = zipfile.ZipFile(archive_stream)
            subtitle_content = self.get_subtitle_from_archive(
                subtitle, archive)
        else:
            subtitle_content = fix_line_ending(res.content)

        if not subtitle_content:
            logger.debug("Titulky.com: No subtitle content found. The downloading limit has been most likely exceeded.")
            raise DownloadLimitExceeded("Subtitles download limit has been exceeded")

        subtitle.content = subtitle_content

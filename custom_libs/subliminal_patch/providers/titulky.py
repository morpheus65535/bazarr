# -*- coding: utf-8 -*-
import enum
import io
import logging
import re
import zipfile
from random import randint
from urllib.parse import urljoin, urlparse, parse_qs, quote

import rarfile
from guessit import guessit
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError

from subliminal.cache import region as cache
from subliminal.exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded, ProviderError
from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitle import fix_line_ending
from subliminal.video import Episode, Movie

from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin

from subliminal_patch.subtitle import Subtitle, guess_matches

from subliminal_patch.score import framerate_equal

from dogpile.cache.api import NO_VALUE
from subzero.language import Language

from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

logger = logging.getLogger(__name__)


class SubtitlesType(enum.Enum):
    EPISODE = enum.auto()
    MOVIE = enum.auto()

class TitulkySubtitle(Subtitle):
    provider_name = 'titulky'

    hash_verifiable = False
    hearing_impaired_verifiable = False

    def __init__(self,
                 sub_id,
                 imdb_id,
                 language,
                 season,
                 episode,
                 release_info,
                 uploader,
                 approved,
                 page_link,
                 download_link,
                 fps,
                 skip_wrong_fps,
                 asked_for_episode=None):
        super().__init__(language, page_link=page_link)

        self.sub_id = sub_id
        self.imdb_id = imdb_id
        self.season = season
        self.episode = episode
        self.releases = [release_info]
        self.release_info = release_info
        self.approved = approved
        self.page_link = page_link
        self.uploader = uploader
        self.download_link = download_link
        self.fps = fps if skip_wrong_fps else None # This attribute should be ignored if skip_wrong_fps is false
        self.skip_wrong_fps = skip_wrong_fps
        self.asked_for_episode = asked_for_episode
        self.matches = None

    @property
    def id(self):
        return self.sub_id

    def get_matches(self, video):
        matches = set()
        media_type = 'movie' if isinstance(video, Movie) else 'episode'

        if self.skip_wrong_fps and video.fps and self.fps and not framerate_equal(video.fps, self.fps):
            logger.debug(f"Titulky.com: Wrong FPS (expected: {video.fps}, got: {self.fps}, lowering score massively)")
            return set()

        if media_type == 'episode':
            # match imdb_id of a series
            if video.series_imdb_id and video.series_imdb_id == self.imdb_id:
                matches |= {'series_imdb_id', 'series', 'year'}

            # match season/episode
            if self.season and self.season == video.season:
                matches.add('season')
            if self.episode and self.episode == video.episode:
                matches.add('episode')

        elif media_type == 'movie':
            # match imdb_id of a movie
            if video.imdb_id and video.imdb_id == self.imdb_id:
                matches |= {'imdb_id', 'title', 'year'}

        matches |= guess_matches(video, guessit(self.release_info, {"type": media_type}))

        self.matches = matches

        return matches


class TitulkyProvider(Provider, ProviderSubtitleArchiveMixin):
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
                 approved_only=None,
                 skip_wrong_fps=None):
        if not all([username, password]):
            raise ConfigurationError("Username and password must be specified!")
        if type(approved_only) is not bool:
            raise ConfigurationError(f"Approved_only {approved_only} must be a boolean!")
        if type(skip_wrong_fps) is not bool:
            raise ConfigurationError(f"Skip_wrong_fps {skip_wrong_fps} must be a boolean!")

        self.username = username
        self.password = password
        self.approved_only = approved_only
        self.skip_wrong_fps = skip_wrong_fps

        self.session = None

    def initialize(self):
        self.session = Session()

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

        logger.debug("Titulky.com: Logging in...")

        data = {'LoginName': self.username, 'LoginPassword': self.password}
        res = self.session.post(self.server_url,
                                data,
                                allow_redirects=False,
                                timeout=self.timeout,
                                headers={'Referer': self.server_url})

        location_qs = parse_qs(urlparse(res.headers['Location']).query)

        # If the response is a redirect and doesnt point to an error message page, then we are logged in
        if res.status_code == 302 and location_qs['msg_type'][0].lower() == 'i':
            if 'omezené' in location_qs['msg'][0].lower():
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
        if res.is_redirect and location_qs['msg_type'][0] == 'i':
            return True
        else:
            raise AuthenticationError("Logout failed.")

    # GET request a page. This functions acts as a requests.session.get proxy handling expired cached cookies
    # and subsequent relogging and sending the original request again. If all went well, returns the response.
    # Additionally handle allow_redirects by ourselves to follow redirects UNLESS they are redirecting to an
    # error page. In such case we would like to know what has happend and act accordingly.
    def get_request(self, url, ref=server_url, allow_redirects=False, _recursion=0):
        # That's deep... recursion... Stop. We don't have infinite memmory. And don't want to
        # spam titulky's server either. So we have to just accept the defeat. Let it throw!
        if _recursion >= 10:
            raise AuthenticationError("Got into a redirect loop! Oops.")

        logger.debug(f"Titulky.com: Fetching url: {url}")

        res = self.session.get(
            url,
            timeout=self.timeout,
            allow_redirects=False,
            headers={'Referer': quote(ref) if ref else None})  # URL encode ref if it has value

        if res.is_redirect:
            # Dont bother doing anything if we do not want to redirect. Just return the original response..
            if allow_redirects is False:
                return res
            
            location_qs = parse_qs(urlparse(res.headers['Location']).query)

            # If the redirect url does not contain an error message, we follow the redirect right away
            if 'msg_type' not in location_qs or ('msg_type' in location_qs and (location_qs['msg_type'][0]).lower() != 'e'):
                return self.get_request(urljoin(res.headers['Origin'] or self.server_url, res.headers['Location']), ref=url, allow_redirects=True, _recursion=(_recursion + 1))
            
            # We got redirected to a page with an error message:
            error_message = location_qs['msg'][0].lower()

            # Check if we got redirected because login cookies expired and try to relogin
            if "přihlašte" in error_message:
                logger.info(f"Titulky.com: Login cookies expired.")
                self.login(True)
                return self.get_request(url, ref=ref, allow_redirects=True, _recursion=(_recursion + 1))

            # Check if we got redirected because our VIP expired
            if "omezené" in error_message:
                raise AuthenticationError("V.I.P. status expired.");

            # TODO: We don't know why we got redirected to an error page. 
            # What should we do? I am not aware if there is a use case where we want to return such response anway.
            raise ProviderError(f"Got redirected from {url} to an error page with message: \"{location_qs['msg'][0]}\"");
        
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

    # Retrieves the fps value given subtitles id from the details page and caches it.
    def retrieve_subtitles_fps(self, subtitles_id):
        cache_key = f"titulky_subs-{subtitles_id}_fps"
        cached_fps_value = cache.get(cache_key)

        if(cached_fps_value != NO_VALUE):
            logger.debug(f"Titulky.com: Reusing cached fps value {cached_fps_value} for subtitles with id {subtitles_id}")
            return cached_fps_value

        params = {
            'action': 'detail',
            'id': subtitles_id
        }
        browse_url = self.build_url(params)
        html_src = self.fetch_page(browse_url, allow_redirects=True)
        browse_page_soup = ParserBeautifulSoup(html_src, ['lxml', 'html.parser'])

        fps_container = browse_page_soup.select_one("div.ulozil:has(> img[src='img/ico/Movieroll.png'])")
        if(fps_container is None):
            logger.debug("Titulky.com: Could not manage to find the FPS container in the details page")
            cache.set(cache_key, None)
            return None

        fps_text_components = fps_container.get_text(strip=True).split()
        # Check if the container contains valid fps data
        if(len(fps_text_components) < 2 or fps_text_components[1].lower() != "fps"):
            logger.debug(f"Titulky.com: Could not determine FPS value for subtitles with id {subtitles_id}")
            cache.set(cache_key, None)
            return None

        fps_text = fps_text_components[0].replace(",", ".") # Fix decimal comma to decimal point
        try:
            fps = float(fps_text)
            logger.debug(f"Titulky.com: Retrieved FPS value {fps} from details page for subtitles with id {subtitles_id}")
            cache.set(cache_key, fps)
            return fps
        except:
            logger.debug(f"Titulky.com: There was an error parsing FPS value string for subtitles with id {subtitles_id}")
            cache.set(cache_key, None)
            return None


    """ 
        There are multiple ways to find substitles on Titulky.com, however we are 
        going to utilize a page that lists all available subtitles for all episodes in a season
        
        To my surprise, the server in this case treats movies as a tv series with a "0" season and "0" episode
        
        BROWSE subtitles by IMDB ID:
           - Subtitles are here categorised by seasons and episodes
           - URL: https://premium.titulky.com/?action=serial&step=<SEASON>&id=<IMDB ID>
           - it seems that the url redirects to a page with their own internal ID, redirects should be allowed here
    """
    def query(self, languages,
                    media_type,
                    imdb_id,
                    season=0,
                    episode=0):

        params = {
            'action': 'serial',
            # If browsing subtitles for a movie, then set the step parameter to 0
            'step': season,
            # Remove the "tt" prefix
            'id': imdb_id[2:]
        }
        browse_url = self.build_url(params)
        html_src = self.fetch_page(browse_url, allow_redirects=True)

        browse_page_soup = ParserBeautifulSoup(html_src, ['lxml', 'html.parser'])
        # Container element containing subtitle div rows, None if the series was not found or similar
        container = browse_page_soup.find('form', class_='cloudForm')

        # No container with subtitles
        if not container:
            logger.info("Titulky.com: Could not find container element. No subtitles found.")
            return []

        # All rows: subtitle rows, episode number rows, useless rows... Gotta filter this out.
        all_rows = container.find_all('div', class_='row')

        # Filtering and parsing rows
        episodes_dict = {}
        last_ep_num = None
        for row in all_rows:
            # This element holds the episode number of following row(s) of subtitles
            # E.g.: 1., 2., 3., 4.
            number_container = row.find('h5')
            # Link to the sub details
            anchor = row.find('a') if 'pbl1' in row['class'] or 'pbl0' in row['class'] else None

            if number_container:
                # The text content of this container is the episode number
                try:
                    # Remove period at the end and parse the string into a number
                    number_str = number_container.text.strip().rstrip('.')
                    number = int(number_str) if number_str else 0
                    last_ep_num = number
                except:
                    raise ProviderError("Could not parse episode number!")
            elif anchor:
                # The container contains link to details page
                if last_ep_num is None:
                    raise ProviderError("Previous episode number missing, can't parse.")
                
                release_info = anchor.get_text(strip=True)
                if release_info == '???':
                    release_info = ''
                
                details_link = f"{self.server_url}{anchor.get('href')[1:]}"
                
                id_match = re.findall(r'id=(\d+)', details_link)
                sub_id = id_match[0] if len(id_match) > 0 else None
                
                download_link = f"{self.download_url}{sub_id}"
                
                # Approved subtitles have a pbl1 class for their row, others have a pbl0 class
                approved = True if 'pbl1' in row.get('class') else False

                uploader = row.contents[5].get_text(strip=True)
                
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
                    continue
                
                # If the subtitles language is not requested
                if sub_language not in languages:
                    logger.debug("Titulky.com: Language not in desired languages, skipping...")
                    continue
                
                # Skip unapproved subtitles if turned on in settings
                if self.approved_only and not approved:
                    logger.debug("Titulky.com: Approved only, skipping...")
                    continue

                result = {
                    'id': sub_id,
                    'release_info': release_info,
                    'approved': approved,
                    'language': sub_language,
                    'uploader': uploader,
                    'details_link': details_link,
                    'download_link': download_link,
                    'fps': self.retrieve_subtitles_fps(sub_id) if self.skip_wrong_fps else None,
                }

                # If this row contains the first subtitles to an episode number,
                # add an empty array into the episodes dict at its place.
                if not last_ep_num in episodes_dict:
                    episodes_dict[last_ep_num] = []

                episodes_dict[last_ep_num].append(result)
        
        # Clean up
        browse_page_soup.decompose()
        browse_page_soup = None
        
        # Rows parsed into episodes_dict, now lets read what we got.
        if not episode in episodes_dict:
            # well, we got nothing, that happens!
            logger.info("Titulky.com: No subtitles found")
            return []

        sub_infos = episodes_dict[episode]

        # After parsing, create new instances of Subtitle class
        subtitles = []
        for sub_info in sub_infos:
            subtitle_instance = self.subtitle_class(
                sub_info['id'],
                imdb_id,
                sub_info['language'],
                season if media_type is SubtitlesType.EPISODE else None,
                episode if media_type is SubtitlesType.EPISODE else None,
                sub_info['release_info'],
                sub_info['uploader'],
                sub_info['approved'],
                sub_info['details_link'],
                sub_info['download_link'],
                sub_info['fps'],
                self.skip_wrong_fps,
                asked_for_episode=(media_type is SubtitlesType.EPISODE),
            )
            subtitles.append(subtitle_instance)

        return subtitles

    def list_subtitles(self, video, languages):
        subtitles = []

        if isinstance(video, Episode):
            if video.series_imdb_id:
                logger.info("Titulky.com: Searching subtitles for a TV series episode")
                subtitles = self.query(languages, SubtitlesType.EPISODE,
                                                    imdb_id=video.series_imdb_id,
                                                    season=video.season,
                                                    episode=video.episode)
            else:
                logger.info(f"Titulky.com: Skipping {video}! No IMDB ID found.")
        elif isinstance(video, Movie):
            if video.imdb_id:
                logger.info("Titulky.com: Searching subtitles for a movie")
                subtitles = self.query(languages, SubtitlesType.MOVIE, imdb_id=video.imdb_id)
            else:
                logger.info(f"Titulky.com: Skipping {video}! No IMDB ID found.")

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
            subtitle_content = self.get_subtitle_from_archive(subtitle, archive)
        elif zipfile.is_zipfile(archive_stream):
            logger.debug("Titulky.com: Identified zip archive")
            archive = zipfile.ZipFile(archive_stream)
            subtitle_content = self.get_subtitle_from_archive(subtitle, archive)
        else:
            subtitle_content = fix_line_ending(res.content)

        if archive and len(archive.infolist()) > 1 and not subtitle_content:
            logger.info(f"Titulky.com: Couldn't find a proper subtitle file in the downloaded archive.")
        elif archive and len(archive.infolist()) == 1 and not subtitle_content:
            raise DownloadLimitExceeded("Subtitles download limit has been exceeded")
        elif not subtitle_content:
            raise ProviderError("No subtitles provided from titulky")

        subtitle.content = subtitle_content

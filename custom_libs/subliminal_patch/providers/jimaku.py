from __future__ import absolute_import

import io
import logging
import re
import time
import rarfile
import zipfile
import requests

from requests import Session
from subliminal import __short_version__
from subliminal.exceptions import ConfigurationError, AuthenticationError
from subliminal.utils import sanitize
from subliminal.video import Episode, Movie
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.exceptions import APIThrottled
from subliminal_patch.providers.utils import get_subtitle_from_archive
from urllib.parse import urlencode, urljoin
from guessit import guessit
from functools import cache
from subzero.language import Language, FULL_LANGUAGE_LIST

logger = logging.getLogger(__name__)

class JimakuSubtitle(Subtitle):
    '''Jimaku Subtitle.'''
    provider_name = 'jimaku'
    
    hash_verifiable = False

    def __init__(self, language, video, subtitle_url, subtitle_filename):
        super(JimakuSubtitle, self).__init__(language, page_link=subtitle_url)
        
        self.video = video
        self.subtitle_url = subtitle_url
        self.subtitle_filename = subtitle_filename
        self.release_info = subtitle_filename
        
    @property
    def id(self):
        return self.subtitle_url

    def get_matches(self, video):
        matches = set()
        
        # Episode/Movie specific matches
        if isinstance(video, Episode):
            if sanitize(video.series) and sanitize(self.video.series) in (
                    sanitize(name) for name in [video.series] + video.alternative_series):
                matches.add('series')
            
            if video.season and self.video.season is None or video.season and video.season == self.video.season:
                matches.add('season')
        elif isinstance(video, Movie):
            if sanitize(video.title) and sanitize(self.video.title) in (
                    sanitize(name) for name in [video.title] + video.alternative_titles):
                matches.add('title')

        # General matches
        if video.year and video.year == self.video.year:
            matches.add('year')

        video_type = 'movie' if isinstance(video, Movie) else 'episode'
        matches.add(video_type)
        
        guess = guessit(self.subtitle_filename, {'type': video_type})
        logger.debug(f"Guessit: {guess}")
        for g in guess:
            if g[0] == "release_group" or "source":
                if video.release_group == g[1]:
                    matches.add('release_group')
                    break
                
        # Prioritize .srt by misusing the audio_codec match
        if self.subtitle_filename.endswith(".srt"):
            matches.add('audio_codec')

        return matches

class JimakuProvider(Provider):
    '''Jimaku Provider.'''
    video_types = (Episode, Movie)
    
    api_url = 'https://jimaku.cc/api'
    api_ratelimit_max_delay_seconds = 5
    api_ratelimit_backoff_limit = 3
    
    corrupted_file_size_threshold = 500
    
    languages = {Language.fromietf("ja")}

    def __init__(self, enable_name_search_fallback, enable_archives, enable_ai_subs, api_key):
        if api_key:
            self.api_key = api_key
        else:
            raise ConfigurationError('Missing api_key.')

        self.enable_name_search_fallback = enable_name_search_fallback
        self.enable_archives = enable_archives
        self.enable_ai_subs = enable_ai_subs
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/%s' % __short_version__
        self.session.headers['Content-Type'] = 'application/json'
        self.session.headers['Authorization'] = self.api_key

    def terminate(self):
        self.session.close()

    def _query(self, video):
        if isinstance(video, Movie):
            media_name = video.title.lower()
        elif isinstance(video, Episode):
            media_name = video.series.lower()
            
            # With entries that have a season larger than 1, Jimaku appends the corresponding season number to the name.
            # We'll reassemble media_name here to account for cases where we can only search by name alone.
            season_addendum = str(video.season) if video.season > 1 else None
            media_name = f"{media_name} {season_addendum}" if season_addendum else media_name

        # Search for entry
        searching_for_entry_attempts = 0
        additional_url_params = {}
        while searching_for_entry_attempts < 2:
            searching_for_entry_attempts += 1
            url = self._assemble_jimaku_search_url(video, media_name, additional_url_params)
            if not url:
                logger.error(f"Skipping '{media_name}': Got no AniList ID and fuzzy matching using name is disabled.")
                return None
            
            searching_for_entry = "query" in url
            data = self._do_jimaku_request(url)
            if not data:
                if searching_for_entry and searching_for_entry_attempts < 2:
                    logger.info("Maybe this is live action media? Will retry search without anime parameter...")
                    additional_url_params = {'anime': "false"}
                else:
                    return None
            else:
                break

        # We only go for the first entry
        entry = data[0]
        
        entry_id = entry.get('id')
        anilist_id = entry.get('anilist_id', None)
        entry_name = entry.get('name')
        
        logger.info(f"Matched entry: ID: '{entry_id}', anilist_id: '{anilist_id}', name: '{entry_name}', english_name: '{entry.get('english_name')}'")
        if entry.get("flags").get("unverified"):
            logger.warning(f"This entry '{entry_id}' is unverified, subtitles might be incomplete or have quality issues!")    
        
        # Get a list of subtitles for entry
        episode_number = video.episode if "episode" in dir(video) else None
        url_params = {'episode': episode_number} if isinstance(video, Episode) else {}
        only_look_for_archives = False
        
        retry_count = 0
        while retry_count <= 1:
            retry_count += 1

            url = f"entries/{entry_id}/files"
            data = self._do_jimaku_request(url, url_params)
            
            if not data:
                if isinstance(video, Episode) and retry_count <= 1:
                    # Edge case: When dealing with a cour, episodes could be uploaded with their episode numbers having an offset applied
                    # Vice versa, users may have media files with absolute episode numbering, but the subs on Jimaku follow the Season/Episode format
                    
                    offset_value = 0
                    if video.series_anidb_season_episode_offset:
                        offset_value = video.series_anidb_season_episode_offset

                    has_offset = offset_value > 0
                    if has_offset:
                        reverse_offset = episode_number > offset_value
                        if reverse_offset:
                            adjusted_ep_num = episode_number - offset_value
                        else:
                            adjusted_ep_num = episode_number + offset_value
                            
                        logger.warning(f"Found no subtitles for episode number {episode_number}, but will retry with offset-adjusted episode number {adjusted_ep_num} (reversed: {reverse_offset})")
                        url_params = {'episode': adjusted_ep_num}
                    else:
                        # The entry might only have archives uploaded
                        logger.warning(f"Found no subtitles for episode number {episode_number}, but will retry without 'episode' parameter.")
                        url_params = {}
                        only_look_for_archives = True
                else:
                    return None
            else:
                break
        
        # Filter subtitles
        list_of_subtitles = []

        archive_formats_blacklist = (".7z",) # Unhandled formats; This list will always match
        additional_archive_formats = (".zip", ".rar")
        if not self.enable_archives and not only_look_for_archives:
            # Handle shows that only have archives uploaded
            filter = [item for item in data if not item['name'].endswith(additional_archive_formats)]
            if len(filter) == 0:
                logger.warning("Archives are disabled, but only archived subtitles have been returned. Will therefore download those anyway.")
            else:
                archive_formats_blacklist += additional_archive_formats
        elif only_look_for_archives:
            data = [item for item in data if item['name'].endswith(additional_archive_formats)]
            logger.warning(f"Will only match archives: {data}")

        for item in data:
            subtitle_filename = item.get('name')
            subtitle_url = item.get('url')

            if not self.enable_ai_subs:
                if re.match(r'(\(|\[).*(whisper|whisperai).*(\)|\])', subtitle_filename.lower()):
                    logger.warning(f"Skipping subtitle '{subtitle_filename}' as it's suspected of being AI generated.")
                    continue
            
            sub_languages = self._try_determine_subtitle_languages(subtitle_filename)
            if len(sub_languages) > 1:
                logger.warning(f"Skipping subtitle '{subtitle_filename}' as it's suspected of containing multiple languages.")
                continue
            
            # Check if file is obviously corrupt. If no size is returned, assume OK
            subtitle_filesize = item.get('size', self.corrupted_file_size_threshold)
            if subtitle_filesize < self.corrupted_file_size_threshold:
                logger.warning(f"Skipping possibly corrupt file '{subtitle_filename}': Filesize is just {subtitle_filesize} bytes.")
                continue
            
            if not subtitle_filename.endswith(archive_formats_blacklist):
                lang = sub_languages[0] if len(sub_languages) > 1 else Language("jpn")
                list_of_subtitles.append(JimakuSubtitle(lang, video, subtitle_url, subtitle_filename))
            else:
                logger.debug(f"> Skipping subtitle of name '{subtitle_filename}' due to archive blacklist. (enable_archives: {self.enable_archives})")
        
        return list_of_subtitles

    def list_subtitles(self, video, languages=None):
        subtitles = self._query(video)
        if not subtitles:
            return []
        
        return [s for s in subtitles]

    def download_subtitle(self, subtitle: JimakuSubtitle):
        target_url = subtitle.subtitle_url
        response = self.session.get(target_url, timeout=10)
        response.raise_for_status()
        
        archive = self._is_archive(response.content)
        if archive:
            subtitle.content = get_subtitle_from_archive(archive, subtitle.video.episode)
        elif not archive and subtitle.subtitle_url.endswith(('.zip', '.rar')):
            logger.warning("Archive seems not to be an archive! File possibly corrupt? Skipping.")
            return None
        else:
            subtitle.content = response.content
    
    @staticmethod
    def _is_archive(archive: bytes):
        archive_stream = io.BytesIO(archive)
        
        if rarfile.is_rarfile(archive_stream):
            logger.debug("Identified rar archive")
            return rarfile.RarFile(archive_stream)
        elif zipfile.is_zipfile(archive_stream):
            logger.debug("Identified zip archive")
            return zipfile.ZipFile(archive_stream)
        else:
            logger.debug("Doesn't seem like an archive")
            return None
    
    #@cache
    def _do_jimaku_request(self, url_path, url_params={}):
        url = urljoin(f"{self.api_url}/{url_path}", '?' + urlencode(url_params))
        logger.debug(f"get_jimaku_response: url, params: {url}, {url_params}")
        
        retry_count = 0
        while retry_count < self.api_ratelimit_backoff_limit:
            retry_count += 1
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 429:
                api_reset_time = float(response.headers.get("x-ratelimit-reset-after", 5))
                reset_time = self.api_ratelimit_max_delay_seconds if api_reset_time > self.api_ratelimit_max_delay_seconds else api_reset_time
                
                logger.warning(f"Jimaku ratelimit hit, waiting for '{reset_time}' seconds ({retry_count}/{self.api_ratelimit_backoff_limit} tries)")
                time.sleep(reset_time)
                continue
            elif response.status_code == 401:
                raise AuthenticationError("Unauthorized. API key possibly invalid")
            else:
                response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Length of response on {url}: {len(data)}")
            if len(data) == 0:
                logger.error(f"Jimaku returned no items for our our query: {url}")                
                return None
            elif 'error' in data:
                logger.error(f"Jimaku returned an error for our query.\nMessage: '{data.get('error')}', Code: '{data.get('code')}'")
                return None
            else:
                return data

        raise APIThrottled(f"Jimaku ratelimit max backoff limit of {self.api_ratelimit_backoff_limit} reached, aborting.")
    
    @staticmethod
    @cache
    def _webrequest_with_cache(url, headers=None):
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        try:
            return response.json()
        except:
            return response.content
        
    @staticmethod
    def _try_determine_subtitle_languages(filename):
        # This is more like a guess and not a 100% fool-proof way of detecting multi-lang subs:
        # It assumes that language codes, if present, are in the last metadata group of the subs filename.
        # If such codes are not present, or we failed to match any at all, then we'll just assume that the sub is purely Japanese.
        default_language = Language("jpn")
        
        dot_delimit = filename.split(".")
        bracket_delimit = re.split(r'[\[\]\(\)]+', filename)

        candidate_list = list()
        if len(dot_delimit) > 2:
            candidate_list = dot_delimit[-2]
        elif len(bracket_delimit) > 2:
            candidate_list = bracket_delimit[-2]
        
        candidates = [] if len(candidate_list) == 0 else re.split(r'[,\-\+\& ]+', candidate_list)
        
        # Discard match group if any candidate...
        # ...contains any numbers, as the group is likely encoding information
        if any(re.compile(r'\d').search(string) for string in candidates):
            return [default_language]
        # ...is >= 5 chars long, as the group is likely other unrelated metadata
        if any(len(string) >= 5 for string in candidates):
            return [default_language]
        
        languages = list()
        for candidate in candidates:
            candidate = candidate.lower()
            if candidate in ["ass", "srt"]:
                continue
            
            # Sometimes, languages are hidden in 4 character blocks, i.e. "JPSC"
            if len(candidate) == 4:
                for addendum in [candidate[:2], candidate[2:]]:
                    candidates.append(addendum)
                continue
            
            # Sometimes, language codes can have additional info such as 'cc' or 'sdh'. For example: "ja[cc]"
            if len(dot_delimit) > 2 and any(c in candidate for c in '[]()'):
                candidate = re.split(r'[\[\]\(\)]+', candidate)[0]

            try:
                language_squash = {
                    "jp": "ja",
                    "jap": "ja",
                    "chs": "zho",
                    "cht": "zho",
                    "zhi": "zho",
                    "cn": "zho"
                }
                
                candidate = language_squash[candidate] if candidate in language_squash else candidate
                if len(candidate) > 2:
                    language = Language(candidate)
                else:
                    language = Language.fromietf(candidate)
                    
                if not any(l.alpha3 == language.alpha3 for l in languages):
                    languages.append(language)
            except:
                if candidate in FULL_LANGUAGE_LIST:
                    # Create a dummy for the unknown language
                    languages.append(Language("zul"))
        
        if len(languages) > 1:
            # Sometimes a metadata group that actually contains info about codecs gets processed as valid languages.
            # To prevent false positives, we'll check if Japanese language codes are in the processed languages list.
            # If not, then it's likely that we didn't actually match language codes -> Assume Japanese only subtitle.
            contains_jpn = any([l for l in languages if l.alpha3 == "jpn"])
            
            return languages if contains_jpn else [Language("jpn")]
        else:
            return [default_language]
    
    def _assemble_jimaku_search_url(self, video, media_name, additional_params={}):
        """
        Return a search URL for the Jimaku API.
        """
                       
        endpoint = "entries/search"
        anilist_id = video.anilist_id
        
        params = {}
        if anilist_id:
            params = {'anilist_id': anilist_id}
        else:
            if self.enable_name_search_fallback or isinstance(video, Movie):
                params = {'query': media_name}
            else:
                return None
            
        if additional_params:
            params.update(additional_params)
        
        logger.info(f"Will search for entry based on params: {params}")
        return urljoin(endpoint, '?' + urlencode(params))
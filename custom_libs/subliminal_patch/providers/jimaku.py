from __future__ import absolute_import

from datetime import timedelta
import logging
import os
import re
import time

from requests import Session
from subliminal import region, __short_version__
from subliminal.cache import REFINER_EXPIRATION_TIME
from subliminal.exceptions import ConfigurationError, AuthenticationError, ServiceUnavailable
from subliminal.utils import sanitize
from subliminal.video import Episode, Movie
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.exceptions import APIThrottled
from subliminal_patch.providers.utils import get_subtitle_from_archive, get_archive_from_bytes
from urllib.parse import urlencode, urljoin
from guessit import guessit
from subzero.language import Language, FULL_LANGUAGE_LIST

logger = logging.getLogger(__name__)

# Unhandled formats, such files will always get filtered out
unhandled_archive_formats = (".7z",)
accepted_archive_formats = (".zip", ".rar")

class JimakuSubtitle(Subtitle):
    '''Jimaku Subtitle.'''
    provider_name = 'jimaku'
    
    hash_verifiable = False

    def __init__(self, language, video, download_url, filename):
        super(JimakuSubtitle, self).__init__(language, page_link=download_url)
        
        self.video = video
        self.download_url = download_url
        self.filename = filename
        self.release_info = filename
        self.is_archive = filename.endswith(accepted_archive_formats)
        self.matches = set()
        
    @property
    def id(self):
        return self.download_url

    def get_matches(self, video):
        # Episode/Movie specific matches
        if isinstance(video, Episode):
            if sanitize(video.series) and sanitize(self.video.series) in (
                    sanitize(name) for name in [video.series] + video.alternative_series):
                self.matches.add('series')
            
            if video.season and self.video.season is None or video.season and video.season == self.video.season:
                self.matches.add('season')
        elif isinstance(video, Movie):
            if sanitize(video.title) and sanitize(self.video.title) in (
                    sanitize(name) for name in [video.title] + video.alternative_titles):
                self.matches.add('title')

        # General matches
        if video.year and video.year == self.video.year:
            self.matches.add('year')

        video_type = 'movie' if isinstance(video, Movie) else 'episode'
        self.matches.add(video_type)
        
        guess = guessit(self.filename, {'type': video_type})
        for g in guess:
            if g[0] == "release_group" or "source":
                if video.release_group == g[1]:
                    self.matches.add('release_group')
                    break
                
        # Prioritize .srt by repurposing the audio_codec match
        if self.filename.endswith(".srt"):
            self.matches.add('audio_codec')

        return self.matches

class JimakuProvider(Provider):
    '''Jimaku Provider.'''
    video_types = (Episode, Movie)
    
    api_url = 'https://jimaku.cc/api'
    api_ratelimit_max_delay_seconds = 5
    api_ratelimit_backoff_limit = 3
    
    corrupted_file_size_threshold = 500
    
    languages = {Language.fromietf("ja")}

    def __init__(self, enable_name_search_fallback, enable_archives_download, enable_ai_subs, api_key):
        if api_key:
            self.api_key = api_key
        else:
            raise ConfigurationError('Missing api_key.')

        self.enable_name_search_fallback = enable_name_search_fallback
        self.download_archives = enable_archives_download
        self.enable_ai_subs = enable_ai_subs
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['Content-Type'] = 'application/json'
        self.session.headers['Authorization'] = self.api_key
        self.session.headers['User-Agent'] = os.environ.get("SZ_USER_AGENT")

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
                return None
            
            searching_for_entry = "query" in url
            data = self._search_for_entry(url)

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
        is_movie = entry.get('flags', {}).get('movie', False)
        
        if isinstance(video, Episode) and is_movie:
            logger.warn("Bazarr thinks this is a series, but Jimaku says this is a movie! May not be able to match subtitles...")
        
        logger.info(f"Matched entry: ID: '{entry_id}', anilist_id: '{anilist_id}', name: '{entry_name}', english_name: '{entry.get('english_name')}', movie: {is_movie}")
        if entry.get("flags").get("unverified"):
            logger.warning(f"This entry '{entry_id}' is unverified, subtitles might be incomplete or have quality issues!")    
        
        # Get a list of subtitles for entry
        episode_number = video.episode if "episode" in dir(video) else None
        url_params = {'episode': episode_number} if isinstance(video, Episode) and not is_movie else {}
        only_look_for_archives = False
        
        has_offset = isinstance(video, Episode) and video.series_anidb_season_episode_offset is not None

        retry_count = 0
        adjusted_ep_num = None
        while retry_count <= 1:
            # Account for positive episode offset first
            if isinstance(video, Episode) and not is_movie and retry_count < 1:
                if video.season > 1 and has_offset:
                    offset_value = video.series_anidb_season_episode_offset
                    offset_value = offset_value if offset_value > 0 else -offset_value

                    if episode_number < offset_value:
                        adjusted_ep_num = episode_number + offset_value
                        logger.warning(f"Will try using adjusted episode number {adjusted_ep_num} first")
                        url_params = {'episode': adjusted_ep_num}

            url = f"entries/{entry_id}/files"
            data = self._search_for_subtitles(url, url_params)
            
            if not data:
                if isinstance(video, Episode) and not is_movie and has_offset and retry_count < 1:
                    logger.warning(f"Found no subtitles for adjusted episode number, but will retry with normal episode number {episode_number}")
                    url_params = {'episode': episode_number}
                elif isinstance(video, Episode) and not is_movie and retry_count < 1:
                    logger.warning(f"Found no subtitles for episode number {episode_number}, but will retry without 'episode' parameter")
                    url_params = {}
                    only_look_for_archives = True
                else:
                    return None
                
                retry_count += 1
            else:
                if adjusted_ep_num:
                    video.episode = adjusted_ep_num
                    logger.debug(f"This videos episode attribute has been updated to: {video.episode}")
                break
        
        # Filter subtitles
        list_of_subtitles = []
        
        data = [item for item in data if not item['name'].endswith(unhandled_archive_formats)]
        
        # Detect only archives being uploaded
        archive_entries = [item for item in data if item['name'].endswith(accepted_archive_formats)]
        subtitle_entries = [item for item in data if not item['name'].endswith(accepted_archive_formats)]
        has_only_archives = len(archive_entries) > 0 and len(subtitle_entries) == 0
        if has_only_archives:
            logger.warning("Have only found archived subtitles")
                
        elif only_look_for_archives:
            data = [item for item in data if item['name'].endswith(accepted_archive_formats)]

        for item in data:
            filename = item.get('name')
            download_url = item.get('url')
            is_archive = filename.endswith(accepted_archive_formats)
            
            # Archives will still be considered if they're the only files available, as is mostly the case for movies.
            if is_archive and not has_only_archives and not self.download_archives: 
                logger.warning(f"Skipping archive '{filename}' because normal subtitles are available instead")
                continue

            if not self.enable_ai_subs:
                p = re.compile(r'[\[\(]?(whisperai)[\]\)]?|[\[\(]whisper[\]\)]', re.IGNORECASE)
                if p.search(filename):
                    logger.warning(f"Skipping subtitle '{filename}' as it's suspected of being AI generated")
                    continue
            
            sub_languages = self._try_determine_subtitle_languages(filename)
            if len(sub_languages) > 1:
                logger.warning(f"Skipping subtitle '{filename}' as it's suspected of containing multiple languages")
                continue
            
            # Check if file is obviously corrupt. If no size is returned, assume OK
            filesize = item.get('size', self.corrupted_file_size_threshold)
            if filesize < self.corrupted_file_size_threshold:
                logger.warning(f"Skipping possibly corrupt file '{filename}': Filesize is just {filesize} bytes")
                continue
            
            if not filename.endswith(unhandled_archive_formats):
                lang = sub_languages[0] if len(sub_languages) > 1 else Language("jpn")
                list_of_subtitles.append(JimakuSubtitle(lang, video, download_url, filename))
            else:
                logger.debug(f"Skipping archive '{filename}' as it's not a supported format")
        
        return list_of_subtitles

    def list_subtitles(self, video, languages=None):
        subtitles = self._query(video)
        if not subtitles:
            return []
        
        return [s for s in subtitles]

    def download_subtitle(self, subtitle: JimakuSubtitle):
        target_url = subtitle.download_url
        response = self.session.get(target_url, timeout=10)
        response.raise_for_status()
        
        if subtitle.is_archive:
            archive = get_archive_from_bytes(response.content)
            if archive:
                if isinstance(subtitle.video, Episode):
                    subtitle.content = get_subtitle_from_archive(
                        archive, 
                        episode=subtitle.video.episode,
                        episode_title=subtitle.video.title
                    )
                else:                
                    subtitle.content = get_subtitle_from_archive(
                        archive
                    )
            else:
                logger.warning("Archive seems to not be an archive! File possibly corrupt?")
                return None
        else:
            subtitle.content = response.content
    
    def _do_jimaku_request(self, url_path, url_params={}):
        url = urljoin(f"{self.api_url}/{url_path}", '?' + urlencode(url_params))
        
        retry_count = 0
        while retry_count < self.api_ratelimit_backoff_limit:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 429:
                reset_time = 5
                retry_count + 1
                
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
                raise ServiceUnavailable(f"Jimaku returned an error: '{data.get('error')}', Code: '{data.get('code')}'")
            else:
                return data

        raise APIThrottled(f"Jimaku ratelimit max backoff limit of {self.api_ratelimit_backoff_limit} reached, aborting")
    
    # Wrapper functions to indirectly call _do_jimaku_request with different cache configs
    @region.cache_on_arguments(expiration_time=REFINER_EXPIRATION_TIME)
    def _search_for_entry(self, url_path, url_params={}):
        return self._do_jimaku_request(url_path, url_params)

    @region.cache_on_arguments(expiration_time=timedelta(minutes=1).total_seconds())
    def _search_for_subtitles(self, url_path, url_params={}):
        return self._do_jimaku_request(url_path, url_params)

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
        endpoint = "entries/search"
        anilist_id = video.anilist_id
        
        params = {}
        if anilist_id:
            params = {'anilist_id': anilist_id}
        else:
            if self.enable_name_search_fallback or isinstance(video, Movie):
                params = {'query': media_name}
            else:
                logger.error(f"Skipping '{media_name}': Got no AniList ID and fuzzy matching using name is disabled")
                return None
            
        if additional_params:
            params.update(additional_params)
        
        logger.info(f"Will search for entry based on params: {params}")
        return urljoin(endpoint, '?' + urlencode(params))
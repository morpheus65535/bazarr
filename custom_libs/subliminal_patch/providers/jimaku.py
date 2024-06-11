from __future__ import absolute_import

import io
import logging
import re
import time
import traceback
import urllib.parse
import rarfile
import zipfile
import requests
import xml.etree.ElementTree as etree

from requests import Session
from subliminal import __short_version__
from subliminal.exceptions import ConfigurationError
from subliminal.utils import sanitize
from subliminal.video import Episode, Movie
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.exceptions import APIThrottled
from subliminal_patch.providers.utils import get_subtitle_from_archive
from functools import cache
from subzero.language import Language

logger = logging.getLogger(__name__)

class JimakuSubtitle(Subtitle):
    '''Jimaku Subtitle.'''
    provider_name = 'jimaku'
    
    hash_verifiable = False

    def __init__(self, video, subtitle_id, subtitle_url, release_info, anilist_id=None):
        # Override param 'language' as it could only ever be "ja"
        super(JimakuSubtitle, self).__init__(Language("jpn"))
        
        self.video = video
        self.subtitle_id = subtitle_id
        self.subtitle_url = subtitle_url
        self.release_info = release_info
        self.anilist_id = anilist_id
        
    @property
    def id(self):
        return self.subtitle_id

    def get_matches(self, video):
        matches = set()
        
        # Specific matches
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
        else:
            raise ValueError(f"Unhandled instance of argument 'video': {type(video)}")

        # General matches
        if video.year and video.year == self.video.year:
            matches.add('year')

        video_type = 'movie' if isinstance(video, Movie) else 'episode'
        matches.add(video_type)

        return matches

class JimakuProvider(Provider):
    '''Jimaku Provider.'''
    video_types = (Episode, Movie)
    api_url = 'https://jimaku.cc/api'
    
    api_ratelimit_max_delay_seconds = 5
    api_ratelimit_backoff_limit = 3
    
    # See _get_tvdb_anidb_mapping()
    episode_number_override = False
    
    languages = {Language.fromietf("ja")}

    def __init__(self, enable_archives, enable_ai_subs, api_key):
        if api_key:
            self.api_key = api_key
        else:
            raise ConfigurationError('Missing api_key.')

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
            media_name = video.title
        elif isinstance(video, Episode):
            media_name = video.series.lower()
            
            # Check if media_name ends with "Sn", if so strip chars as Jimaku only lists seasons by numbers alone
            # If 'n' is 1, completely strip it as first seasons don't have a season number
            if re.search(r's\d$', media_name):
                if int(media_name[-1]) == 1:
                    media_name = re.sub(r's\d$', "", media_name)
                else:
                    # As shows sometimes have the wrong season number in the title, we'll reassemble it
                    media_name = re.sub(r's\d$', str(video.season), media_name)

        # Search for entry
        jimaku_search = self._assemble_jimaku_search_url(video, media_name)
        data = self._get_jimaku_response(jimaku_search['url'])
        if not data:
            return None
        
        # Determine entry
        entry_id = None
        entry_name = None
        anilist_id = None
        name_is_japanese = self._is_string_japanese(f"{media_name}")
        
        for entry in data:
            if jimaku_search['derived_anilist_id']:
                dict_field = 'anilist_id'
            else:
                entry_has_jp_name_field = 'japanese_name' in entry
                dict_field = 'japanese_name' if (name_is_japanese and entry_has_jp_name_field) else 'english_name'
                logger.debug(f"Attempting to get entry based on '{dict_field}' (name_is_japanese: {name_is_japanese} | entry_has_jp_name_field: {entry_has_jp_name_field})")
            
            # Only match first entry
            entry_property_value = entry.get(dict_field, None)
            if entry_property_value is not None:
                entry_id = entry.get('id')
                anilist_id = entry.get('anilist_id', None)
                entry_name = entry.get('name')
                
                logger.info(f"Matched entry: ID: '{entry_id}', anilist_id: '{anilist_id}', name: '{entry_name}', english_name: '{entry.get('english_name')}'")
                if entry.get("flags").get("unverified"):
                    logger.warning(f"This entry '{entry_id}' is unverified, subtitles might be incomplete or have quality issues!")
                
                break
            
        if entry_property_value is None:
            logger.error('Matched no entries.')
            return None
        
        # Get a list of subtitles for entry
        if isinstance(video, Episode):
            episode_number = video.episode
        
        retry_count = 0
        while retry_count <= 1:
            retry_count += 1
            
            if isinstance(video, Episode):
                url = f"entries/{entry_id}/files?episode={episode_number}"
            else:
                url = f"entries/{entry_id}/files"
            data = self._get_jimaku_response(url)
            
            # Edge case: When dealing with a cour, episodes could be uploaded with their episode numbers having an offset applied
            if not data and isinstance(video, Episode) and self.episode_number_override and retry_count < 1:
                logger.warning(f"Found no subtitles for {episode_number}, but will retry with offset-adjusted episode number {video.series_series_anidb_episode_no}.")
                episode_number = video.series_series_anidb_episode_no
            elif not data:
                return None
        
        # Filter subtitles
        list_of_subtitles = []

        archive_formats_blacklist = (".7z",) # Unhandled format
        if not self.enable_archives:
            disabled_archives = (".zip", ".rar")
            
            # Handle shows that only have archives uploaded
            filter = [item for item in data if not item['name'].endswith(disabled_archives)]
            if len(filter) == 0:
                logger.warning("Archives are disabled, but only archived subtitles have been returned. Will therefore download anyway.")
            else:
                archive_formats_blacklist += disabled_archives

        # Order subtitles to maximize quality
        # Certain subtitle sources, such as Netflix/WebRip usually yield superior quality over others
        sorted_data = sorted(data, key=self._subtitle_sorting_key)

        for item in sorted_data:
            subtitle_filename = item.get('name')
            subtitle_filesize = item.get('size')
            subtitle_url = item.get('url')
            
            if not self.enable_ai_subs:
                for ai_keyword in ["generated", "whisper"]:
                    if re.search(r'\b' + re.escape(ai_keyword) + r'\b', subtitle_filename.lower()):
                        logger.warning(f"Skipping AI generated subtitle '{subtitle_filename}'")
                        continue
            
            # Check if file is corrupt; The average file stands at ~20kB, we'll set the threshold at 5kB though 
            if subtitle_filesize < 5000:
                logger.warning(f"Skipping possibly corrupt file '{subtitle_filename}': Filesize is just {subtitle_filesize} bytes.")
                continue
            
            if not subtitle_filename.endswith(archive_formats_blacklist):
                number = episode_number if isinstance(video, Episode) else 0
                subtitle_id = f"{str(anilist_id)}_{number}_{video.release_group}"
                
                list_of_subtitles.append(JimakuSubtitle(video, subtitle_id, subtitle_url, subtitle_filename, anilist_id))
            else:
                logger.debug(f"> Skipping subtitle of name '{subtitle_filename}' due to archive blacklist. (enable_archives: {self.enable_archives})")
        
        return list_of_subtitles

    # As we'll only ever handle "ja", we'll just ignore the parameter "languages"
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
    def _is_string_japanese(string):
        for char in string:
            if ('\u3040' <= char <= '\u309F' or  # Hiragana
                '\u30A0' <= char <= '\u30FF' or  # Katakana
                '\u4E00' <= char <= '\u9FFF' or  # Kanji (CJK Unified Ideographs)
                '\uFF66' <= char <= '\uFF9D'):   # Half-width Katakana
                return True
        return False
    
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
        
    @staticmethod
    def _subtitle_sorting_key(file):
        name = file["name"].lower()
        is_srt = name.endswith('.srt')
        
        # Usually netflix > webrip > amazon, with the rest having the lowest priority
        sub_sources = ["netflix", "webrip", "amazon"]
        priority = len(sub_sources)
        for index, source in enumerate(sub_sources):
            if source in name:
                priority = index
                break
        
        return (not is_srt, priority, file["name"])
    
    @cache
    def _get_jimaku_response(self, url_path):
        url = f"{self.api_url}/{url_path}"
        
        retry_count = 0
        while retry_count < self.api_ratelimit_backoff_limit:
            retry_count += 1
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 429:
                api_reset_time = float(response.headers.get("x-ratelimit-reset-after", 5))
                reset_time = self.api_ratelimit_max_delay_seconds if api_reset_time > self.api_ratelimit_max_delay_seconds else api_reset_time
                
                logger.warning(f"Jimaku ratelimit hit, waiting for '{reset_time}' seconds ({retry_count}/{self.api_ratelimit_backoff_limit} tries)")
                time.sleep(reset_time)
            else:
                response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Length of response on {url}: {len(data)}")
            if len(data) == 0:
                logger.error(f"Jimaku returned no items for our our query: {url_path}")
                return None
            else:
                return data
            
        # Max retries exceeded
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
    
    @cache
    def _assemble_jimaku_search_url(self, video, media_name):
        """
        Return a search URL for the Jimaku API.
        Will first try to determine an Anilist ID based on properties of the video object.
        If that fails, will simply assemble a query URL that relies on Jimakus fuzzy search instead.
        """
        
        # Attempt to derive anilist_id
        derived_anilist_id = None
        derived_anidb_id = None
        tag_to_derive_from = ""
        tag_list = ["imdb_id"] if isinstance(video, Movie) else [
            "series_anidb_id",
            "tvdb_id",
            "series_tvdb_id"
        ]
        
        logger.info(f"Attempting to derive anilist ID...")
        for tag in tag_list:
            candidate = getattr(video, tag, None)
            
            if candidate:
                # Because tvdb assigns a single ID to all seasons of a show, we'll have to use another list to determine the correct AniDB ID
                if isinstance(video, Episode) and "tvdb" in tag and video.season > 1:
                    if video.series_anidb_episode_no != None and video.series_anidb_episode_no != video.episode:
                        self.episode_number_override = True
                    
                tag_to_derive_from = tag
                logger.info(f"Got candidate tag '{tag_to_derive_from}' with value '{candidate}'")
                break

        if tag_to_derive_from or derived_anidb_id:
            try:
                url = "https://raw.githubusercontent.com/Fribb/anime-lists/master/anime-list-mini.json"
                anime_list = self._webrequest_with_cache(url)
                
                if derived_anidb_id:
                    mapped_tag = "anidb_id"
                    value_to_use = derived_anidb_id
                else:
                    # video <-> anime-lists
                    tag_map = {
                        "series_anidb_id": "anidb_id",
                        "series_anidb_episode_id": "anidb_id",
                        "tvdb_id": "thetvdb_id",
                        "series_tvdb_id": "thetvdb_id",
                    }

                    mapped_tag = tag_map.get(tag_to_derive_from, tag_to_derive_from)
                    value_to_use = getattr(video, tag_to_derive_from)
                
                obj = [obj for obj in anime_list if mapped_tag in obj and str(obj[mapped_tag]) == str(value_to_use)]
                logger.debug(f"Based on '{mapped_tag}': '{value_to_use}', anime-list matched: {obj}")

                if len(obj) > 0:
                    derived_anilist_id = obj[0]["anilist_id"]
                else:
                    logger.warning(f"Could not find corresponding Anilist ID with '{mapped_tag}': {value_to_use}")
            except Exception as e:
                logger.error(f"Failed deriving anilist_id: {traceback.format_exc()}")
                
        url = "entries/search"
        if derived_anilist_id:
            logger.info(f"Will search for entry based on anilist_id: {derived_anilist_id}")
            url = f"{url}?anilist_id={derived_anilist_id}"
        else:
            logger.info(f"Will search for entry based on media_name: {media_name}")
            url = f"{url}?query={urllib.parse.quote_plus(media_name)}"
            
        return {
            'url': url,
            'derived_anilist_id': derived_anilist_id
        }
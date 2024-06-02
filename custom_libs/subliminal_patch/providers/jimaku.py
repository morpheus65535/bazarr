from __future__ import absolute_import

import logging
import re
import urllib.parse
import requests
import xml.etree.ElementTree as etree

from requests import Session
from subliminal import __short_version__
from subliminal.exceptions import ConfigurationError
from subliminal.utils import sanitize
from subliminal.video import Episode, Movie
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle
from functools import cache
from subzero.language import Language

logger = logging.getLogger(__name__)

class JimakuSubtitle(Subtitle):
    '''Jimaku Subtitle.'''
    provider_name = 'jimaku'
    
    hash_verifiable = False

    def __init__(self, video, subtitle_id, subtitle_url, anilist_id=None):
        # Override param 'language' as it could only ever be "ja"
        super(JimakuSubtitle, self).__init__(Language("jpn"))
        
        self.video = video
        self.subtitle_id = subtitle_id
        self.subtitle_url = subtitle_url
        self.anilist_id = anilist_id
        
    @property
    def id(self):
        return self.subtitle_id

    def get_matches(self, video):
        matches = set()
        
        if isinstance(video, Episode):
            # series name
            if sanitize(video.series) and sanitize(self.video.series) in (
                    sanitize(name) for name in [video.series] + video.alternative_series):
                matches.add('series')
            
            # season
            if video.season and self.video.season is None or video.season and video.season == self.video.season:
                matches.add('season')            

            # year
            if video.original_series and self.video.year is None or video.year and video.year == self.video.year:
                matches.add('year')
                
            # episode
            if video.episode == self.video.episode:
                matches.add('episode')
        else:
            raise ValueError(f"Unhandled instance of argument 'video': {type(video)}")

        return matches

class JimakuProvider(Provider):
    '''Jimaku Provider.'''
    video_types = (Episode, Movie)
    api_url = 'https://jimaku.cc/api'
    
    languages = {Language.fromietf("ja")}

    def __init__(self, api_key=None):
        if api_key:
            self.api_key = api_key
        else:
            raise ConfigurationError('Missing api_key.')

        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/%s' % __short_version__
        self.session.headers['Content-Type'] = 'application/json'
        self.session.headers['Authorization'] = self.api_key

    def terminate(self):
        self.session.close()

    def query(self, video):
        series_name = sanitize(video.alternative_series[0] if len(video.alternative_series) > 0 else str(video.series_name))
        episode_number = video.episode

        # Check if series_name ends with "Sn", if so strip chars as Jimaku only lists seasons by numbers alone
        # If 'n' is 1, completely strip it as first seasons don't have a season number
        if re.search(r'S\d$', series_name):
            if int(series_name[-1]) == 1:
                series_name = re.sub(r'S\d$', "",  series_name)
            else:
                # As shows sometimes have the wrong season number in the title, we'll reassemble it
                series_name = re.sub(r'S\d$', str(video.season),  series_name)

        # Attempt to derive anilist_id
        derived_anilist_id = None
        derived_anidb_id = None
        tag_to_derive_from = ""
        
        logger.info(f"Attempting to derive anilist ID...")
        for tag in ["series_anidb_id", "series_anidb_episode_id", "tvdb_id", "series_tvdb_id"]:
            candidate = getattr(video, tag, None)
            
            if candidate:
                # Because tvdb assigns a single ID to all seasons of a show, we'll have to use another list to determine the correct AniDB ID
                if "tvdb" in tag and video.season > 1:
                    derived_anidb_id = self._get_tvdb_anidb_mapping(candidate, video.season)
                    logger.info(f"Found AniDB ID '{derived_anidb_id}' for TVDB ID '{candidate}', season '{video.season}'")
                    break
                    
                tag_to_derive_from = tag
                logger.info(f"Got candidate tag '{tag_to_derive_from}' with value '{candidate}'")
                break

        if tag_to_derive_from or derived_anidb_id:
            try:
                anime_list = self._get_anime_list_map()
                
                if derived_anidb_id:
                    mapped_tag = "anidb_id"
                    value_to_use = derived_anidb_id
                else:
                    # Left: video, right: anime-lists
                    tag_map = {
                        "series_anidb_id": "anidb_id",
                        "series_anidb_episode_id": "anidb_id",
                        "tvdb_id": "thetvdb_id",
                        "series_tvdb_id": "thetvdb_id",
                    }
                    mapped_tag = tag_map[tag_to_derive_from]
                    value_to_use = getattr(video, tag_to_derive_from)
                
                obj = [obj for obj in anime_list if mapped_tag in obj and str(obj[mapped_tag]) == str(value_to_use)]
                logger.debug(f"Based on '{mapped_tag}': '{value_to_use}', anime-list matched: {obj}")

                if len(obj) > 0:
                    derived_anilist_id = obj[0]["anilist_id"]
                else:
                    logger.warning(f"Could not find corresponding Anilist ID with '{mapped_tag}': {value_to_use}")
            except Exception as e:
                logger.error(f"Failed deriving anilist_id: {str(e)}")
                
        url_search_param = None
        if derived_anilist_id:
            logger.info(f"Will search for entry based on anilist_id: {derived_anilist_id}")
            url_search_param = f"anilist_id={derived_anilist_id}"
        else:
            logger.info(f"Will search for entry based on series_name: {series_name}")
            url_search_param = f"query={urllib.parse.quote_plus(series_name)}"
        
        # Search for entry
        url = f"{self.api_url}/entries/search?{url_search_param}"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.debug(f"Length of response on {url}: {len(data)}")
        if len(data) == 0:
            logger.error(f"Jimaku returned no items for our our query: {url_search_param}")
            return None
        
        # Determine entry
        entry_id = None
        anilist_id = None
        name_is_japanese = self._is_string_japanese(f"series_name")
        
        for entry in data:
            if derived_anilist_id:
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
                logger.info(f"Matched entry: ID: '{entry_id}', anilist_id: '{anilist_id}', name: '{entry.get('name')}', english_name: '{entry.get('english_name')}'")
                break
            
        if entry_property_value is None:
            logger.error('Matched no entries.')
            return None
        
        # Get a list of subtitles for entry
        url = f"{self.api_url}/entries/{entry_id}/files?episode={episode_number}"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        logger.debug(f"Length of response on {url}: {len(data)}")
        if len(data) == 0:
            logger.error(f"No subtitles have been returned by entry '{entry_id}' for episode number {episode_number}.")
            return None
        
        # Filter subtitles
        list_of_subtitles = []
        archive_formats = ('.rar', '.zip', '.7z')
        for item in data:
            if not item['name'].endswith(archive_formats):
                subtitle_url = item.get('url')
                subtitle_id = f"{str(anilist_id)}_{episode_number}_{video.release_group}"
                list_of_subtitles.append(JimakuSubtitle(video, subtitle_id, subtitle_url, anilist_id))
            else:
                logger.debug(f"> Skipping subtitle of name {item['name']} as it did not pass the archive format filter.")
        
        return list_of_subtitles

    # As we'll only ever handle "ja", we'll just ignore the parameter "languages"
    def list_subtitles(self, video, languages=None):
        subtitles = self.query(video)
        if not subtitles:
            return []
        
        return [s for s in subtitles]

    def download_subtitle(self, subtitle: JimakuSubtitle):
        target_url = subtitle.subtitle_url
        response = self.session.get(target_url, timeout=10)
        response.raise_for_status()
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
    @cache
    def _get_anime_list_map():
        # We won't use self.session as the endpoint doesnt need our API key
        response = requests.get(
            "https://raw.githubusercontent.com/Fribb/anime-lists/master/anime-list-mini.json",
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        
        return response.json()
    
    @staticmethod
    @cache
    def _get_tvdb_anidb_map():
        # We won't use self.session as the endpoint doesnt need our API key
        response = requests.get(
            "https://raw.githubusercontent.com/Anime-Lists/anime-lists/master/anime-list.xml"
        )
        response.raise_for_status()
        
        return response.content

    def _get_tvdb_anidb_mapping(self, tvdbid, season=1):
        xml = etree.fromstring(self._get_tvdb_anidb_map())
        findings = xml.findall(
            f".//anime[@tvdbid='{tvdbid}'][@defaulttvdbseason='{season}']"
        )
        
        if len(findings) > 0:
            for i, v in enumerate(findings):
                try:
                    return v.attrib.get('anidbid')
                except Exception as e:
                    logger.debug(f"Error returning on index {i}: {str(e)}")
                    continue
        else:
            logger.warning(f"Could not find an AniDB ID for provided TVDB ID and season ({season})!")
        
        return None
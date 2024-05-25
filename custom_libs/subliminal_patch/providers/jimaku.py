from __future__ import absolute_import
import logging
from rapidfuzz import process, fuzz

from requests import Session
import urllib.parse

import requests

from subliminal import __short_version__
from subliminal.exceptions import ConfigurationError
from subliminal.utils import sanitize
from subliminal.video import Episode, Movie
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle
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
        series_name = str(video.series)
        episode_number = video.episode
        
        # Attempt to derive anilist_id
        derived_anilist_id = None
        derive_from_tag = ""
        
        # Not yet handled: series_anidb_series_id being '(None, )' (class 'str')
        for tag in ["series_anidb_id", "tvdb_id", "series_tvdb_id"]:
            candidate = getattr(video, tag, None)
            if candidate:
                derive_from_tag = tag
                break
            
        if derive_from_tag:
            logger.info(f"Will attempt to derive Anilist ID based on '{derive_from_tag}'")
            
            # Left: video, right: anime-lists
            tag_map = {
                "series_anidb_id": "anidb_id",
                "tvdb_id": "thetvdb_id",
                "series_tvdb_id": "thetvdb_id",
            }
            mapped_tag = tag_map[derive_from_tag]
            
            try:
                # We won't use self.session as the endpoint doesnt need our API key
                response = requests.get(
                    "https://raw.githubusercontent.com/Fribb/anime-lists/master/anime-list-mini.json",
                    headers={'Content-Type': 'application/json'}
                )
                response.raise_for_status()
                
                data = response.json()
                obj = [obj for obj in data if mapped_tag in obj and obj[mapped_tag] == getattr(video, derive_from_tag)]
                derived_anilist_id = obj[0]["anilist_id"]
            except Exception as e:
                logger.error(f"Could not derive anilist_id: {str(e)}")
                
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
            logger.error(f"No entries have been returned.")
            return None
        
        # Determine entry
        entry_id = None
        anilist_id = None
        name_is_japanese = self._is_string_japanese(f"series_name")
        
        for entry in data:
            if not derived_anilist_id:
                entry_has_jp_name_field = 'japanese_name' in entry
                dict_field = 'japanese_name' if (name_is_japanese and entry_has_jp_name_field) else 'english_name'
                logger.debug(f"Attempting to get entry based on '{dict_field}' because name_is_japanese: {name_is_japanese} and entry_has_jp_name_field: {entry_has_jp_name_field}")
            else:
                dict_field = 'anilist_id'
            
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
        
        # Determine which subtitle to use
        # Unfortunatley, subtitles will have differing name schemes
        # For that reason, we'll just try our luck with fuzyy matching
        fuzzy_verdict = process.extractOne(video.original_name, [item['name'] for item in data], scorer=fuzz.WRatio)
        logger.debug(f"fuzzy_verdict: {fuzzy_verdict}")
        logger.info(f"Matched subtitle: '{fuzzy_verdict[0]}' based on '{video.original_name}'")
        
        archive_formats = ('.rar', '.zip', '.7z')
        subtitle_object = next(item for item in data if (item['name'] == fuzzy_verdict[0] and not item['name'].endswith(archive_formats)))
        subtitle_url = subtitle_object.get('url')
        subtitle_id = f"{str(anilist_id)}_{episode_number}_{video.release_group}"
        
        return [JimakuSubtitle(video, subtitle_id, subtitle_url, anilist_id)]

    # As we'll only ever handle "ja", we'll just ignore the parameter "languages"
    def list_subtitles(self, video, languages=None):
        subtitles = self.query(video)
        if not subtitles:
            return []
        
        return [s for s in subtitles]

    def download_subtitle(self, subtitle: JimakuSubtitle):
        target_url = subtitle.subtitle_url
        logger.debug(f"Will attempt download of '{target_url}'...")
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

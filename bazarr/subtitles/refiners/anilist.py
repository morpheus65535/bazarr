# coding=utf-8
# fmt: off

import logging
import time
import requests
from collections import namedtuple
from datetime import timedelta

from app.config import settings
from subliminal import Episode, region, __short_version__
from subliminal.cache import REFINER_EXPIRATION_TIME

logger = logging.getLogger(__name__)
refined_providers = {'jimaku'}

class AniListClient(object):
    api_ratelimit_backoff_limit = 3
    max_api_reset_time = 5
    
    anilist_api_query_template = '''
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    id
    episodes
    relations {
      edges {
        relationType
        node {
          id
          format
        }
      }
    }
  }
}
'''
    
    def __init__(self, session=None, timeout=10):
        self.session = session or requests.Session()
        self.session.timeout = timeout
        self.session.headers['Content-Type'] = 'application/json'
        self.session.headers['User-Agent'] = 'Subliminal/%s' % __short_version__
    
    @region.cache_on_arguments(expiration_time=timedelta(days=1).total_seconds())
    def get_series_mappings(self):
        r = self.session.get(
            'https://raw.githubusercontent.com/Fribb/anime-lists/master/anime-list-mini.json'
        )

        r.raise_for_status()
        return r.json()

    def get_series_id(self, candidate_id_name, candidate_id_value):
        anime_list = self.get_series_mappings()
        
        tag_map = {
            "series_anidb_id": "anidb_id",
            "imdb_id": "imdb_id"
        }
        mapped_tag = tag_map.get(candidate_id_name, candidate_id_name)        
        
        obj = [obj for obj in anime_list if mapped_tag in obj and str(obj[mapped_tag]) == str(candidate_id_value)]
        logger.debug(f"Based on '{mapped_tag}': '{candidate_id_value}', anime-list matched: {obj}")

        if len(obj) > 0:
            return obj[0]["anilist_id"]
        else:
            logger.debug(f"Could not find corresponding AniList ID with '{mapped_tag}': {candidate_id_value}")
            return None
    
    @region.cache_on_arguments(expiration_time=REFINER_EXPIRATION_TIME)
    def _query_anilist_api_for_entry(self, anilist_id):
        url = 'https://graphql.anilist.co'
        response = self.session.post(
            url,
            json = {
                'query': self.anilist_api_query_template,
                'variables': {'id': anilist_id}
            }
        )
    
        retry_count = 0
        while retry_count < self.api_ratelimit_backoff_limit:
            retry_count += 1
            if response.status_code == 429:
                api_reset_time = float(response.headers.get("Retry-After", 5))
                reset_time = self.max_api_reset_time if api_reset_time > 5 else self.max_api_reset_time
                
                time.sleep(reset_time)
            else:
                response.raise_for_status()
            
            return response.json()

    def _process_anilist_entry(self, data):
        relations_ids = []
        media = data["data"]["Media"]
        
        episodes = media["episodes"]
        
        # Only select actual seasons; no OVAs etc.
        # We also only care about prequels (top-down)
        relevant_edges = [x for x in media["relations"]["edges"] if x["node"]["format"] == "TV"]
        relevant_edges = [x for x in relevant_edges if x["relationType"] == "PREQUEL"]
        
        if len(relevant_edges) > 0:
            for edge in relevant_edges:
                relations_ids.append(edge["node"]["id"])

        return episodes, relations_ids

    def compute_episode_offsets(self, start_id):
        self.initial_anilist_id = start_id
        
        entries, processed_ids = [], []
        ids_to_query = [self.initial_anilist_id]
        
        while ids_to_query:
            current_id = ids_to_query.pop(0)
            if current_id in processed_ids:
                continue
            
            data = self._query_anilist_api_for_entry(current_id)
            episodes, ids = self._process_anilist_entry(data)
            
            processed_ids.append(current_id)
            entries.append({
                "id": current_id,
                "episodes": episodes
            })
            
            ids_to_query.extend(ids)
        
        # Sort IDs in ascending order als lowest ID = first season
        entries = sorted(entries, key=lambda x: x['id'])
        
        offset = 0
        for entry in entries:
            entry["offset"] = offset
            offset += entry["episodes"]
            
        return entries

def refine_from_anilist(path, video):
    # Safety checks
    if isinstance(video, Episode):
        if not video.series_anidb_id:
            logger.error(f"Will not refine '{video.series}' as it does not have an AniDB ID.")
            return

    if refined_providers.intersection(settings.general.enabled_providers) and video.series_anilist_id is None:
        refine_anilist_ids(video)

def refine_anilist_ids(video):
    anilist_client = AniListClient()
    
    if isinstance(video, Episode):
        candidate_id_name = "series_anidb_id"
    else:
        candidate_id_name = "imdb_id"
        
    candidate_id_value = getattr(video, candidate_id_name, None)
    if not candidate_id_value:
        logger.error(f"Found no value for property {candidate_id_name} of video.")
        return video
    
    anilist_id = anilist_client.get_series_id(candidate_id_name, candidate_id_value)
    if not anilist_id:
        return video
    
    # Compute episode offsets
    try:
        offsets = anilist_client.compute_episode_offsets(anilist_id)
        logger.debug(f"Episode offsets for this AniList ID ({anilist_id}): {offsets}")
        video.series_anilist_episode_offset = next(
            item for item in offsets if item["id"] == anilist_id
        )["offset"]
    except Exception as e:
        logger.warning(f"Could not compute episode offsets: {str(e)}")

    video.series_anilist_id = anilist_id
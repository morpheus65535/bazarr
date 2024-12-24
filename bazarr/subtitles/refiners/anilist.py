# coding=utf-8
# fmt: off

import logging
import time
import requests
from collections import namedtuple
from datetime import timedelta

from app.config import settings
from subliminal import Episode, region, __short_version__

logger = logging.getLogger(__name__)
refined_providers = {'jimaku'}


class AniListClient(object):    
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
            anilist_id = obj[0].get("anilist_id")
            if not anilist_id:
                logger.error("This entry does not have an AniList ID")
            
            return anilist_id
        else:
            logger.debug(f"Could not find corresponding AniList ID with '{mapped_tag}': {candidate_id_value}")
        
        return None


def refine_from_anilist(path, video):
    # Safety checks
    if isinstance(video, Episode):
        if not video.series_anidb_id:
            return

    if refined_providers.intersection(settings.general.enabled_providers) and video.anilist_id is None:
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

    video.anilist_id = anilist_id

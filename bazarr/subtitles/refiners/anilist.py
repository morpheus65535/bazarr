# coding=utf-8
# fmt: off

import logging
import requests
from collections import namedtuple
from datetime import timedelta

from app.config import settings
from subliminal import Episode, Movie, region

logger = logging.getLogger(__name__)
refined_providers = {'jimaku'}

class AniListClient(object):
    def __init__(self, session=None):
        self.session = session or requests.Session()

    AnimeInfo = namedtuple('AnimeInfo', ['anime'])
    
    @region.cache_on_arguments(expiration_time=timedelta(days=1).total_seconds())
    def get_series_mappings(self):
        r = self.session.get(
            'https://raw.githubusercontent.com/Fribb/anime-lists/master/anime-list-mini.json',
            timeout=10
        )

        r.raise_for_status()
        return r.json()

    #@region.cache_on_arguments(expiration_time=timedelta(days=1).total_seconds())
    def get_series_id(self, candidate_id_name, candidate_id_value):
        anime_list = self.get_series_mappings()
        
        tag_map = {
            "series_anidb_id": "anidb_id",
            "series_tvdb_id": "thetvdb_id",
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

def refine_from_anilist(path, video):
    # Safety checks
    if isinstance(video, Episode):
        season = video.season if video.season else 0
        if season > 1 and not video.series_anidb_id:
            logger.error(
                f"Will not refine '{video.series}' as it only has a TVDB ID, but its season ({season}) is higher than 1.",
                "\nSuch IDs are not unique to each season; To allow refinement for this series, you must enable AniDB integration."
            )
            return

    if refined_providers.intersection(settings.general.enabled_providers) and video.anilist_id is None:
        refine_anilist_ids(video)

def refine_anilist_ids(video):
    anilist_client = AniListClient()
    
    if isinstance(video, Episode):
        season = video.season if video.season else 0
        if season > 1:
            candidate_id_name = "series_anidb_id"
        else:
            candidate_id_name = "series_tvdb_id"
    else:
        candidate_id_name = "imdb_id"
        
    candidate_id_value = getattr(video, candidate_id_name, None)
    if not candidate_id_value:
        logger.error(f"Found no value for property {candidate_id_name} of video.")
    
    anilist_id = anilist_client.get_series_id(candidate_id_name, candidate_id_value)
    if not anilist_id:
        return video

    video.anilist_id = anilist_id

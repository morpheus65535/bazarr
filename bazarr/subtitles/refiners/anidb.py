# coding=utf-8
# fmt: off

import logging
import requests
from collections import namedtuple
from datetime import datetime, timedelta
from requests.exceptions import HTTPError

from app.config import settings
from subliminal import Episode, region
from subliminal.cache import REFINER_EXPIRATION_TIME
from subliminal_patch.exceptions import TooManyRequests

try:
    from lxml import etree
except ImportError:
    try:
        import xml.etree.cElementTree as etree
    except ImportError:
        import xml.etree.ElementTree as etree

refined_providers = {'animetosho', 'jimaku'}

logger = logging.getLogger(__name__)

api_url = 'http://api.anidb.net:9001/httpapi'

cache_key_refiner = "anidb_refiner"

# Soft Limit for amount of requests per day
daily_limit_request_count = 200


class AniDBClient(object):
    def __init__(self, api_client_key=None, api_client_ver=1, session=None):
        self.session = session or requests.Session()
        self.api_client_key = api_client_key
        self.api_client_ver = api_client_ver
        self.cache = region.get(cache_key_refiner, expiration_time=timedelta(days=1).total_seconds())

    @property
    def is_throttled(self):
        return self.cache and self.cache.get('is_throttled')
    
    @property
    def has_api_credentials(self):
        return self.api_client_key != '' or None

    @property
    def daily_api_request_count(self):
        if not self.cache:
            return 0

        return self.cache.get('daily_api_request_count', 0)

    AnimeInfo = namedtuple('AnimeInfo', ['anime', 'episode_offset'])

    @region.cache_on_arguments(expiration_time=timedelta(days=1).total_seconds())
    def get_series_mappings(self):
        r = self.session.get(
            'https://raw.githubusercontent.com/Anime-Lists/anime-lists/master/anime-list.xml',
            timeout=10
        )

        r.raise_for_status()

        return r.content

    @region.cache_on_arguments(expiration_time=timedelta(days=1).total_seconds())
    def get_series_and_episode_info(self, tvdb_series_id, tvdb_series_season, episode):
        mappings = etree.fromstring(self.get_series_mappings())
        
        # Enrich the collection of anime with the episode offset
        animes = [
            self.AnimeInfo(anime, int(anime.attrib.get('episodeoffset', 0)))
            for anime in mappings.findall(
                f".//anime[@tvdbid='{tvdb_series_id}'][@defaulttvdbseason='{tvdb_series_season}']"
            )
        ]

        if not animes:
            return None, None

        # Sort the anime by offset in ascending order
        animes.sort(key=lambda a: a.episode_offset)

        # Different from Tvdb, Anidb have different ids for the Parts of a season
        anidb_id = None
        offset = 0

        for index, anime_info in enumerate(animes):
            anime, episode_offset = anime_info

            mapping_list = anime.find('mapping-list')

            # Handle mapping list for Specials
            if mapping_list:
                for mapping in mapping_list.findall("mapping"):
                    # Mapping values are usually like ;1-1;2-1;3-1;
                    for episode_ref in mapping.text.split(';'):
                        if not episode_ref:
                            continue

                        anidb_episode, tvdb_episode = map(int, episode_ref.split('-'))
                        if tvdb_episode == episode:
                            anidb_id = int(anime.attrib.get('anidbid'))

                            return anidb_id, anidb_episode

            if episode > episode_offset:
                anidb_id = int(anime.attrib.get('anidbid'))
                offset = episode_offset

        return anidb_id, episode - offset

    @region.cache_on_arguments(expiration_time=timedelta(days=1).total_seconds())
    def get_episode_ids(self, series_id, episode_no):
        if not series_id:
            return None

        episodes = etree.fromstring(self.get_episodes(series_id))

        episode = episodes.find(f".//episode[epno='{episode_no}']")

        if not episode:
            return series_id, None

        return series_id, int(episode.attrib.get('id'))

    @region.cache_on_arguments(expiration_time=REFINER_EXPIRATION_TIME)
    def get_episodes(self, series_id):
        if self.daily_api_request_count >= 200:
            raise TooManyRequests('Daily API request limit exceeded')

        r = self.session.get(
            api_url,
            params={
                'request': 'anime',
                'client': self.api_client_key,
                'clientver': self.api_client_ver,
                'protover': 1,
                'aid': series_id
            },
            timeout=10)
        r.raise_for_status()

        xml_root = etree.fromstring(r.content)

        response_code = xml_root.attrib.get('code')
        if response_code == '500':
            raise TooManyRequests('AniDB API Abuse detected. Banned status.')
        elif response_code == '302':
            raise HTTPError('AniDB API Client error. Client is disabled or does not exists.')

        self.increment_daily_quota()

        episode_elements = xml_root.find('episodes')

        if not episode_elements:
            raise ValueError

        return etree.tostring(episode_elements, encoding='utf8', method='xml')

    def increment_daily_quota(self):
        daily_quota = self.daily_api_request_count + 1

        if not self.cache:
            region.set(cache_key_refiner, {'daily_api_request_count': daily_quota})

            return

        self.cache['daily_api_request_count'] = daily_quota

        region.set(cache_key_refiner, self.cache)

    @staticmethod
    def mark_as_throttled():
        region.set(cache_key_refiner, {'is_throttled': True})


def refine_from_anidb(path, video):
    if not isinstance(video, Episode) or not video.series_tvdb_id:
        logger.debug(f'Video is not an Anime TV series, skipping refinement for {video}')

        return

    if refined_providers.intersection(settings.general.enabled_providers) and video.series_anidb_id is None:
        refine_anidb_ids(video)


def refine_anidb_ids(video):
    anidb_client = AniDBClient(settings.anidb.api_client, settings.anidb.api_client_ver)

    season = video.season if video.season else 0

    anidb_series_id, anidb_episode_no = anidb_client.get_series_and_episode_info(
        video.series_tvdb_id,
        season,
        video.episode,
    )
    
    if not anidb_series_id:
        logger.error(f'Could not find anime series {video.series}')
        return video
    
    anidb_episode_id = None
    if anidb_client.has_api_credentials:
        if anidb_client.is_throttled:
            logger.warning(f'API daily limit reached. Skipping episode ID refinement for {video.series}')
        else:
            try:
                anidb_episode_id = anidb_client.get_episode_ids(
                    anidb_series_id,
                    anidb_episode_no
                )
            except TooManyRequests:
                logger.error(f'API daily limit reached while refining {video.series}')
                anidb_client.mark_as_throttled()
    else:
        logger.warn(f'AniDB API credentials not fully set up, will not refine episode IDs for {video.series}')

    video.series_anidb_id = anidb_series_id
    video.series_anidb_episode_id = anidb_episode_id
    video.series_anidb_episode_no = anidb_episode_no

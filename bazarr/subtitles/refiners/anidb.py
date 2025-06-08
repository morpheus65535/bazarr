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
providers_requiring_anidb_api = {'animetosho'}

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
        return self.api_client_key != '' and self.api_client_key is not None

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
    def get_show_information(self, tvdb_series_id, tvdb_series_season, episode):
        mappings = etree.fromstring(self.get_series_mappings())
        
        # Enrich the collection of anime with the episode offset
        animes = [
            self.AnimeInfo(anime, int(anime.attrib.get('episodeoffset', 0)))
            for anime in mappings.findall(
                f".//anime[@tvdbid='{tvdb_series_id}'][@defaulttvdbseason='{tvdb_series_season}']"
            )
        ]

        is_special_entry = False
        if not animes:
            # Some entries will store TVDB seasons in a nested mapping list, identifiable by the value 'a' as the season
            special_entries = mappings.findall(
                f".//anime[@tvdbid='{tvdb_series_id}'][@defaulttvdbseason='a']"
            )

            if not special_entries:
                return None, None, None

            is_special_entry = True

            for special_entry in special_entries:
                mapping_list = special_entry.findall(f".//mapping[@tvdbseason='{tvdb_series_season}']")
                anidb_id = int(special_entry.attrib.get('anidbid'))
                offset = int(mapping_list[0].attrib.get('offset', 0)) if len(mapping_list) > 0 else 0

        if not is_special_entry:
            # Sort the anime by offset in ascending order
            animes.sort(key=lambda a: a.episode_offset)

            # Different from Tvdb, Anidb have different ids for the Parts of a season
            anidb_id = None
            offset = 0

            for index, anime_info in enumerate(animes):
                anime, episode_offset = anime_info
                
                mapping_list = anime.find('mapping-list')

                # Handle mapping list for Specials
                if mapping_list is not None:
                    for mapping in mapping_list.findall("mapping"):
                        if mapping.text is None:
                            continue

                        # Mapping values are usually like ;1-1;2-1;3-1;
                        for episode_ref in mapping.text.split(';'):
                            if not episode_ref:
                                continue

                            # One AniDB episode can be mapped to multiple TVDB episodes, in which case the string is 'n-x+y'
                            if '+' in episode_ref:
                                tvdb_episodes = episode_ref.split('-')[1].split('+')
                            else:
                                tvdb_episodes = [episode_ref.split('-')[1]]

                            logger.info(f"Comparing {tvdb_episodes} with {episode}")
                            for tvdb_episode in tvdb_episodes:
                                if int(tvdb_episode) == episode:
                                    anidb_id = int(anime.attrib.get('anidbid'))
                                    anidb_episode = int(episode_ref.split('-')[0])
                                    return anidb_id, anidb_episode, 0

                if episode > episode_offset:
                    anidb_id = int(anime.attrib.get('anidbid'))
                    offset = episode_offset

        return anidb_id, episode - offset, offset

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

        if episode_elements is None:
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
        return

    if refined_providers.intersection(settings.general.enabled_providers) and video.series_anidb_id is None:
        refine_anidb_ids(video)


def refine_anidb_ids(video):
    anidb_client = AniDBClient(settings.anidb.api_client, settings.anidb.api_client_ver)

    season = video.season if video.season else 0

    anidb_series_id, anidb_episode_no, anidb_season_episode_offset = anidb_client.get_show_information(
        video.series_tvdb_id,
        season,
        video.episode,
    )
    
    if not anidb_series_id:
        return video

    logger.debug(f'AniDB refinement identified {video.series} as {anidb_series_id}.')
    
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
        intersect = providers_requiring_anidb_api.intersection(settings.general.enabled_providers)
        if len(intersect) >= 1:
            logger.warn(f'AniDB API credentials are not fully set up, the following providers may not work: {intersect}')

    video.series_anidb_id = anidb_series_id
    video.series_anidb_episode_id = anidb_episode_id
    video.series_anidb_episode_no = anidb_episode_no
    video.series_anidb_season_episode_offset = anidb_season_episode_offset

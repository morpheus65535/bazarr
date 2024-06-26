# coding=utf-8
# fmt: off

import logging
import requests
from collections import namedtuple
from datetime import timedelta
from requests.exceptions import HTTPError

from app.config import settings
from subliminal import Episode, region
from subliminal_patch.exceptions import TooManyRequests

try:
    from lxml import etree
except ImportError:
    try:
        import xml.etree.cElementTree as etree
    except ImportError:
        import xml.etree.ElementTree as etree

refined_providers = {'animetosho'}

api_url = 'http://api.anidb.net:9001/httpapi'

cache_key = "anidb_refiner"

# Soft Limit for amount of requests per day
daily_limit_request_count = 200


class AniDBClient(object):
    def __init__(self, api_client_key=None, api_client_ver=1, session=None):
        self.session = session or requests.Session()
        self.api_client_key = api_client_key
        self.api_client_ver = api_client_ver
        self.cache = region.get(cache_key, expiration_time=timedelta(days=1).total_seconds())

    @property
    def is_throttled(self):
        return self.cache and self.cache.get('is_throttled')

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
    def get_series_id(self, mappings, tvdb_series_season, tvdb_series_id, episode):
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
            anidb_id = int(anime.attrib.get('anidbid'))
            if episode > episode_offset:
                anidb_id = anidb_id
                offset = episode_offset

        return anidb_id, episode - offset

    @region.cache_on_arguments(expiration_time=timedelta(days=1).total_seconds())
    def get_series_episodes_ids(self, tvdb_series_id, season, episode):
        mappings = etree.fromstring(self.get_series_mappings())

        series_id, episode_no = self.get_series_id(mappings, season, tvdb_series_id, episode)

        if not series_id:
            return None, None

        episodes = etree.fromstring(self.get_episodes(series_id))

        return series_id, int(episodes.find(f".//episode[epno='{episode_no}']").attrib.get('id'))

    @region.cache_on_arguments(expiration_time=timedelta(days=1).total_seconds())
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
            region.set(cache_key, {'daily_api_request_count': daily_quota})

            return

        self.cache['daily_api_request_count'] = daily_quota

        region.set(cache_key, self.cache)

    @staticmethod
    def mark_as_throttled():
        region.set(cache_key, {'is_throttled': True})


def refine_from_anidb(path, video):
    if not isinstance(video, Episode) or not video.series_tvdb_id:
        logging.debug(f'Video is not an Anime TV series, skipping refinement for {video}')

        return

    if refined_providers.intersection(settings.general.enabled_providers) and video.series_anidb_id is None:
        refine_anidb_ids(video)


def refine_anidb_ids(video):
    anidb_client = AniDBClient(settings.anidb.api_client, settings.anidb.api_client_ver)

    season = video.season if video.season else 0

    if anidb_client.is_throttled:
        logging.warning(f'API daily limit reached. Skipping refinement for {video.series}')

        return video

    try:
        anidb_series_id, anidb_episode_id = anidb_client.get_series_episodes_ids(
            video.series_tvdb_id,
            season, video.episode,
        )
    except TooManyRequests:
        logging.error(f'API daily limit reached while refining {video.series}')

        anidb_client.mark_as_throttled()

        return video

    if not anidb_episode_id:
        logging.error(f'Could not find anime series {video.series}')

        return video

    video.series_anidb_id = anidb_series_id
    video.series_anidb_episode_id = anidb_episode_id

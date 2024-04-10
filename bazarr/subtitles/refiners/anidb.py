# coding=utf-8
# fmt: off

import logging
import requests
from datetime import timedelta
from requests.exceptions import HTTPError

from app.config import settings
from subliminal import Episode, region

try:
    from lxml import etree
except ImportError:
    try:
        import xml.etree.cElementTree as etree
    except ImportError:
        import xml.etree.ElementTree as etree

refined_providers = {'animetosho'}

api_url = 'http://api.anidb.net:9001/httpapi'


class AniDBClient(object):
    def __init__(self, api_client_key=None, api_client_ver=1, session=None):
        self.session = session or requests.Session()
        self.api_client_key = api_client_key
        self.api_client_ver = api_client_ver

    @region.cache_on_arguments(expiration_time=timedelta(days=1).total_seconds())
    def get_series_mappings(self):
        r = self.session.get(
            'https://raw.githubusercontent.com/Anime-Lists/anime-lists/master/anime-list.xml',
            timeout=10
        )

        r.raise_for_status()

        return r.content

    @staticmethod
    @region.cache_on_arguments(expiration_time=timedelta(days=1).total_seconds())
    def get_series_id(mappings, tvdb_series_season, tvdb_series_id):
        anime = mappings.find(f".//anime[@tvdbid='{tvdb_series_id}'][@defaulttvdbseason='{tvdb_series_season}']")

        if not anime:
            return None

        return int(anime.attrib.get('anidbid'))

    @region.cache_on_arguments(expiration_time=timedelta(days=1).total_seconds())
    def get_series_episodes_ids(self, tvdb_series_id, season, episode):
        mappings = etree.fromstring(self.get_series_mappings())

        series_id = self.get_series_id(mappings, season, tvdb_series_id)

        if not series_id:
            return None, None

        episodes = etree.fromstring(self.get_episodes(series_id))

        return series_id, int(episodes.find(f".//episode[epno='{episode}']").attrib.get('id'))

    @region.cache_on_arguments(expiration_time=timedelta(days=1).total_seconds())
    def get_episodes(self, series_id):
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
            raise HTTPError('AniDB API Abuse detected. Banned status.')
        elif response_code == '302':
            raise HTTPError('AniDB API Client error. Client is disabled or does not exists.')

        episode_elements = xml_root.find('episodes')

        if not episode_elements:
            raise ValueError

        return etree.tostring(episode_elements, encoding='utf8', method='xml')


def refine_from_anidb(path, video):
    if refined_providers.intersection(settings.general.enabled_providers) and video.series_anidb_id is None:
        refine_anidb_ids(video)


def refine_anidb_ids(video):
    if not isinstance(video, Episode) and not video.series_tvdb_id:
        logging.debug(f'Video is not an Anime TV series, skipping refinement for {video}')

        return video

    anidb_client = AniDBClient(settings.anidb.api_client, settings.anidb.api_client_ver)

    season = video.season if video.season else 0

    anidb_series_id, anidb_episode_id = anidb_client.get_series_episodes_ids(video.series_tvdb_id, season, video.episode)

    if not anidb_episode_id:
        logging.error(f'Could not find anime series {video.series}')

        return video

    video.series_anidb_id = anidb_series_id
    video.series_anidb_episode_id = anidb_episode_id

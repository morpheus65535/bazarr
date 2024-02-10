# coding=utf-8
# fmt: off

import logging

from app.config import settings
from guessit import guessit
from sonarr.info import url_api_sonarr
from sonarr.sync.utils import get_history_from_sonarr_api
from subliminal import Movie

from utilities.path_mappings import path_mappings
from app.database import TableEpisodes, TableMovies, database, select
from utilities.video_analyzer import parse_video_metadata


def refine_from_sonarr(path, video):
    refine_info_url(video)


def refine_info_url(video):
    history = get_history_from_sonarr_api(settings.sonarr.apikey, video.sonarrEpisodeId)
    for grab in history['records']:
        if ('releaseGroup' in grab['data'] and grab['data']['releaseGroup'] == video.release_group
                and 'nzbInfoUrl' in grab['data'] and grab['data']['nzbInfoUrl']):
            video.info_url = grab['data']['nzbInfoUrl']
            logging.info(f'Refining {video} with Info URL: {video.info_url}')
            break

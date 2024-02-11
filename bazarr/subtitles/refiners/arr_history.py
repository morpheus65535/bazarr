# coding=utf-8
# fmt: off

import logging

from app.config import settings
from radarr.sync.utils import get_history_from_radarr_api
from sonarr.sync.utils import get_history_from_sonarr_api
from subliminal import Episode, Movie


def refine_from_arr_history(path, video):
    if 'avistaz' in settings.general.enabled_providers and video.info_url is None:
        refine_info_url(video)


def refine_info_url(video):
    if isinstance(video, Episode):
        history = get_history_from_sonarr_api(settings.sonarr.apikey, video.sonarrEpisodeId)
    else:
        history = get_history_from_radarr_api(settings.radarr.apikey, video.radarrId)

    for grab in history['records']:
        if ('releaseGroup' in grab['data'] and grab['data']['releaseGroup'] == video.release_group
                and 'nzbInfoUrl' in grab['data'] and grab['data']['nzbInfoUrl']):
            video.info_url = grab['data']['nzbInfoUrl']
            logging.debug(f'Refining {video} with Info URL: {video.info_url}')
            break

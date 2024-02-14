# coding=utf-8
# fmt: off

import logging

from app.config import settings
from radarr.sync.utils import get_history_from_radarr_api
from sonarr.sync.utils import get_history_from_sonarr_api
from subliminal import Episode, Movie

refined_providers = {'avistaz', 'cinemaz'}


def refine_from_arr_history(path, video):
    if refined_providers.intersection(settings.general.enabled_providers) and video.info_url is None:
        refine_info_url(video)


def refine_info_url(video):
    if isinstance(video, Episode) and video.sonarrEpisodeId:
        history = get_history_from_sonarr_api(settings.sonarr.apikey, video.sonarrEpisodeId)
    elif isinstance(video, Movie) and video.radarrId:
        history = get_history_from_radarr_api(settings.radarr.apikey, video.radarrId)
    else:
        return

    for grab in history['records']:
        # take the latest grab for the episode
        if 'nzbInfoUrl' in grab['data'] and grab['data']['nzbInfoUrl']:
            video.info_url = grab['data']['nzbInfoUrl']
            logging.debug(f'Refining {video} with Info URL: {video.info_url}')
            break

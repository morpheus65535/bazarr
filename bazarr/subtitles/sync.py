# coding=utf-8
# fmt: off

import logging
import gc

from app.config import settings
from subtitles.tools.subsyncer import SubSyncer


def sync_subtitles(video_path, srt_path, srt_lang, forced, percent_score, sonarr_series_id=None,
                   sonarr_episode_id=None, radarr_id=None):
    if forced:
        logging.debug('BAZARR cannot sync forced subtitles. Skipping sync routine.')
    elif not settings.subsync.use_subsync:
        logging.debug('BAZARR automatic syncing is disabled in settings. Skipping sync routine.')
    else:
        logging.debug(f'BAZARR automatic syncing is enabled in settings. We\'ll try to sync this '
                      f'subtitles: {srt_path}.')
        if sonarr_episode_id:
            use_subsync_threshold = settings.subsync.use_subsync_threshold
            subsync_threshold = settings.subsync.subsync_threshold
        else:
            use_subsync_threshold = settings.subsync.use_subsync_movie_threshold
            subsync_threshold = settings.subsync.subsync_movie_threshold

        if not use_subsync_threshold or (use_subsync_threshold and percent_score < float(subsync_threshold)):
            subsync = SubSyncer()
            sync_kwargs = {
                'video_path': video_path,
                'srt_path': srt_path,
                'srt_lang': srt_lang,
                'max_offset_seconds': str(settings.subsync.max_offset_seconds),
                'no_fix_framerate': settings.subsync.no_fix_framerate,
                'gss': settings.subsync.gss,
                'reference': None,  # means choose automatically within video file
                'sonarr_series_id': sonarr_series_id,
                'sonarr_episode_id': sonarr_episode_id,
                'radarr_id': radarr_id,
            }
            subsync.sync(**sync_kwargs)
            del subsync
            gc.collect()
            return True
        else:
            logging.debug(f"BAZARR subsync skipped because subtitles score isn't below this "
                          f"threshold value: {subsync_threshold}%")
    return False

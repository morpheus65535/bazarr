# coding=utf-8
# fmt: off

import logging
import gc
import os

from app.config import settings
from app.event_handler import show_progress, hide_progress
from subtitles.tools.subsyncer import SubSyncer


def sync_subtitles(video_path, srt_path, srt_lang, forced, hi, percent_score, sonarr_series_id=None,
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
                'forced': forced,
                'hi': hi,
                'max_offset_seconds': str(settings.subsync.max_offset_seconds),
                'no_fix_framerate': settings.subsync.no_fix_framerate,
                'gss': settings.subsync.gss,
                'reference': None,  # means choose automatically within video file
                'sonarr_series_id': sonarr_series_id,
                'sonarr_episode_id': sonarr_episode_id,
                'radarr_id': radarr_id,
            }
            subtitles_filename = os.path.basename(srt_path)
            show_progress(id=f'subsync_{subtitles_filename}',
                          header='Syncing Subtitle',
                          name=srt_path,
                          value=0,
                          count=1)
            try:
                subsync.sync(**sync_kwargs)
            except Exception:
                hide_progress(id=f'subsync_{subtitles_filename}')
            else:
                show_progress(id=f'subsync_{subtitles_filename}',
                              header='Syncing Subtitle',
                              name=srt_path,
                              value=1,
                              count=1)
            del subsync
            gc.collect()
            return True
        else:
            logging.debug(f"BAZARR subsync skipped because subtitles score isn't below this "
                          f"threshold value: {subsync_threshold}%")
    return False

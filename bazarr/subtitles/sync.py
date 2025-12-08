# coding=utf-8
# fmt: off

import logging
import gc

from app.config import settings
from app.jobs_queue import jobs_queue
from subtitles.tools.subsyncer import SubSyncer


def sync_subtitles(video_path,
                   srt_path,
                   srt_lang,
                   forced,
                   hi,
                   percent_score,
                   sonarr_series_id=None,
                   sonarr_episode_id=None,
                   radarr_id=None,
                   job_id=None,
                   max_offset_seconds=str(settings.subsync.max_offset_seconds),
                   gss=settings.subsync.gss,
                   no_fix_framerate=settings.subsync.no_fix_framerate,
                   reference=None,
                   force_sync=False,
                   job_sub_function=False):
    if not settings.subsync.use_subsync and not force_sync:
        logging.debug('BAZARR automatic syncing is disabled in settings. Skipping sync routine.')
        return False

    if not job_id:
        jobs_queue.add_job_from_function("Syncing Subtitle", is_progress=True)
        return False

    if job_sub_function:
        jobs_queue.update_job_progress_status(job_id=job_id, is_progress=True)

    jobs_queue.update_job_progress(job_id=job_id, progress_message=f"Syncing {srt_path}")

    if forced:
        logging.debug('BAZARR cannot sync forced subtitles. Skipping sync routine.')
    else:
        logging.debug(f'BAZARR automatic syncing is enabled in settings. We\'ll try to sync this '
                      f'subtitles: {srt_path}.')
        if sonarr_episode_id:
            use_subsync_threshold = settings.subsync.use_subsync_threshold
            subsync_threshold = settings.subsync.subsync_threshold
        else:
            use_subsync_threshold = settings.subsync.use_subsync_movie_threshold
            subsync_threshold = settings.subsync.subsync_movie_threshold

        if not use_subsync_threshold or (use_subsync_threshold and percent_score <= float(subsync_threshold)):
            subsync = SubSyncer()
            sync_kwargs = {
                'video_path': video_path,
                'srt_path': srt_path,
                'srt_lang': srt_lang,
                'forced': forced,
                'hi': hi,
                'max_offset_seconds': max_offset_seconds,
                'no_fix_framerate': no_fix_framerate,
                'gss': gss,
                'reference': reference,
                'sonarr_series_id': sonarr_series_id,
                'sonarr_episode_id': sonarr_episode_id,
                'radarr_id': radarr_id,
                'progress_callback': lambda x: jobs_queue.update_job_progress(job_id=x['job_id'],
                                                                              progress_value=x['value'],
                                                                              progress_max=x['count'],
                                                                              progress_message=f"Syncing {srt_path}"),
                'job_id': job_id,
                'force_sync': force_sync,
            }
            try:
                subsync.sync(**sync_kwargs)
            except Exception:
                logging.exception(f'BAZARR an unhandled exception occurs during the synchronization process for this '
                                  f'subtitle file: {srt_path}')
                return False
            else:
                jobs_queue.update_job_progress(job_id=job_id, progress_value="max")
                return True
            finally:
                del subsync
                gc.collect()
        else:
            logging.debug(f"BAZARR subsync skipped because subtitles score isn't below this "
                          f"threshold value: {subsync_threshold}%")

    jobs_queue.update_job_progress(job_id=job_id, progress_value="max")
    return False

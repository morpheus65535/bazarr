# coding=utf-8
from __future__ import absolute_import

from collections import defaultdict
import logging
import time

from subliminal.core import check_video

logger = logging.getLogger(__name__)

# list_all_subtitles, list_supported_languages, list_supported_video_types, download_subtitles, download_best_subtitles
def list_all_subtitles(videos, languages, pool_instance):
    listed_subtitles = defaultdict(list)

    # return immediatly if no video passed the checks
    if not videos:
        return listed_subtitles

    for video in videos:
        logger.info("Listing subtitles for %r", video)
        subtitles = pool_instance.list_subtitles(
            video, languages - video.subtitle_languages
        )
        listed_subtitles[video].extend(subtitles)
        logger.info("Found %d subtitle(s)", len(subtitles))

    return listed_subtitles


def list_supported_languages(pool_instance):
    return pool_instance.list_supported_languages()


def list_supported_video_types(pool_instance):
    return pool_instance.list_supported_video_types()


def download_subtitles(subtitles, pool_instance):
    for subtitle in subtitles:
        logger.info("Downloading subtitle %r with score %s", subtitle, subtitle.score)
        pool_instance.download_subtitle(subtitle)


def download_best_subtitles(
    videos,
    languages,
    pool_instance,
    min_score=0,
    hearing_impaired=False,
    only_one=False,
    compute_score=None,
    throttle_time=0,
    score_obj=None,
):
    downloaded_subtitles = defaultdict(list)

    # check videos
    checked_videos = []
    for video in videos:
        if not check_video(video, languages=languages, undefined=only_one):
            logger.info("Skipping video %r", video)
            continue
        checked_videos.append(video)

    # return immediately if no video passed the checks
    if not checked_videos:
        return downloaded_subtitles

    got_multiple = len(checked_videos) > 1

    # download best subtitles
    for video in checked_videos:
        logger.info("Downloading best subtitles for %r", video)
        subtitles = pool_instance.download_best_subtitles(
            pool_instance.list_subtitles(video, languages - video.subtitle_languages),
            video,
            languages,
            min_score=min_score,
            hearing_impaired=hearing_impaired,
            only_one=only_one,
            compute_score=compute_score,
            score_obj=score_obj,
        )
        logger.info("Downloaded %d subtitle(s)", len(subtitles))
        downloaded_subtitles[video].extend(subtitles)

        if got_multiple and throttle_time:
            logger.debug("Waiting %ss before continuing ...", throttle_time)
            time.sleep(throttle_time)

    return downloaded_subtitles

# coding=utf-8
# fmt: off

import logging
import operator
import gc

from functools import reduce

from utilities.path_mappings import path_mappings
from subtitles.indexer.series import store_subtitles, list_missing_subtitles
from sonarr.history import history_log
from app.notifier import send_notifications
from app.get_providers import get_providers
from app.database import get_exclusion_clause, get_audio_profile_languages, TableShows, TableEpisodes, database, \
    update, select, get_subtitles
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue
from app.config import settings

from ..adaptive_searching import is_search_active, updateFailedAttempts
from ..download import generate_subtitles
from ..language_utils import (
    build_search_payload,
    format_episode_part,
    has_unindexed_external_subtitle,
    resolve_audio_language,
    stamp_failed_attempts,
)


def _wanted_episode(episode, providers_list, job_id=None):
    audio_language_list = get_audio_profile_languages(episode.audio_language)
    audio_language = resolve_audio_language(audio_language_list)

    def _include_language(canonical_language):
        active = is_search_active(desired_language=canonical_language, attempt_string=episode.failedAttempts)
        if not active:
            logging.debug(
                f"BAZARR Search is throttled by adaptive search for this episode {episode.path} and "
                f"language: {canonical_language}"
            )
        return active

    languages, languages_to_stamp = build_search_payload(
        episode.missing_subtitles,
        "wanted episode search",
        include_predicate=_include_language,
    )

    if not episode.path:
        logging.debug("BAZARR wanted episode search skipped because episode path is missing: %s", episode.sonarrEpisodeId)
        return

    def _persist_failed_attempts(updated):
        database.execute(
            update(TableEpisodes)
            .values(failedAttempts=updated)
            .where(TableEpisodes.sonarrEpisodeId == episode.sonarrEpisodeId)
        )

    found_any = False
    for result in generate_subtitles(path_mappings.path_replace(episode.path),
                                     languages,
                                     audio_language,
                                     episode.sceneName,
                                     episode.title,
                                     'series',
                                     episode.profileId,
                                     check_if_still_required=True,
                                     job_id=job_id,
                                     fallback_allowed=settings.general.use_whisper_fallback):
        if result:
            found_any = True
            if isinstance(result, tuple) and len(result):
                result = result[0]
            store_subtitles(episode.sonarrEpisodeId)
            history_log(1, episode.sonarrSeriesId, episode.sonarrEpisodeId, result)
            if hasattr(result, 'message'):
                send_notifications(episode.sonarrSeriesId, episode.sonarrEpisodeId, result.message)
            event_stream(type='series', action='update', payload=episode.sonarrSeriesId)
            event_stream(type='episode-wanted', action='delete', payload=episode.sonarrEpisodeId)

    if not found_any and providers_list:
        stamp_failed_attempts(
            languages_to_stamp,
            episode.failedAttempts or '[]',
            update_fn=updateFailedAttempts,
            persist_fn=_persist_failed_attempts,
        )


def wanted_download_subtitles(sonarr_episode_id, job_id=None):
    stmt = select(TableEpisodes.path,
                  TableEpisodes.missing_subtitles,
                  TableEpisodes.sonarrEpisodeId,
                  TableEpisodes.sonarrSeriesId,
                  TableEpisodes.audio_language,
                  TableEpisodes.sceneName,
                  TableEpisodes.failedAttempts,
                  TableShows.title,
                  TableShows.profileId) \
        .select_from(TableEpisodes) \
        .join(TableShows) \
        .where((TableEpisodes.sonarrEpisodeId == sonarr_episode_id))
    episode_details = database.execute(stmt).first()

    previously_indexed_subtitles = get_subtitles(sonarr_episode_id=sonarr_episode_id) or []

    if not episode_details:
        logging.debug(f"BAZARR no episode with that sonarrId can be found in database: {sonarr_episode_id}")
        return
    elif not previously_indexed_subtitles or has_unindexed_external_subtitle(previously_indexed_subtitles):
        # subtitles indexing for this episode might be incomplete, we'll do it again
        store_subtitles(sonarr_episode_id)
        episode_details = database.execute(stmt).first()
        if not episode_details:
            logging.debug(f"BAZARR no episode with that sonarrId can be found in database after subtitles refresh: {sonarr_episode_id}")
            return
    elif episode_details.missing_subtitles is None:
        # missing subtitles calculation for this episode is incomplete, we'll do it again
        list_missing_subtitles(epno=sonarr_episode_id)
        episode_details = database.execute(stmt).first()
        if not episode_details:
            logging.debug(f"BAZARR no episode with that sonarrId can be found in database after missing-subtitles refresh: {sonarr_episode_id}")
            return

    providers_list = get_providers()

    if providers_list:
        _wanted_episode(episode_details, providers_list, job_id=job_id)
    else:
        logging.info("BAZARR All providers are throttled")


def wanted_search_missing_subtitles_series(job_id=None, wait_for_completion=False):
    if not job_id:
        jobs_queue.add_job_from_function("Searching for missing series subtitles", is_progress=True,
                                         wait_for_completion=wait_for_completion)
        return

    conditions = [(TableEpisodes.missing_subtitles.is_not(None)),
                  (TableEpisodes.missing_subtitles != '[]')]
    conditions += get_exclusion_clause('series')
    episodes = database.execute(
        select(TableEpisodes.sonarrSeriesId,
               TableEpisodes.sonarrEpisodeId,
               TableShows.tags,
               TableEpisodes.monitored,
               TableShows.title,
               TableEpisodes.season,
               TableEpisodes.episode,
               TableEpisodes.title.label('episodeTitle'),
               TableShows.seriesType)
        .select_from(TableEpisodes)
        .join(TableShows)
        .where(reduce(operator.and_, conditions))) \
        .all()

    count_episodes = len(episodes)
    jobs_queue.update_job_progress(job_id=job_id, progress_max=count_episodes)

    if count_episodes == 0:
        jobs_queue.update_job_progress(job_id=job_id, progress_value='max')

    throttled = False
    for i, episode in enumerate(episodes, start=1):
        season_part = format_episode_part(episode.season)
        episode_part = format_episode_part(episode.episode)
        jobs_queue.update_job_progress(job_id=job_id, progress_value=i,
                                       progress_message=f'{episode.title} - S{season_part}E{episode_part}'
                                                        f' - {episode.episodeTitle}')

        providers = get_providers()
        if providers:
            wanted_download_subtitles(episode.sonarrEpisodeId, job_id=job_id)

            # make sure to override the progress value updated by the subtitles synchronization
            jobs_queue.update_job_progress(job_id=job_id, progress_value=i, progress_max=count_episodes)
        else:
            logging.info("BAZARR All providers are throttled")
            throttled = True
            break

    outcome_msg = ("All providers throttled" if throttled
                   else "Search completed")
    jobs_queue.update_job_progress(job_id=job_id, progress_message=outcome_msg)
    jobs_queue.update_job_name(job_id=job_id, new_job_name="Searched for missing series subtitles")
    logging.info('BAZARR Finished searching for missing Series Subtitles. Check History for more information.')

    gc.collect()

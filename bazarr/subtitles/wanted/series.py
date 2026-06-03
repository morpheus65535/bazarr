# coding=utf-8
# fmt: off

import logging
import operator

from functools import reduce

from sqlalchemy import bindparam

from utilities.path_mappings import path_mappings
from subtitles.indexer.series import store_subtitles
from subtitles.indexer.series import list_missing_subtitles
from sonarr.history import history_log
from app.notifier import send_notifications
from app.get_providers import get_providers
from app.database import get_exclusion_clause, get_audio_profile_languages, TableShows, TableEpisodes, \
    TableEpisodesSubtitles, database, update, select, get_subtitles
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue
from app.config import settings

from ..adaptive_searching import get_adaptive_search_policy, update_failed_attempts
from ..download import generate_subtitles
from ..language_utils import format_episode_part, has_unindexed_external_subtitle, resolve_audio_language
from .utils import get_due_missing_languages, get_language_search_items


_WANTED_EPISODE_DETAILS_SELECT = select(TableEpisodes.path,
                                        TableEpisodes.missing_subtitles,
                                        TableEpisodes.sonarrEpisodeId,
                                        TableEpisodes.sonarrSeriesId,
                                        TableEpisodes.audio_language,
                                        TableEpisodes.sceneName,
                                        TableEpisodes.failedAttempts,
                                        TableShows.title,
                                        TableShows.profileId,
                                        TableEpisodes.season,
                                        TableEpisodes.episode,
                                        TableEpisodes.title.label('episodeTitle'),
                                        select(TableEpisodesSubtitles.id)
                                        .where(TableEpisodesSubtitles.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId)
                                        .limit(1)
                                        .exists()
                                        .label("has_indexed_subtitles"),
                                        select(TableEpisodesSubtitles.id)
                                        .where(TableEpisodesSubtitles.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId)
                                        .where(TableEpisodesSubtitles.path.is_(None))
                                        .where(TableEpisodesSubtitles.embedded_track_id.is_(None))
                                        .limit(1)
                                        .exists()
                                        .label("has_incomplete_embedded_subtitles")) \
    .select_from(TableEpisodes) \
    .join(TableShows)
_WANTED_EPISODE_DETAILS_STMT = _WANTED_EPISODE_DETAILS_SELECT \
    .where(TableEpisodes.sonarrEpisodeId == bindparam("wanted_sonarr_episode_id"))


def _episode_needs_wanted_lookup_refresh(episode):
    return (
        episode.missing_subtitles is None or
        not getattr(episode, "has_indexed_subtitles", True) or
        getattr(episode, "has_incomplete_embedded_subtitles", False)
    )


def _wanted_episode(episode, providers_list, due_languages=None, job_id=None, adaptive_search_policy=None,
                    fallback_allowed=None):
    audio_language_list = get_audio_profile_languages(episode.audio_language)
    audio_language = resolve_audio_language(audio_language_list)

    due_missing_languages = due_languages
    if due_missing_languages is None:
        due_missing_languages = get_due_missing_languages(
            episode.missing_subtitles,
            episode.failedAttempts,
            adaptive_search_policy=adaptive_search_policy,
        )
    if not due_missing_languages:
        return
    if not episode.path:
        logging.debug("BAZARR wanted episode search skipped because episode path is missing: %s", episode.sonarrEpisodeId)
        return

    if fallback_allowed is None:
        fallback_allowed = settings.general.use_whisper_fallback

    languages = get_language_search_items(due_missing_languages)

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
                                     fallback_allowed=fallback_allowed):
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
        database.execute(
            update(TableEpisodes)
            .values(failedAttempts=update_failed_attempts(due_missing_languages, episode.failedAttempts))
            .where(TableEpisodes.sonarrEpisodeId == episode.sonarrEpisodeId))


def wanted_download_subtitles(
    sonarr_episode_id,
    job_id=None,
    providers_list=None,
    episode_details=None,
    due_languages=None,
    adaptive_search_policy=None,
    fallback_allowed=None,
):
    stmt_params = {"wanted_sonarr_episode_id": sonarr_episode_id}

    if episode_details is not None and due_languages is not None and not _episode_needs_wanted_lookup_refresh(episode_details):
        if providers_list is None:
            providers_list = get_providers()
        if adaptive_search_policy is None:
            adaptive_search_policy = get_adaptive_search_policy()
        if providers_list:
            _wanted_episode(
                episode_details,
                providers_list,
                due_languages=due_languages,
                job_id=job_id,
                adaptive_search_policy=adaptive_search_policy,
                fallback_allowed=fallback_allowed,
            )
        else:
            logging.info("BAZARR All providers are throttled")
        return

    if episode_details is None:
        episode_details = database.execute(_WANTED_EPISODE_DETAILS_STMT, stmt_params).first()

    if not episode_details:
        logging.debug(f"BAZARR no episode with that sonarrId can be found in database: {sonarr_episode_id}")
        return
    if _episode_needs_wanted_lookup_refresh(episode_details):
        previously_indexed_subtitles = get_subtitles(sonarr_episode_id=sonarr_episode_id) or []
        if not previously_indexed_subtitles or has_unindexed_external_subtitle(previously_indexed_subtitles):
            # subtitles indexing for this episode might be incomplete, we'll do it again
            store_subtitles(sonarr_episode_id)
            episode_details = database.execute(_WANTED_EPISODE_DETAILS_STMT, stmt_params).first()
            if not episode_details:
                logging.debug(f"BAZARR no episode with that sonarrId can be found in database after subtitles refresh: {sonarr_episode_id}")
                return
        if episode_details.missing_subtitles is None:
            # missing subtitles calculation for this episode is incomplete, we'll do it again
            list_missing_subtitles(epno=sonarr_episode_id)
        episode_details = database.execute(_WANTED_EPISODE_DETAILS_STMT, stmt_params).first()
        if not episode_details:
            logging.debug(f"BAZARR no episode with that sonarrId can be found in database after missing-subtitles refresh: {sonarr_episode_id}")
            return
        due_languages = None
        providers_list = None

    if providers_list is None:
        providers_list = get_providers()
    if adaptive_search_policy is None:
        adaptive_search_policy = get_adaptive_search_policy()

    if providers_list:
        _wanted_episode(
            episode_details,
            providers_list,
            due_languages=due_languages,
            job_id=job_id,
            adaptive_search_policy=adaptive_search_policy,
            fallback_allowed=fallback_allowed,
        )
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
    adaptive_search_policy = get_adaptive_search_policy()

    episodes = database.execute(
        _WANTED_EPISODE_DETAILS_SELECT
        .where(reduce(operator.and_, conditions))) \
        .all()

    episodes_to_search = []
    fallback_allowed = settings.general.use_whisper_fallback
    for episode in episodes:
        due_languages = get_due_missing_languages(
            episode.missing_subtitles,
            episode.failedAttempts,
            adaptive_search_policy=adaptive_search_policy,
        )
        if due_languages:
            episodes_to_search.append((episode, due_languages))

    count_episodes = len(episodes_to_search)
    jobs_queue.update_job_progress(job_id=job_id, progress_max=count_episodes)

    if count_episodes == 0:
        jobs_queue.update_job_progress(job_id=job_id, progress_value='max')
        throttled = False
    else:
        throttled = False

    for i, (episode, due_languages) in enumerate(episodes_to_search, start=1):
        season_part = format_episode_part(episode.season)
        episode_part = format_episode_part(episode.episode)
        jobs_queue.update_job_progress(job_id=job_id, progress_value=i,
                                       progress_message=f'{episode.title} - S{season_part}E{episode_part}'
                                                         f' - {episode.episodeTitle}')

        providers = get_providers()
        if providers:
            if _episode_needs_wanted_lookup_refresh(episode):
                wanted_download_subtitles(
                    episode.sonarrEpisodeId,
                    job_id=job_id,
                    providers_list=providers,
                    episode_details=episode,
                    adaptive_search_policy=adaptive_search_policy,
                    fallback_allowed=fallback_allowed,
                )
            else:
                _wanted_episode(
                    episode,
                    providers,
                    due_languages=due_languages,
                    job_id=job_id,
                    adaptive_search_policy=adaptive_search_policy,
                    fallback_allowed=fallback_allowed,
                )

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

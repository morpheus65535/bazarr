# coding=utf-8
# fmt: off

import logging
import operator
import os

from functools import reduce

from utilities.path_mappings import path_mappings
from subtitles.indexer.series import store_subtitles, list_missing_subtitles
from sonarr.history import history_log
from app.notifier import send_notifications
from app.get_providers import get_providers
from app.database import (get_exclusion_clause, get_audio_profile_languages, TableShows, TableEpisodes,
                          TableMissingSubtitles, database, select, get_profile_id, get_subtitles)
from app.jobs_queue import jobs_queue
from app.event_handler import event_stream
from app.config import settings

from ..download import generate_subtitles
from ..language_utils import format_episode_part, has_unindexed_external_subtitle, resolve_audio_language
from ..serialization import missing_subtitle_to_language_tuple
from ..wanted_state import get_missing_languages, get_missing_languages_map


def series_download_subtitles(no, job_id=None, job_sub_function=False):
    if not job_sub_function and not job_id:
        jobs_queue.add_job_from_function(f"""Downloading missing subtitles for {database.scalar(
            select(TableShows.title).where(TableShows.sonarrSeriesId == no)) or 'Unknown Series'}""", is_progress=True)
        return

    series_row = database.execute(
        select(TableShows.path,
               TableShows.title)
        .where(TableShows.sonarrSeriesId == no))\
        .first()

    if not series_row:
        logging.debug(f"BAZARR no series with that sonarrSeriesId can be found in database: {no}")
        jobs_queue.update_job_progress(job_id=job_id, progress_message="Series not found in database.")
        return

    if series_row and not os.path.exists(path_mappings.path_replace(series_row.path)):
        raise OSError

    conditions = [(TableEpisodes.sonarrSeriesId == no),
                  select(TableMissingSubtitles.id)
                  .where(TableMissingSubtitles.media_type == 'series')
                  .where(TableMissingSubtitles.media_id == TableEpisodes.sonarrEpisodeId)
                  .exists()]
    conditions += get_exclusion_clause('series')
    episodes_details = database.execute(
        select(TableEpisodes.sonarrEpisodeId,
               TableShows.title,
               TableEpisodes.season,
               TableEpisodes.episode,
               TableEpisodes.title.label('episodeTitle'))
        .select_from(TableEpisodes)
        .join(TableShows)
        .where(reduce(operator.and_, conditions))) \
        .all()
    throttled = False
    if not episodes_details:
        logging.debug(f"BAZARR no episode for that sonarrSeriesId have been found in database or they have all been "
                      f"ignored because of monitored status, series type or series tags: {no}")
    else:
        count_episodes_details = len(episodes_details)
        missing_languages_by_episode = get_missing_languages_map(
            'series',
            [episode.sonarrEpisodeId for episode in episodes_details],
        )

        jobs_queue.update_job_progress(job_id=job_id, progress_max=count_episodes_details)
        for i, episode in enumerate(episodes_details, start=1):
            season_part = format_episode_part(episode.season)
            episode_part = format_episode_part(episode.episode)
            jobs_queue.update_job_progress(job_id=job_id, progress_value=i,
                                           progress_message=f'{episode.title} - S{season_part}E'
                                                            f'{episode_part} - {episode.episodeTitle}')

            providers_list = get_providers()
            fallback_allowed = settings.general.use_whisper_fallback and settings.general.use_whisper_fallback_series
            if providers_list:
                episode_download_subtitles(no=episode.sonarrEpisodeId, job_id=job_id, job_sub_function=True,
                                           providers_list=providers_list, fallback_allowed=fallback_allowed,
                                           missing_languages=missing_languages_by_episode[episode.sonarrEpisodeId])
            else:
                jobs_queue.update_job_progress(job_id=job_id, progress_value=count_episodes_details)
                logging.info("BAZARR All providers are throttled")
                throttled = True
                break

    outcome_msg = ("All providers throttled" if throttled
                   else "Search completed")
    jobs_queue.update_job_progress(job_id=job_id, progress_message=outcome_msg)
    jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Downloaded missing subtitles for {series_row.title}")


def episode_download_subtitles(no, job_id=None, job_sub_function=False, providers_list=None, fallback_allowed=False,
                               missing_languages=None):
    if not job_sub_function and not job_id:
        jobs_queue.add_job_from_function(f"""Downloading missing subtitles for {database.scalar(
            select(TableShows.title).where(TableShows.sonarrSeriesId == no)) or 'Unknown Series'}""", is_progress=True)
        return

    conditions = [(TableEpisodes.sonarrEpisodeId == no)]
    conditions += get_exclusion_clause('series')
    stmt = select(TableEpisodes.path,
                  TableEpisodes.missing_subtitles,
                  TableEpisodes.monitored,
                  TableEpisodes.sonarrEpisodeId,
                  TableEpisodes.sceneName,
                  TableShows.tags,
                  TableShows.title,
                  TableShows.sonarrSeriesId,
                  TableEpisodes.audio_language,
                  TableShows.seriesType,
                  TableEpisodes.title.label('episodeTitle'),
                  TableEpisodes.season,
                  TableEpisodes.episode,
                  TableShows.profileId) \
        .select_from(TableEpisodes) \
        .join(TableShows) \
        .where(reduce(operator.and_, conditions))
    episode = database.execute(stmt).first()

    if not episode:
        logging.debug("BAZARR no episode with that sonarrEpisodeId can be found in database:", str(no))
        jobs_queue.update_job_progress(job_id=job_id, progress_message="Episode not found in database.")
        return

    previously_indexed_subtitles = get_subtitles(sonarr_episode_id=episode.sonarrEpisodeId) or []
    if not previously_indexed_subtitles or has_unindexed_external_subtitle(previously_indexed_subtitles):
        # subtitles indexing for this episode might be incomplete, we'll do it again
        store_subtitles(episode.sonarrEpisodeId)
        missing_languages = None
        episode = database.execute(stmt).first()
        if not episode:
            logging.debug(f"BAZARR no episode with that sonarrEpisodeId can be found in database after subtitles refresh: {no}")
            jobs_queue.update_job_progress(job_id=job_id, progress_message="Episode not found in database.")
            return
    if episode.missing_subtitles is None:
        # missing subtitles calculation for this episode is incomplete, we'll do it again
        list_missing_subtitles(epno=no)
        missing_languages = None
        episode = database.execute(stmt).first()
        if not episode:
            logging.debug(f"BAZARR no episode with that sonarrEpisodeId can be found in database after missing-subtitles refresh: {no}")
            jobs_queue.update_job_progress(job_id=job_id, progress_message="Episode not found in database.")
            return

    episodePath = path_mappings.path_replace(episode.path)

    if not os.path.exists(episodePath):
        logging.debug(f"BAZARR episode file not found. Path mapping issue?: {episodePath}")
        jobs_queue.update_job_progress(job_id=job_id, progress_message=f"Episode path doesn't exists: {episodePath}")
        raise OSError

    if not providers_list:
        providers_list = get_providers()

    downloaded_count = 0
    if providers_list:
        audio_language_list = get_audio_profile_languages(episode.audio_language)
        audio_language = resolve_audio_language(audio_language_list)

        languages = []

        if not job_sub_function and job_id:
            season_part = format_episode_part(episode.season)
            episode_part = format_episode_part(episode.episode)
            jobs_queue.update_job_progress(job_id=job_id, progress_max=1,
                                           progress_message=f'{episode.title} - S{season_part}E'
                                                            f'{episode_part} - {episode.episodeTitle}')

        if missing_languages is None:
            missing_languages = get_missing_languages('series', episode.sonarrEpisodeId)

        for language in missing_languages:
            languages.append(missing_subtitle_to_language_tuple(language))

        if languages:
            for result in generate_subtitles(episodePath,
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
                    if isinstance(result, tuple) and len(result):
                        result = result[0]
                    store_subtitles(episode.sonarrEpisodeId)
                    history_log(1, episode.sonarrSeriesId, episode.sonarrEpisodeId, result)
                    if hasattr(result, 'message'):
                        send_notifications(episode.sonarrSeriesId, episode.sonarrEpisodeId, result.message)
                    downloaded_count += 1
        outcome_msg = (f"{downloaded_count} subtitle(s) downloaded"
                       if downloaded_count else "No subtitles found")
    else:
        logging.info("BAZARR All providers are throttled")
        outcome_msg = "All providers throttled"

    if not job_sub_function and job_id:
        jobs_queue.update_job_progress(job_id=job_id, progress_value='max',
                                       progress_message=outcome_msg)
        jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Downloaded missing subtitles for {episode.title}")


def episode_download_specific_subtitles(sonarr_series_id, sonarr_episode_id, language, hi, forced, job_id=None):
    if not job_id:
        return jobs_queue.add_job_from_function("Searching subtitles", progress_max=1, is_progress=False)

    episodeInfo = database.execute(
        select(TableEpisodes.path,
               TableEpisodes.sceneName,
               TableEpisodes.audio_language,
               TableEpisodes.season,
               TableEpisodes.episode,
               TableEpisodes.title.label("episodeTitle"),
               TableShows.title)
        .select_from(TableEpisodes)
        .join(TableShows)
        .where(TableEpisodes.sonarrEpisodeId == sonarr_episode_id)) \
        .first()

    if not episodeInfo:
        return 'Episode not found', 404

    episodePath = path_mappings.path_replace(episodeInfo.path)

    if not os.path.exists(episodePath):
        return 'Episode file not found. Path mapping issue?', 500

    sceneName = episodeInfo.sceneName

    title = episodeInfo.title

    season_part = format_episode_part(episodeInfo.season)
    episode_part = format_episode_part(episodeInfo.episode)
    episode_long_title = f'{title} - S{season_part}E{episode_part} - {episodeInfo.episodeTitle}'

    if hi == 'True':
        language_str = f'{language}:hi'
    elif forced == 'True':
        language_str = f'{language}:forced'
    else:
        language_str = language

    jobs_queue.update_job_name(job_id=job_id,
                               new_job_name=f"Searching {language_str.upper()} for {episode_long_title}")

    audio_language = resolve_audio_language(get_audio_profile_languages(episodeInfo.audio_language), fallback=None)

    try:
        result = list(generate_subtitles(episodePath, [(language, hi, forced)], audio_language, sceneName,
                                         title, 'series', profile_id=get_profile_id(episode_id=sonarr_episode_id),
                                         job_id=job_id))
        if isinstance(result, list) and len(result):
            result = result[0]
            if isinstance(result, tuple) and len(result):
                result = result[0]
            store_subtitles(sonarr_episode_id)
            history_log(1, sonarr_series_id, sonarr_episode_id, result)
            if hasattr(result, 'message'):
                send_notifications(sonarr_series_id, sonarr_episode_id, result.message)
        else:
            event_stream(type='episode', payload=sonarr_episode_id)
            return '', 204
    except OSError:
        return 'Unable to save subtitles file. Permission or path mapping issue?', 409
    else:
        jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Searched {language_str.upper()} for {episode_long_title}")
        return '', 204

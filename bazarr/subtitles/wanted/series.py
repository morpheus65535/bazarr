# coding=utf-8
# fmt: off

import ast
import logging
import operator

from functools import reduce

from utilities.path_mappings import path_mappings
from subtitles.indexer.series import store_subtitles, list_missing_subtitles
from subtitles.indexer.series import store_subtitles
from sonarr.history import history_log
from app.notifier import send_notifications
from app.get_providers import get_providers
from app.database import get_exclusion_clause, get_audio_profile_languages, TableShows, TableEpisodes, database, \
    update, select
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue

from ..adaptive_searching import is_search_active, updateFailedAttempts
from ..download import generate_subtitles


def _wanted_episode(episode, job_id=None):
    audio_language_list = get_audio_profile_languages(episode.audio_language)
    if len(audio_language_list) > 0:
        audio_language = audio_language_list[0]['name']
    else:
        audio_language = 'None'

    languages = []
    for language in ast.literal_eval(episode.missing_subtitles):
        if is_search_active(desired_language=language, attempt_string=episode.failedAttempts):
            database.execute(
                update(TableEpisodes)
                .values(failedAttempts=updateFailedAttempts(desired_language=language,
                                                            attempt_string=episode.failedAttempts))
                .where(TableEpisodes.sonarrEpisodeId == episode.sonarrEpisodeId))

            hi_ = "True" if language.endswith(':hi') else "False"
            forced_ = "True" if language.endswith(':forced') else "False"
            languages.append((language.split(":")[0], hi_, forced_))

        else:
            logging.debug(
                f"BAZARR Search is throttled by adaptive search for this episode {episode.path} and "
                f"language: {language}")

    for result in generate_subtitles(path_mappings.path_replace(episode.path),
                                     languages,
                                     audio_language,
                                     str(episode.sceneName),
                                     episode.title,
                                     'series',
                                     episode.profileId,
                                     check_if_still_required=True,
                                     job_id=job_id):
        if result:
            if isinstance(result, tuple) and len(result):
                result = result[0]
            store_subtitles(episode.path, path_mappings.path_replace(episode.path))
            history_log(1, episode.sonarrSeriesId, episode.sonarrEpisodeId, result)
            event_stream(type='series', action='update', payload=episode.sonarrSeriesId)
            event_stream(type='episode-wanted', action='delete', payload=episode.sonarrEpisodeId)
            send_notifications(episode.sonarrSeriesId, episode.sonarrEpisodeId, result.message)


def wanted_download_subtitles(sonarr_episode_id, job_id=None):
    stmt = select(TableEpisodes.path,
                  TableEpisodes.missing_subtitles,
                  TableEpisodes.sonarrEpisodeId,
                  TableEpisodes.sonarrSeriesId,
                  TableEpisodes.audio_language,
                  TableEpisodes.sceneName,
                  TableEpisodes.failedAttempts,
                  TableShows.title,
                  TableShows.profileId,
                  TableEpisodes.subtitles) \
        .select_from(TableEpisodes) \
        .join(TableShows) \
        .where((TableEpisodes.sonarrEpisodeId == sonarr_episode_id))
    episode_details = database.execute(stmt).first()

    if not episode_details:
        logging.debug(f"BAZARR no episode with that sonarrId can be found in database: {sonarr_episode_id}")
        return
    elif episode_details.subtitles is None:
        # subtitles indexing for this episode is incomplete, we'll do it again
        store_subtitles(episode_details.path, path_mappings.path_replace(episode_details.path))
        episode_details = database.execute(stmt).first()
    elif episode_details.missing_subtitles is None:
        # missing subtitles calculation for this episode is incomplete, we'll do it again
        list_missing_subtitles(epno=sonarr_episode_id)
        episode_details = database.execute(stmt).first()

    providers_list = get_providers()

    if providers_list:
        _wanted_episode(episode_details, job_id=job_id)
    else:
        logging.info("BAZARR All providers are throttled")


def wanted_search_missing_subtitles_series(job_id=None):
    if not job_id:
        jobs_queue.add_job_from_function("Searching for missing series subtitles", is_progress=True)
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

    for i, episode in enumerate(episodes, start=1):
        jobs_queue.update_job_progress(job_id=job_id, progress_value=i,
                                       progress_message=f'{episode.title} - S{episode.season:02d}E{episode.episode:02d}'
                                                        f' - {episode.episodeTitle}')

        providers = get_providers()
        if providers:
            wanted_download_subtitles(episode.sonarrEpisodeId, job_id=job_id)
        else:
            logging.info("BAZARR All providers are throttled")
            break

    logging.info('BAZARR Finished searching for missing Series Subtitles. Check History for more information.')

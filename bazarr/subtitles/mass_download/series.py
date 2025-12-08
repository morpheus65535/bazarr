# coding=utf-8
# fmt: off

import ast
import logging
import operator
import os

from functools import reduce

from utilities.path_mappings import path_mappings
from subtitles.indexer.series import store_subtitles, list_missing_subtitles
from sonarr.history import history_log
from app.notifier import send_notifications
from app.get_providers import get_providers
from app.database import (get_exclusion_clause, get_audio_profile_languages, TableShows, TableEpisodes, database,
                          select, get_profile_id)
from app.jobs_queue import jobs_queue
from app.event_handler import event_stream

from ..download import generate_subtitles


def series_download_subtitles(no, job_id=None, job_sub_function=False):
    if not job_sub_function and not job_id:
        jobs_queue.add_job_from_function("Searching missing subtitles", is_progress=True)
        return

    series_row = database.execute(
        select(TableShows.path)
        .where(TableShows.sonarrSeriesId == no))\
        .first()

    if series_row and not os.path.exists(path_mappings.path_replace(series_row.path)):
        raise OSError

    conditions = [(TableEpisodes.sonarrSeriesId == no),
                  (TableEpisodes.missing_subtitles != '[]')]
    conditions += get_exclusion_clause('series')
    episodes_details = database.execute(
        select(TableEpisodes.sonarrEpisodeId,
               TableShows.title,
               TableEpisodes.season,
               TableEpisodes.episode,
               TableEpisodes.title.label('episodeTitle'),
               TableEpisodes.missing_subtitles)
        .select_from(TableEpisodes)
        .join(TableShows)
        .where(reduce(operator.and_, conditions))) \
        .all()
    if not episodes_details:
        logging.debug(f"BAZARR no episode for that sonarrSeriesId have been found in database or they have all been "
                      f"ignored because of monitored status, series type or series tags: {no}")
        return

    count_episodes_details = len(episodes_details)

    jobs_queue.update_job_progress(job_id=job_id, progress_max=count_episodes_details)
    for i, episode in enumerate(episodes_details, start=1):
        jobs_queue.update_job_progress(job_id=job_id, progress_value=i,
                                       progress_message=f'{episode.title} - S{episode.season:02d}E'
                                                        f'{episode.episode:02d} - {episode.episodeTitle}')

        providers_list = get_providers()

        if providers_list:
            episode_download_subtitles(no=episode.sonarrEpisodeId, job_id=job_id, job_sub_function=True,
                                       providers_list=providers_list)
        else:
            jobs_queue.update_job_progress(job_id=job_id, progress_value=count_episodes_details)
            logging.info("BAZARR All providers are throttled")
            break


def episode_download_subtitles(no, job_id=None, job_sub_function=False, providers_list=None):
    if not job_sub_function and not job_id:
        jobs_queue.add_job_from_function("Searching missing subtitles", is_progress=True)
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
                  TableShows.profileId,
                  TableEpisodes.subtitles) \
        .select_from(TableEpisodes) \
        .join(TableShows) \
        .where(reduce(operator.and_, conditions))
    episode = database.execute(stmt).first()

    if not episode:
        logging.debug("BAZARR no episode with that sonarrEpisodeId can be found in database:", str(no))
        jobs_queue.update_job_progress(job_id=job_id, progress_message="Episode not found in database.")
        return
    elif episode.subtitles is None:
        # subtitles indexing for this episode is incomplete, we'll do it again
        store_subtitles(episode.path, path_mappings.path_replace_movie(episode.path))
        episode = database.execute(stmt).first()
    elif episode.missing_subtitles is None:
        # missing subtitles calculation for this episode is incomplete, we'll do it again
        list_missing_subtitles(epno=no)
        episode = database.execute(stmt).first()

    episodePath = path_mappings.path_replace(episode.path)

    if not os.path.exists(episodePath):
        logging.debug(f"BAZARR episode file not found. Path mapping issue?: {episodePath}")
        jobs_queue.update_job_progress(job_id=job_id, progress_message=f"Episode path doesn't exists: {episodePath}")
        raise OSError

    if not providers_list:
        providers_list = get_providers()

    if providers_list:
        audio_language_list = get_audio_profile_languages(episode.audio_language)
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = 'None'

        languages = []

        if not job_sub_function and job_id:
            jobs_queue.update_job_progress(job_id=job_id, progress_max=1,
                                           progress_message=f'{episode.title} - S{episode.season:02d}E'
                                                            f'{episode.episode:02d} - {episode.episodeTitle}')

        for language in ast.literal_eval(episode.missing_subtitles):
            if language is not None:
                hi_ = "True" if language.endswith(':hi') else "False"
                forced_ = "True" if language.endswith(':forced') else "False"
                languages.append((language.split(":")[0], hi_, forced_))

        if languages:
            for result in generate_subtitles(episodePath,
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
                    send_notifications(episode.sonarrSeriesId, episode.sonarrEpisodeId, result.message)
    else:
        logging.info("BAZARR All providers are throttled")

    if not job_sub_function and job_id:
        jobs_queue.update_job_progress(job_id=job_id, progress_value='max')


def episode_download_specific_subtitles(sonarr_series_id, sonarr_episode_id, language, hi, forced, job_id=None):
    if not job_id:
        return jobs_queue.add_job_from_function("Searching subtitles", progress_max=1, is_progress=True)

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

    sceneName = episodeInfo.sceneName or "None"

    title = episodeInfo.title

    episode_long_title = f'{title} - S{episodeInfo.season:02d}E{episodeInfo.episode:02d} - {episodeInfo.episodeTitle}'

    if hi == 'True':
        language_str = f'{language}:hi'
    elif forced == 'True':
        language_str = f'{language}:forced'
    else:
        language_str = language

    jobs_queue.update_job_progress(job_id=job_id,
                                   progress_message=f"Searching {language_str.upper()} for {episode_long_title}")

    audio_language_list = get_audio_profile_languages(episodeInfo.audio_language)
    if len(audio_language_list) > 0:
        audio_language = audio_language_list[0]['name']
    else:
        audio_language = None

    try:
        result = list(generate_subtitles(episodePath, [(language, hi, forced)], audio_language, sceneName,
                                         title, 'series', profile_id=get_profile_id(episode_id=sonarr_episode_id),
                                         job_id=job_id))
        if isinstance(result, list) and len(result):
            result = result[0]
            if isinstance(result, tuple) and len(result):
                result = result[0]
            history_log(1, sonarr_series_id, sonarr_episode_id, result)
            send_notifications(sonarr_series_id, sonarr_episode_id, result.message)
            store_subtitles(result.path, episodePath)
        else:
            event_stream(type='episode', payload=sonarr_episode_id)
            jobs_queue.update_job_progress(job_id=job_id, progress_value='max',
                                           progress_message=f'No {language_str.upper()} subtitles found for '
                                                            f'{episode_long_title}')
            return '', 204
    except OSError:
        return 'Unable to save subtitles file. Permission or path mapping issue?', 409
    else:
        jobs_queue.update_job_progress(job_id=job_id, progress_value='max')
        return '', 204

# coding=utf-8
# fmt: off

import ast
import logging
import operator

from functools import reduce

from utilities.path_mappings import path_mappings
from subtitles.indexer.series import store_subtitles
from sonarr.history import history_log
from app.notifier import send_notifications
from app.get_providers import get_providers
from app.database import get_exclusion_clause, get_audio_profile_languages, TableShows, TableEpisodes, database, \
    update, select
from app.event_handler import event_stream, show_progress, hide_progress

from ..adaptive_searching import is_search_active, updateFailedAttempts
from ..download import generate_subtitles


def _wanted_episode(episode):
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
                                                            attempt_string=episode.failedAttempts))) \
                .where(TableEpisodes.sonarrEpisodeId == episode.sonarrEpisodeId) \
                .execute()
            database.commit()

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
                                     check_if_still_required=True):
        if result:
            store_subtitles(episode.path, path_mappings.path_replace(episode.path))
            history_log(1, episode.sonarrSeriesId, episode.sonarrEpisodeId, result)
            event_stream(type='series', action='update', payload=episode.sonarrSeriesId)
            event_stream(type='episode-wanted', action='delete', payload=episode.sonarrEpisodeId)
            send_notifications(episode.sonarrSeriesId, episode.sonarrEpisodeId, result.message)


def wanted_download_subtitles(sonarr_episode_id):
    episodes_details = database.execute(
        select(TableEpisodes.path,
               TableEpisodes.missing_subtitles,
               TableEpisodes.sonarrEpisodeId,
               TableEpisodes.sonarrSeriesId,
               TableEpisodes.audio_language,
               TableEpisodes.sceneName,
               TableEpisodes.failedAttempts,
               TableShows.title)
        .join(TableShows, TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId)
        .where((TableEpisodes.sonarrEpisodeId == sonarr_episode_id))) \
        .all()

    for episode in episodes_details:
        providers_list = get_providers()

        if providers_list:
            _wanted_episode(episode)
        else:
            logging.info("BAZARR All providers are throttled")
            break


def wanted_search_missing_subtitles_series():
    conditions = [(TableEpisodes.missing_subtitles != '[]')]
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
        .join(TableShows, TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId)
        .where(reduce(operator.and_, conditions))) \
        .all()

    count_episodes = len(episodes)
    for i, episode in enumerate(episodes):
        show_progress(id='wanted_episodes_progress',
                      header='Searching subtitles...',
                      name='{0} - S{1:02d}E{2:02d} - {3}'.format(episode.title,
                                                                 episode.season,
                                                                 episode.episode,
                                                                 episode.episodeTitle),
                      value=i,
                      count=count_episodes)

        providers = get_providers()
        if providers:
            wanted_download_subtitles(episode.sonarrEpisodeId)
        else:
            logging.info("BAZARR All providers are throttled")
            break

    hide_progress(id='wanted_episodes_progress')

    logging.info('BAZARR Finished searching for missing Series Subtitles. Check History for more information.')

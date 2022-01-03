# coding=utf-8
# fmt: off

import ast
import logging
import operator

from functools import reduce

from helper import path_mappings
from list_subtitles import store_subtitles
from utils import history_log
from notifier import send_notifications
from get_providers import get_providers
from database import get_exclusion_clause, get_audio_profile_languages, TableShows, TableEpisodes
from event_handler import event_stream, show_progress, hide_progress
from ..adaptive_searching import is_search_active, updateFailedAttempts
from ..download import generate_subtitles


def _wanted_episode(episode):
    audio_language_list = get_audio_profile_languages(episode_id=episode['sonarrEpisodeId'])
    if len(audio_language_list) > 0:
        audio_language = audio_language_list[0]['name']
    else:
        audio_language = 'None'

    languages = []
    for language in ast.literal_eval(episode['missing_subtitles']):

        # confirm if language is still missing or if cutoff have been reached
        confirmed_missing_subs = TableEpisodes.select(TableEpisodes.missing_subtitles) \
            .where(TableEpisodes.sonarrEpisodeId == episode['sonarrEpisodeId']) \
            .dicts() \
            .get()
        if language not in ast.literal_eval(confirmed_missing_subs['missing_subtitles']):
            continue

        if is_search_active(desired_language=language, attempt_string=episode['failedAttempts']):
            TableEpisodes.update({TableEpisodes.failedAttempts:
                                  updateFailedAttempts(desired_language=language,
                                                       attempt_string=episode['failedAttempts'])}) \
                .where(TableEpisodes.sonarrEpisodeId == episode['sonarrEpisodeId']) \
                .execute()

            hi_ = "True" if language.endswith(':hi') else "False"
            forced_ = "True" if language.endswith(':forced') else "False"
            languages.append((language.split(":")[0], hi_, forced_))

        else:
            logging.debug(
                f"BAZARR Search is throttled by adaptive search for this episode {episode['path']} and "
                f"language: {language}")

    for result in generate_subtitles(path_mappings.path_replace(episode['path']),
                                     languages,
                                     audio_language,
                                     str(episode['scene_name']),
                                     episode['title'],
                                     'series'):
        if result:
            message = result[0]
            path = result[1]
            forced = result[5]
            if result[8]:
                language_code = result[2] + ":hi"
            elif forced:
                language_code = result[2] + ":forced"
            else:
                language_code = result[2]
            provider = result[3]
            score = result[4]
            subs_id = result[6]
            subs_path = result[7]
            store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))
            history_log(1, episode['sonarrSeriesId'], episode['sonarrEpisodeId'], message, path,
                        language_code, provider, score, subs_id, subs_path)
            event_stream(type='series', action='update', payload=episode['sonarrSeriesId'])
            event_stream(type='episode-wanted', action='delete', payload=episode['sonarrEpisodeId'])
            send_notifications(episode['sonarrSeriesId'], episode['sonarrEpisodeId'], message)


def wanted_download_subtitles(sonarr_episode_id):
    episodes_details = TableEpisodes.select(TableEpisodes.path,
                                            TableEpisodes.missing_subtitles,
                                            TableEpisodes.sonarrEpisodeId,
                                            TableEpisodes.sonarrSeriesId,
                                            TableEpisodes.audio_language,
                                            TableEpisodes.scene_name,
                                            TableEpisodes.failedAttempts,
                                            TableShows.title)\
        .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId))\
        .where((TableEpisodes.sonarrEpisodeId == sonarr_episode_id))\
        .dicts()
    episodes_details = list(episodes_details)

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
    episodes = TableEpisodes.select(TableEpisodes.sonarrSeriesId,
                                    TableEpisodes.sonarrEpisodeId,
                                    TableShows.tags,
                                    TableEpisodes.monitored,
                                    TableShows.title,
                                    TableEpisodes.season,
                                    TableEpisodes.episode,
                                    TableEpisodes.title.alias('episodeTitle'),
                                    TableShows.seriesType)\
        .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId))\
        .where(reduce(operator.and_, conditions))\
        .dicts()
    episodes = list(episodes)

    count_episodes = len(episodes)
    for i, episode in enumerate(episodes):
        show_progress(id='wanted_episodes_progress',
                      header='Searching subtitles...',
                      name='{0} - S{1:02d}E{2:02d} - {3}'.format(episode['title'],
                                                                 episode['season'],
                                                                 episode['episode'],
                                                                 episode['episodeTitle']),
                      value=i,
                      count=count_episodes)

        providers = get_providers()
        if providers:
            wanted_download_subtitles(episode['sonarrEpisodeId'])
        else:
            logging.info("BAZARR All providers are throttled")
            return

    hide_progress(id='wanted_episodes_progress')

    logging.info('BAZARR Finished searching for missing Series Subtitles. Check History for more information.')

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
from event_handler import show_progress, hide_progress
from ..download import generate_subtitles


def series_download_subtitles(no):
    conditions = [(TableEpisodes.sonarrSeriesId == no),
                  (TableEpisodes.missing_subtitles != '[]')]
    conditions += get_exclusion_clause('series')
    episodes_details = TableEpisodes.select(TableEpisodes.path,
                                            TableEpisodes.missing_subtitles,
                                            TableEpisodes.monitored,
                                            TableEpisodes.sonarrEpisodeId,
                                            TableEpisodes.scene_name,
                                            TableShows.tags,
                                            TableShows.seriesType,
                                            TableEpisodes.audio_language,
                                            TableShows.title,
                                            TableEpisodes.season,
                                            TableEpisodes.episode,
                                            TableEpisodes.title.alias('episodeTitle')) \
        .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId)) \
        .where(reduce(operator.and_, conditions)) \
        .dicts()
    if not episodes_details:
        logging.debug("BAZARR no episode for that sonarrSeriesId have been found in database or they have all been "
                      "ignored because of monitored status, series type or series tags: {}".format(no))
        return

    count_episodes_details = len(episodes_details)

    for i, episode in enumerate(episodes_details):
        providers_list = get_providers()

        if providers_list:
            show_progress(id='series_search_progress_{}'.format(no),
                          header='Searching missing subtitles...',
                          name='{0} - S{1:02d}E{2:02d} - {3}'.format(episode['title'],
                                                                     episode['season'],
                                                                     episode['episode'],
                                                                     episode['episodeTitle']),
                          value=i,
                          count=count_episodes_details)

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

                if language is not None:
                    hi_ = "True" if language.endswith(':hi') else "False"
                    forced_ = "True" if language.endswith(':forced') else "False"
                    languages.append((language.split(":")[0], hi_, forced_))

            if not languages:
                continue

            for result in generate_subtitles(path_mappings.path_replace(episode['path']),
                                             languages,
                                             audio_language,
                                             str(episode['scene_name']),
                                             episode['title'], 'series'):
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
                    history_log(1, no, episode['sonarrEpisodeId'], message, path, language_code, provider, score,
                                subs_id, subs_path)
                    send_notifications(no, episode['sonarrEpisodeId'], message)
        else:
            logging.info("BAZARR All providers are throttled")
            break

    hide_progress(id='series_search_progress_{}'.format(no))


def episode_download_subtitles(no, send_progress=False):
    conditions = [(TableEpisodes.sonarrEpisodeId == no)]
    conditions += get_exclusion_clause('series')
    episodes_details = TableEpisodes.select(TableEpisodes.path,
                                            TableEpisodes.missing_subtitles,
                                            TableEpisodes.monitored,
                                            TableEpisodes.sonarrEpisodeId,
                                            TableEpisodes.scene_name,
                                            TableShows.tags,
                                            TableShows.title,
                                            TableShows.sonarrSeriesId,
                                            TableEpisodes.audio_language,
                                            TableShows.seriesType,
                                            TableEpisodes.title.alias('episodeTitle'),
                                            TableEpisodes.season,
                                            TableEpisodes.episode) \
        .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId)) \
        .where(reduce(operator.and_, conditions)) \
        .dicts()
    if not episodes_details:
        logging.debug("BAZARR no episode with that sonarrEpisodeId can be found in database:", str(no))
        return

    for episode in episodes_details:
        providers_list = get_providers()

        if providers_list:
            if send_progress:
                show_progress(id='episode_search_progress_{}'.format(no),
                              header='Searching missing subtitles...',
                              name='{0} - S{1:02d}E{2:02d} - {3}'.format(episode['title'],
                                                                         episode['season'],
                                                                         episode['episode'],
                                                                         episode['episodeTitle']),
                              value=0,
                              count=1)

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

                if language is not None:
                    hi_ = "True" if language.endswith(':hi') else "False"
                    forced_ = "True" if language.endswith(':forced') else "False"
                    languages.append((language.split(":")[0], hi_, forced_))

            if not languages:
                continue

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
                    send_notifications(episode['sonarrSeriesId'], episode['sonarrEpisodeId'], message)

            if send_progress:
                hide_progress(id='episode_search_progress_{}'.format(no))
        else:
            logging.info("BAZARR All providers are throttled")
            break

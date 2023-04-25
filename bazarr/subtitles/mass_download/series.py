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
from app.database import get_exclusion_clause, get_audio_profile_languages, TableShows, TableEpisodes, database, select
from app.event_handler import show_progress, hide_progress

from ..download import generate_subtitles


def series_download_subtitles(no):
    conditions = [(TableEpisodes.sonarrSeriesId == no),
                  (TableEpisodes.missing_subtitles != '[]')]
    conditions += get_exclusion_clause('series')
    episodes_details = database.execute(
        select(TableEpisodes.path,
               TableEpisodes.missing_subtitles,
               TableEpisodes.monitored,
               TableEpisodes.sonarrEpisodeId,
               TableEpisodes.sceneName,
               TableShows.tags,
               TableShows.seriesType,
               TableEpisodes.audio_language,
               TableShows.title,
               TableEpisodes.season,
               TableEpisodes.episode,
               TableEpisodes.title.label('episodeTitle'))
        .join(TableShows, TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId)
        .where(reduce(operator.and_, conditions))) \
        .all()
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
                          name='{0} - S{1:02d}E{2:02d} - {3}'.format(episode.title,
                                                                     episode.season,
                                                                     episode.episode,
                                                                     episode.episodeTitle),
                          value=i,
                          count=count_episodes_details)

            audio_language_list = get_audio_profile_languages(episode.audio_language)
            if len(audio_language_list) > 0:
                audio_language = audio_language_list[0]['name']
            else:
                audio_language = 'None'

            languages = []
            for language in ast.literal_eval(episode.missing_subtitles):
                if language is not None:
                    hi_ = "True" if language.endswith(':hi') else "False"
                    forced_ = "True" if language.endswith(':forced') else "False"
                    languages.append((language.split(":")[0], hi_, forced_))

            if not languages:
                continue

            for result in generate_subtitles(path_mappings.path_replace(episode.path),
                                             languages,
                                             audio_language,
                                             str(episode.sceneName),
                                             episode.title,
                                             'series',
                                             check_if_still_required=True):
                if result:
                    store_subtitles(episode.path, path_mappings.path_replace(episode.path))
                    history_log(1, no, episode.sonarrEpisodeId, result)
                    send_notifications(no, episode.sonarrEpisodeId, result.message)
        else:
            logging.info("BAZARR All providers are throttled")
            break

    hide_progress(id='series_search_progress_{}'.format(no))


def episode_download_subtitles(no, send_progress=False):
    conditions = [(TableEpisodes.sonarrEpisodeId == no)]
    conditions += get_exclusion_clause('series')
    episodes_details = database.execute(
        select(TableEpisodes.path,
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
               TableEpisodes.episode)
        .join(TableShows, TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId)
        .where(reduce(operator.and_, conditions))) \
        .all()
    if not episodes_details:
        logging.debug("BAZARR no episode with that sonarrEpisodeId can be found in database:", str(no))
        return

    for episode in episodes_details:
        providers_list = get_providers()

        if providers_list:
            if send_progress:
                show_progress(id='episode_search_progress_{}'.format(no),
                              header='Searching missing subtitles...',
                              name='{0} - S{1:02d}E{2:02d} - {3}'.format(episode.title,
                                                                         episode.season,
                                                                         episode.episode,
                                                                         episode.episodeTitle),
                              value=0,
                              count=1)

            audio_language_list = get_audio_profile_languages(episode.audio_language)
            if len(audio_language_list) > 0:
                audio_language = audio_language_list[0]['name']
            else:
                audio_language = 'None'

            languages = []
            for language in ast.literal_eval(episode.missing_subtitles):
                if language is not None:
                    hi_ = "True" if language.endswith(':hi') else "False"
                    forced_ = "True" if language.endswith(':forced') else "False"
                    languages.append((language.split(":")[0], hi_, forced_))

            if not languages:
                continue

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
                    send_notifications(episode.sonarrSeriesId, episode.sonarrEpisodeId, result.message)

            if send_progress:
                hide_progress(id='episode_search_progress_{}'.format(no))
        else:
            logging.info("BAZARR All providers are throttled")
            break

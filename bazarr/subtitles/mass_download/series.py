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
from app.database import get_exclusion_clause, get_audio_profile_languages, TableShows, TableEpisodes, database, select
from app.event_handler import show_progress, hide_progress

from ..download import generate_subtitles


def series_download_subtitles(no):
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

    for i, episode in enumerate(episodes_details):
        providers_list = get_providers()

        if providers_list:
            show_progress(id=f'series_search_progress_{no}',
                          header='Searching missing subtitles...',
                          name=f'{episode.title} - S{episode.season:02d}E{episode.episode:02d} - {episode.episodeTitle}',
                          value=i,
                          count=count_episodes_details)

            episode_download_subtitles(no=episode.sonarrEpisodeId, send_progress=False, providers_list=providers_list)
        else:
            logging.info("BAZARR All providers are throttled")
            break

    show_progress(id=f'series_search_progress_{no}',
                  header='Searching missing subtitles...',
                  name='',
                  value=count_episodes_details,
                  count=count_episodes_details)


def episode_download_subtitles(no, send_progress=False, providers_list=None):
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
        return
    elif episode.subtitles is None:
        # subtitles indexing for this episode is incomplete, we'll do it again
        store_subtitles(episode.path, path_mappings.path_replace_movie(episode.path))
        episode = database.execute(stmt).first()
    elif episode.missing_subtitles is None:
        # missing subtitles calculation for this episode is incomplete, we'll do it again
        list_missing_subtitles(epno=no)
        episode = database.execute(stmt).first()

    if not providers_list:
        providers_list = get_providers()

    if providers_list:
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

        if languages:
            if send_progress:
                show_progress(id=f'episode_search_progress_{no}',
                              header='Searching missing subtitles...',
                              name=f'{episode.title} - S{episode.season:02d}E{episode.episode:02d} - {episode.episodeTitle}',
                              value=0,
                              count=1)

            for result in generate_subtitles(path_mappings.path_replace(episode.path),
                                             languages,
                                             audio_language,
                                             str(episode.sceneName),
                                             episode.title,
                                             'series',
                                             episode.profileId,
                                             check_if_still_required=True):
                if result:
                    if isinstance(result, tuple) and len(result):
                        result = result[0]
                    store_subtitles(episode.path, path_mappings.path_replace(episode.path))
                    history_log(1, episode.sonarrSeriesId, episode.sonarrEpisodeId, result)
                    send_notifications(episode.sonarrSeriesId, episode.sonarrEpisodeId, result.message)

            if send_progress:
                show_progress(id=f'episode_search_progress_{no}',
                              header='Searching missing subtitles...',
                              name=f'{episode.title} - S{episode.season:02d}E{episode.episode:02d} - {episode.episodeTitle}',
                              value=1,
                              count=1)
    else:
        logging.info("BAZARR All providers are throttled")

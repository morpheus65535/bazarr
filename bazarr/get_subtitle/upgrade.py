# coding=utf-8
# fmt: off

import os
import logging
import operator

from functools import reduce
from peewee import fn
from datetime import datetime, timedelta

from config import settings
from helper import path_mappings
from list_subtitles import store_subtitles, store_subtitles_movie
from utils import history_log, history_log_movie
from notifier import send_notifications, send_notifications_movie
from get_providers import get_providers
from database import get_exclusion_clause, get_audio_profile_languages, TableShows, TableEpisodes, TableMovies, \
    TableHistory, TableHistoryMovie
from event_handler import show_progress, hide_progress
from .download import generate_subtitles


def upgrade_subtitles():
    days_to_upgrade_subs = settings.general.days_to_upgrade_subs
    minimum_timestamp = ((datetime.now() - timedelta(days=int(days_to_upgrade_subs))) -
                         datetime(1970, 1, 1)).total_seconds()

    if settings.general.getboolean('upgrade_manual'):
        query_actions = [1, 2, 3, 4, 6]
    else:
        query_actions = [1, 3]

    if settings.general.getboolean('use_sonarr'):
        upgradable_episodes_conditions = [(TableHistory.action << query_actions),
                                          (TableHistory.timestamp > minimum_timestamp),
                                          (TableHistory.score is not None)]
        upgradable_episodes_conditions += get_exclusion_clause('series')
        upgradable_episodes = TableHistory.select(TableHistory.video_path,
                                                  TableHistory.language,
                                                  TableHistory.score,
                                                  TableShows.tags,
                                                  TableShows.profileId,
                                                  TableEpisodes.audio_language,
                                                  TableEpisodes.scene_name,
                                                  TableEpisodes.title,
                                                  TableEpisodes.sonarrSeriesId,
                                                  TableHistory.action,
                                                  TableHistory.subtitles_path,
                                                  TableEpisodes.sonarrEpisodeId,
                                                  fn.MAX(TableHistory.timestamp).alias('timestamp'),
                                                  TableEpisodes.monitored,
                                                  TableEpisodes.season,
                                                  TableEpisodes.episode,
                                                  TableShows.title.alias('seriesTitle'),
                                                  TableShows.seriesType)\
            .join(TableShows, on=(TableHistory.sonarrSeriesId == TableShows.sonarrSeriesId))\
            .join(TableEpisodes, on=(TableHistory.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId))\
            .where(reduce(operator.and_, upgradable_episodes_conditions))\
            .group_by(TableHistory.video_path, TableHistory.language)\
            .dicts()
        upgradable_episodes_not_perfect = []
        for upgradable_episode in upgradable_episodes:
            if upgradable_episode['timestamp'] > minimum_timestamp:
                try:
                    int(upgradable_episode['score'])
                except ValueError:
                    pass
                else:
                    if int(upgradable_episode['score']) < 360 or (settings.general.getboolean('upgrade_manual') and
                                                                  upgradable_episode['action'] in [2, 4, 6]):
                        upgradable_episodes_not_perfect.append(upgradable_episode)

        episodes_to_upgrade = []
        for episode in upgradable_episodes_not_perfect:
            if os.path.exists(path_mappings.path_replace(episode['subtitles_path'])) and int(episode['score']) < 357:
                episodes_to_upgrade.append(episode)

        count_episode_to_upgrade = len(episodes_to_upgrade)

    if settings.general.getboolean('use_radarr'):
        upgradable_movies_conditions = [(TableHistoryMovie.action << query_actions),
                                        (TableHistoryMovie.timestamp > minimum_timestamp),
                                        (TableHistoryMovie.score is not None)]
        upgradable_movies_conditions += get_exclusion_clause('movie')
        upgradable_movies = TableHistoryMovie.select(TableHistoryMovie.video_path,
                                                     TableHistoryMovie.language,
                                                     TableHistoryMovie.score,
                                                     TableMovies.profileId,
                                                     TableHistoryMovie.action,
                                                     TableHistoryMovie.subtitles_path,
                                                     TableMovies.audio_language,
                                                     TableMovies.sceneName,
                                                     fn.MAX(TableHistoryMovie.timestamp).alias('timestamp'),
                                                     TableMovies.monitored,
                                                     TableMovies.tags,
                                                     TableMovies.radarrId,
                                                     TableMovies.title)\
            .join(TableMovies, on=(TableHistoryMovie.radarrId == TableMovies.radarrId))\
            .where(reduce(operator.and_, upgradable_movies_conditions))\
            .group_by(TableHistoryMovie.video_path, TableHistoryMovie.language)\
            .dicts()
        upgradable_movies_not_perfect = []
        for upgradable_movie in upgradable_movies:
            if upgradable_movie['timestamp'] > minimum_timestamp:
                try:
                    int(upgradable_movie['score'])
                except ValueError:
                    pass
                else:
                    if int(upgradable_movie['score']) < 120 or (settings.general.getboolean('upgrade_manual') and
                                                                upgradable_movie['action'] in [2, 4, 6]):
                        upgradable_movies_not_perfect.append(upgradable_movie)

        movies_to_upgrade = []
        for movie in upgradable_movies_not_perfect:
            if os.path.exists(path_mappings.path_replace_movie(movie['subtitles_path'])) and int(movie['score']) < 117:
                movies_to_upgrade.append(movie)

        count_movie_to_upgrade = len(movies_to_upgrade)

    if settings.general.getboolean('use_sonarr'):
        for i, episode in enumerate(episodes_to_upgrade):
            providers_list = get_providers()

            show_progress(id='upgrade_episodes_progress',
                          header='Upgrading episodes subtitles...',
                          name='{0} - S{1:02d}E{2:02d} - {3}'.format(episode['seriesTitle'],
                                                                     episode['season'],
                                                                     episode['episode'],
                                                                     episode['title']),
                          value=i,
                          count=count_episode_to_upgrade)

            if not providers_list:
                logging.info("BAZARR All providers are throttled")
                return
            if episode['language'].endswith('forced'):
                language = episode['language'].split(':')[0]
                is_forced = "True"
                is_hi = "False"
            elif episode['language'].endswith('hi'):
                language = episode['language'].split(':')[0]
                is_forced = "False"
                is_hi = "True"
            else:
                language = episode['language'].split(':')[0]
                is_forced = "False"
                is_hi = "False"

            audio_language_list = get_audio_profile_languages(episode_id=episode['sonarrEpisodeId'])
            if len(audio_language_list) > 0:
                audio_language = audio_language_list[0]['name']
            else:
                audio_language = 'None'

            result = list(generate_subtitles(path_mappings.path_replace(episode['video_path']),
                                             [(language, is_hi, is_forced)],
                                             audio_language,
                                             str(episode['scene_name']),
                                             episode['seriesTitle'],
                                             'series',
                                             forced_minimum_score=int(episode['score']),
                                             is_upgrade=True))

            if result:
                result = result[0]
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
                store_subtitles(episode['video_path'], path_mappings.path_replace(episode['video_path']))
                history_log(3, episode['sonarrSeriesId'], episode['sonarrEpisodeId'], message, path,
                            language_code, provider, score, subs_id, subs_path)
                send_notifications(episode['sonarrSeriesId'], episode['sonarrEpisodeId'], message)

        hide_progress(id='upgrade_episodes_progress')

    if settings.general.getboolean('use_radarr'):
        for i, movie in enumerate(movies_to_upgrade):
            providers_list = get_providers()

            show_progress(id='upgrade_movies_progress',
                          header='Upgrading movies subtitles...',
                          name=movie['title'],
                          value=i,
                          count=count_movie_to_upgrade)

            if not providers_list:
                logging.info("BAZARR All providers are throttled")
                return
            if movie['language'].endswith('forced'):
                language = movie['language'].split(':')[0]
                is_forced = "True"
                is_hi = "False"
            elif movie['language'].endswith('hi'):
                language = movie['language'].split(':')[0]
                is_forced = "False"
                is_hi = "True"
            else:
                language = movie['language'].split(':')[0]
                is_forced = "False"
                is_hi = "False"

            audio_language_list = get_audio_profile_languages(movie_id=movie['radarrId'])
            if len(audio_language_list) > 0:
                audio_language = audio_language_list[0]['name']
            else:
                audio_language = 'None'

            result = list(generate_subtitles(path_mappings.path_replace_movie(movie['video_path']),
                                             [(language, is_hi, is_forced)],
                                             audio_language,
                                             str(movie['sceneName']),
                                             movie['title'],
                                             'movie',
                                             forced_minimum_score=int(movie['score']),
                                             is_upgrade=True))
            if result:
                result = result[0]
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
                store_subtitles_movie(movie['video_path'],
                                      path_mappings.path_replace_movie(movie['video_path']))
                history_log_movie(3, movie['radarrId'], message, path, language_code, provider, score, subs_id, subs_path)
                send_notifications_movie(movie['radarrId'], message)

        hide_progress(id='upgrade_movies_progress')

    logging.info('BAZARR Finished searching for Subtitles to upgrade. Check History for more information.')

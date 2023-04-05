# coding=utf-8
# fmt: off

import logging
import operator
import os
from datetime import datetime, timedelta
from functools import reduce

from app.config import settings
from app.database import get_exclusion_clause, get_audio_profile_languages, TableShows, TableEpisodes, TableMovies, \
    TableHistory, TableHistoryMovie, database
from app.event_handler import show_progress, hide_progress
from app.get_providers import get_providers
from app.notifier import send_notifications, send_notifications_movie
from radarr.history import history_log_movie
from sonarr.history import history_log
from subtitles.indexer.movies import store_subtitles_movie
from subtitles.indexer.series import store_subtitles
from utilities.path_mappings import path_mappings
from .download import generate_subtitles


def upgrade_subtitles():
    use_sonarr = settings.general.getboolean('use_sonarr')
    use_radarr = settings.general.getboolean('use_radarr')

    if use_sonarr:
        episodes_to_upgrade = get_upgradable_episode_subtitles()
        count_episode_to_upgrade = len(episodes_to_upgrade)

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

            language, is_forced, is_hi = parse_language_string(episode['language'])

            audio_language_list = get_audio_profile_languages(episode['audio_language'])
            if len(audio_language_list) > 0:
                audio_language = audio_language_list[0]['name']
            else:
                audio_language = 'None'

            result = list(generate_subtitles(path_mappings.path_replace(episode['video_path']),
                                             [(language, is_hi, is_forced)],
                                             audio_language,
                                             str(episode['sceneName']),
                                             episode['seriesTitle'],
                                             'series',
                                             forced_minimum_score=int(episode['score']),
                                             is_upgrade=True))

            if result:
                result = result[0]
                store_subtitles(episode['video_path'], path_mappings.path_replace(episode['video_path']))
                history_log(3, episode['sonarrSeriesId'], episode['sonarrEpisodeId'], result)
                send_notifications(episode['sonarrSeriesId'], episode['sonarrEpisodeId'], result.message)

        hide_progress(id='upgrade_episodes_progress')

    if use_radarr:
        movies_to_upgrade = get_upgradable_movies_subtitles()
        count_movie_to_upgrade = len(movies_to_upgrade)

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

            language, is_forced, is_hi = parse_language_string(movie['language'])

            audio_language_list = get_audio_profile_languages(movie['audio_language'])
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
                store_subtitles_movie(movie['video_path'],
                                      path_mappings.path_replace_movie(movie['video_path']))
                history_log_movie(3, movie['radarrId'], result)
                send_notifications_movie(movie['radarrId'], result.message)

        hide_progress(id='upgrade_movies_progress')

    logging.info('BAZARR Finished searching for Subtitles to upgrade. Check History for more information.')


def get_queries_condition_parameters():
    days_to_upgrade_subs = settings.general.days_to_upgrade_subs
    minimum_timestamp = (datetime.now() - timedelta(days=int(days_to_upgrade_subs)))

    if settings.general.getboolean('upgrade_manual'):
        query_actions = [1, 2, 3, 4, 6]
    else:
        query_actions = [1, 3]

    return [minimum_timestamp, query_actions]


def parse_upgradable_list(upgradable_list, perfect_score, media_type):
    if media_type == 'series':
        path_replace_method = path_mappings.path_replace
    else:
        path_replace_method = path_mappings.path_replace_movie

    items_to_upgrade = []

    for item in upgradable_list:
        logging.debug(f"Trying to validate eligibility to upgrade for this subtitles: "
                      f"{item.subtitles_path}")
        if (item.video_path, item.language) in \
                [(x.video_path, x.language) for x in items_to_upgrade]:
            logging.debug("Newer video path and subtitles language combination already in list of subtitles to "
                          "upgrade, we skip this one.")
            continue

        if os.path.exists(path_replace_method(item.subtitles_path)) and \
                os.path.exists(path_replace_method(item.video_path)):
            logging.debug("Video and subtitles file are still there, we continue the eligibility validation.")
            pass

        items_to_upgrade.append(item)

    if not settings.general.getboolean('upgrade_manual'):
        logging.debug("Removing history items for manually downloaded or translated subtitles.")
        items_to_upgrade = [x for x in items_to_upgrade if x.action in [2, 4, 6]]

    logging.debug("Removing history items for already perfectly scored subtitles.")
    items_to_upgrade = [x for x in items_to_upgrade if x.score < perfect_score]

    logging.debug(f"Bazarr will try to upgrade {len(items_to_upgrade)} subtitles.")

    return items_to_upgrade


def parse_language_string(language_string):
    if language_string.endswith('forced'):
        language = language_string.split(':')[0]
        is_forced = "True"
        is_hi = "False"
    elif language_string.endswith('hi'):
        language = language_string.split(':')[0]
        is_forced = "False"
        is_hi = "True"
    else:
        language = language_string.split(':')[0]
        is_forced = "False"
        is_hi = "False"

    return [language, is_forced, is_hi]


def get_upgradable_episode_subtitles():
    minimum_timestamp, query_actions = get_queries_condition_parameters()

    upgradable_episodes_conditions = [(TableHistory.action.in_(query_actions)),
                                      (TableHistory.timestamp > minimum_timestamp),
                                      TableHistory.score]
    upgradable_episodes_conditions += get_exclusion_clause('series')
    upgradable_episodes = database.query(TableHistory.video_path,
                                         TableHistory.language,
                                         TableHistory.score,
                                         TableShows.tags,
                                         TableShows.profileId,
                                         TableEpisodes.audio_language,
                                         TableEpisodes.sceneName,
                                         TableEpisodes.title,
                                         TableEpisodes.sonarrSeriesId,
                                         TableHistory.action,
                                         TableHistory.subtitles_path,
                                         TableEpisodes.sonarrEpisodeId,
                                         TableHistory.timestamp.label('timestamp'),
                                         TableEpisodes.monitored,
                                         TableEpisodes.season,
                                         TableEpisodes.episode,
                                         TableShows.title.label('seriesTitle'),
                                         TableShows.seriesType)\
        .join(TableShows, TableHistory.sonarrSeriesId == TableShows.sonarrSeriesId) \
        .join(TableEpisodes, TableHistory.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId) \
        .where(reduce(operator.and_, upgradable_episodes_conditions)) \
        .order_by(TableHistory.timestamp.desc())\
        .all()

    if not upgradable_episodes:
        return []
    else:
        logging.debug(f"{len(upgradable_episodes)} potentially upgradable episode subtitles have been found, let's "
                      f"filter them...")

        return parse_upgradable_list(upgradable_list=upgradable_episodes, perfect_score=357, media_type='series')


def get_upgradable_movies_subtitles():
    minimum_timestamp, query_actions = get_queries_condition_parameters()

    upgradable_movies_conditions = [(TableHistoryMovie.action.in_(query_actions)),
                                    (TableHistoryMovie.timestamp > minimum_timestamp),
                                    TableHistoryMovie.score]
    upgradable_movies_conditions += get_exclusion_clause('movie')
    upgradable_movies = database.query(TableHistoryMovie.video_path,
                                       TableHistoryMovie.language,
                                       TableHistoryMovie.score,
                                       TableMovies.profileId,
                                       TableHistoryMovie.action,
                                       TableHistoryMovie.subtitles_path,
                                       TableMovies.audio_language,
                                       TableMovies.sceneName,
                                       TableHistoryMovie.timestamp.label('timestamp'),
                                       TableMovies.monitored,
                                       TableMovies.tags,
                                       TableMovies.radarrId,
                                       TableMovies.title)\
        .join(TableMovies, TableHistoryMovie.radarrId == TableMovies.radarrId) \
        .where(reduce(operator.and_, upgradable_movies_conditions)) \
        .order_by(TableHistoryMovie.timestamp.desc()) \
        .all()

    if not upgradable_movies:
        return []
    else:
        logging.debug(f"{len(upgradable_movies)} potentially upgradable movie subtitles have been found, let's filter "
                      f"them...")

        return parse_upgradable_list(upgradable_list=upgradable_movies, perfect_score=117, media_type='movie')

# coding=utf-8
# fmt: off

import logging
import operator
import ast

from datetime import datetime, timedelta
from functools import reduce
from sqlalchemy import and_

from app.config import settings
from app.database import get_exclusion_clause, get_audio_profile_languages, TableShows, TableEpisodes, TableMovies, \
    TableHistory, TableHistoryMovie, database, select, func, get_profiles_list
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
    use_sonarr = settings.general.use_sonarr
    use_radarr = settings.general.use_radarr

    if use_sonarr:
        episodes_to_upgrade = get_upgradable_episode_subtitles()
        episodes_data = [{
            'id': x.id,
            'seriesTitle': x.seriesTitle,
            'season': x.season,
            'episode': x.episode,
            'title': x.title,
            'language': x.language,
            'audio_language': x.audio_language,
            'video_path': x.video_path,
            'sceneName': x.sceneName,
            'score': x.score,
            'sonarrEpisodeId': x.sonarrEpisodeId,
            'sonarrSeriesId': x.sonarrSeriesId,
            'subtitles_path': x.subtitles_path,
            'path': x.path,
            'profileId': x.profileId,
            'external_subtitles': [ast.literal_eval(f'"{y[1]}"') for y in ast.literal_eval(x.external_subtitles) if y[1]],
            'upgradable': bool(x.upgradable),
        } for x in database.execute(
            select(TableHistory.id,
                   TableShows.title.label('seriesTitle'),
                   TableEpisodes.season,
                   TableEpisodes.episode,
                   TableEpisodes.title,
                   TableHistory.language,
                   TableEpisodes.audio_language,
                   TableHistory.video_path,
                   TableEpisodes.sceneName,
                   TableHistory.score,
                   TableHistory.sonarrEpisodeId,
                   TableHistory.sonarrSeriesId,
                   TableHistory.subtitles_path,
                   TableEpisodes.path,
                   TableShows.profileId,
                   TableEpisodes.subtitles.label('external_subtitles'),
                   episodes_to_upgrade.c.id.label('upgradable'))
            .select_from(TableHistory)
            .join(TableShows, onclause=TableHistory.sonarrSeriesId == TableShows.sonarrSeriesId)
            .join(TableEpisodes, onclause=TableHistory.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId)
            .join(episodes_to_upgrade, onclause=TableHistory.id == episodes_to_upgrade.c.id, isouter=True)
            .where(episodes_to_upgrade.c.id.is_not(None)))
            .all() if _language_still_desired(x.language, x.profileId) and
            x.video_path == x.path
        ]

        for item in episodes_data:
            # do not consider subtitles that do not exist on disk anymore
            if item['subtitles_path'] not in item['external_subtitles']:
                episodes_data.remove(item)

            # cleanup the unused attributes
            del item['path']
            del item['external_subtitles']

        count_episode_to_upgrade = len(episodes_data)

        for i, episode in enumerate(episodes_data):
            providers_list = get_providers()

            show_progress(id='upgrade_episodes_progress',
                          header='Upgrading episodes subtitles...',
                          name=f'{episode["seriesTitle"]} - S{episode["season"]:02d}E{episode["episode"]:02d} - {episode["title"]}',
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
                                             episode['profileId'],
                                             forced_minimum_score=int(episode['score']),
                                             is_upgrade=True,
                                             previous_subtitles_to_delete=path_mappings.path_replace(
                                                 episode['subtitles_path'])))

            if result:
                if isinstance(result, list) and len(result):
                    result = result[0]
                if isinstance(result, tuple) and len(result):
                    result = result[0]
                store_subtitles(episode['video_path'], path_mappings.path_replace(episode['video_path']))
                history_log(3, episode['sonarrSeriesId'], episode['sonarrEpisodeId'], result)
                send_notifications(episode['sonarrSeriesId'], episode['sonarrEpisodeId'], result.message)

        hide_progress(id='upgrade_episodes_progress')

    if use_radarr:
        movies_to_upgrade = get_upgradable_movies_subtitles()
        movies_data = [{
            'title': x.title,
            'language': x.language,
            'audio_language': x.audio_language,
            'video_path': x.video_path,
            'sceneName': x.sceneName,
            'score': x.score,
            'radarrId': x.radarrId,
            'path': x.path,
            'profileId': x.profileId,
            'subtitles_path': x.subtitles_path,
            'external_subtitles': [ast.literal_eval(f'"{y[1]}"') for y in ast.literal_eval(x.external_subtitles) if y[1]],
            'upgradable': bool(x.upgradable),
        } for x in database.execute(
            select(TableMovies.title,
                   TableHistoryMovie.language,
                   TableMovies.audio_language,
                   TableHistoryMovie.video_path,
                   TableMovies.sceneName,
                   TableHistoryMovie.score,
                   TableHistoryMovie.radarrId,
                   TableHistoryMovie.subtitles_path,
                   TableMovies.path,
                   TableMovies.profileId,
                   TableMovies.subtitles.label('external_subtitles'),
                   movies_to_upgrade.c.id.label('upgradable'))
            .select_from(TableHistoryMovie)
            .join(TableMovies, onclause=TableHistoryMovie.radarrId == TableMovies.radarrId)
            .join(movies_to_upgrade, onclause=TableHistoryMovie.id == movies_to_upgrade.c.id, isouter=True)
            .where(movies_to_upgrade.c.id.is_not(None)))
            .all() if _language_still_desired(x.language, x.profileId) and
            x.video_path == x.path
        ]

        for item in movies_data:
            # do not consider subtitles that do not exist on disk anymore
            if item['subtitles_path'] not in item['external_subtitles']:
                movies_data.remove(item)

            # cleanup the unused attributes
            del item['path']
            del item['external_subtitles']

        count_movie_to_upgrade = len(movies_data)

        for i, movie in enumerate(movies_data):
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
                                             movie['profileId'],
                                             forced_minimum_score=int(movie['score']),
                                             is_upgrade=True,
                                             previous_subtitles_to_delete=path_mappings.path_replace_movie(
                                                 movie['subtitles_path'])))
            if result:
                if isinstance(result, list) and len(result):
                    result = result[0]
                if isinstance(result, tuple) and len(result):
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

    if settings.general.upgrade_manual:
        query_actions = [1, 2, 3, 4, 6]
    else:
        query_actions = [1, 3]

    return [minimum_timestamp, query_actions]


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
    if not settings.general.upgrade_subs:
        # return an empty set of rows
        return select(TableHistory.id) \
            .where(TableHistory.id.is_(None)) \
            .subquery()

    max_id_timestamp = select(TableHistory.video_path,
                              TableHistory.language,
                              func.max(TableHistory.timestamp).label('timestamp')) \
        .group_by(TableHistory.video_path, TableHistory.language) \
        .distinct() \
        .subquery()

    minimum_timestamp, query_actions = get_queries_condition_parameters()

    upgradable_episodes_conditions = [(TableHistory.action.in_(query_actions)),
                                      (TableHistory.timestamp > minimum_timestamp),
                                      TableHistory.score.is_not(None),
                                      (TableHistory.score < 357)]
    upgradable_episodes_conditions += get_exclusion_clause('series')
    return select(TableHistory.id)\
        .select_from(TableHistory) \
        .join(max_id_timestamp, onclause=and_(TableHistory.video_path == max_id_timestamp.c.video_path,
                                              TableHistory.language == max_id_timestamp.c.language,
                                              max_id_timestamp.c.timestamp == TableHistory.timestamp)) \
        .join(TableShows, onclause=TableHistory.sonarrSeriesId == TableShows.sonarrSeriesId) \
        .join(TableEpisodes, onclause=TableHistory.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId) \
        .where(reduce(operator.and_, upgradable_episodes_conditions)) \
        .order_by(TableHistory.timestamp.desc())\
        .subquery()


def get_upgradable_movies_subtitles():
    if not settings.general.upgrade_subs:
        # return an empty set of rows
        return select(TableHistoryMovie.id) \
            .where(TableHistoryMovie.id.is_(None)) \
            .subquery()

    max_id_timestamp = select(TableHistoryMovie.video_path,
                              TableHistoryMovie.language,
                              func.max(TableHistoryMovie.timestamp).label('timestamp')) \
        .group_by(TableHistoryMovie.video_path, TableHistoryMovie.language) \
        .distinct() \
        .subquery()

    minimum_timestamp, query_actions = get_queries_condition_parameters()

    upgradable_movies_conditions = [(TableHistoryMovie.action.in_(query_actions)),
                                    (TableHistoryMovie.timestamp > minimum_timestamp),
                                    TableHistoryMovie.score.is_not(None),
                                    (TableHistoryMovie.score < 117)]
    upgradable_movies_conditions += get_exclusion_clause('movie')
    return select(TableHistoryMovie.id) \
        .select_from(TableHistoryMovie) \
        .join(max_id_timestamp, onclause=and_(TableHistoryMovie.video_path == max_id_timestamp.c.video_path,
                                              TableHistoryMovie.language == max_id_timestamp.c.language,
                                              max_id_timestamp.c.timestamp == TableHistoryMovie.timestamp)) \
        .join(TableMovies, onclause=TableHistoryMovie.radarrId == TableMovies.radarrId) \
        .where(reduce(operator.and_, upgradable_movies_conditions)) \
        .order_by(TableHistoryMovie.timestamp.desc()) \
        .subquery()


def _language_still_desired(language, profile_id):
    if not profile_id:
        return False

    profile = get_profiles_list(profile_id)
    if profile and language in _language_from_items(profile['items']):
        return True
    else:
        return False


def _language_from_items(items):
    results = []
    for item in items:
        if item['forced'] == 'True':
            results.append(f'{item["language"]}:forced')
        elif item['hi'] == 'True':
            results.append(f'{item["language"]}:hi')
        else:
            results.append(item['language'])
            results.append(f'{item["language"]}:hi')
    return results

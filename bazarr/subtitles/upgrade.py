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
            'external_subtitles': [y[1] for y in ast.literal_eval(x.external_subtitles) if y[1]],
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
                   TableEpisodes.subtitles.label('external_subtitles'))
            .select_from(TableHistory)
            .join(TableShows, onclause=TableHistory.sonarrSeriesId == TableShows.sonarrSeriesId)
            .join(TableEpisodes, onclause=TableHistory.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId))
            .all() if _language_still_desired(x.language, x.profileId) and
            x.video_path == x.path
        ]

        for item in episodes_data:
            # do not consider subtitles that do not exist on disk anymore
            if item['subtitles_path'] not in item['external_subtitles']:
                continue

            # Mark upgradable and get original_id
            item.update({'original_id': episodes_to_upgrade.get(item['id'])})
            item.update({'upgradable': bool(item['original_id'])})

            # cleanup the unused attributes
            del item['path']
            del item['external_subtitles']

        # Make sure to keep only upgradable episode subtitles
        episodes_data = [x for x in episodes_data if 'upgradable' in x and x['upgradable']]

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
            if is_hi and not _is_hi_required(language, episode['profileId']):
                is_hi = 'False'

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
                history_log(3, episode['sonarrSeriesId'], episode['sonarrEpisodeId'], result,
                            upgraded_from_id=episode['original_id'])
                send_notifications(episode['sonarrSeriesId'], episode['sonarrEpisodeId'], result.message)

        show_progress(id='upgrade_episodes_progress',
                      header='Upgrading episodes subtitles...',
                      name='',
                      value=count_episode_to_upgrade,
                      count=count_episode_to_upgrade)

    if use_radarr:
        movies_to_upgrade = get_upgradable_movies_subtitles()
        movies_data = [{
            'id': x.id,
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
            'external_subtitles': [y[1] for y in ast.literal_eval(x.external_subtitles) if y[1]],
        } for x in database.execute(
            select(TableHistoryMovie.id,
                   TableMovies.title,
                   TableHistoryMovie.language,
                   TableMovies.audio_language,
                   TableHistoryMovie.video_path,
                   TableMovies.sceneName,
                   TableHistoryMovie.score,
                   TableHistoryMovie.radarrId,
                   TableHistoryMovie.subtitles_path,
                   TableMovies.path,
                   TableMovies.profileId,
                   TableMovies.subtitles.label('external_subtitles'))
            .select_from(TableHistoryMovie)
            .join(TableMovies, onclause=TableHistoryMovie.radarrId == TableMovies.radarrId))
            .all() if _language_still_desired(x.language, x.profileId) and
            x.video_path == x.path
        ]

        for item in movies_data:
            # do not consider subtitles that do not exist on disk anymore
            if item['subtitles_path'] not in item['external_subtitles']:
                continue

            # Mark upgradable and get original_id
            item.update({'original_id': movies_to_upgrade.get(item['id'])})
            item.update({'upgradable': bool(item['original_id'])})

            # cleanup the unused attributes
            del item['path']
            del item['external_subtitles']

        # Make sure to keep only upgradable movie subtitles
        movies_data = [x for x in movies_data if 'upgradable' in x and x['upgradable']]

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
            if is_hi and not _is_hi_required(language, movie['profileId']):
                is_hi = 'False'

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
                history_log_movie(3, movie['radarrId'], result, upgraded_from_id=movie['original_id'])
                send_notifications_movie(movie['radarrId'], result.message)

        show_progress(id='upgrade_movies_progress',
                      header='Upgrading movies subtitles...',
                      name='',
                      value=count_movie_to_upgrade,
                      count=count_movie_to_upgrade)

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
        logging.debug("Subtitles upgrade is disabled so we wont go further.")
        return {}

    logging.debug("Determining upgradable episode subtitles")
    max_id_timestamp = select(TableHistory.video_path,
                              TableHistory.language,
                              func.max(TableHistory.timestamp).label('timestamp')) \
        .group_by(TableHistory.video_path, TableHistory.language) \
        .distinct() \
        .subquery()

    minimum_timestamp, query_actions = get_queries_condition_parameters()
    logging.debug(f"Minimum timestamp used for subtitles upgrade: {minimum_timestamp}")
    logging.debug(f"These actions are considered for subtitles upgrade: {query_actions}")

    upgradable_episodes_conditions = [(TableHistory.action.in_(query_actions)),
                                      (TableHistory.timestamp > minimum_timestamp),
                                      TableHistory.score.is_not(None),
                                      (TableHistory.score < 357)]
    upgradable_episodes_conditions += get_exclusion_clause('series')
    subtitles_to_upgrade = database.execute(
        select(TableHistory.id,
               TableHistory.video_path,
               TableHistory.language,
               TableHistory.upgradedFromId)
        .select_from(TableHistory)
        .join(TableShows, onclause=TableHistory.sonarrSeriesId == TableShows.sonarrSeriesId)
        .join(TableEpisodes, onclause=TableHistory.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId)
        .join(max_id_timestamp, onclause=and_(TableHistory.video_path == max_id_timestamp.c.video_path,
                                              TableHistory.language == max_id_timestamp.c.language,
                                              max_id_timestamp.c.timestamp == TableHistory.timestamp))
        .where(reduce(operator.and_, upgradable_episodes_conditions))
        .order_by(TableHistory.timestamp.desc())) \
        .all()
    logging.debug(f"{len(subtitles_to_upgrade)} subtitles are candidates and we've selected the latest timestamp for "
                  f"each of them.")

    query_actions_without_upgrade = [x for x in query_actions if x != 3]
    upgradable_episode_subtitles = {}
    for subtitle_to_upgrade in subtitles_to_upgrade:
        # check if we have the original subtitles id in database and use it instead of guessing
        if subtitle_to_upgrade.upgradedFromId:
            upgradable_episode_subtitles.update({subtitle_to_upgrade.id: subtitle_to_upgrade.upgradedFromId})
            logging.debug(f"The original subtitles ID for TableHistory ID {subtitle_to_upgrade.id} stored in DB is: "
                          f"{subtitle_to_upgrade.upgradedFromId}")
            continue

        # if not, we have to try to guess the original subtitles id
        logging.debug("We don't have the original subtitles ID for this subtitle so we'll have to guess it.")
        potential_parents = database.execute(
            select(TableHistory.id, TableHistory.action)
            .where(TableHistory.video_path == subtitle_to_upgrade.video_path,
                   TableHistory.language == subtitle_to_upgrade.language,)
            .order_by(TableHistory.timestamp.desc())
        ).all()

        logging.debug(f"The potential original subtitles IDs for TableHistory ID {subtitle_to_upgrade.id} are: "
                      f"{[x.id for x in potential_parents]}")
        confirmed_parent = None
        for potential_parent in potential_parents:
            if potential_parent.action in query_actions_without_upgrade:
                confirmed_parent = potential_parent.id
                logging.debug(f"This ID is the first one to match selected query actions so it's been selected as "
                              f"original subtitles ID: {potential_parent.id}")
                break

        if confirmed_parent not in upgradable_episode_subtitles.values():
            logging.debug("We haven't defined this ID as original subtitles ID for any other ID so we'll add it to "
                          "upgradable episode subtitles.")
            upgradable_episode_subtitles.update({subtitle_to_upgrade.id: confirmed_parent})

    logging.debug(f"We've found {len(upgradable_episode_subtitles)} episode subtitles IDs to be upgradable")
    return upgradable_episode_subtitles


def get_upgradable_movies_subtitles():
    if not settings.general.upgrade_subs:
        # return an empty set of rows
        logging.debug("Subtitles upgrade is disabled so we won't go further.")
        return {}

    logging.debug("Determining upgradable movie subtitles")
    max_id_timestamp = select(TableHistoryMovie.video_path,
                              TableHistoryMovie.language,
                              func.max(TableHistoryMovie.timestamp).label('timestamp')) \
        .group_by(TableHistoryMovie.video_path, TableHistoryMovie.language) \
        .distinct() \
        .subquery()

    minimum_timestamp, query_actions = get_queries_condition_parameters()
    logging.debug(f"Minimum timestamp used for subtitles upgrade: {minimum_timestamp}")
    logging.debug(f"These actions are considered for subtitles upgrade: {query_actions}")

    upgradable_movies_conditions = [(TableHistoryMovie.action.in_(query_actions)),
                                    (TableHistoryMovie.timestamp > minimum_timestamp),
                                    TableHistoryMovie.score.is_not(None),
                                    (TableHistoryMovie.score < 117)]
    upgradable_movies_conditions += get_exclusion_clause('movie')
    subtitles_to_upgrade = database.execute(
        select(TableHistoryMovie.id,
               TableHistoryMovie.video_path,
               TableHistoryMovie.language,
               TableHistoryMovie.upgradedFromId)
        .select_from(TableHistoryMovie)
        .join(TableMovies, onclause=TableHistoryMovie.radarrId == TableMovies.radarrId)
        .join(max_id_timestamp, onclause=and_(TableHistoryMovie.video_path == max_id_timestamp.c.video_path,
                                              TableHistoryMovie.language == max_id_timestamp.c.language,
                                              max_id_timestamp.c.timestamp == TableHistoryMovie.timestamp))
        .where(reduce(operator.and_, upgradable_movies_conditions))
        .order_by(TableHistoryMovie.timestamp.desc())) \
        .all()
    logging.debug(f"{len(subtitles_to_upgrade)} subtitles are candidates and we've selected the latest timestamp for "
                  f"each of them.")

    query_actions_without_upgrade = [x for x in query_actions if x != 3]
    upgradable_movie_subtitles = {}
    for subtitle_to_upgrade in subtitles_to_upgrade:
        # check if we have the original subtitles id in database and use it instead of guessing
        if subtitle_to_upgrade.upgradedFromId:
            upgradable_movie_subtitles.update({subtitle_to_upgrade.id: subtitle_to_upgrade.upgradedFromId})
            logging.debug(f"The original subtitles ID for TableHistoryMovie ID {subtitle_to_upgrade.id} stored in DB "
                          f"is: {subtitle_to_upgrade.upgradedFromId}")
            continue

        # if not, we have to try to guess the original subtitles id
        logging.debug("We don't have the original subtitles ID for this subtitle so we'll have to guess it.")
        potential_parents = database.execute(
            select(TableHistoryMovie.id, TableHistoryMovie.action)
            .where(TableHistoryMovie.video_path == subtitle_to_upgrade.video_path,
                   TableHistoryMovie.language == subtitle_to_upgrade.language, )
            .order_by(TableHistoryMovie.timestamp.desc())
        ).all()

        logging.debug(f"The potential original subtitles IDs for TableHistoryMovie ID {subtitle_to_upgrade.id} are: "
                      f"{[x.id for x in potential_parents]}")
        confirmed_parent = None
        for potential_parent in potential_parents:
            if potential_parent.action in query_actions_without_upgrade:
                confirmed_parent = potential_parent.id
                logging.debug(f"This ID is the newest one to match selected query actions so it's been selected as "
                              f"original subtitles ID: {potential_parent.id}")
                break

        if confirmed_parent not in upgradable_movie_subtitles.values():
            logging.debug("We haven't defined this ID as original subtitles ID for any other ID so we'll add it to "
                          "upgradable episode subtitles.")
            upgradable_movie_subtitles.update({subtitle_to_upgrade.id: confirmed_parent})

    logging.debug(f"We've found {len(upgradable_movie_subtitles)} movie subtitles IDs to be upgradable")
    return upgradable_movie_subtitles


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


def _is_hi_required(language, profile_id):
    profile = get_profiles_list(profile_id=profile_id)
    for item in profile['items']:
        if language.split(':')[0] == item['language'] and item['hi'] == 'True':
            return True
    return False

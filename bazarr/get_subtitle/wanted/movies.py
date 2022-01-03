# coding=utf-8
# fmt: off

import ast
import logging
import operator

from functools import reduce

from helper import path_mappings
from list_subtitles import store_subtitles_movie
from utils import history_log_movie
from notifier import send_notifications_movie
from get_providers import get_providers
from database import get_exclusion_clause, get_audio_profile_languages, TableMovies
from event_handler import event_stream, show_progress, hide_progress
from ..adaptive_searching import is_search_active, updateFailedAttempts
from ..download import generate_subtitles


def _wanted_movie(movie):
    audio_language_list = get_audio_profile_languages(movie_id=movie['radarrId'])
    if len(audio_language_list) > 0:
        audio_language = audio_language_list[0]['name']
    else:
        audio_language = 'None'

    languages = []

    for language in ast.literal_eval(movie['missing_subtitles']):
        # confirm if language is still missing or if cutoff have been reached
        confirmed_missing_subs = TableMovies.select(TableMovies.missing_subtitles) \
            .where(TableMovies.radarrId == movie['radarrId']) \
            .dicts() \
            .get()
        if language not in ast.literal_eval(confirmed_missing_subs['missing_subtitles']):
            continue

        if is_search_active(desired_language=language, attempt_string=movie['failedAttempts']):
            TableMovies.update({TableMovies.failedAttempts:
                                updateFailedAttempts(desired_language=language,
                                                     attempt_string=movie['failedAttempts'])}) \
                .where(TableMovies.radarrId == movie['radarrId']) \
                .execute()

            hi_ = "True" if language.endswith(':hi') else "False"
            forced_ = "True" if language.endswith(':forced') else "False"
            languages.append((language.split(":")[0], hi_, forced_))

        else:
            logging.info(f"BAZARR Search is throttled by adaptive search for this movie {movie['path']} and "
                         f"language: {language}")

    for result in generate_subtitles(path_mappings.path_replace_movie(movie['path']),
                                     languages,
                                     audio_language,
                                     str(movie['sceneName']),
                                     movie['title'], 'movie'):

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
            store_subtitles_movie(movie['path'], path_mappings.path_replace_movie(movie['path']))
            history_log_movie(1, movie['radarrId'], message, path, language_code, provider, score,
                              subs_id, subs_path)
            event_stream(type='movie-wanted', action='delete', payload=movie['radarrId'])
            send_notifications_movie(movie['radarrId'], message)


def wanted_download_subtitles_movie(radarr_id):
    movies_details = TableMovies.select(TableMovies.path,
                                        TableMovies.missing_subtitles,
                                        TableMovies.radarrId,
                                        TableMovies.audio_language,
                                        TableMovies.sceneName,
                                        TableMovies.failedAttempts,
                                        TableMovies.title)\
        .where((TableMovies.radarrId == radarr_id))\
        .dicts()
    movies_details = list(movies_details)

    for movie in movies_details:
        providers_list = get_providers()

        if providers_list:
            _wanted_movie(movie)
        else:
            logging.info("BAZARR All providers are throttled")
            break


def wanted_search_missing_subtitles_movies():
    conditions = [(TableMovies.missing_subtitles != '[]')]
    conditions += get_exclusion_clause('movie')
    movies = TableMovies.select(TableMovies.radarrId,
                                TableMovies.tags,
                                TableMovies.monitored,
                                TableMovies.title) \
        .where(reduce(operator.and_, conditions)) \
        .dicts()
    movies = list(movies)

    count_movies = len(movies)
    for i, movie in enumerate(movies):
        show_progress(id='wanted_movies_progress',
                      header='Searching subtitles...',
                      name=movie['title'],
                      value=i,
                      count=count_movies)

        providers = get_providers()
        if providers:
            wanted_download_subtitles_movie(movie['radarrId'])
        else:
            logging.info("BAZARR All providers are throttled")
            return

    hide_progress(id='wanted_movies_progress')

    logging.info('BAZARR Finished searching for missing Movies Subtitles. Check History for more information.')

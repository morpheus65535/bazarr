# coding=utf-8
# fmt: off

import ast
import logging
import operator
import os

from functools import reduce

from utilities.path_mappings import path_mappings
from subtitles.indexer.movies import store_subtitles_movie, list_missing_subtitles_movies
from radarr.history import history_log_movie
from app.notifier import send_notifications_movie
from app.get_providers import get_providers
from app.database import get_exclusion_clause, get_audio_profile_languages, TableMovies, database, select
from app.event_handler import show_progress, hide_progress

from ..download import generate_subtitles


def movies_download_subtitles(no):
    conditions = [(TableMovies.radarrId == no)]
    conditions += get_exclusion_clause('movie')
    stmt = select(TableMovies.path,
                  TableMovies.missing_subtitles,
                  TableMovies.audio_language,
                  TableMovies.radarrId,
                  TableMovies.sceneName,
                  TableMovies.title,
                  TableMovies.tags,
                  TableMovies.monitored,
                  TableMovies.profileId,
                  TableMovies.subtitles) \
        .where(reduce(operator.and_, conditions))
    movie = database.execute(stmt).first()

    if not movie:
        logging.debug(f"BAZARR no movie with that radarrId can be found in database: {no}")
        return
    elif movie.subtitles is None:
        # subtitles indexing for this movie is incomplete, we'll do it again
        store_subtitles_movie(movie.path, path_mappings.path_replace_movie(movie.path))
        movie = database.execute(stmt).first()
    elif movie.missing_subtitles is None:
        # missing subtitles calculation for this movie is incomplete, we'll do it again
        list_missing_subtitles_movies(no=no)
        movie = database.execute(stmt).first()

    moviePath = path_mappings.path_replace_movie(movie.path)

    if not os.path.exists(moviePath):
        raise OSError

    if ast.literal_eval(movie.missing_subtitles):
        count_movie = len(ast.literal_eval(movie.missing_subtitles))
    else:
        count_movie = 0

    audio_language_list = get_audio_profile_languages(movie.audio_language)
    if len(audio_language_list) > 0:
        audio_language = audio_language_list[0]['name']
    else:
        audio_language = 'None'

    languages = []

    for language in ast.literal_eval(movie.missing_subtitles):
        providers_list = get_providers()

        if providers_list:
            if language is not None:
                hi_ = "True" if language.endswith(':hi') else "False"
                forced_ = "True" if language.endswith(':forced') else "False"
                languages.append((language.split(":")[0], hi_, forced_))
        else:
            logging.info("BAZARR All providers are throttled")
            break

    if languages:
        show_progress(id=f'movie_search_progress_{no}',
                      header='Searching missing subtitles...',
                      name=movie.title,
                      value=0,
                      count=count_movie)

        for result in generate_subtitles(moviePath,
                                         languages,
                                         audio_language,
                                         str(movie.sceneName),
                                         movie.title,
                                         'movie',
                                         movie.profileId,
                                         check_if_still_required=True):

            if result:
                if isinstance(result, tuple) and len(result):
                    result = result[0]
                store_subtitles_movie(movie.path, moviePath)
                history_log_movie(1, no, result)
                send_notifications_movie(no, result.message)

        show_progress(id=f'movie_search_progress_{no}',
                      header='Searching missing subtitles...',
                      name=movie.title,
                      value=count_movie,
                      count=count_movie)

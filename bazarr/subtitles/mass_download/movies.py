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
from app.database import (get_exclusion_clause, get_audio_profile_languages, TableMovies, database, select,
                          get_profile_id)
from app.jobs_queue import jobs_queue
from app.event_handler import event_stream

from ..download import generate_subtitles


def movies_download_subtitles(no, job_id=None, job_sub_function=False):
    if not job_sub_function and not job_id:
        jobs_queue.add_job_from_function("Searching missing subtitles", is_progress=True)
        return

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
        jobs_queue.update_job_progress(job_id=job_id, progress_message="Movie not found in database.")
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
        logging.debug(f"BAZARR movie file not found. Path mapping issue?: {moviePath}")
        jobs_queue.update_job_progress(job_id=job_id, progress_message=f"Movie path doesn't exists: {moviePath}")
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

    jobs_queue.update_job_progress(job_id=job_id, progress_max=count_movie, progress_message=movie.title)

    providers_list = get_providers()

    if providers_list:
        for language in ast.literal_eval(movie.missing_subtitles):
            if language is not None:
                hi_ = "True" if language.endswith(':hi') else "False"
                forced_ = "True" if language.endswith(':forced') else "False"
                languages.append((language.split(":")[0], hi_, forced_))

        if languages:
            for result in generate_subtitles(moviePath,
                                             languages,
                                             audio_language,
                                             str(movie.sceneName),
                                             movie.title,
                                             'movie',
                                             movie.profileId,
                                             check_if_still_required=True,
                                             job_id=job_id):
                if result:
                    if isinstance(result, tuple) and len(result):
                        result = result[0]
                    store_subtitles_movie(movie.path, moviePath)
                    history_log_movie(1, no, result)
                    send_notifications_movie(no, result.message)
    else:
        logging.info("BAZARR All providers are throttled")

    jobs_queue.update_job_progress(job_id=job_id, progress_value="max")


def movie_download_specific_subtitles(radarr_id, language, hi, forced, job_id=None):
    if not job_id:
        return jobs_queue.add_job_from_function("Searching subtitles", progress_max=1, is_progress=True)

    movieInfo = database.execute(
        select(
            TableMovies.title,
            TableMovies.path,
            TableMovies.sceneName,
            TableMovies.audio_language)
        .where(TableMovies.radarrId == radarr_id)) \
        .first()

    if not movieInfo:
        return 'Movie not found', 404

    moviePath = path_mappings.path_replace_movie(movieInfo.path)

    if not os.path.exists(moviePath):
        return 'Movie file not found. Path mapping issue?', 500

    sceneName = movieInfo.sceneName or 'None'

    title = movieInfo.title

    if hi == 'True':
        language_str = f'{language}:hi'
    elif forced == 'True':
        language_str = f'{language}:forced'
    else:
        language_str = language

    jobs_queue.update_job_progress(job_id=job_id, progress_message=f"Searching {language_str.upper()} for {title}")

    audio_language_list = get_audio_profile_languages(movieInfo.audio_language)
    if len(audio_language_list) > 0:
        audio_language = audio_language_list[0]['name']
    else:
        audio_language = None

    try:
        result = list(generate_subtitles(moviePath, [(language, hi, forced)], audio_language,
                                         sceneName, title, 'movie', profile_id=get_profile_id(movie_id=radarr_id),
                                         job_id=job_id))
        if isinstance(result, list) and len(result):
            result = result[0]
            if isinstance(result, tuple) and len(result):
                result = result[0]
            history_log_movie(1, radarr_id, result)
            send_notifications_movie(radarr_id, result.message)
            store_subtitles_movie(result.path, moviePath)
        else:
            event_stream(type='movie', payload=radarr_id)
            jobs_queue.update_job_progress(job_id=job_id, progress_value='max',
                                           progress_message=f'No {language_str.upper()} subtitles found for {title}')
            return '', 204
    except OSError:
        return 'Unable to save subtitles file. Permission or path mapping issue?', 409
    else:
        jobs_queue.update_job_progress(job_id=job_id, progress_value='max')
        return '', 204

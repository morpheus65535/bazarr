# coding=utf-8
# fmt: off

import ast
import logging
import operator

from functools import reduce

from utilities.path_mappings import path_mappings
from subtitles.indexer.movies import store_subtitles_movie, list_missing_subtitles_movies
from radarr.history import history_log_movie
from app.notifier import send_notifications_movie
from app.get_providers import get_providers
from app.database import get_exclusion_clause, get_audio_profile_languages, TableMovies, database, update, select
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue

from ..adaptive_searching import is_search_active, updateFailedAttempts
from ..download import generate_subtitles


def _wanted_movie(movie, providers_list, job_id=None):
    audio_language_list = get_audio_profile_languages(movie.audio_language)
    if len(audio_language_list) > 0:
        audio_language = audio_language_list[0]['name']
    else:
        audio_language = 'None'

    languages = []
    languages_to_stamp = []

    for language in ast.literal_eval(movie.missing_subtitles):
        if is_search_active(desired_language=language, attempt_string=movie.failedAttempts):
            hi_ = "True" if language.endswith(':hi') else "False"
            forced_ = "True" if language.endswith(':forced') else "False"
            languages.append((language.split(":")[0], hi_, forced_))
            languages_to_stamp.append(language)

        else:
            logging.info(f"BAZARR Search is throttled by adaptive search for this movie {movie.path} and "
                         f"language: {language}")

    found_any = False
    for result in generate_subtitles(path_mappings.path_replace_movie(movie.path),
                                     languages,
                                     audio_language,
                                     str(movie.sceneName),
                                     movie.title,
                                     'movie',
                                     movie.profileId,
                                     check_if_still_required=True,
                                     job_id=job_id):

        if result:
            found_any = True
            if isinstance(result, tuple) and len(result):
                result = result[0]
            store_subtitles_movie(movie.path, path_mappings.path_replace_movie(movie.path))
            history_log_movie(1, movie.radarrId, result)
            event_stream(type='movie-wanted', action='delete', payload=movie.radarrId)
            send_notifications_movie(movie.radarrId, result.message)

    if not found_any and providers_list:
        for language in languages_to_stamp:
            updated = updateFailedAttempts(
                desired_language=language,
                attempt_string=movie.failedAttempts)
            database.execute(
                update(TableMovies)
                .values(failedAttempts=updated)
                .where(TableMovies.radarrId == movie.radarrId))


def wanted_download_subtitles_movie(radarr_id, job_id=None):
    stmt = select(TableMovies.path,
                  TableMovies.missing_subtitles,
                  TableMovies.radarrId,
                  TableMovies.audio_language,
                  TableMovies.sceneName,
                  TableMovies.failedAttempts,
                  TableMovies.title,
                  TableMovies.profileId,
                  TableMovies.subtitles) \
        .where(TableMovies.radarrId == radarr_id)
    movie = database.execute(stmt).first()

    if not movie:
        logging.debug(f"BAZARR no movie with that radarrId can be found in database: {radarr_id}")
        return
    elif movie.subtitles is None:
        # subtitles indexing for this movie is incomplete, we'll do it again
        store_subtitles_movie(movie.path, path_mappings.path_replace_movie(movie.path))
        movie = database.execute(stmt).first()
    elif movie.missing_subtitles is None:
        # missing subtitles calculation for this movie is incomplete, we'll do it again
        list_missing_subtitles_movies(no=radarr_id)
        movie = database.execute(stmt).first()

    providers_list = get_providers()

    if providers_list:
        _wanted_movie(movie, providers_list, job_id=job_id)
    else:
        logging.info("BAZARR All providers are throttled")


def wanted_search_missing_subtitles_movies(job_id=None, wait_for_completion=False):
    if not job_id:
        jobs_queue.add_job_from_function("Searching for missing movies subtitles", is_progress=True,
                                         wait_for_completion=wait_for_completion)
        return

    conditions = [(TableMovies.missing_subtitles.is_not(None)),
                  (TableMovies.missing_subtitles != '[]')]
    conditions += get_exclusion_clause('movie')
    movies = database.execute(
        select(TableMovies.radarrId,
               TableMovies.tags,
               TableMovies.monitored,
               TableMovies.title)
        .where(reduce(operator.and_, conditions))) \
        .all()

    count_movies = len(movies)
    jobs_queue.update_job_progress(job_id=job_id, progress_max=count_movies)

    if count_movies == 0:
        jobs_queue.update_job_progress(job_id=job_id, progress_value='max')

    throttled = False
    for i, movie in enumerate(movies, start=1):
        jobs_queue.update_job_progress(job_id=job_id, progress_value=i, progress_message=movie.title)

        providers = get_providers()
        if providers:
            wanted_download_subtitles_movie(movie.radarrId, job_id=job_id)

            # make sure to override the progress value updated by the subtitles synchronization
            jobs_queue.update_job_progress(job_id=job_id, progress_value=i, progress_max=count_movies)
        else:
            logging.info("BAZARR All providers are throttled")
            throttled = True
            break

    outcome_msg = ("All providers throttled" if throttled
                   else "Search completed")
    jobs_queue.update_job_progress(job_id=job_id, progress_message=outcome_msg)
    jobs_queue.update_job_name(job_id=job_id, new_job_name="Searched for missing movies subtitles")
    logging.info('BAZARR Finished searching for missing Movies Subtitles. Check History for more information.')

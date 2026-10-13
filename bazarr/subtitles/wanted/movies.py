# coding=utf-8
# fmt: off

import logging
import operator

from functools import reduce

from utilities.path_mappings import path_mappings
from subtitles.indexer.movies import store_subtitles_movie, list_missing_subtitles_movies
from radarr.history import history_log_movie
from app.notifier import send_notifications_movie
from app.get_providers import get_providers
from app.database import (get_exclusion_clause, get_audio_profile_languages, TableMovies, database, select,
                          get_subtitles)
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue, JobCanceled
from app.config import settings

from ..adaptive_searching import is_search_active
from ..serialization import parse_missing_subtitles, missing_subtitle_to_language_tuple
from ..wanted_state import get_failed_attempt_pairs, record_failed_subtitle_attempts
from ..download import generate_subtitles


def _wanted_movie(movie, providers_list, job_id=None):
    audio_language_list = get_audio_profile_languages(movie.audio_language)
    if len(audio_language_list) > 0:
        audio_language = audio_language_list[0]['name']
    else:
        audio_language = 'None'

    languages = []
    languages_to_stamp = []
    attempts = get_failed_attempt_pairs('movie', movie.radarrId)

    for language in parse_missing_subtitles(movie.missing_subtitles):
        if is_search_active(desired_language=language, attempt_string=attempts):
            languages.append(missing_subtitle_to_language_tuple(language))
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
                                     job_id=job_id,
                                     fallback_allowed=settings.general.use_whisper_fallback):

        if result:
            found_any = True
            store_subtitles_movie(movie.radarrId)
            history_log_movie(1, movie.radarrId, result)
            send_notifications_movie(movie.radarrId, result.message)
            event_stream(type='movie-wanted', action='delete', payload=movie.radarrId)

    if not found_any and providers_list:
        record_failed_subtitle_attempts('movie', movie.radarrId, languages_to_stamp)


def wanted_download_subtitles_movie(radarr_id, job_id=None):
    stmt = select(TableMovies.path,
                  TableMovies.missing_subtitles,
                  TableMovies.radarrId,
                  TableMovies.audio_language,
                  TableMovies.sceneName,
                  TableMovies.title,
                  TableMovies.profileId) \
        .where(TableMovies.radarrId == radarr_id)
    movie = database.execute(stmt).first()

    previously_indexed_subtitles = get_subtitles(radarr_id=radarr_id)

    if not movie:
        logging.debug(f"BAZARR no movie with that radarrId can be found in database: {radarr_id}")
        return
    elif not len(previously_indexed_subtitles) or \
            any([not x['embedded_track_id'] for x in previously_indexed_subtitles if not x['path']]):
        # subtitles indexing for this movie might be incomplete, we'll do it again
        store_subtitles_movie(radarr_id)
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
                                         wait_for_completion=wait_for_completion, is_cancellable=True)
        return
    else:
        job = jobs_queue.get_job(job_id=job_id)

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
        if job.cancel_event.is_set():
            raise JobCanceled

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

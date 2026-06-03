# coding=utf-8
# fmt: off

import logging
import operator

from functools import reduce

from sqlalchemy import bindparam

from utilities.path_mappings import path_mappings
from subtitles.indexer.movies import store_subtitles_movie, list_missing_subtitles_movies
from radarr.history import history_log_movie
from app.notifier import send_notifications_movie
from app.get_providers import get_providers
from app.database import (get_exclusion_clause, get_audio_profile_languages, TableMovies, TableMoviesSubtitles,
                          database, update, select, get_subtitles)
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue
from app.config import settings

from ..adaptive_searching import get_adaptive_search_policy, update_failed_attempts
from ..download import generate_subtitles
from ..language_utils import has_unindexed_external_subtitle, resolve_audio_language
from .utils import get_due_missing_languages, get_language_search_items


_WANTED_MOVIE_DETAILS_SELECT = select(TableMovies.path,
                                      TableMovies.missing_subtitles,
                                      TableMovies.radarrId,
                                      TableMovies.audio_language,
                                      TableMovies.sceneName,
                                      TableMovies.failedAttempts,
                                      TableMovies.title,
                                      TableMovies.profileId,
                                      select(TableMoviesSubtitles.id)
                                      .where(TableMoviesSubtitles.radarrId == TableMovies.radarrId)
                                      .limit(1)
                                      .exists()
                                      .label("has_indexed_subtitles"),
                                      select(TableMoviesSubtitles.id)
                                      .where(TableMoviesSubtitles.radarrId == TableMovies.radarrId)
                                      .where(TableMoviesSubtitles.path.is_(None))
                                      .where(TableMoviesSubtitles.embedded_track_id.is_(None))
                                      .limit(1)
                                      .exists()
                                      .label("has_incomplete_embedded_subtitles"))
_WANTED_MOVIE_DETAILS_STMT = _WANTED_MOVIE_DETAILS_SELECT \
    .where(TableMovies.radarrId == bindparam("wanted_radarr_id"))


def _movie_needs_wanted_lookup_refresh(movie):
    return (
        movie.missing_subtitles is None or
        not getattr(movie, "has_indexed_subtitles", True) or
        getattr(movie, "has_incomplete_embedded_subtitles", False)
    )


def _wanted_movie(movie, providers_list, due_languages=None, job_id=None, adaptive_search_policy=None,
                  fallback_allowed=None):
    audio_language_list = get_audio_profile_languages(movie.audio_language)
    audio_language = resolve_audio_language(audio_language_list)

    due_missing_languages = due_languages
    if due_missing_languages is None:
        due_missing_languages = get_due_missing_languages(
            movie.missing_subtitles,
            movie.failedAttempts,
            adaptive_search_policy=adaptive_search_policy,
        )
    if not due_missing_languages:
        return
    if not movie.path:
        logging.debug("BAZARR wanted movie search skipped because movie path is missing: %s", movie.radarrId)
        return

    if fallback_allowed is None:
        fallback_allowed = settings.general.use_whisper_fallback

    languages = get_language_search_items(due_missing_languages)

    found_any = False
    for result in generate_subtitles(path_mappings.path_replace_movie(movie.path),
                                     languages,
                                     audio_language,
                                     movie.sceneName,
                                     movie.title,
                                     'movie',
                                     movie.profileId,
                                     check_if_still_required=True,
                                     job_id=job_id,
                                     fallback_allowed=fallback_allowed):

        if result:
            found_any = True
            if isinstance(result, tuple) and len(result):
                result = result[0]
            store_subtitles_movie(movie.radarrId)
            history_log_movie(1, movie.radarrId, result)
            if hasattr(result, 'message'):
                send_notifications_movie(movie.radarrId, result.message)
            event_stream(type='movie-wanted', action='delete', payload=movie.radarrId)

    if not found_any and providers_list:
        database.execute(
            update(TableMovies)
            .values(failedAttempts=update_failed_attempts(due_missing_languages, movie.failedAttempts))
            .where(TableMovies.radarrId == movie.radarrId))


def wanted_download_subtitles_movie(
    radarr_id,
    job_id=None,
    providers_list=None,
    movie=None,
    due_languages=None,
    adaptive_search_policy=None,
    fallback_allowed=None,
):
    stmt_params = {"wanted_radarr_id": radarr_id}

    if movie is not None and due_languages is not None and not _movie_needs_wanted_lookup_refresh(movie):
        if providers_list is None:
            providers_list = get_providers()
        if adaptive_search_policy is None:
            adaptive_search_policy = get_adaptive_search_policy()
        if providers_list:
            _wanted_movie(
                movie,
                providers_list,
                due_languages=due_languages,
                job_id=job_id,
                adaptive_search_policy=adaptive_search_policy,
                fallback_allowed=fallback_allowed,
            )
        else:
            logging.info("BAZARR All providers are throttled")
        return

    if movie is None:
        movie = database.execute(_WANTED_MOVIE_DETAILS_STMT, stmt_params).first()

    if not movie:
        logging.debug(f"BAZARR no movie with that radarrId can be found in database: {radarr_id}")
        return
    if _movie_needs_wanted_lookup_refresh(movie):
        previously_indexed_subtitles = get_subtitles(radarr_id=radarr_id) or []
        if not previously_indexed_subtitles or has_unindexed_external_subtitle(previously_indexed_subtitles):
            # subtitles indexing for this movie might be incomplete, we'll do it again
            store_subtitles_movie(radarr_id)
            movie = database.execute(_WANTED_MOVIE_DETAILS_STMT, stmt_params).first()
            if not movie:
                logging.debug(f"BAZARR no movie with that radarrId can be found in database after subtitles refresh: {radarr_id}")
                return
        if movie.missing_subtitles is None:
            # missing subtitles calculation for this movie is incomplete, we'll do it again
            list_missing_subtitles_movies(no=radarr_id)
        movie = database.execute(_WANTED_MOVIE_DETAILS_STMT, stmt_params).first()
        if not movie:
            logging.debug(f"BAZARR no movie with that radarrId can be found in database after missing-subtitles refresh: {radarr_id}")
            return
        due_languages = None
        providers_list = None

    if providers_list is None:
        providers_list = get_providers()
    if adaptive_search_policy is None:
        adaptive_search_policy = get_adaptive_search_policy()

    if providers_list:
        _wanted_movie(
            movie,
            providers_list,
            due_languages=due_languages,
            job_id=job_id,
            adaptive_search_policy=adaptive_search_policy,
            fallback_allowed=fallback_allowed,
        )
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
               TableMovies.audio_language,
               TableMovies.failedAttempts,
               TableMovies.missing_subtitles,
               TableMovies.path,
               TableMovies.profileId,
               TableMovies.sceneName,
               TableMovies.tags,
               TableMovies.monitored,
               TableMovies.title,
               select(TableMoviesSubtitles.id)
               .where(TableMoviesSubtitles.radarrId == TableMovies.radarrId)
               .limit(1)
               .exists()
               .label("has_indexed_subtitles"),
               select(TableMoviesSubtitles.id)
               .where(TableMoviesSubtitles.radarrId == TableMovies.radarrId)
               .where(TableMoviesSubtitles.path.is_(None))
               .where(TableMoviesSubtitles.embedded_track_id.is_(None))
               .limit(1)
               .exists()
               .label("has_incomplete_embedded_subtitles"))
        .where(reduce(operator.and_, conditions))) \
        .all()

    movies_to_search = []
    adaptive_search_policy = get_adaptive_search_policy()
    fallback_allowed = settings.general.use_whisper_fallback
    for movie in movies:
        due_languages = get_due_missing_languages(
            movie.missing_subtitles,
            movie.failedAttempts,
            adaptive_search_policy=adaptive_search_policy,
        )
        if due_languages:
            movies_to_search.append((movie, due_languages))

    count_movies = len(movies_to_search)
    jobs_queue.update_job_progress(job_id=job_id, progress_max=count_movies)

    if count_movies == 0:
        jobs_queue.update_job_progress(job_id=job_id, progress_value='max')
        throttled = False
    else:
        throttled = False

    for i, (movie, due_languages) in enumerate(movies_to_search, start=1):
        jobs_queue.update_job_progress(job_id=job_id, progress_value=i, progress_message=movie.title)

        providers = get_providers()
        if providers:
            if _movie_needs_wanted_lookup_refresh(movie):
                wanted_download_subtitles_movie(
                    movie.radarrId,
                    job_id=job_id,
                    providers_list=providers,
                    movie=movie,
                    adaptive_search_policy=adaptive_search_policy,
                    fallback_allowed=fallback_allowed,
                )
            else:
                _wanted_movie(
                    movie,
                    providers,
                    due_languages=due_languages,
                    job_id=job_id,
                    adaptive_search_policy=adaptive_search_policy,
                    fallback_allowed=fallback_allowed,
                )

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

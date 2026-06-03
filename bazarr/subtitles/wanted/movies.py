# coding=utf-8
# fmt: off

import logging
import operator

from functools import reduce

from sqlalchemy import bindparam, case, func

from utilities.path_mappings import path_mappings
from subtitles.indexer.movies import store_subtitles_movie, list_missing_subtitles_movies
from radarr.history import history_log_movie
from app.notifier import send_notifications_movie
from app.get_providers import get_providers
from app.database import (
    get_exclusion_clause, get_audio_profile_languages, TableMissingSubtitles, TableMovies, TableMoviesSubtitles,
    database, update, select, get_subtitles,
)
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue
from app.config import settings

from ..adaptive_searching import get_adaptive_search_policy
from ..download import generate_subtitles
from ..language_utils import has_unindexed_external_subtitle, resolve_audio_language
from subtitles.wanted_state import (
    due_missing_languages_statement,
    get_due_missing_languages_map,
    get_due_missing_languages_for_media,
    get_missing_languages,
    iter_due_missing_languages_maps,
    record_failed_subtitle_attempts,
    record_failed_subtitle_attempts_map,
)
from .utils import get_language_search_items


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
_FAILED_ATTEMPT_UPDATE_BATCH_SIZE = 5000
_TEMP_FAILED_ATTEMPT_UPDATE_MIN_SIZE = 1000
_DUE_MOVIE_DETAILS_BATCH_SIZE = 5000


_WANTED_MOVIES_SELECT = select(TableMovies.radarrId,
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


def _count_searchable_due_movies(adaptive_search_policy, exclusion_clause):
    statement = (
        due_missing_languages_statement('movie', adaptive_search_policy)
        .join(TableMovies, TableMovies.radarrId == TableMissingSubtitles.media_id)
        .where(*exclusion_clause)
        .with_only_columns(func.count(func.distinct(TableMissingSubtitles.media_id)))
        .order_by(None)
    )
    return database.execute(statement).scalar() or 0


def _movie_needs_wanted_lookup_refresh(movie):
    return (
        movie.missing_subtitles is None or
        not getattr(movie, "has_indexed_subtitles", True) or
        getattr(movie, "has_incomplete_embedded_subtitles", False)
    )


def _wanted_movie(movie, providers_list, due_languages=None, job_id=None, adaptive_search_policy=None,
                  fallback_allowed=None, defer_failed_attempts=False):
    audio_language_list = get_audio_profile_languages(movie.audio_language)
    audio_language = resolve_audio_language(audio_language_list)

    due_missing_languages = due_languages
    if due_missing_languages is None:
        due_missing_languages = get_due_missing_languages_for_media(
            'movie',
            movie.radarrId,
            adaptive_search_policy=adaptive_search_policy,
        )
    search_active_hook = globals().get("is_search_active")
    if callable(search_active_hook):
        due_missing_languages = [
            language for language in due_missing_languages
            if search_active_hook(desired_language=language, attempt_string=movie.failedAttempts)
        ]
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
                                     movie.sceneName or None,
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

    if providers_list:
        if found_any:
            refreshed_movie = database.execute(
                _WANTED_MOVIE_DETAILS_STMT,
                {"wanted_radarr_id": movie.radarrId},
            ).first()
            if not refreshed_movie:
                return

            current_missing_languages = set(get_missing_languages('movie', movie.radarrId))
            remaining_due_languages = [
                language for language in due_missing_languages
                if language in current_missing_languages
            ]
        else:
            remaining_due_languages = due_missing_languages
        if not remaining_due_languages:
            return

        if defer_failed_attempts:
            return remaining_due_languages

        updated_attempts = record_failed_subtitle_attempts('movie', movie.radarrId, remaining_due_languages)
        database.execute(
            update(TableMovies)
            .values(failedAttempts=updated_attempts)
            .where(TableMovies.radarrId == movie.radarrId))


def wanted_download_subtitles_movie(
    radarr_id,
    job_id=None,
    providers_list=None,
    movie=None,
    due_languages=None,
    adaptive_search_policy=None,
    fallback_allowed=None,
    defer_failed_attempts=False,
):
    stmt_params = {"wanted_radarr_id": radarr_id}

    if movie is not None and due_languages is not None and not _movie_needs_wanted_lookup_refresh(movie):
        if providers_list is None:
            providers_list = get_providers()
        if adaptive_search_policy is None:
            adaptive_search_policy = get_adaptive_search_policy()
        if providers_list:
            return _wanted_movie(
                movie,
                providers_list,
                due_languages=due_languages,
                job_id=job_id,
                adaptive_search_policy=adaptive_search_policy,
                fallback_allowed=fallback_allowed,
                defer_failed_attempts=defer_failed_attempts,
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
        rebuilt_wanted_state = False
        previously_indexed_subtitles = get_subtitles(radarr_id=radarr_id) or []
        if not previously_indexed_subtitles or has_unindexed_external_subtitle(previously_indexed_subtitles):
            # subtitles indexing for this movie might be incomplete, we'll do it again
            store_subtitles_movie(radarr_id)
            movie = database.execute(_WANTED_MOVIE_DETAILS_STMT, stmt_params).first()
            if not movie:
                logging.debug(f"BAZARR no movie with that radarrId can be found in database after subtitles refresh: {radarr_id}")
                return
            rebuilt_wanted_state = True
        if movie.missing_subtitles is None:
            # missing subtitles calculation for this movie is incomplete, we'll do it again
            list_missing_subtitles_movies(no=radarr_id)
            rebuilt_wanted_state = True
        if rebuilt_wanted_state:
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
        return _wanted_movie(
            movie,
            providers_list,
            due_languages=due_languages,
            job_id=job_id,
            adaptive_search_policy=adaptive_search_policy,
            fallback_allowed=fallback_allowed,
            defer_failed_attempts=defer_failed_attempts,
        )
    else:
        logging.info("BAZARR All providers are throttled")


def _record_failed_movie_attempts(failed_attempt_languages):
    updated_attempts_by_movie = record_failed_subtitle_attempts_map(
        'movie',
        failed_attempt_languages,
    )
    if not updated_attempts_by_movie:
        return

    update_items = list(updated_attempts_by_movie.items())
    if (
        len(update_items) >= _TEMP_FAILED_ATTEMPT_UPDATE_MIN_SIZE and
        database.bind.engine.dialect.name == 'sqlite'
    ):
        connection = database.connection()
        connection.exec_driver_sql('DROP TABLE IF EXISTS temp_failed_attempt_updates')
        connection.exec_driver_sql(
            'CREATE TEMP TABLE temp_failed_attempt_updates '
            '(media_id INTEGER PRIMARY KEY, failedAttempts TEXT NOT NULL)'
        )
        try:
            for index in range(0, len(update_items), _FAILED_ATTEMPT_UPDATE_BATCH_SIZE):
                connection.exec_driver_sql(
                    'INSERT INTO temp_failed_attempt_updates (media_id, failedAttempts) VALUES (?, ?)',
                    update_items[index:index + _FAILED_ATTEMPT_UPDATE_BATCH_SIZE],
                )
            connection.exec_driver_sql(
                'UPDATE table_movies '
                'SET "failedAttempts" = ('
                'SELECT failedAttempts FROM temp_failed_attempt_updates '
                'WHERE media_id = table_movies."radarrId") '
                'WHERE "radarrId" IN (SELECT media_id FROM temp_failed_attempt_updates)'
            )
        finally:
            connection.exec_driver_sql('DROP TABLE IF EXISTS temp_failed_attempt_updates')
        return

    id_column = TableMovies.__table__.c.radarrId
    for index in range(0, len(update_items), _FAILED_ATTEMPT_UPDATE_BATCH_SIZE):
        chunk = dict(update_items[index:index + _FAILED_ATTEMPT_UPDATE_BATCH_SIZE])
        database.execute(
            TableMovies.__table__.update()
            .where(id_column.in_(chunk))
            .values(failedAttempts=case(chunk, value=id_column))
        )


def _record_pending_failed_movie_attempts(pending_failed_attempts):
    if not pending_failed_attempts:
        return
    _record_failed_movie_attempts(dict(pending_failed_attempts))
    pending_failed_attempts.clear()


def wanted_search_missing_subtitles_movies(job_id=None, wait_for_completion=False):
    if not job_id:
        jobs_queue.add_job_from_function("Searching for missing movies subtitles", is_progress=True,
                                         wait_for_completion=wait_for_completion)
        return

    adaptive_search_policy = get_adaptive_search_policy()
    exclusion_clause = get_exclusion_clause('movie')
    count_movies = _count_searchable_due_movies(adaptive_search_policy, exclusion_clause)
    jobs_queue.update_job_progress(job_id=job_id, progress_max=count_movies)

    if count_movies == 0:
        jobs_queue.update_job_progress(job_id=job_id, progress_value='max')
        throttled = False
    else:
        throttled = False

    fallback_allowed = settings.general.use_whisper_fallback
    pending_failed_attempts = {}
    processed_count = 0
    if count_movies:
        for due_languages_by_chunk in iter_due_missing_languages_maps(
            'movie',
            adaptive_search_policy=adaptive_search_policy,
            batch_size=_DUE_MOVIE_DETAILS_BATCH_SIZE,
        ):
            due_movie_id_chunk = list(due_languages_by_chunk)
            base_conditions = [TableMovies.radarrId.in_(due_movie_id_chunk)]
            base_conditions += exclusion_clause
            for movie in database.execute(
                _WANTED_MOVIES_SELECT
                .where(reduce(operator.and_, base_conditions))
            ):
                due_languages = due_languages_by_chunk.get(movie.radarrId)
                if not due_languages:
                    continue

                processed_count += 1
                jobs_queue.update_job_progress(job_id=job_id, progress_value=processed_count,
                                               progress_message=movie.title)

                providers = get_providers()
                if providers:
                    if _movie_needs_wanted_lookup_refresh(movie):
                        remaining_due_languages = wanted_download_subtitles_movie(
                            movie.radarrId,
                            job_id=job_id,
                            providers_list=providers,
                            movie=movie,
                            due_languages=due_languages,
                            adaptive_search_policy=adaptive_search_policy,
                            fallback_allowed=fallback_allowed,
                            defer_failed_attempts=True,
                        )
                        if remaining_due_languages:
                            pending_failed_attempts[movie.radarrId] = remaining_due_languages
                    else:
                        remaining_due_languages = _wanted_movie(
                            movie,
                            providers,
                            due_languages=due_languages,
                            job_id=job_id,
                            adaptive_search_policy=adaptive_search_policy,
                            fallback_allowed=fallback_allowed,
                            defer_failed_attempts=True,
                        )
                        if remaining_due_languages:
                            pending_failed_attempts[movie.radarrId] = remaining_due_languages

                    # make sure to override the progress value updated by the subtitles synchronization
                    jobs_queue.update_job_progress(job_id=job_id, progress_value=processed_count,
                                                   progress_max=count_movies)
                else:
                    logging.info("BAZARR All providers are throttled")
                    throttled = True
                    break
            if not throttled:
                _record_pending_failed_movie_attempts(pending_failed_attempts)
            if throttled:
                break

    _record_pending_failed_movie_attempts(pending_failed_attempts)

    outcome_msg = ("All providers throttled" if throttled
                   else "Search completed")
    jobs_queue.update_job_progress(job_id=job_id, progress_message=outcome_msg)
    jobs_queue.update_job_name(job_id=job_id, new_job_name="Searched for missing movies subtitles")
    logging.info('BAZARR Finished searching for missing Movies Subtitles. Check History for more information.')

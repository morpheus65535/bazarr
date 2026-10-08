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
                          get_profile_id, get_subtitles)
from app.jobs_queue import jobs_queue, JobCanceled
from app.event_handler import event_stream

from ..download import generate_subtitles


def movies_download_subtitles(no, job_id=None, job_sub_function=False):
    if not job_sub_function and not job_id:
        jobs_queue.add_job_from_function(f"""Downloading missing subtitles for """
                                         f"""{database.scalar(select(TableMovies.title)
                                                              .where(TableMovies.radarrId == no))}"""
                                         f""" ({database.scalar(select(TableMovies.year)
                                                                .where(TableMovies.radarrId == no))})""",
                                         is_progress=True)
        return

    # When this runs as one step of a batch task (job_sub_function), the batch owns the job's progress, name and
    # message: don't let this movie overwrite them.
    own_job = not job_sub_function

    conditions = [(TableMovies.radarrId == no)]
    conditions += get_exclusion_clause('movie')
    stmt = select(TableMovies.path,
                  TableMovies.missing_subtitles,
                  TableMovies.audio_language,
                  TableMovies.radarrId,
                  TableMovies.sceneName,
                  TableMovies.title,
                  TableMovies.year,
                  TableMovies.tags,
                  TableMovies.monitored,
                  TableMovies.profileId) \
        .where(reduce(operator.and_, conditions))
    movie = database.execute(stmt).first()

    if not movie:
        logging.debug(f"BAZARR no movie with that radarrId can be found in database: {no}")
        if own_job:
            jobs_queue.update_job_progress(job_id=job_id, progress_message="Movie not found in database.")
        return

    previously_indexed_subtitles = get_subtitles(radarr_id=movie.radarrId)

    if not len(previously_indexed_subtitles) or \
            any([not x['embedded_track_id'] for x in previously_indexed_subtitles if not x['path']]):
        # subtitles indexing for this movie might be incomplete, we'll do it again
        store_subtitles_movie(no)
        movie = database.execute(stmt).first()
    elif movie.missing_subtitles is None:
        # missing subtitles calculation for this movie is incomplete, we'll do it again
        list_missing_subtitles_movies(no=no)
        movie = database.execute(stmt).first()

    moviePath = path_mappings.path_replace_movie(movie.path)

    if not os.path.exists(moviePath):
        logging.debug(f"BAZARR movie file not found. Path mapping issue?: {moviePath}")
        if own_job:
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

    if own_job:
        jobs_queue.update_job_progress(job_id=job_id, progress_max=count_movie, progress_message=movie.title)

    providers_list = get_providers()

    downloaded_count = 0
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
                                             job_id=job_id if own_job else None):
                if result:
                    store_subtitles_movie(no)
                    history_log_movie(1, no, result)
                    send_notifications_movie(no, result.message)
                    downloaded_count += 1
        outcome_msg = (f"{downloaded_count} subtitle(s) downloaded"
                       if downloaded_count else "No subtitles found")
    else:
        logging.info("BAZARR All providers are throttled")
        outcome_msg = "All providers throttled"

    if own_job:
        jobs_queue.update_job_progress(job_id=job_id, progress_value="max",
                                       progress_message=outcome_msg)
        jobs_queue.update_job_name(job_id=job_id,
                                   new_job_name=f"Downloaded missing subtitles for {movie.title} ({movie.year})")


def movies_batch_download_subtitles(movie_ids, job_id=None):
    """Single, cancellable task that searches missing subtitles for each selected movie, one after the other."""
    if not job_id:
        # add_job_from_function() binds this function's local variables to its signature: don't define any other
        # local variable before calling it.
        jobs_queue.add_job_from_function(f"Searching for missing subtitles for {len(movie_ids)} selected movies",
                                         is_progress=True, is_cancellable=True)
        return

    total = len(movie_ids)
    batch_name = f"Searching for missing subtitles for {total} selected movies"
    job = jobs_queue.get_job(job_id=job_id)

    jobs_queue.update_job_progress(job_id=job_id, progress_max=total)

    skipped = 0
    throttled = False
    for i, movie_id in enumerate(movie_ids, start=1):
        if job.cancel_event.is_set():
            raise JobCanceled

        title = database.scalar(select(TableMovies.title).where(TableMovies.radarrId == movie_id))
        jobs_queue.update_job_progress(job_id=job_id, progress_value=i, progress_message=title or 'Unknown movie')

        if not get_providers():
            logging.info("BAZARR All providers are throttled")
            throttled = True
            break

        try:
            movies_download_subtitles(movie_id, job_id=job_id, job_sub_function=True)
        except JobCanceled:
            raise
        except Exception as e:
            # One movie that can't be searched (e.g. path mapping issue) must not stop the rest of the batch.
            skipped += 1
            logging.warning(f"BAZARR skipped movie {title or movie_id} ({movie_id}) while searching for missing "
                            f"subtitles: {e!r}")

        # The per movie search reports its own progress and renames the job: put the batch ones back.
        jobs_queue.update_job_progress(job_id=job_id, progress_value=i, progress_max=total,
                                      progress_message=title or 'Unknown movie')
        jobs_queue.update_job_name(job_id=job_id, new_job_name=batch_name)

    if throttled:
        outcome_msg = "All providers throttled"
    elif skipped:
        outcome_msg = f"Search completed ({skipped} skipped, see logs)"
    else:
        outcome_msg = "Search completed"
    jobs_queue.update_job_progress(job_id=job_id, progress_message=outcome_msg)
    jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Searched for missing subtitles for {total} selected movies")


def movie_download_specific_subtitles(radarr_id, language, hi, forced, job_id=None):
    if not job_id:
        return jobs_queue.add_job_from_function("Searching subtitles", progress_max=1, is_progress=False)

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

    jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Searching {language_str.upper()} for {title}")

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
            store_subtitles_movie(radarr_id)
            history_log_movie(1, radarr_id, result)
            send_notifications_movie(radarr_id, result.message)
        else:
            event_stream(type='movie', payload=radarr_id)
            return '', 204
    except OSError:
        return 'Unable to save subtitles file. Permission or path mapping issue?', 409
    else:
        jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Searched {language_str.upper()} for {title}")
        return '', 204

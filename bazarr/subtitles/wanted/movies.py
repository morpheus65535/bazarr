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
from app.config import settings
from app.database import (get_exclusion_clause, get_audio_profile_languages, get_profiles_list, TableMovies,
                          TableHistoryMovie, database, update, select, get_subtitles)
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue
from subtitles.tools.score import movie_score

from ..adaptive_searching import is_search_active, updateFailedAttempts
from ..download import generate_subtitles


def _find_existing_subtitle_path(subtitles_field, source_lang):
    """Return on-disk path of an existing external subtitle for source_lang
    (ignoring :hi / :forced variants), or None. subtitles_field is the raw
    DB value (a python-literal list of [code, path, length] tuples)."""
    if not subtitles_field:
        return None
    try:
        entries = ast.literal_eval(subtitles_field)
    except (ValueError, SyntaxError):
        return None
    # First pass: prefer plain (non-HI, non-forced) source language
    for entry in entries:
        if not entry or len(entry) < 2:
            continue
        code = (entry[0] or '')
        path = entry[1]
        if code == source_lang and path and os.path.exists(path):
            return path
    # Fallback: accept any source-language variant
    for entry in entries:
        if not entry or len(entry) < 2:
            continue
        code = (entry[0] or '').split(':')[0]
        path = entry[1]
        if code == source_lang and path and os.path.exists(path):
            return path
    return None


def _wanted_movie(movie, providers_list, job_id=None):
    audio_language_list = get_audio_profile_languages(movie.audio_language)
    if len(audio_language_list) > 0:
        audio_language = audio_language_list[0]['name']
    else:
        audio_language = 'None'

    # Pre-resolve which missing languages can be satisfied by translating an
    # existing on-disk subtitle. For those, queue the translation directly and
    # skip the provider search to avoid wasting a provider call.
    profile = get_profiles_list(profile_id=movie.profileId) if movie.profileId else None
    translate_from_map = {}
    if profile:
        for prof_item in profile.get('items', []):
            src = prof_item.get('translate_from')
            if src:
                translate_from_map[prof_item.get('language')] = {
                    'from': src,
                    'hi': prof_item.get('hi') == 'True',
                    'forced': prof_item.get('forced') == 'True',
                }

    languages = []
    languages_to_stamp = []
    video_path = path_mappings.path_replace_movie(movie.path)

    for language in ast.literal_eval(movie.missing_subtitles):
        lang_code = language.split(':')[0]

        # If this language is configured to translate_from another, and the
        # source subtitle exists on disk, queue translation instead of search.
        translate_cfg = translate_from_map.get(lang_code)
        if translate_cfg:
            source_srt = _find_existing_subtitle_path(movie.subtitles, translate_cfg['from'])
            if source_srt:
                # Quality gate: only auto-translate from sources whose history score
                # meets the configured minimum. Falls through to provider search
                # when score is unknown or below threshold.
                min_score = settings.translator.min_source_score
                history = database.execute(
                    select(TableHistoryMovie.score)
                    .where(TableHistoryMovie.radarrId == movie.radarrId)
                    .where(TableHistoryMovie.language == translate_cfg['from'])
                    .where(TableHistoryMovie.score.is_not(None))
                    .order_by(TableHistoryMovie.timestamp.desc())
                    .limit(1)
                ).first()
                source_score_pct = (
                    round((history.score / movie_score.max_score) * 100, 1)
                    if history and history.score else 0
                )
                if source_score_pct < min_score:
                    logging.debug(
                        f"BAZARR auto-translate (wanted-scan) skipped for {video_path}: "
                        f"source score {source_score_pct}% < threshold {min_score}% "
                        f"(falling back to provider search)"
                    )
                else:
                    try:
                        from subtitles.tools.translate.main import translate_subtitles_file
                        logging.info(f"BAZARR auto-translate (wanted-scan) queuing "
                                     f"{translate_cfg['from']} -> {lang_code} for {video_path}")
                        translate_subtitles_file(
                            video_path=video_path,
                            source_srt_file=source_srt,
                            from_lang=translate_cfg['from'],
                            to_lang=lang_code,
                            forced=language.endswith(':forced') or translate_cfg['forced'],
                            hi=language.endswith(':hi') or translate_cfg['hi'],
                            media_type='movies',
                            sonarr_series_id=None,
                            sonarr_episode_id=None,
                            radarr_id=movie.radarrId,
                            metadata=None,
                        )
                        # Skip provider search for this language — translation queued.
                        continue
                    except Exception:
                        logging.exception(f"BAZARR failed to queue auto-translate for {video_path} "
                                          f"language {lang_code}; falling back to provider search")

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
                                     job_id=job_id,
                                     fallback_allowed=settings.general.use_whisper_fallback):

        if result:
            found_any = True
            if isinstance(result, tuple) and len(result):
                result = result[0]
            store_subtitles_movie(movie.radarrId)
            history_log_movie(1, movie.radarrId, result)
            send_notifications_movie(movie.radarrId, result.message)
            event_stream(type='movie-wanted', action='delete', payload=movie.radarrId)

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

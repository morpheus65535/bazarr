# coding=utf-8
# fmt: off

from typing import cast

import logging
import operator
import time
import gc

from functools import reduce

from sqlalchemy import bindparam, func

from utilities.path_mappings import path_mappings
from subtitles.indexer.sports import store_subtitles_sports, list_missing_subtitles_sports
from sportarr.history import history_log_sports
from app.get_providers import get_providers
from app.database import (
    get_exclusion_clause, get_audio_profile_languages, TableMissingSubtitles, TableSportsLeagues, TableSportsEvents,
    TableSportsEventsSubtitles, database, select, get_sports_subtitles,
)
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue, JobCanceled
from app.config import settings

from ..adaptive_searching import AdaptiveSearchPolicy, get_adaptive_search_policy
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
from .utils import WantedSportsEvent, get_language_search_items


_WANTED_SPORTS_EVENT_DETAILS_SELECT = select(TableSportsEvents.path,
                                             TableSportsEvents.missing_subtitles_calculated,
                                             TableSportsEvents.id,
                                             TableSportsEvents.sportarrLeagueId,
                                             TableSportsEvents.audio_language,
                                             TableSportsEvents.sceneName,
                                             TableSportsEvents.title,
                                             TableSportsLeagues.profileId,
                                             select(TableSportsEventsSubtitles.id)
                                             .where(TableSportsEventsSubtitles.sportsEventId == TableSportsEvents.id)
                                             .limit(1)
                                             .exists()
                                             .label("has_indexed_subtitles"),
                                             select(TableSportsEventsSubtitles.id)
                                             .where(TableSportsEventsSubtitles.sportsEventId == TableSportsEvents.id)
                                             .where(TableSportsEventsSubtitles.path.is_(None))
                                             .where(TableSportsEventsSubtitles.embedded_track_id.is_(None))
                                             .limit(1)
                                             .exists()
                                             .label("has_incomplete_embedded_subtitles")) \
    .select_from(TableSportsEvents) \
    .join(TableSportsLeagues)
_WANTED_SPORTS_EVENT_DETAILS_STMT = _WANTED_SPORTS_EVENT_DETAILS_SELECT \
    .where(TableSportsEvents.id == bindparam("wanted_sports_event_id"))
_DUE_SPORTS_EVENT_DETAILS_BATCH_SIZE = 300


def _count_searchable_due_events(adaptive_search_policy, exclusion_clause):
    statement = (
        due_missing_languages_statement('sports', adaptive_search_policy)
        .join(TableSportsEvents, TableSportsEvents.id == TableMissingSubtitles.media_id)
        .join(TableSportsLeagues, TableSportsLeagues.sportarrLeagueId == TableSportsEvents.sportarrLeagueId)
        .where(*exclusion_clause)
        .with_only_columns(func.count(func.distinct(TableMissingSubtitles.media_id)))
        .order_by(None)
    )
    return database.execute(statement).scalar() or 0


def _event_needs_wanted_lookup_refresh(event: WantedSportsEvent) -> bool:
    return (
        not event.missing_subtitles_calculated or
        not getattr(event, "has_indexed_subtitles", True) or
        getattr(event, "has_incomplete_embedded_subtitles", False)
    )


def _wanted_event(event, providers_list, due_languages=None, job_id=None, adaptive_search_policy=None,
                  fallback_allowed=None, defer_failed_attempts=False):
    audio_language_list = get_audio_profile_languages(event.audio_language)
    audio_language = resolve_audio_language(audio_language_list)

    due_missing_languages = due_languages
    if due_missing_languages is None:
        due_missing_languages = get_due_missing_languages_for_media(
            'sports',
            event.id,
            adaptive_search_policy=adaptive_search_policy,
        )
    else:
        current_due_languages = get_due_missing_languages_map(
            'sports',
            [event.id],
            adaptive_search_policy=adaptive_search_policy,
        ).get(event.id, [])
        current_due_languages = set(current_due_languages)
        due_missing_languages = [language for language in due_missing_languages if language in current_due_languages]
    if not due_missing_languages:
        return
    if not event.path:
        logging.debug("BAZARR wanted sports event search skipped because event path is missing: %s", event.id)
        return

    if fallback_allowed is None:
        fallback_allowed = settings.general.use_whisper_fallback

    languages = get_language_search_items(due_missing_languages)
    attempted_languages = set() if defer_failed_attempts else None

    found_any = False
    for result in generate_subtitles(path_mappings.path_replace_sports(event.path),
                                     languages,
                                     audio_language,
                                     event.sceneName or None,
                                     event.title,
                                     'sports',
                                     event.profileId,
                                     check_if_still_required=True,
                                     job_id=job_id,
                                     fallback_allowed=fallback_allowed,
                                     attempted_languages=attempted_languages):
        if result:
            found_any = True
            store_subtitles_sports(event.id)
            history_log_sports(1, event.sportarrLeagueId, event.id, result)
            event_stream(type='sports-league', action='update', payload=event.sportarrLeagueId)
            event_stream(type='sports-event-wanted', action='delete', payload=event.id)

    attempted_due_languages = due_missing_languages
    if attempted_languages is not None:
        attempted_due_languages = [
            missing_language
            for missing_language, search_language in zip(due_missing_languages, languages)
            if search_language in attempted_languages
        ]

    if providers_list:
        if found_any:
            refreshed_event = database.execute(
                _WANTED_SPORTS_EVENT_DETAILS_STMT,
                {"wanted_sports_event_id": event.id},
            ).first()
            if not refreshed_event:
                return

            current_missing_languages = set(get_missing_languages('sports', event.id))
            remaining_due_languages = [
                language for language in attempted_due_languages
                if language in current_missing_languages
            ]
        else:
            remaining_due_languages = attempted_due_languages
        if not remaining_due_languages:
            return

        if defer_failed_attempts:
            return remaining_due_languages

        record_failed_subtitle_attempts('sports', event.id, remaining_due_languages)


def wanted_download_subtitles_sports(
    sports_event_id: int,
    job_id: int | None = None,
    providers_list: list[str] | None = None,
    event_details: WantedSportsEvent | None = None,
    due_languages: list[str] | None = None,
    adaptive_search_policy: AdaptiveSearchPolicy | None = None,
    fallback_allowed: bool | None = None,
    defer_failed_attempts: bool = False,
) -> list[str] | None:
    stmt_params = {"wanted_sports_event_id": sports_event_id}

    if event_details is not None and due_languages is not None and not _event_needs_wanted_lookup_refresh(event_details):
        if providers_list is None:
            providers_list = get_providers()
        if adaptive_search_policy is None:
            adaptive_search_policy = get_adaptive_search_policy()
        if providers_list:
            return _wanted_event(
                event_details,
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

    if event_details is None:
        event_details = cast(WantedSportsEvent | None,
                             database.execute(_WANTED_SPORTS_EVENT_DETAILS_STMT, stmt_params).first())

    if not event_details:
        logging.debug(f"BAZARR no sports event with that id can be found in database: {sports_event_id}")
        return
    if _event_needs_wanted_lookup_refresh(event_details):
        rebuilt_wanted_state = False
        previously_indexed_subtitles = get_sports_subtitles(sports_event_id=sports_event_id) or []
        if not previously_indexed_subtitles or has_unindexed_external_subtitle(previously_indexed_subtitles):
            # subtitles indexing for this event might be incomplete, we'll do it again
            store_subtitles_sports(sports_event_id)
            event_details = cast(WantedSportsEvent | None,
                                 database.execute(_WANTED_SPORTS_EVENT_DETAILS_STMT, stmt_params).first())
            if not event_details:
                logging.debug(f"BAZARR no sports event with that id can be found in database after subtitles "
                              f"refresh: {sports_event_id}")
                return
            rebuilt_wanted_state = True
        if not event_details.missing_subtitles_calculated:
            # missing subtitles calculation for this event is incomplete, we'll do it again
            list_missing_subtitles_sports(evno=sports_event_id)
            rebuilt_wanted_state = True
        if rebuilt_wanted_state:
            event_details = cast(WantedSportsEvent | None,
                                 database.execute(_WANTED_SPORTS_EVENT_DETAILS_STMT, stmt_params).first())
            if not event_details:
                logging.debug(f"BAZARR no sports event with that id can be found in database after "
                              f"missing-subtitles refresh: {sports_event_id}")
                return
            due_languages = None
            providers_list = None

    if providers_list is None:
        providers_list = get_providers()
    if adaptive_search_policy is None:
        adaptive_search_policy = get_adaptive_search_policy()

    if providers_list:
        return _wanted_event(
            event_details,
            providers_list,
            due_languages=due_languages,
            job_id=job_id,
            adaptive_search_policy=adaptive_search_policy,
            fallback_allowed=fallback_allowed,
            defer_failed_attempts=defer_failed_attempts,
        )
    else:
        logging.info("BAZARR All providers are throttled")


def _record_failed_event_attempts(failed_attempt_languages, attempted_at_by_media_id=None):
    return record_failed_subtitle_attempts_map(
        'sports',
        failed_attempt_languages,
        attempted_at_by_media_id=attempted_at_by_media_id,
    )


def _record_pending_failed_event_attempts(pending_failed_attempts):
    if not pending_failed_attempts:
        return
    languages_by_media_id = {}
    attempted_at_by_media_id = {}
    for media_id, (languages, attempted_at) in pending_failed_attempts.items():
        languages_by_media_id[media_id] = languages
        attempted_at_by_media_id[media_id] = attempted_at
    _record_failed_event_attempts(languages_by_media_id, attempted_at_by_media_id)
    pending_failed_attempts.clear()


def wanted_search_missing_subtitles_sports(job_id=None, wait_for_completion=False):
    if not job_id:
        jobs_queue.add_job_from_function("Searching for missing sports events subtitles", is_progress=True,
                                         wait_for_completion=wait_for_completion, is_cancellable=True)
        return
    pending_failed_attempts = {}
    try:
        _run_wanted_search_missing_subtitles_sports(job_id, pending_failed_attempts)
    except Exception:
        try:
            _record_pending_failed_event_attempts(pending_failed_attempts)
        except Exception:
            logging.exception("BAZARR failed to save completed sports search attempts after a search error")
        raise


def _run_wanted_search_missing_subtitles_sports(job_id, pending_failed_attempts):
    job = jobs_queue.get_job(job_id=job_id)
    adaptive_search_policy = get_adaptive_search_policy()
    exclusion_clause = get_exclusion_clause('sports')
    count_events = _count_searchable_due_events(adaptive_search_policy, exclusion_clause)
    jobs_queue.update_job_progress(job_id=job_id, progress_max=count_events)

    if count_events == 0:
        jobs_queue.update_job_progress(job_id=job_id, progress_value='max')
    throttled = False

    fallback_allowed = settings.general.use_whisper_fallback
    processed_count = 0
    if count_events:
        eligible_media_ids = (
            select(TableSportsEvents.id)
            .join(TableSportsLeagues, TableSportsLeagues.sportarrLeagueId == TableSportsEvents.sportarrLeagueId)
            .where(*exclusion_clause)
        )
        for due_languages_by_chunk in iter_due_missing_languages_maps(
            'sports',
            adaptive_search_policy=adaptive_search_policy,
            batch_size=_DUE_SPORTS_EVENT_DETAILS_BATCH_SIZE,
            eligible_media_ids=eligible_media_ids,
        ):
            due_event_id_chunk = list(due_languages_by_chunk)
            base_conditions = [TableSportsEvents.id.in_(due_event_id_chunk)]
            base_conditions += exclusion_clause
            for event in database.execute(
                _WANTED_SPORTS_EVENT_DETAILS_SELECT
                .with_only_columns(
                    TableSportsEvents.id,
                    TableSportsLeagues.title,
                    TableSportsEvents.partName,
                    TableSportsEvents.title.label('eventTitle'),
                )
                .where(reduce(operator.and_, base_conditions))
            ):
                if job.cancel_event.is_set():
                    raise JobCanceled

                due_languages = due_languages_by_chunk.get(event.id)
                if not due_languages:
                    continue

                processed_count += 1
                # The part identifies which file of the event this is, so it belongs in
                # the progress message. Most events have one file and no part name.
                part = f' - {event.partName}' if event.partName else ''
                jobs_queue.update_job_progress(
                    job_id=job_id,
                    progress_value=processed_count,
                    progress_message=f'{event.title} - {event.eventTitle}{part}',
                )

                providers = get_providers()
                if providers:
                    remaining_due_languages = wanted_download_subtitles_sports(
                        event.id,
                        job_id=job_id,
                        providers_list=providers,
                        due_languages=due_languages,
                        adaptive_search_policy=adaptive_search_policy,
                        fallback_allowed=fallback_allowed,
                        defer_failed_attempts=True,
                    )
                    if remaining_due_languages:
                        pending_failed_attempts[event.id] = (remaining_due_languages, time.time())

                    # make sure to override the progress value updated by the subtitles synchronization
                    jobs_queue.update_job_progress(job_id=job_id, progress_value=processed_count,
                                                   progress_max=count_events)
                else:
                    logging.info("BAZARR All providers are throttled")
                    throttled = True
                    break
            if not throttled:
                _record_pending_failed_event_attempts(pending_failed_attempts)
            if throttled:
                break

    _record_pending_failed_event_attempts(pending_failed_attempts)

    outcome_msg = ("All providers throttled" if throttled
                   else "Search completed")
    jobs_queue.update_job_progress(job_id=job_id, progress_message=outcome_msg)
    jobs_queue.update_job_name(job_id=job_id, new_job_name="Searched for missing sports events subtitles")
    logging.info('BAZARR Finished searching for missing sports events Subtitles. Check History for more information.')

    gc.collect()

# coding=utf-8
# fmt: off

import ast
import logging
import operator
import gc

from functools import reduce

from utilities.path_mappings import path_mappings
from subtitles.indexer.sports import store_subtitles_sports, list_missing_subtitles_sports
from sportarr.history import history_log_sports
from app.get_providers import get_providers
from app.database import get_exclusion_clause, get_audio_profile_languages, TableSportsLeagues, TableSportsEvents, \
    database, update, select, get_sports_subtitles
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue
from app.config import settings

from ..adaptive_searching import is_search_active, updateFailedAttempts
from ..download import generate_subtitles


def _wanted_event(event, providers_list, job_id=None):
    audio_language_list = get_audio_profile_languages(event.audio_language)
    if len(audio_language_list) > 0:
        audio_language = audio_language_list[0]['name']
    else:
        audio_language = 'None'

    languages = []
    languages_to_stamp = []
    for language in ast.literal_eval(event.missing_subtitles):
        if is_search_active(desired_language=language, attempt_string=event.failedAttempts):
            hi_ = "True" if language.endswith(':hi') else "False"
            forced_ = "True" if language.endswith(':forced') else "False"
            languages.append((language.split(":")[0], hi_, forced_))
            languages_to_stamp.append(language)

        else:
            logging.debug(
                f"BAZARR Search is throttled by adaptive search for this sports event {event.path} and "
                f"language: {language}")

    found_any = False
    for result in generate_subtitles(path_mappings.path_replace_sports(event.path),
                                     languages,
                                     audio_language,
                                     str(event.sceneName),
                                     event.title,
                                     'sports',
                                     event.profileId,
                                     check_if_still_required=True,
                                     job_id=job_id,
                                     fallback_allowed=settings.general.use_whisper_fallback):
        if result:
            found_any = True
            store_subtitles_sports(event.id)
            history_log_sports(1, event.sportarrLeagueId, event.id, result)
            event_stream(type='sports-league', action='update', payload=event.sportarrLeagueId)
            event_stream(type='sports-event-wanted', action='delete', payload=event.id)

    if not found_any and providers_list:
        for language in languages_to_stamp:
            updated = updateFailedAttempts(
                desired_language=language,
                attempt_string=event.failedAttempts)
            database.execute(
                update(TableSportsEvents)
                .values(failedAttempts=updated)
                .where(TableSportsEvents.id == event.id))


def wanted_download_subtitles_sports(sports_event_id, job_id=None):
    stmt = select(TableSportsEvents.path,
                  TableSportsEvents.missing_subtitles,
                  TableSportsEvents.id,
                  TableSportsEvents.sportarrLeagueId,
                  TableSportsEvents.audio_language,
                  TableSportsEvents.sceneName,
                  TableSportsEvents.failedAttempts,
                  TableSportsEvents.title,
                  TableSportsLeagues.profileId) \
        .select_from(TableSportsEvents) \
        .join(TableSportsLeagues) \
        .where((TableSportsEvents.id == sports_event_id))
    event_details = database.execute(stmt).first()

    previously_indexed_subtitles = get_sports_subtitles(sports_event_id=sports_event_id)

    if not event_details:
        logging.debug(f"BAZARR no sports event with that id can be found in database: {sports_event_id}")
        return
    elif not len(previously_indexed_subtitles) or \
            any([not x['embedded_track_id'] for x in previously_indexed_subtitles if not x['path']]):
        # subtitles indexing for this event might be incomplete, we'll do it again
        store_subtitles_sports(sports_event_id)
        event_details = database.execute(stmt).first()
    elif event_details.missing_subtitles is None:
        # missing subtitles calculation for this event is incomplete, we'll do it again
        list_missing_subtitles_sports(evno=sports_event_id)
        event_details = database.execute(stmt).first()

    providers_list = get_providers()

    if providers_list:
        _wanted_event(event_details, providers_list, job_id=job_id)
    else:
        logging.info("BAZARR All providers are throttled")


def wanted_search_missing_subtitles_sports(job_id=None, wait_for_completion=False):
    if not job_id:
        jobs_queue.add_job_from_function("Searching for missing sports events subtitles", is_progress=True,
                                         wait_for_completion=wait_for_completion)
        return

    conditions = [(TableSportsEvents.missing_subtitles.is_not(None)),
                  (TableSportsEvents.missing_subtitles != '[]')]
    conditions += get_exclusion_clause('sports')
    events = database.execute(
        select(TableSportsEvents.sportarrLeagueId,
               TableSportsEvents.id,
               TableSportsLeagues.tags,
               TableSportsEvents.monitored,
               TableSportsLeagues.title,
               TableSportsEvents.partName,
               TableSportsEvents.title.label('eventTitle'),
               TableSportsLeagues.sport)
        .select_from(TableSportsEvents)
        .join(TableSportsLeagues)
        .where(reduce(operator.and_, conditions))) \
        .all()

    count_events = len(events)
    jobs_queue.update_job_progress(job_id=job_id, progress_max=count_events)

    if count_events == 0:
        jobs_queue.update_job_progress(job_id=job_id, progress_value='max')

    throttled = False
    for i, event in enumerate(events, start=1):
        # The part identifies which file of the event this is, so it belongs in
        # the progress message. Most events have one file and no part name.
        part = f' - {event.partName}' if event.partName else ''
        jobs_queue.update_job_progress(job_id=job_id, progress_value=i,
                                       progress_message=f'{event.title} - {event.eventTitle}{part}')

        providers = get_providers()
        if providers:
            wanted_download_subtitles_sports(event.id, job_id=job_id)

            # make sure to override the progress value updated by the subtitles synchronization
            jobs_queue.update_job_progress(job_id=job_id, progress_value=i, progress_max=count_events)
        else:
            logging.info("BAZARR All providers are throttled")
            throttled = True
            break

    outcome_msg = ("All providers throttled" if throttled
                   else "Search completed")
    jobs_queue.update_job_progress(job_id=job_id, progress_message=outcome_msg)
    jobs_queue.update_job_name(job_id=job_id, new_job_name="Searched for missing sports events subtitles")
    logging.info('BAZARR Finished searching for missing sports events Subtitles. Check History for more information.')

    gc.collect()

# coding=utf-8
# fmt: off

import ast
import logging
import operator
import os

from functools import reduce

from utilities.path_mappings import path_mappings
from subtitles.indexer.sports import store_subtitles_sports, list_missing_subtitles_sports
from sportarr.history import history_log_sports
from app.get_providers import get_providers
from app.database import (get_exclusion_clause, get_audio_profile_languages, TableSportsLeagues, TableSportsEvents,
                          database, select, get_sports_subtitles, get_profile_id)
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue
from app.config import settings

from ..download import generate_subtitles


def _event_label(event):
    # The part identifies which file of the event this is. Most events have one
    # file and no part name.
    part = f' - {event.partName}' if event.partName else ''
    return f'{event.title} - {event.eventTitle}{part}'


def league_download_subtitles(no, job_id=None, job_sub_function=False):
    if not job_sub_function and not job_id:
        jobs_queue.add_job_from_function(f"""Downloading missing subtitles for {database.scalar(
            select(TableSportsLeagues.title).where(TableSportsLeagues.sportarrLeagueId == no))
            or 'Unknown League'}""", is_progress=True)
        return

    league_row = database.execute(
        select(TableSportsLeagues.path,
               TableSportsLeagues.title)
        .where(TableSportsLeagues.sportarrLeagueId == no))\
        .first()

    if league_row and not os.path.exists(path_mappings.path_replace_sports(league_row.path)):
        raise OSError

    conditions = [(TableSportsEvents.sportarrLeagueId == no),
                  (TableSportsEvents.missing_subtitles != '[]')]
    conditions += get_exclusion_clause('sports')
    events_details = database.execute(
        select(TableSportsEvents.id,
               TableSportsLeagues.title,
               TableSportsEvents.partName,
               TableSportsEvents.title.label('eventTitle'),
               TableSportsEvents.missing_subtitles)
        .select_from(TableSportsEvents)
        .join(TableSportsLeagues)
        .where(reduce(operator.and_, conditions))) \
        .all()
    throttled = False
    if not events_details:
        logging.debug(f"BAZARR no sports event for that league have been found in database or they have all been "
                      f"ignored because of monitored status, sport or league tags: {no}")
    else:
        count_events_details = len(events_details)

        jobs_queue.update_job_progress(job_id=job_id, progress_max=count_events_details)
        for i, event in enumerate(events_details, start=1):
            jobs_queue.update_job_progress(job_id=job_id, progress_value=i, progress_message=_event_label(event))

            providers_list = get_providers()
            fallback_allowed = settings.general.use_whisper_fallback and settings.general.use_whisper_fallback_series
            if providers_list:
                sports_event_download_subtitles(no=event.id, job_id=job_id, job_sub_function=True,
                                                providers_list=providers_list, fallback_allowed=fallback_allowed)
            else:
                jobs_queue.update_job_progress(job_id=job_id, progress_value=count_events_details)
                logging.info("BAZARR All providers are throttled")
                throttled = True
                break

    outcome_msg = ("All providers throttled" if throttled
                   else "Search completed")
    jobs_queue.update_job_progress(job_id=job_id, progress_message=outcome_msg)
    jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Downloaded missing subtitles for {league_row.title}")


def sports_event_download_subtitles(no, job_id=None, job_sub_function=False, providers_list=None,
                                    fallback_allowed=False):
    if not job_sub_function and not job_id:
        jobs_queue.add_job_from_function(f"""Downloading missing subtitles for {database.scalar(
            select(TableSportsEvents.title).where(TableSportsEvents.id == no)) or 'Unknown Event'}""",
                                         is_progress=True)
        return

    conditions = [(TableSportsEvents.id == no)]
    conditions += get_exclusion_clause('sports')
    stmt = select(TableSportsEvents.path,
                  TableSportsEvents.missing_subtitles,
                  TableSportsEvents.monitored,
                  TableSportsEvents.id,
                  TableSportsEvents.sceneName,
                  TableSportsLeagues.tags,
                  TableSportsLeagues.title,
                  TableSportsLeagues.sportarrLeagueId,
                  TableSportsEvents.audio_language,
                  TableSportsLeagues.sport,
                  TableSportsEvents.title.label('eventTitle'),
                  TableSportsEvents.partName,
                  TableSportsLeagues.profileId) \
        .select_from(TableSportsEvents) \
        .join(TableSportsLeagues) \
        .where(reduce(operator.and_, conditions))
    event = database.execute(stmt).first()

    if not event:
        logging.debug(f"BAZARR no sports event with that id can be found in database: {no}")
        jobs_queue.update_job_progress(job_id=job_id, progress_message="Sports event not found in database.")
        return

    previously_indexed_subtitles = get_sports_subtitles(sports_event_id=event.id)

    if not len(previously_indexed_subtitles) or \
            any([not x['embedded_track_id'] for x in previously_indexed_subtitles if not x['path']]):
        # subtitles indexing for this event might be incomplete, we'll do it again
        store_subtitles_sports(event.id)
        event = database.execute(stmt).first()
    elif event.missing_subtitles is None:
        # missing subtitles calculation for this event is incomplete, we'll do it again
        list_missing_subtitles_sports(evno=no)
        event = database.execute(stmt).first()

    eventPath = path_mappings.path_replace_sports(event.path)

    if not os.path.exists(eventPath):
        logging.debug(f"BAZARR sports event file not found. Path mapping issue?: {eventPath}")
        jobs_queue.update_job_progress(job_id=job_id,
                                       progress_message=f"Sports event path doesn't exists: {eventPath}")
        raise OSError

    if not providers_list:
        providers_list = get_providers()

    downloaded_count = 0
    if providers_list:
        audio_language_list = get_audio_profile_languages(event.audio_language)
        if len(audio_language_list) > 0:
            audio_language = audio_language_list[0]['name']
        else:
            audio_language = 'None'

        languages = []

        if not job_sub_function and job_id:
            jobs_queue.update_job_progress(job_id=job_id, progress_max=1, progress_message=_event_label(event))

        for language in ast.literal_eval(event.missing_subtitles):
            if language is not None:
                hi_ = "True" if language.endswith(':hi') else "False"
                forced_ = "True" if language.endswith(':forced') else "False"
                languages.append((language.split(":")[0], hi_, forced_))

        if languages:
            for result in generate_subtitles(eventPath,
                                             languages,
                                             audio_language,
                                             str(event.sceneName),
                                             event.title,
                                             'sports',
                                             event.profileId,
                                             check_if_still_required=True,
                                             job_id=job_id,
                                             fallback_allowed=fallback_allowed):
                if result:
                    store_subtitles_sports(event.id)
                    history_log_sports(1, event.sportarrLeagueId, event.id, result)
                    downloaded_count += 1
        outcome_msg = (f"{downloaded_count} subtitle(s) downloaded"
                       if downloaded_count else "No subtitles found")
    else:
        logging.info("BAZARR All providers are throttled")
        outcome_msg = "All providers throttled"

    if not job_sub_function and job_id:
        jobs_queue.update_job_progress(job_id=job_id, progress_value='max',
                                       progress_message=outcome_msg)
        jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Downloaded missing subtitles for {event.title}")


def sports_event_download_specific_subtitles(sportarr_league_id, sports_event_id, language, hi, forced, job_id=None):
    if not job_id:
        return jobs_queue.add_job_from_function("Searching subtitles", progress_max=1, is_progress=False)

    eventInfo = database.execute(
        select(TableSportsEvents.path,
               TableSportsEvents.sceneName,
               TableSportsEvents.audio_language,
               TableSportsEvents.partName,
               TableSportsEvents.title.label('eventTitle'),
               TableSportsLeagues.title)
        .select_from(TableSportsEvents)
        .join(TableSportsLeagues)
        .where(TableSportsEvents.id == sports_event_id)) \
        .first()

    if not eventInfo:
        return 'Sports event not found', 404

    eventPath = path_mappings.path_replace_sports(eventInfo.path)

    if not os.path.exists(eventPath):
        return 'Sports event file not found. Path mapping issue?', 500

    sceneName = eventInfo.sceneName or "None"

    title = eventInfo.title

    event_long_title = _event_label(eventInfo)

    if hi == 'True':
        language_str = f'{language}:hi'
    elif forced == 'True':
        language_str = f'{language}:forced'
    else:
        language_str = language

    jobs_queue.update_job_name(job_id=job_id,
                               new_job_name=f"Searching {language_str.upper()} for {event_long_title}")

    audio_language_list = get_audio_profile_languages(eventInfo.audio_language)
    if len(audio_language_list) > 0:
        audio_language = audio_language_list[0]['name']
    else:
        audio_language = None

    try:
        result = list(generate_subtitles(eventPath, [(language, hi, forced)], audio_language, sceneName,
                                         title, 'sports',
                                         profile_id=get_profile_id(sports_event_id=sports_event_id),
                                         job_id=job_id))
        if isinstance(result, list) and len(result):
            result = result[0]
            store_subtitles_sports(sports_event_id)
            history_log_sports(1, sportarr_league_id, sports_event_id, result)
        else:
            event_stream(type='sports-event', payload=sports_event_id)
            return '', 204
    except OSError:
        return 'Unable to save subtitles file. Permission or path mapping issue?', 409
    else:
        jobs_queue.update_job_name(job_id=job_id,
                                   new_job_name=f"Searched {language_str.upper()} for {event_long_title}")
        return '', 204

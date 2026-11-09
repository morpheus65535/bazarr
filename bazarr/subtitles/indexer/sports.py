# coding=utf-8

import gc
import os
import logging

from subliminal_patch import core, search_external_subtitles
from sqlalchemy import not_, tuple_

from languages.custom_lang import CustomLanguage
from app.database import get_profiles_list, get_profile_cutoff, TableSportsEvents, TableSportsLeagues, \
    TableSportsEventsSubtitles, get_audio_profile_languages, get_sports_subtitles, database, select, insert, delete
from languages.get_languages import alpha2_from_alpha3, get_language_set
from app.config import settings
from utilities.helper import get_subtitle_destination_folder
from utilities.path_mappings import path_mappings
from utilities.video_analyzer import embedded_subs_reader
from app.event_handler import event_stream
from subtitles.indexer.utils import guess_external_subtitles, get_external_subtitles_path
from subtitles.pool import get_language_equals
from subtitles.indexer.profile_requirements import calculate_missing_subtitles, \
    calculate_enhanced_missing_subtitles
from subtitles.wanted_state import store_missing_subtitles
from app.jobs_queue import jobs_queue

gc.enable()


def store_subtitles_sports(sports_event_id, use_cache=True):
    item = database.execute(
        select(TableSportsEvents.sportarrLeagueId,
               TableSportsEvents.path,
               TableSportsEvents.file_id,
               TableSportsEvents.file_size)
        .where(TableSportsEvents.id == sports_event_id)
    ).first()

    if not item:
        logging.warning(f"BAZARR could not find sports event with ID {sports_event_id} in the database.")
        return
    else:
        original_path = item.path
        mapped_path = path_mappings.path_replace_sports(original_path)

    logging.debug(f'BAZARR started subtitles indexing for this file: {mapped_path}')
    embedded_subtitles = []
    external_subtitles = []

    if os.path.exists(mapped_path):
        if settings.general.use_embedded_subs:
            logging.debug("BAZARR is trying to index embedded subtitles.")
            try:
                subtitle_languages = embedded_subs_reader(mapped_path,
                                                          file_size=item.file_size,
                                                          sports_event_id=sports_event_id,
                                                          use_cache=use_cache)
                for track_id, subtitle_language, subtitle_forced, subtitle_hi, subtitle_codec in subtitle_languages:
                    try:
                        if (settings.general.ignore_pgs_subs and subtitle_codec.lower() == "pgs") or \
                                (settings.general.ignore_vobsub_subs and subtitle_codec.lower() == "vobsub") or \
                                (settings.general.ignore_ass_subs and subtitle_codec.lower() == "ass"):
                            logging.debug(f"BAZARR skipping {subtitle_codec} sub for language: "
                                          f"{alpha2_from_alpha3(subtitle_language)}")
                            continue

                        if alpha2_from_alpha3(subtitle_language) is not None:
                            lang = alpha2_from_alpha3(subtitle_language)
                            logging.debug(f"BAZARR embedded subtitles detected: {lang}"
                                          f"{':forced' if subtitle_forced else ''}{':hi' if subtitle_hi else ''}")
                            embedded_subtitles.append({'sportarrLeagueId': item.sportarrLeagueId,
                                                       'sportsEventId': sports_event_id,
                                                       'language': lang,
                                                       'forced': subtitle_forced,
                                                       'hi': subtitle_hi,
                                                       'embedded_track_id': track_id})
                    except Exception as error:
                        logging.debug(f"BAZARR unable to index this unrecognized language: {subtitle_language} "
                                      f"({error})")

                database.execute(
                    delete(TableSportsEventsSubtitles)
                    .where(TableSportsEventsSubtitles.sportsEventId == sports_event_id)
                    .where(TableSportsEventsSubtitles.path.is_(None))
                    .where(TableSportsEventsSubtitles.embedded_track_id.is_(None))
                )

                embedded_subtitles_list = []

                if len(embedded_subtitles):
                    embedded_stmt = insert(TableSportsEventsSubtitles).values(embedded_subtitles)
                    embedded_stmt = embedded_stmt.on_conflict_do_update(
                        index_elements=['embedded_track_id', 'sportarrLeagueId', 'sportsEventId', 'language',
                                        'forced', 'hi'],
                        set_={
                            'language': embedded_stmt.excluded.language,
                            'forced': embedded_stmt.excluded.forced,
                            'hi': embedded_stmt.excluded.hi,
                            'size': embedded_stmt.excluded.size,
                            'embedded_track_id': embedded_stmt.excluded.embedded_track_id
                        },
                        index_where=TableSportsEventsSubtitles.path.is_(None)
                    )
                    database.execute(embedded_stmt)
                    embedded_subtitles_list = [
                        (x['embedded_track_id'], x['language'], x['forced'], x['hi'])
                        for x in embedded_subtitles
                    ]

                database.execute(
                    delete(TableSportsEventsSubtitles)
                    .where(TableSportsEventsSubtitles.sportsEventId == sports_event_id)
                    .where(TableSportsEventsSubtitles.path.is_(None))
                    .where(not_(tuple_(
                        TableSportsEventsSubtitles.embedded_track_id,
                        TableSportsEventsSubtitles.language,
                        TableSportsEventsSubtitles.forced,
                        TableSportsEventsSubtitles.hi,
                    ).in_(embedded_subtitles_list)))
                )
            except Exception:
                logging.exception(f"BAZARR error when trying to analyze this {os.path.splitext(mapped_path)[1]} file: "
                                  f"{mapped_path}")

        try:
            dest_folder = get_subtitle_destination_folder()
            core.CUSTOM_PATHS = [dest_folder] if dest_folder else []

            previously_indexed_subtitles = get_sports_subtitles(sports_event_id=sports_event_id)

            previously_indexed_subtitles_to_delete = \
                [path_mappings.path_replace_reverse_sports(x['path']) for x in previously_indexed_subtitles
                 if x['path'] and not os.path.isfile(x['path'])]

            if previously_indexed_subtitles_to_delete:
                database.execute(
                    delete(TableSportsEventsSubtitles)
                    .where(TableSportsEventsSubtitles.path.in_(previously_indexed_subtitles_to_delete)))

            subtitles = search_external_subtitles(mapped_path, languages=get_language_set(),
                                                  only_one=settings.general.single_language)
            full_dest_folder_path = os.path.dirname(mapped_path)
            if dest_folder:
                if settings.general.subfolder == "absolute":
                    full_dest_folder_path = dest_folder
                elif settings.general.subfolder == "relative":
                    full_dest_folder_path = os.path.join(os.path.dirname(mapped_path), dest_folder)
            subtitles = guess_external_subtitles(full_dest_folder_path, subtitles,
                                                 previously_indexed_subtitles_to_exclude=previously_indexed_subtitles)
        except Exception as e:
            logging.exception(f"BAZARR unable to index external subtitles for this file {mapped_path}: {repr(e)}")
        else:
            for subtitle, language in subtitles.items():
                subtitle_path = get_external_subtitles_path(mapped_path, subtitle)

                try:
                    subtitle_size = os.stat(subtitle_path).st_size
                except FileNotFoundError:
                    logging.debug(f"BAZARR skipping missing subtitle file: {subtitle_path}")
                    continue

                custom = CustomLanguage.found_external(subtitle, subtitle_path)
                if custom is not None:
                    logging.debug(f"BAZARR external subtitles detected: {custom}")
                    external_subtitles.append({'sportarrLeagueId': item.sportarrLeagueId,
                                               'sportsEventId': sports_event_id,
                                               'language': custom.split(':')[0],
                                               'forced': custom.endswith(':forced'),
                                               'hi': custom.endswith(':hi'),
                                               'path': path_mappings.path_replace_reverse_sports(subtitle_path),
                                               'size': subtitle_size})

                elif str(language.basename) != 'und':
                    logging.debug(f"BAZARR external subtitles detected: {language}"
                                  f"{':forced' if language.forced else ''}"
                                  f"{':hi' if language.hi else ''}")
                    external_subtitles.append({'sportarrLeagueId': item.sportarrLeagueId,
                                               'sportsEventId': sports_event_id,
                                               'language': language.basename,
                                               'forced': language.forced,
                                               'hi': language.hi,
                                               'path': path_mappings.path_replace_reverse_sports(subtitle_path),
                                               'size': subtitle_size})

            if len(external_subtitles):
                stmt = insert(TableSportsEventsSubtitles).values(external_subtitles)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['path', 'sportarrLeagueId', 'sportsEventId', 'language', 'forced', 'hi'],
                    set_={
                        'language': stmt.excluded.language,
                        'forced': stmt.excluded.forced,
                        'hi': stmt.excluded.hi,
                        'size': stmt.excluded.size
                    }
                )
                database.execute(stmt)
    else:
        logging.debug("BAZARR this file doesn't seems to exist or isn't accessible.")
        return

    logging.debug(f"BAZARR has stored those languages to DB: {embedded_subtitles + external_subtitles}")

    list_missing_subtitles_sports(evno=sports_event_id)

    logging.debug(f'BAZARR ended subtitles indexing for this file: {mapped_path}')


def list_missing_subtitles_sports(
    no: int | None = None,
    evno: int | None = None,
    job_id: int | None = None,
) -> None:
    stmt = select(TableSportsLeagues.sportarrLeagueId,
                  TableSportsEvents.id.label("sportsEventId"),
                  TableSportsLeagues.profileId,
                  TableSportsEvents.audio_language) \
        .select_from(TableSportsEvents) \
        .join(TableSportsLeagues)

    if evno is not None:
        events_subtitles = database.execute(stmt.where(TableSportsEvents.id == evno))
    elif no is not None:
        events_subtitles = database.execute(stmt.where(TableSportsEvents.sportarrLeagueId == no))
    else:
        events_subtitles = database.execute(stmt)

    use_embedded_subs = settings.general.use_embedded_subs

    # Get language equals configuration
    lang_equals = core._LanguageEquals(get_language_equals())

    for event_subtitles in events_subtitles:
        missing_subtitles_text = '[]'
        if event_subtitles.profileId:
            audio_language_codes = {
                x['code2']
                for x in get_audio_profile_languages(event_subtitles.audio_language)
            }
            matches_audio = lambda language: language['language'] in audio_language_codes

            # get desired subtitles
            desired_subtitles_temp = get_profiles_list(profile_id=event_subtitles.profileId)
            profile_items = desired_subtitles_temp.get('items', []) if isinstance(desired_subtitles_temp, dict) else []
            if not isinstance(profile_items, (list, tuple)):
                profile_items = []

            # get existing subtitles
            actual_subtitles_temp = get_sports_subtitles(sports_event_id=event_subtitles.sportsEventId) or []
            if not use_embedded_subs:
                actual_subtitles_temp = [x for x in actual_subtitles_temp if isinstance(x, dict) and x.get('path')]

            profile_groups = desired_subtitles_temp.get('groups') if isinstance(desired_subtitles_temp, dict) else None
            if profile_groups is not None:
                missing_subtitles_list = calculate_enhanced_missing_subtitles(
                    profile_groups, desired_subtitles_temp.get('cutoff'), actual_subtitles_temp, matches_audio,
                    lang_equals)
            else:
                missing_subtitles_list = calculate_missing_subtitles(
                    profile_items, get_profile_cutoff(profile_id=event_subtitles.profileId), actual_subtitles_temp,
                    matches_audio, lang_equals)
            missing_subtitles_text = str(missing_subtitles_list)

        store_missing_subtitles(
            TableSportsEvents.__table__, 'id', 'sports', event_subtitles.sportsEventId,
            missing_subtitles_text,
        )

        event_stream(type='sports-event', payload=event_subtitles.sportsEventId)
        event_stream(type='sports-event-wanted', action='update', payload=event_subtitles.sportsEventId)
    event_stream(type='badges')


def sports_full_scan_subtitles(job_id=None, use_cache=None, wait_for_completion=False):
    if not job_id:
        jobs_queue.add_job_from_function("Indexing all existing sports events subtitles", is_progress=True,
                                         wait_for_completion=wait_for_completion)
        return

    if use_cache is None:
        use_cache = settings.sportarr.use_ffprobe_cache

    events = database.execute(
        select(TableSportsEvents.path,
               TableSportsLeagues.title,
               TableSportsEvents.title.label("eventTitle"),
               TableSportsEvents.id)
        .select_from(TableSportsEvents)
        .join(TableSportsLeagues)
    ).all()

    jobs_queue.update_job_progress(job_id=job_id, progress_max=len(events), progress_message='Indexing')
    for i, event in enumerate(events, start=1):
        jobs_queue.update_job_progress(job_id=job_id, progress_value=i,
                                       progress_message=f"{event.title} - {event.eventTitle}")
        store_subtitles_sports(event.id, use_cache=use_cache)

    logging.info('BAZARR All existing sports events subtitles indexed from disk.')

    jobs_queue.update_job_name(job_id=job_id, new_job_name="Indexed all existing sports events subtitles")

    gc.collect()


def sports_scan_subtitles(no):
    events = database.execute(
        select(TableSportsEvents.id)
        .where(TableSportsEvents.sportarrLeagueId == no)
        .order_by(TableSportsEvents.id)) \
        .all()

    for event in events:
        store_subtitles_sports(event.id, use_cache=False)

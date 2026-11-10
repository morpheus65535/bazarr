# coding=utf-8

import logging

from sqlalchemy.exc import IntegrityError
from datetime import datetime

from constants import MINIMUM_VIDEO_SIZE
from app.database import database, TableSportsLeagues, TableSportsEvents, update, insert, select
from app.config import settings
from utilities.helper import bool_map
from utilities.path_mappings import path_mappings
from app.event_handler import event_stream
from subtitles.indexer.sports import store_subtitles_sports
from subtitles.wanted_state import delete_media_and_wanted_search_state

from .parser import eventParser
from .utils import get_events_from_sportarr_api

FEATURE_PREFIX = "SYNC_EVENTS "


def trace(message):
    if settings.general.debug:
        logging.debug(FEATURE_PREFIX + message)


def get_event_row_id(sportarr_event_id, part_number):
    # The row id is not known until the insert runs, and the indexer needs it.
    row = database.execute(
        select(TableSportsEvents.id)
        .where(TableSportsEvents.sportarrEventId == sportarr_event_id)
        .where(TableSportsEvents.partNumber == part_number)).first()
    return row[0] if row else None


def _has_part_number(file):
    if not isinstance(file, dict):
        return False
    part_number = file.get('partNumber')
    return part_number is None or (type(part_number) is int and part_number >= 0)


def _has_usable_event_file(file):
    # None means the response cannot tell us whether a known file was removed.
    file_path = file.get('filePath')
    if not isinstance(file_path, str) or not file_path.strip():
        return None
    if type(file.get('id')) is not int or file['id'] <= 0:
        return None

    try:
        file_size = int(file['size'])
    except (KeyError, TypeError, ValueError):
        return None

    return file_size > MINIMUM_VIDEO_SIZE


def get_events_monitored_table(league_id):
    events_monitored = database.execute(
        select(TableSportsEvents.sportarrEventId, TableSportsEvents.monitored)
        .where(TableSportsEvents.sportarrLeagueId == league_id))\
        .all()
    return dict((x, y) for x, y in events_monitored)


def sync_events(league_id):
    logging.debug(f'BAZARR Starting events sync from Sportarr for league ID {league_id}.')
    apikey_sportarr = settings.sportarr.apikey

    if not league_id:
        return

    # Current rows for this league, keyed by the event and its part
    current_events_in_db_row_as_dict = {
        (row[0].sportarrEventId, row[0].partNumber): row[0].to_dict()
        for row in database.execute(
            select(TableSportsEvents)
            .where(TableSportsEvents.sportarrLeagueId == league_id))
        .all()}
    current_events_id_db_list = list(current_events_in_db_row_as_dict)

    current_events_sportarr = []
    events_to_update = []
    events_to_add = []

    events = get_events_from_sportarr_api(apikey_sportarr=apikey_sportarr, league_id=league_id)
    if not isinstance(events, list):
        # The walk failed partway, so nothing can be said about what still
        # exists. Returning stops a failed request being read as a league
        # that lost its events.
        logging.debug(f'BAZARR could not read every event page for league {league_id}, so nothing is removed.')
        return

    sync_monitored = settings.sportarr.sync_only_monitored_leagues and settings.sportarr.sync_only_monitored_events
    events_monitored = get_events_monitored_table(league_id) if sync_monitored else None
    skipped_count = 0
    complete_event_list = True

    for event in events:
        if not isinstance(event, dict) or type(event.get('id')) is not int or event['id'] <= 0:
            complete_event_list = False
            continue
        # Sportarr sets hasFile only when every monitored part has a file. A
        # partly downloaded card still has files on disk, so each file decides
        # its row.
        files = event.get('files')
        if not isinstance(files, list) or not all(_has_part_number(file) for file in files):
            # The parts cannot be identified, so keep this event's rows as they are.
            current_events_sportarr.extend(key for key in current_events_id_db_list if key[0] == event['id'])
            continue

        if sync_monitored:
            try:
                monitored_status_db = bool_map[events_monitored[event['id']]]
            except KeyError:
                monitored_status_db = None

            if monitored_status_db is None:
                # not in db, might need to add, if we have a file on disk
                pass
            elif monitored_status_db != event['monitored']:
                # monitored status changed and we don't know about it until now
                trace(f"(Monitor Status Mismatch) {event['title']}")
            elif not event['monitored']:
                # Keep unmonitored events in the seen list, otherwise they are
                # deleted from the database
                for existing_file in files:
                    current_events_sportarr.append((event['id'], existing_file.get('partNumber') or 0))
                skipped_count += 1
                continue

        # One row per playable file. A card ships prelims and a main card
        # separately, and each needs its own subtitles.
        for file in files:
            key = (event['id'], file.get('partNumber') or 0)
            usable_file = _has_usable_event_file(file)
            if usable_file is None:
                # The file data is incomplete, so a known part is kept unchanged.
                current_events_sportarr.append(key)
                continue
            if not usable_file:
                continue

            current_events_sportarr.append(key)

            parsed_event = eventParser(event, file)
            if key in current_events_in_db_row_as_dict:
                if not set(parsed_event.items()).issubset(set(current_events_in_db_row_as_dict[key].items())):
                    events_to_update.append(parsed_event)
            else:
                events_to_add.append(parsed_event)

    if sync_monitored and settings.general.debug:
        trace(f"Skipped {skipped_count} unmonitored events out of {len(events)} for league {league_id}")

    # Remove old events from DB
    events_to_delete = (
        list(set(current_events_id_db_list) - set(current_events_sportarr)) if complete_event_list else []
    )
    if not complete_event_list:
        logging.warning(f'BAZARR Skipping events deletion because Sportarr returned unidentified events for league '
                        f'{league_id}.')

    if len(events_to_delete):
        # The shared search state is keyed by the row id, not the Sportarr event id.
        row_ids_to_delete = {current_events_in_db_row_as_dict[key]['id']: key[0] for key in events_to_delete}
        try:
            deleted_row_ids = delete_media_and_wanted_search_state(
                'sports', TableSportsEvents, 'id', list(row_ids_to_delete),
            )
        except IntegrityError as e:
            logging.error(f"BAZARR cannot delete events because of {e}")
        else:
            for removed_row_id in deleted_row_ids:
                event_stream(type='sports-event', action='delete', payload=row_ids_to_delete[removed_row_id])

    # Insert new events in DB
    for added_event in events_to_add:
        try:
            added_event['created_at_timestamp'] = datetime.now()
            database.execute(insert(TableSportsEvents).values(added_event))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot insert events because of {e}. We'll try to update it instead.")
            del added_event['created_at_timestamp']
            events_to_update.append(added_event)
        else:
            row_id = get_event_row_id(added_event['sportarrEventId'], added_event['partNumber'])
            if row_id:
                store_subtitles_sports(row_id)
            event_stream(type='sports-event', payload=added_event['sportarrEventId'])

    # Update existing events in DB
    for updated_event in events_to_update:
        try:
            previous_event_data = database.execute(
                select(TableSportsEvents.id, TableSportsEvents.file_id, TableSportsEvents.path)
                .where(TableSportsEvents.sportarrEventId == updated_event['sportarrEventId'])
                .where(TableSportsEvents.partNumber == updated_event['partNumber'])
            ).first()

            updated_event['updated_at_timestamp'] = datetime.now()
            database.execute(
                update(TableSportsEvents)
                .values(updated_event)
                .where(TableSportsEvents.sportarrEventId == updated_event['sportarrEventId'])
                .where(TableSportsEvents.partNumber == updated_event['partNumber']))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot update events because of {e}")
        else:
            if previous_event_data and (previous_event_data.file_id != updated_event['file_id'] or
                                        previous_event_data.path != updated_event['path']):
                # Sportarr gives a new file_id when it replaces a file. The path can
                # stay the same through an upgrade, so the id is what proves the
                # media changed.
                logging.debug(f'BAZARR updating subtitles for event '
                              f'{path_mappings.path_replace_sports(updated_event["path"])}')
                store_subtitles_sports(previous_event_data.id)
            event_stream(type='sports-event', action='update', payload=updated_event['sportarrEventId'])

    league_title = database.execute(
        select(TableSportsLeagues.title)
        .where(TableSportsLeagues.sportarrLeagueId == league_id)).first()
    if league_title:
        logging.debug(f'BAZARR All events synced from Sportarr into database for {league_title[0]}.')

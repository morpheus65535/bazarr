# coding=utf-8

import logging

from sqlalchemy.exc import IntegrityError
from datetime import datetime

from constants import MINIMUM_VIDEO_SIZE
from app.database import database, TableSportsLeagues, TableSportsEvents, delete, update, insert, select
from app.config import settings
from utilities.helper import bool_map
from app.event_handler import event_stream

from .parser import eventParser
from .utils import get_events_from_sportarr_api

FEATURE_PREFIX = "SYNC_EVENTS "


def trace(message):
    if settings.general.debug:
        logging.debug(FEATURE_PREFIX + message)


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
    if events is None:
        # The walk failed partway, so nothing can be said about what still
        # exists. Returning stops a failed request being read as a league
        # that lost its events.
        logging.debug(f'BAZARR could not read every event page for league {league_id}, so nothing is removed.')
        return

    sync_monitored = settings.sportarr.sync_only_monitored_leagues and settings.sportarr.sync_only_monitored_events
    events_monitored = get_events_monitored_table(league_id) if sync_monitored else None
    skipped_count = 0

    for event in events:
        if not event.get('hasFile'):
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
                for existing_file in event.get('files') or []:
                    current_events_sportarr.append((event['id'], existing_file.get('partNumber') or 0))
                skipped_count += 1
                continue

        # One row per playable file. A card ships prelims and a main card
        # separately, and each needs its own subtitles.
        for file in event.get('files') or []:
            if not file.get('filePath'):
                continue
            if (file.get('size') or 0) <= MINIMUM_VIDEO_SIZE:
                continue

            key = (event['id'], file.get('partNumber') or 0)
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
    events_to_delete = list(set(current_events_id_db_list) - set(current_events_sportarr))

    for event_key in events_to_delete:
        try:
            database.execute(
                delete(TableSportsEvents)
                .where(TableSportsEvents.sportarrEventId == event_key[0])
                .where(TableSportsEvents.partNumber == event_key[1]))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot delete events because of {e}")
        else:
            event_stream(type='event', action='delete', payload=event_key[0])

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
            event_stream(type='event', payload=added_event['sportarrEventId'])

    # Update existing events in DB
    for updated_event in events_to_update:
        try:
            updated_event['updated_at_timestamp'] = datetime.now()
            database.execute(
                update(TableSportsEvents)
                .values(updated_event)
                .where(TableSportsEvents.sportarrEventId == updated_event['sportarrEventId'])
                .where(TableSportsEvents.partNumber == updated_event['partNumber']))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot update events because of {e}")
        else:
            event_stream(type='event', action='update', payload=updated_event['sportarrEventId'])

    league_title = database.execute(
        select(TableSportsLeagues.title)
        .where(TableSportsLeagues.sportarrLeagueId == league_id)).first()
    if league_title:
        logging.debug(f'BAZARR All events synced from Sportarr into database for {league_title[0]}.')

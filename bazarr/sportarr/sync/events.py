# coding=utf-8

import logging
import os

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased
from datetime import datetime
from requests.exceptions import RequestException

from constants import MINIMUM_VIDEO_SIZE
from app.database import (database, TableSportsLeagues, TableSportsEvents, TableSportsEventsSubtitles,
                          TableHistorySports, TableBlacklistSports, delete, update, insert, select)
from app.config import settings
from utilities.helper import bool_map
from utilities.path_mappings import path_mappings
from app.event_handler import event_stream
from subtitles.indexer.sports import list_missing_subtitles_sports, store_subtitles_sports
from subtitles.wanted_state import (delete_media_and_wanted_search_state, delete_wanted_search_state,
                                    _wanted_state_transaction)

from .parser import eventParser
from .utils import get_event_from_sportarr_api, get_events_from_sportarr_api, get_league_from_sportarr_api

FEATURE_PREFIX = "SYNC_EVENTS "

# Rows read in one query, below the SQLite limit on bound parameters.
QUERY_CHUNK_SIZE = 500

# Results of sync_one_event.
EVENT_SYNCED = 'synced'
EVENT_SKIPPED = 'skipped'
EVENT_NEEDS_LEAGUE_SYNC = 'league'


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


def _media_on_disk(row):
    try:
        return os.path.isfile(path_mappings.path_replace_sports(row['path']))
    except (TypeError, ValueError, OSError):
        return False


def get_events_monitored_table(league_id):
    events_monitored = database.execute(
        select(TableSportsEvents.sportarrEventId, TableSportsEvents.monitored)
        .where(TableSportsEvents.sportarrLeagueId == league_id))\
        .all()
    return dict((x, y) for x, y in events_monitored)


def league_in_bazarr(league_id):
    return database.execute(
        select(TableSportsLeagues.sportarrLeagueId)
        .where(TableSportsLeagues.sportarrLeagueId == league_id)).first() is not None


def league_left_unmonitored(league_id):
    """True when Bazarr holds the league as unmonitored and syncs only monitored leagues.

    The full sync then skips the league if Sportarr also has it unmonitored.
    """
    if not settings.sportarr.sync_only_monitored_leagues:
        return False
    row = database.execute(
        select(TableSportsLeagues.monitored)
        .where(TableSportsLeagues.sportarrLeagueId == league_id)).first()
    return bool(row) and not bool_map.get(row[0], False)


def _rows_by_key(*conditions):
    return {
        (row[0].sportarrEventId, row[0].partNumber): row[0].to_dict()
        for row in database.execute(select(TableSportsEvents).where(*conditions)).all()}


def _keys_by_event(rows_by_key):
    keys_by_event = {}
    for key in rows_by_key:
        keys_by_event.setdefault(key[0], []).append(key)
    return keys_by_event


class _LeagueFiles:
    """The files that one complete league read lists.

    Sportarr lists no file for an event it has just added again. Its kept
    files return only once Sportarr imports them again. A row of such an
    event keeps its subtitles while its file is still on disk, unless
    Sportarr lists that file elsewhere in the league. In every other case
    the files list decides, because Sportarr returns only the files on disk.
    """

    def __init__(self, events):
        self.file_ids = set()
        self.paths = set()
        for event in events:
            files = event.get('files') if isinstance(event, dict) else None
            for file in files if isinstance(files, list) else []:
                if isinstance(file, dict):
                    self.file_ids.add(file.get('id'))
                    self.paths.add(file.get('filePath'))

    def keeps(self, row):
        return row['file_id'] not in self.file_ids and row['path'] not in self.paths and _media_on_disk(row)


def _plan_event(event, rows_by_key, keys_by_event, events_monitored, sync_monitored, league_files=None):
    """Compare one Sportarr event with the rows Bazarr holds.

    Returns the keys that still exist, the rows to add, the rows to update,
    and the rows whose part number changes, as (row id, new row).
    """
    seen = []
    to_add = []
    to_update = []
    renumbers = []
    event_keys = keys_by_event.get(event['id'], [])

    # Sportarr sets hasFile only when every monitored part has a file. A
    # partly downloaded card still has files on disk, so each file decides
    # its row.
    files = event.get('files')
    if not isinstance(files, list) or not all(_has_part_number(file) for file in files):
        # The parts cannot be identified, so keep this event's rows as they are.
        seen.extend(event_keys)
        return seen, to_add, to_update, renumbers

    if not files:
        # This applies to monitored and unmonitored events alike, because an
        # event without files has nothing to add or update either way.
        if league_files is not None:
            seen.extend(key for key in event_keys if league_files.keeps(rows_by_key[key]))
        return seen, to_add, to_update, renumbers

    # Sportarr changes a part number in place and keeps the file id, and the
    # path too. The row that holds the file moves with it and keeps its history.
    by_file_id = {rows_by_key[key]['file_id']: key for key in event_keys if rows_by_key[key]['file_id']}
    by_path = {rows_by_key[key]['path']: key for key in event_keys if not rows_by_key[key]['file_id']}
    owners = {}
    for index, file in enumerate(files):
        owner = by_file_id.get(file.get('id')) or by_path.get(file.get('filePath'))
        if owner is not None and owner != (event['id'], file.get('partNumber') or 0):
            owners[index] = owner

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
            # deleted from the database. A renumbered file still moves its row,
            # so the row keeps its history whatever the monitoring state.
            for index, existing_file in enumerate(files):
                if index in owners and _has_usable_event_file(existing_file):
                    seen.append(owners[index])
                    renumbers.append((rows_by_key[owners[index]]['id'], eventParser(event, existing_file)))
                else:
                    seen.append((event['id'], existing_file.get('partNumber') or 0))
            return seen, to_add, to_update, renumbers

    # One row per playable file. A card ships prelims and a main card
    # separately, and each needs its own subtitles.
    for index, file in enumerate(files):
        key = (event['id'], file.get('partNumber') or 0)
        usable_file = _has_usable_event_file(file)
        if usable_file is None:
            # The file data is incomplete, so a known part is kept unchanged.
            seen.append(key)
            continue
        if not usable_file:
            continue

        parsed_event = eventParser(event, file)
        if index not in owners:
            # A renumbered file keeps the row it moves from. A row that waits at
            # its new number and owns no listed file is gone, so it is not kept.
            seen.append(key)
        if index in owners:
            seen.append(owners[index])
            renumbers.append((rows_by_key[owners[index]]['id'], parsed_event))
        elif key in rows_by_key and key not in owners.values():
            if not set(parsed_event.items()).issubset(set(rows_by_key[key].items())):
                to_update.append(parsed_event)
        else:
            to_add.append(parsed_event)

    return seen, to_add, to_update, renumbers


def _event_league_id(event, league_id=None):
    # leagueId is optional in the contract, and it is the foreign key of the row.
    event_league_id = event.get('leagueId')
    if type(event_league_id) is not int or (league_id is not None and event_league_id != league_id):
        logging.info(f"BAZARR skipped Sportarr event {event.get('id')} because it has no league in Sportarr, "
                     f"or not the league that lists it.")
        return None
    return event_league_id


def _moved_rows(to_add, rows_by_key, sportarr_event_ids, fileless_events_by_external_id, league_files):
    """Match rows of events that left Sportarr to their new events, by external id and part.

    Sportarr gives an event a new id when its league is removed and added
    again. The external id stays, so the old row moves to the new id with
    its subtitles and history instead of being deleted. Returns the moves
    with a file, the parts left to add, and the moves of parts that have no
    file in Sportarr yet.
    """
    orphans = {}
    for key, row in rows_by_key.items():
        if key[0] not in sportarr_event_ids and row.get('externalId'):
            orphans.setdefault((row['externalId'], key[1]), []).append(key)

    moves = []
    remaining = []
    for parsed_event in to_add:
        candidates = orphans.pop((parsed_event['externalId'], parsed_event['partNumber']), None) \
            if parsed_event['externalId'] else None
        if candidates and len(candidates) == 1:
            moves.append((candidates[0], parsed_event))
        else:
            remaining.append(parsed_event)

    # The new event lists no file yet, because Sportarr has not imported the
    # kept files again. The row moves to the new event id and keeps its data
    # under the same rule as a row of a fileless event.
    waiting = []
    for (external_id, part_number), candidates in orphans.items():
        new_event_id = fileless_events_by_external_id.get(external_id)
        if new_event_id is None or len(candidates) != 1 or (new_event_id, part_number) in rows_by_key:
            continue
        if league_files.keeps(rows_by_key[candidates[0]]):
            waiting.append((candidates[0], new_event_id))
    return moves, remaining, waiting


def _delete_rows(rows_by_key, keys):
    if not keys:
        return
    # The shared search state is keyed by the row id, not the Sportarr event id.
    row_ids_to_delete = {rows_by_key[key]['id']: key[0] for key in keys}
    try:
        deleted_row_ids = delete_media_and_wanted_search_state(
            'sports', TableSportsEvents, 'id', list(row_ids_to_delete),
        )
    except IntegrityError as e:
        logging.error(f"BAZARR cannot delete events because of {e}")
    else:
        for removed_row_id in deleted_row_ids:
            event_stream(type='sports-event', action='delete', payload=row_ids_to_delete[removed_row_id])


def _move_child_rows(connection, row_id: int, league_id: int) -> None:
    """Give the subtitles, history and blacklist rows of an event row the league of the row."""
    # These rows are deleted with their league. Rows that kept the old league
    # would go when that league leaves Bazarr, although the event stays.
    twin = aliased(TableSportsEventsSubtitles)
    kept_twin = select(twin.id).where(
        twin.sportsEventId == row_id, twin.id != TableSportsEventsSubtitles.id,
        twin.language == TableSportsEventsSubtitles.language, twin.forced == TableSportsEventsSubtitles.forced,
        twin.hi == TableSportsEventsSubtitles.hi,
        or_(twin.path == TableSportsEventsSubtitles.path,
            twin.embedded_track_id == TableSportsEventsSubtitles.embedded_track_id),
        or_(twin.sportarrLeagueId == league_id, twin.id < TableSportsEventsSubtitles.id)).exists()
    # The indexer can hold the same subtitles under more than one league. The
    # unique key allows one copy in the new league. That copy stays, or else
    # the oldest copy, and the others go.
    connection.execute(delete(TableSportsEventsSubtitles)
                       .where(TableSportsEventsSubtitles.sportsEventId == row_id,
                              TableSportsEventsSubtitles.sportarrLeagueId != league_id, kept_twin))
    connection.execute(update(TableSportsEventsSubtitles).values(sportarrLeagueId=league_id)
                       .where(TableSportsEventsSubtitles.sportsEventId == row_id))
    connection.execute(update(TableHistorySports).values(sportarrLeagueId=league_id)
                       .where(TableHistorySports.sportsEventId == row_id))
    connection.execute(update(TableBlacklistSports).values(sportarr_league_id=league_id)
                       .where(TableBlacklistSports.sports_event_id == row_id))


def _stranded_child_rows() -> set[tuple[int, int]]:
    """The event rows, with their league, that have subtitles, history or blacklist rows under another league."""
    stranded = set()
    child_columns = (
        (TableSportsEventsSubtitles.sportsEventId, TableSportsEventsSubtitles.sportarrLeagueId),
        (TableHistorySports.sportsEventId, TableHistorySports.sportarrLeagueId),
        (TableBlacklistSports.sports_event_id, TableBlacklistSports.sportarr_league_id),
    )
    for event_column, league_column in child_columns:
        stranded.update((row[0], row[1]) for row in database.execute(
            select(event_column, TableSportsEvents.sportarrLeagueId)
            .join(TableSportsEvents, TableSportsEvents.id == event_column)
            .where(league_column != TableSportsEvents.sportarrLeagueId)
            .distinct()))
    return stranded


def repair_stranded_child_rows() -> None:
    """Move child rows that an earlier league move left under the old league.

    The full sync runs this before it reads Sportarr, so a league that the
    sync deletes cannot take them with it.
    """
    # Earlier builds moved only the event row. The child rows stayed in the
    # old league, so a delete of that league would delete them too.
    for row_id in sorted({row_id for row_id, _ in _stranded_child_rows()}):
        try:
            with _wanted_state_transaction() as connection:
                # The stream can move the event while the repair runs, so the
                # league is read again inside the transaction.
                league_id = connection.execute(
                    select(TableSportsEvents.sportarrLeagueId).where(TableSportsEvents.id == row_id)).scalar()
                if league_id is None:
                    continue
                _move_child_rows(connection, row_id, league_id)
        except IntegrityError as e:
            logging.error(f"BAZARR cannot move the subtitles and history of sports event row {row_id} to its "
                          f"league because of {e}")
            continue
        # The new league can have another profile.
        list_missing_subtitles_sports(evno=row_id)


def _update_row(row_id, updated_event):
    previous_event_data = database.execute(
        select(TableSportsEvents.id, TableSportsEvents.file_id, TableSportsEvents.path,
               TableSportsEvents.sportarrLeagueId)
        .where(TableSportsEvents.id == row_id)
    ).first()
    new_league_id = updated_event.get('sportarrLeagueId')
    moves_league = bool(previous_event_data) and new_league_id is not None and \
        previous_event_data.sportarrLeagueId != new_league_id
    try:
        updated_event['updated_at_timestamp'] = datetime.now()
        if moves_league:
            # The row and its child rows move together. A failure leaves all of
            # them in the old league, so the next sync tries the move again.
            with _wanted_state_transaction() as connection:
                connection.execute(
                    update(TableSportsEvents)
                    .values(updated_event)
                    .where(TableSportsEvents.id == row_id))
                _move_child_rows(connection, row_id, new_league_id)
        else:
            database.execute(
                update(TableSportsEvents)
                .values(updated_event)
                .where(TableSportsEvents.id == row_id))
    except IntegrityError as e:
        logging.error(f"BAZARR cannot update events because of {e}")
        return

    if moves_league:
        logging.info(f"BAZARR moved {updated_event.get('title')} to the league that Sportarr moved it to, with its "
                     f"subtitles and history.")

    if moves_league or (previous_event_data and (previous_event_data.file_id != updated_event['file_id'] or
                                                 previous_event_data.path != updated_event['path'])):
        # Sportarr gives a new file_id when it replaces a file. The path can
        # stay the same through an upgrade, so the id is what proves the
        # media changed. A new league can have another profile, so the
        # missing subtitles are worked out again.
        logging.debug(f'BAZARR updating subtitles for event '
                      f'{path_mappings.path_replace_sports(updated_event["path"])}')
        store_subtitles_sports(row_id)
    event_stream(type='sports-event', action='update', payload=updated_event['sportarrEventId'])


def _renumber_rows(renumbers, occupants):
    """Give rows their new part numbers in one transaction.

    The rows that wait at the new numbers and own no listed file go first.
    Two parts can swap numbers, so each row then takes a number no other row
    has. A part number is never negative, and a row id is unique.
    """
    if not renumbers:
        return
    occupant_ids = {row['id']: row['sportarrEventId'] for row in occupants}
    with _wanted_state_transaction() as connection:
        if occupant_ids:
            connection.execute(delete(TableSportsEvents).where(TableSportsEvents.id.in_(list(occupant_ids))))
            delete_wanted_search_state('sports', list(occupant_ids), connection=connection)
        for row_id, _ in renumbers:
            connection.execute(update(TableSportsEvents).values(partNumber=-row_id)
                               .where(TableSportsEvents.id == row_id))
        for row_id, renumbered_event in renumbers:
            connection.execute(update(TableSportsEvents).values(partNumber=renumbered_event['partNumber'])
                               .where(TableSportsEvents.id == row_id))
    for sportarr_event_id in occupant_ids.values():
        event_stream(type='sports-event', action='delete', payload=sportarr_event_id)
    for row_id, renumbered_event in renumbers:
        # The rest of the row follows, and a changed file is indexed again.
        _update_row(row_id, renumbered_event)


def _renumbers_that_fit(rows_by_key, keys_to_delete, renumbers):
    """Drop a renumber whose new number holds a row that stays.

    That happens after an incomplete read, because nothing is deleted then.
    The row keeps its number until a later sync clears the way.
    """
    renumbers = list(renumbers)
    while True:
        moving = {row_id for row_id, _ in renumbers}
        blocked = [(row_id, renumbered) for row_id, renumbered in renumbers
                   if (key := (renumbered['sportarrEventId'], renumbered['partNumber'])) in rows_by_key
                   and key not in keys_to_delete and rows_by_key[key]['id'] not in moving]
        if not blocked:
            return renumbers
        for row_id, renumbered in blocked:
            logging.debug(f"BAZARR keeps the part number of {renumbered['title']} for now, because another row "
                          f"still holds part {renumbered['partNumber']}.")
            renumbers.remove((row_id, renumbered))


def _write_changes(rows_by_key, keys_to_delete, to_add, to_update, moves=(), waiting_moves=(), renumbers=()):
    renumbers = _renumbers_that_fit(rows_by_key, keys_to_delete, renumbers)
    destinations = {(renumbered['sportarrEventId'], renumbered['partNumber']) for _, renumbered in renumbers}
    occupants = [key for key in keys_to_delete if key in destinations]
    _delete_rows(rows_by_key, [key for key in keys_to_delete if key not in destinations])
    try:
        _renumber_rows(renumbers, [rows_by_key[key] for key in occupants])
    except IntegrityError as e:
        logging.error(f"BAZARR cannot change the part numbers of events because of {e}")

    for old_key, new_event_id in waiting_moves:
        row = rows_by_key[old_key]
        logging.info(f"BAZARR kept the subtitles of {row['title']} because Sportarr added it again with the same "
                     f"external id. Its file is still on disk, and Sportarr has not imported it again yet.")
        try:
            database.execute(
                update(TableSportsEvents)
                .values(sportarrEventId=new_event_id, updated_at_timestamp=datetime.now())
                .where(TableSportsEvents.id == row['id']))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot move event {row['title']} to its new Sportarr id because of {e}")
        else:
            event_stream(type='sports-event', action='update', payload=new_event_id)

    for old_key, moved_event in moves:
        logging.info(f"BAZARR kept the subtitles of {moved_event['title']} because Sportarr added it again with "
                     f"the same external id.")
        _update_row(rows_by_key[old_key]['id'], moved_event)

    # Insert new events in DB
    for added_event in to_add:
        try:
            added_event['created_at_timestamp'] = datetime.now()
            database.execute(insert(TableSportsEvents).values(added_event))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot insert events because of {e}. We'll try to update it instead.")
            del added_event['created_at_timestamp']
            to_update.append(added_event)
        else:
            row_id = get_event_row_id(added_event['sportarrEventId'], added_event['partNumber'])
            if row_id:
                store_subtitles_sports(row_id)
            event_stream(type='sports-event', payload=added_event['sportarrEventId'])

    # Update existing events in DB
    for updated_event in to_update:
        row_id = get_event_row_id(updated_event['sportarrEventId'], updated_event['partNumber'])
        if row_id:
            _update_row(row_id, updated_event)


def sync_events(league_id):
    """Sync every event of a league.

    Returns True when Sportarr returned the whole league, and False when
    nothing was synced.
    """
    logging.debug(f'BAZARR Starting events sync from Sportarr for league ID {league_id}.')
    apikey_sportarr = settings.sportarr.apikey

    if not league_id:
        return False

    if not league_in_bazarr(league_id):
        # Every event row needs its league row first.
        logging.debug(f'BAZARR does not hold league {league_id}, so its events are not synced.')
        return False

    events = get_events_from_sportarr_api(apikey_sportarr=apikey_sportarr, league_id=league_id)
    if not isinstance(events, list):
        # The walk failed partway, so nothing can be said about what still
        # exists. Returning stops a failed request being read as a league
        # that lost its events.
        logging.debug(f'BAZARR could not read every event page for league {league_id}, so nothing is removed.')
        return False

    # Current rows for this league, keyed by the event and its part
    current_events_in_db_row_as_dict = _rows_by_key(TableSportsEvents.sportarrLeagueId == league_id)
    listed_event_ids = _listed_event_ids(events, league_id)
    # Sportarr can move an event from another league to this one. Its rows
    # are updated here, so they keep their subtitles and history.
    current_events_in_db_row_as_dict.update(_rows_held_elsewhere(league_id, listed_event_ids))
    current_events_id_db_list = list(current_events_in_db_row_as_dict)
    keys_by_event = _keys_by_event(current_events_in_db_row_as_dict)

    current_events_sportarr = []
    events_to_update = []
    events_to_add = []
    renumbers = []

    sync_monitored = settings.sportarr.sync_only_monitored_leagues and settings.sportarr.sync_only_monitored_events
    events_monitored = get_events_monitored_table(league_id) if sync_monitored else None
    complete_event_list = True
    sportarr_event_ids = set()
    league_files = _LeagueFiles(events)
    # Fileless events of this league by external id. An id shared by two
    # events identifies neither, so it maps to None.
    fileless_events_by_external_id = {}

    for event in events:
        if not isinstance(event, dict) or type(event.get('id')) is not int or event['id'] <= 0:
            complete_event_list = False
            continue
        sportarr_event_ids.add(event['id'])

        if _event_league_id(event, league_id) is None:
            current_events_sportarr.extend(keys_by_event.get(event['id'], []))
            continue
        if event.get('externalId') and event.get('files') == []:
            fileless_events_by_external_id[event['externalId']] = \
                None if event['externalId'] in fileless_events_by_external_id else event['id']

        seen, to_add, to_update, renumbered = _plan_event(event, current_events_in_db_row_as_dict, keys_by_event,
                                                          events_monitored, sync_monitored, league_files)
        renumbers += renumbered
        current_events_sportarr += seen
        events_to_add += to_add
        events_to_update += to_update

    moves = []
    waiting_moves = []
    if complete_event_list:
        moves, events_to_add, waiting_moves = _moved_rows(events_to_add, current_events_in_db_row_as_dict,
                                                          sportarr_event_ids, fileless_events_by_external_id,
                                                          league_files)
        current_events_sportarr += [old_key for old_key, _ in moves + waiting_moves]

    # Remove old events from DB
    events_to_delete = (
        list(set(current_events_id_db_list) - set(current_events_sportarr)) if complete_event_list else []
    )
    if not complete_event_list:
        logging.warning(f'BAZARR Skipping events deletion because Sportarr returned unidentified events for league '
                        f'{league_id}.')
    events_to_delete = _keys_without_moved_events(league_id, current_events_in_db_row_as_dict, events_to_delete,
                                                  listed_event_ids)

    _write_changes(current_events_in_db_row_as_dict, events_to_delete, events_to_add, events_to_update, moves,
                   waiting_moves, renumbers)

    league_title = database.execute(
        select(TableSportsLeagues.title)
        .where(TableSportsLeagues.sportarrLeagueId == league_id)).first()
    if league_title:
        logging.debug(f'BAZARR All events synced from Sportarr into database for {league_title[0]}.')
    return True


def _listed_event_ids(events: list, league_id: int) -> set[int]:
    """The ids of the events that a league read lists for that league."""
    return {event['id'] for event in events
            if isinstance(event, dict) and type(event.get('id')) is int and event.get('leagueId') == league_id}


def _rows_held_elsewhere(league_id: int, event_ids: set[int]) -> dict:
    """The rows of these events that Bazarr holds in another league, keyed as _rows_by_key keys them."""
    rows = {}
    event_ids = sorted(event_ids)
    for offset in range(0, len(event_ids), QUERY_CHUNK_SIZE):
        rows.update(_rows_by_key(TableSportsEvents.sportarrEventId.in_(event_ids[offset:offset + QUERY_CHUNK_SIZE]),
                                 TableSportsEvents.sportarrLeagueId != league_id))
    return rows


def _row_ids_with_kept_data(row_ids: list[int]) -> set[int]:
    """The event rows that have subtitles, history or blacklist rows."""
    kept = set()
    for offset in range(0, len(row_ids), QUERY_CHUNK_SIZE):
        chunk = row_ids[offset:offset + QUERY_CHUNK_SIZE]
        for column in (TableSportsEventsSubtitles.sportsEventId, TableHistorySports.sportsEventId,
                       TableBlacklistSports.sports_event_id):
            kept.update(row[0] for row in database.execute(select(column).where(column.in_(chunk)).distinct()))
    return kept


def _league_bazarr_takes(league_id: int) -> bool:
    """True when Bazarr holds the league, or Sportarr has it with a folder, so a league sync adds it."""
    if league_in_bazarr(league_id):
        return True
    league = get_league_from_sportarr_api(apikey_sportarr=settings.sportarr.apikey, league_id=league_id)
    return isinstance(league, dict) and bool(league.get('path'))


def _keys_without_moved_events(league_id: int, rows_by_key: dict, keys_to_delete: list,
                               listed_event_ids: set[int]) -> list:
    """Drop the keys of events that Sportarr moved to another league that Bazarr holds or adds.

    The sync of that league takes the rows over with their subtitles and
    history. A full sync can read this league first, so it must not delete
    them. Only rows with something to keep are checked, so a large removal
    reads Sportarr once for each event that had subtitles.
    """
    if not keys_to_delete:
        return keys_to_delete
    kept_row_ids = _row_ids_with_kept_data([rows_by_key[key]['id'] for key in keys_to_delete])
    # An event that the read still lists here only lost a part, so Sportarr is not asked.
    event_ids = sorted({key[0] for key in keys_to_delete
                        if rows_by_key[key]['id'] in kept_row_ids and key[0] not in listed_event_ids})
    moved_event_ids = set()
    league_takes = {}
    for index, event_id in enumerate(event_ids):
        try:
            event = get_event_from_sportarr_api(apikey_sportarr=settings.sportarr.apikey, event_id=event_id)
            if isinstance(event, dict) and 'leagueId' not in event:
                # leagueId is optional in the contract. Without it Bazarr cannot
                # tell where the event went, so its rows stay.
                moved_event_ids.add(event_id)
                continue
            new_league_id = event.get('leagueId') if isinstance(event, dict) else None
            moved = type(new_league_id) is int and new_league_id != league_id
            if moved:
                if new_league_id not in league_takes:
                    league_takes[new_league_id] = _league_bazarr_takes(new_league_id)
                moved = league_takes[new_league_id]
        except RequestException:
            # Sportarr did not answer. The rows of this event and of the events
            # not read yet stay until a later sync can tell.
            logging.debug(f'BAZARR could not read Sportarr event {event_id}, so its rows stay for now.')
            moved_event_ids.update(event_ids[index:])
            break
        if moved:
            logging.debug(f'BAZARR keeps Sportarr event {event_id}, because Sportarr moved it to league '
                          f'{new_league_id}. The sync of that league takes it over.')
            moved_event_ids.add(event_id)
    return [key for key in keys_to_delete if key[0] not in moved_event_ids]


def sync_one_event(event):
    """Sync the parts of one event, as Sportarr returned it.

    Returns EVENT_NEEDS_LEAGUE_SYNC when only a league sync can apply the
    change safely, for example when the league is new to Bazarr.
    """
    if not isinstance(event, dict) or type(event.get('id')) is not int or event['id'] <= 0:
        logging.debug('BAZARR received an unidentified event from Sportarr.')
        return EVENT_SKIPPED

    league_id = _event_league_id(event)
    if league_id is None:
        return EVENT_SKIPPED
    if not league_in_bazarr(league_id):
        return EVENT_NEEDS_LEAGUE_SYNC
    if league_left_unmonitored(league_id):
        # Only a league read tells whether Sportarr monitors the league now.
        return EVENT_NEEDS_LEAGUE_SYNC

    rows_by_key = _rows_by_key(TableSportsEvents.sportarrEventId == event['id'])
    sync_monitored = settings.sportarr.sync_only_monitored_leagues and settings.sportarr.sync_only_monitored_events
    events_monitored = {key[0]: row['monitored'] for key, row in rows_by_key.items()} if sync_monitored else None

    seen, to_add, to_update, renumbers = _plan_event(event, rows_by_key, _keys_by_event(rows_by_key),
                                                     events_monitored, sync_monitored)
    if event.get('files') == [] and any(_media_on_disk(row) for row in rows_by_key.values()):
        # The rule for a fileless event checks the files of the whole league.
        return EVENT_NEEDS_LEAGUE_SYNC

    external_ids = {parsed_event['externalId'] for parsed_event in to_add if parsed_event['externalId']}
    if external_ids and database.execute(
            select(TableSportsEvents.id)
            .where(TableSportsEvents.sportarrLeagueId == league_id)
            .where(TableSportsEvents.sportarrEventId != event['id'])
            .where(TableSportsEvents.externalId.in_(external_ids))).first():
        # A row with this external id may belong to an event that left
        # Sportarr. Only a complete league read can prove that.
        return EVENT_NEEDS_LEAGUE_SYNC

    _write_changes(rows_by_key, list(set(rows_by_key) - set(seen)), to_add, to_update, renumbers=renumbers)
    return EVENT_SYNCED


def delete_event_rows(sportarr_event_id):
    """Delete every part of an event that Sportarr no longer has."""
    rows_by_key = _rows_by_key(TableSportsEvents.sportarrEventId == sportarr_event_id)
    _delete_rows(rows_by_key, list(rows_by_key))

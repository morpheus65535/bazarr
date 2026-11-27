# coding=utf-8

import logging
import gc
import time
from threading import Thread

from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.config import settings
from sportarr.rootfolder import check_sportarr_rootfolder
from app.database import (TableSportsLeagues, TableSportsEvents, TableSportsEventsSubtitles, TableHistorySports,
                          TableBlacklistSports, TableLanguagesProfiles, database, insert, update, select, delete)
from utilities.helper import bool_map
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue
from subtitles.wanted_state import delete_league_and_wanted_search_state, _wanted_state_transaction

# The jobs queue runs this module under a second name, so the state the
# event stream reads lives in a module that is imported by one name only.
from sportarr.sync import state as sync_state
from .events import league_in_bazarr, sync_events
from .parser import leagueParser
from .utils import get_tags, get_leagues_from_sportarr_api

FEATURE_PREFIX = "SYNC_LEAGUES "


def queue_full_sync():
    # The scheduler queues this same call, so the jobs queue keeps one full
    # sync at a time. The call waits for the job, so it gets its own thread.
    Thread(target=update_leagues, kwargs={'wait_for_completion': True}, daemon=True).start()


def full_sync_queued_or_running():
    jobs = list(jobs_queue.jobs_pending_queue) + list(jobs_queue.jobs_running_queue)
    return any(job.func == 'update_leagues' and job.module.endswith('sportarr.sync.leagues') for job in jobs)


def trace(message):
    if settings.general.debug:
        logging.debug(FEATURE_PREFIX + message)


def get_language_profiles():
    return database.execute(
        select(TableLanguagesProfiles.profileId, TableLanguagesProfiles.name, TableLanguagesProfiles.tag)).all()


def get_leagues_monitored_table():
    leagues_monitored = database.execute(
        select(TableSportsLeagues.sportarrLeagueId, TableSportsLeagues.monitored))\
        .all()
    leagues_dict = dict((x, y) for x, y in leagues_monitored)
    return leagues_dict


def update_leagues(job_id=None, wait_for_completion=False):
    """Sync every league. Without job_id, queue the sync and return the job id, or False when one is queued."""
    if not job_id:
        return jobs_queue.add_job_from_function("Syncing leagues with Sportarr", is_progress=True,
                                                wait_for_completion=wait_for_completion)

    started_at = sync_state.last_sync_started_at = time.monotonic()
    unread_leagues = []
    sync_state.last_incomplete_sync_reason = 'Sportarr did not return the league list.'

    # Update root folders and update their health status
    check_sportarr_rootfolder()

    # Get leagues data from Sportarr
    try:
        leagues = get_leagues_from_sportarr_api(apikey_sportarr=settings.sportarr.apikey)
    except Exception as e:
        logging.exception(f"BAZARR Error trying to get leagues from Sportarr: {e}")
        return
    else:
        if not isinstance(leagues, list):
            # The request failed, so nothing can be said about what still exists.
            # Returning here stops a failed call being read as every league
            # having been removed.
            logging.debug('BAZARR Sportarr leagues sync returned an invalid payload. Skipping sync.')
            jobs_queue.update_job_name(job_id=job_id, new_job_name="Synced leagues with Sportarr")
            gc.collect()
            return

        # Get current leagues in DB
        current_leagues_db = [x.sportarrLeagueId for x in
                              database.execute(
                                  select(TableSportsLeagues.sportarrLeagueId))
                              .all()]

        current_leagues_sportarr = []
        valid_leagues = [league for league in leagues if _has_league_id(league)]
        complete_league_list = len(valid_leagues) == len(leagues)
        # A league can move to a new Sportarr id only when the old id is
        # proven gone, which needs the complete list.
        sportarr_league_ids = {league['id'] for league in valid_leagues} if complete_league_list else None

        leagues_count = len(leagues)
        skipped_count = 0
        no_folder_count = 0

        leagues_monitored = None
        if settings.sportarr.sync_only_monitored_leagues:
            # Get current leagues monitored status in DB
            leagues_monitored = get_leagues_monitored_table()

        tagsDict = get_tags()
        language_profiles = get_language_profiles()

        trace(f"Starting sync for {leagues_count} leagues")

        jobs_queue.update_job_progress(job_id=job_id, progress_max=leagues_count)
        for i, league in enumerate(leagues, start=1):
            if not _has_league_id(league):
                skipped_count += 1
                continue
            jobs_queue.update_job_progress(job_id=job_id, progress_value=i,
                                           progress_message=league.get('name', 'Unknown'))

            # A league with no folder of its own cannot be stored, because the
            # path is what identifies it. Sportarr returns null when the user
            # turned Create League Folders off, and then every league resolves
            # to the same root. Sportarr still lists the league, so a row that
            # Bazarr already holds stays as it is, with its events.
            if not league.get('path'):
                trace(f"{i}: (Skipped, no folder) {league.get('name')}")
                current_leagues_sportarr.append(league['id'])
                # A league added again without a folder keeps the held league
                # it matches, so its history waits for the folder.
                old_league_id = _league_with_external_id(league.get('externalId'), league['id'])
                if old_league_id is not None:
                    current_leagues_sportarr.append(old_league_id)
                no_folder_count += 1
                continue

            if settings.sportarr.sync_only_monitored_leagues:
                try:
                    monitored_status_db = bool_map[leagues_monitored[league['id']]]
                except KeyError:
                    monitored_status_db = None
                if monitored_status_db is None:
                    # not in db, need to add
                    pass
                elif monitored_status_db != league['monitored']:
                    # monitored status changed and we don't know about it until now
                    trace(f"{i}: (Monitor Status Mismatch) {league['name']}")
                elif not league['monitored']:
                    # Add unmonitored leagues in sportarr to current leagues list, otherwise it will be deleted from db
                    trace(f"{i}: (Skipped Unmonitored) {league['name']}")
                    current_leagues_sportarr.append(league['id'])
                    skipped_count += 1
                    continue

            trace(f"{i}: (Processing) {league['name']}")

            # Add leagues in Sportarr to current leagues list
            current_leagues_sportarr.append(league['id'])

            # Update league in DB
            update_one_league(league['id'], action='updated', sync_events_after_update=False,
                              league_data=[league], tagsDict=tagsDict, language_profiles=language_profiles,
                              sportarr_league_ids=sportarr_league_ids, from_full_sync=True)

            # Update events in DB. A league that was not stored has no events to sync.
            if league_in_bazarr(league['id']) and not sync_events(league_id=league['id']):
                unread_leagues.append(league.get('name') or str(league['id']))

        # Calculate leagues to remove from DB
        removed_leagues = (
            list(set(current_leagues_db) - set(current_leagues_sportarr)) if complete_league_list else []
        )
        if not complete_league_list:
            logging.warning('BAZARR Skipping leagues deletion because Sportarr returned unidentified leagues.')

        for league in removed_leagues:
            # Remove league from DB
            update_one_league(league, action='deleted')

        if settings.sportarr.sync_only_monitored_leagues:
            trace(f"skipped {skipped_count} unmonitored leagues out of {leagues_count}")

        if no_folder_count:
            logging.info(f"BAZARR Skipped {no_folder_count} {'league' if no_folder_count == 1 else 'leagues'} that "
                         f"{'has' if no_folder_count == 1 else 'have'} no league folder in Sportarr. Turn on Create "
                         f"League Folders in Sportarr to sync them.")

        logging.debug('BAZARR All leagues synced from Sportarr into database.')

        if not complete_league_list:
            sync_state.last_incomplete_sync_reason = 'Sportarr returned leagues without an id.'
        elif unread_leagues:
            sync_state.last_incomplete_sync_reason = \
                f"Sportarr did not return the events of {', '.join(unread_leagues)}."
        else:
            sync_state.last_incomplete_sync_reason = None
            sync_state.last_complete_sync_started_at = max(sync_state.last_complete_sync_started_at, started_at)

    jobs_queue.update_job_name(job_id=job_id, new_job_name="Synced leagues with Sportarr")

    gc.collect()


def _has_league_id(league):
    return isinstance(league, dict) and type(league.get('id')) is int and league['id'] > 0


def _league_with_external_id(external_id, league_id):
    if not external_id:
        return None
    row = database.execute(
        select(TableSportsLeagues.sportarrLeagueId)
        .where(TableSportsLeagues.externalId == external_id)
        .where(TableSportsLeagues.sportarrLeagueId != league_id)).first()
    return row[0] if row else None


def _move_league(old_league_id, league):
    """Give a league row the new Sportarr id that a remove and re-add produced.

    The events, subtitles, history and blacklist rows follow it. Sportarr
    gives the events new ids too, and the next event sync matches those by
    their external id.
    """
    new_league_id = league['sportarrLeagueId']
    with _wanted_state_transaction() as connection:
        old_league = connection.execute(
            select(TableSportsLeagues.profileId, TableSportsLeagues.created_at_timestamp)
            .where(TableSportsLeagues.sportarrLeagueId == old_league_id).with_for_update()).first()
        if old_league is None:
            return False
        # The path is unique, and the new row can use the same folder. The
        # old row lets it go first, and the whole move is one transaction.
        connection.execute(
            update(TableSportsLeagues)
            .values(path=f'sportarr-league-moving-{old_league_id}')
            .where(TableSportsLeagues.sportarrLeagueId == old_league_id))
        league['profileId'] = old_league.profileId
        league['created_at_timestamp'] = old_league.created_at_timestamp
        league['updated_at_timestamp'] = datetime.now()
        connection.execute(insert(TableSportsLeagues).values(league))
        for column in (TableSportsEvents.sportarrLeagueId, TableSportsEventsSubtitles.sportarrLeagueId,
                       TableHistorySports.sportarrLeagueId, TableBlacklistSports.sportarr_league_id):
            connection.execute(
                update(column.class_)
                .values({column.key: new_league_id})
                .where(column == old_league_id))
        connection.execute(delete(TableSportsLeagues).where(TableSportsLeagues.sportarrLeagueId == old_league_id))
    return True


def update_one_league(league_id, action, is_sse=False, sync_events_after_update=True, league_data=None,
                      tagsDict=None, language_profiles=None, sportarr_league_ids=None, from_full_sync=False,
                      request_full_sync=None):
    logging.debug(f'BAZARR syncing this specific league from Sportarr: {league_id}')

    # Check if there's a row in database for this league ID
    existing_league = database.execute(
        select(TableSportsLeagues)
        .where(TableSportsLeagues.sportarrLeagueId == league_id))\
        .first()

    # Delete league from DB
    if action == 'deleted':
        if existing_league:
            delete_league_and_wanted_search_state(league_id)
            event_stream(type='sports-league', action='delete', payload=int(league_id))
        return

    if settings.general.league_default_enabled is True:
        league_default_profile = settings.general.league_default_profile
        if league_default_profile == '':
            league_default_profile = None
    else:
        league_default_profile = None

    if tagsDict is None:
        tagsDict = get_tags()
    if language_profiles is None:
        language_profiles = get_language_profiles()

    if league_data is None:
        try:
            # Get league data from sportarr api
            league_data = get_leagues_from_sportarr_api(apikey_sportarr=settings.sportarr.apikey,
                                                        sportarr_league_id=int(league_id))
        except Exception:
            logging.exception(f'BAZARR cannot get league with ID {league_id} from Sportarr API.')
            return

    if not league_data:
        return

    if not isinstance(league_data[0], dict) or not league_data[0].get('path'):
        # Sportarr still has the league but no folder for it. The row stays as
        # it is, and the full sync logs how many leagues this affects.
        logging.debug(f'BAZARR skipped league {league_id} because it has no league folder in Sportarr.')
        return

    if action == 'updated' and existing_league:
        # Update existing league in DB
        league = leagueParser(league_data[0], action='update', tags_dict=tagsDict,
                              language_profiles=language_profiles,
                              league_default_profile=league_default_profile)
        existing_league_model = existing_league[0]
        existing_league_values = {
            column.name: getattr(existing_league_model, column.name)
            for column in existing_league_model.__table__.columns
        }
        if league.items() <= existing_league_values.items():
            # Sportarr sends event frames for event changes. A league frame
            # skips the event sync.
            if sync_events_after_update and not is_sse:
                sync_events(league_id=int(league_id))
            return

        try:
            league['updated_at_timestamp'] = datetime.now()
            database.execute(
                update(TableSportsLeagues)
                .values(league)
                .where(TableSportsLeagues.sportarrLeagueId == league['sportarrLeagueId']))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot update league {league['title']} because of {e}")
            return

        if sync_events_after_update and not is_sse:
            sync_events(league_id=int(league_id))
        event_stream(type='sports-league', payload=int(league_id))
        logging.debug(f"BAZARR updated this league into the database: {league['path']}")

    elif action == 'updated' and not existing_league:
        # Insert new league in DB
        league = leagueParser(league_data[0], action='insert', tags_dict=tagsDict,
                              language_profiles=language_profiles,
                              league_default_profile=league_default_profile)

        old_league_id = _league_with_external_id(league['externalId'], league_id)
        if old_league_id is not None:
            if not from_full_sync:
                # Only the complete league list proves the old id is gone.
                logging.debug(f'BAZARR league {league_id} matches league {old_league_id} by external id. '
                              f'Syncing every league to resolve it.')
                (request_full_sync or queue_full_sync)()
                return
            if sportarr_league_ids is None:
                # The list is incomplete, so the old id may be gone or not. A
                # plain insert now would let the next complete sync delete the
                # old league with its history, so this league waits for it.
                logging.debug(f'BAZARR league {league_id} matches league {old_league_id} by external id. '
                              f'It waits for a complete league list.')
                return
            if old_league_id not in sportarr_league_ids:
                try:
                    moved = _move_league(old_league_id, league)
                except IntegrityError as e:
                    logging.error(f"BAZARR cannot move league {league['title']} to its new Sportarr id because of {e}")
                    return
                if moved:
                    logging.info(f"BAZARR kept the subtitles of league {league['title']} because Sportarr added it "
                                 f"again with the same external id.")
                    if sync_events_after_update and not is_sse:
                        sync_events(league_id=int(league_id))
                    event_stream(type='sports-league', action='delete', payload=int(old_league_id))
                    event_stream(type='sports-league', action='update', payload=int(league_id))
                    return

        try:
            league['created_at_timestamp'] = datetime.now()
            database.execute(
                insert(TableSportsLeagues)
                .values(league))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot insert league {league['title']} because of {e}")
            return

        # Sportarr does not send the events of a league that Bazarr did not
        # know. Sync them here, or a new league stays empty.
        if sync_events_after_update and not is_sse:
            sync_events(league_id=int(league_id))
        event_stream(type='sports-league', action='update', payload=int(league_id))
        logging.debug(f"BAZARR inserted this league into the database: {league['path']}")

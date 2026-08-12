# coding=utf-8

import logging
import gc

from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.config import settings
from sportarr.rootfolder import check_sportarr_rootfolder
from app.database import TableSportsLeagues, TableLanguagesProfiles, database, insert, update, delete, select
from utilities.helper import bool_map
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue

from .events import sync_events
from .parser import leagueParser
from .utils import get_tags, get_leagues_from_sportarr_api

FEATURE_PREFIX = "SYNC_LEAGUES "


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
    if not job_id:
        jobs_queue.add_job_from_function("Syncing leagues with Sportarr", is_progress=True,
                                         wait_for_completion=wait_for_completion)
        return

    # Update root folders and update their health status
    check_sportarr_rootfolder()

    # Get leagues data from Sportarr
    try:
        leagues = get_leagues_from_sportarr_api(apikey_sportarr=settings.sportarr.apikey)
    except Exception as e:
        logging.exception(f"BAZARR Error trying to get leagues from Sportarr: {e}")
        return
    else:
        if leagues is None:
            # The request failed, so nothing can be said about what still exists.
            # Returning here stops a failed call being read as every league
            # having been removed.
            return

        # Get current leagues in DB
        current_leagues_db = [x.sportarrLeagueId for x in
                              database.execute(
                                  select(TableSportsLeagues.sportarrLeagueId))
                              .all()]

        current_leagues_sportarr = []

        leagues_count = len(leagues)
        skipped_count = 0

        leagues_monitored = None
        if settings.sportarr.sync_only_monitored_leagues:
            # Get current leagues monitored status in DB
            leagues_monitored = get_leagues_monitored_table()

        tagsDict = get_tags()
        language_profiles = get_language_profiles()

        trace(f"Starting sync for {leagues_count} leagues")

        jobs_queue.update_job_progress(job_id=job_id, progress_max=leagues_count)
        for i, league in enumerate(leagues, start=1):
            jobs_queue.update_job_progress(job_id=job_id, progress_value=i, progress_message=league['name'])

            # A league with no folder of its own cannot be stored, because the
            # path is what identifies it. Sportarr returns null when the user
            # turned Create League Folders off, and then every league resolves
            # to the same root.
            if not league.get('path'):
                trace(f"{i}: (Skipped, no folder) {league['name']}")
                skipped_count += 1
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
            update_one_league(league['id'], action='updated', league_data=[league], tagsDict=tagsDict,
                              language_profiles=language_profiles)

            # Update events in DB
            sync_events(league_id=league['id'])

        # Calculate leagues to remove from DB
        removed_leagues = list(set(current_leagues_db) - set(current_leagues_sportarr))

        for league in removed_leagues:
            # Remove league from DB
            update_one_league(league, action='deleted')

        if settings.sportarr.sync_only_monitored_leagues:
            trace(f"skipped {skipped_count} unmonitored leagues out of {leagues_count}")

        logging.debug('BAZARR All leagues synced from Sportarr into database.')

    jobs_queue.update_job_name(job_id=job_id, new_job_name="Synced leagues with Sportarr")

    gc.collect()


def update_one_league(league_id, action, league_data=None, tagsDict=None, language_profiles=None):
    logging.debug(f'BAZARR syncing this specific league from Sportarr: {league_id}')

    # Check if there's a row in database for this league ID
    existing_league = database.execute(
        select(TableSportsLeagues)
        .where(TableSportsLeagues.sportarrLeagueId == league_id))\
        .first()

    # Delete league from DB
    if action == 'deleted' and existing_league:
        database.execute(
            delete(TableSportsLeagues)
            .where(TableSportsLeagues.sportarrLeagueId == int(league_id)))

        event_stream(type='leagues', action='delete', payload=int(league_id))
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

        event_stream(type='leagues', payload=int(league_id))
        logging.debug(f"BAZARR updated this league into the database: {league['path']}")

    elif action == 'updated' and not existing_league:
        # Insert new league in DB
        league = leagueParser(league_data[0], action='insert', tags_dict=tagsDict,
                              language_profiles=language_profiles,
                              league_default_profile=league_default_profile)

        try:
            league['created_at_timestamp'] = datetime.now()
            database.execute(
                insert(TableSportsLeagues)
                .values(league))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot insert league {league['title']} because of {e}")
            return

        event_stream(type='leagues', action='update', payload=int(league_id))
        logging.debug(f"BAZARR inserted this league into the database: {league['path']}")

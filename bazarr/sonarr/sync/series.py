# coding=utf-8

import logging
import gc

from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.config import settings
from subtitles.indexer.series import list_missing_subtitles
from sonarr.rootfolder import check_sonarr_rootfolder
from app.database import TableShows, TableLanguagesProfiles, database, insert, update, delete, select
from utilities.path_mappings import path_mappings
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue

from .episodes import sync_episodes
from .parser import seriesParser
from .utils import get_profile_list, get_tags, get_series_from_sonarr_api

# map between booleans and strings in DB
bool_map = {"True": True, "False": False}

FEATURE_PREFIX = "SYNC_SERIES "


def trace(message):
    if settings.general.debug:
        logging.debug(FEATURE_PREFIX + message)


def get_language_profiles():
    return database.execute(
        select(TableLanguagesProfiles.profileId, TableLanguagesProfiles.name, TableLanguagesProfiles.tag)).all()


def get_series_monitored_table():
    series_monitored = database.execute(
        select(TableShows.sonarrSeriesId, TableShows.monitored))\
        .all()
    series_dict = dict((x, y) for x, y in series_monitored)
    return series_dict


def update_series(job_id=None, wait_for_completion=False):
    if not job_id:
        jobs_queue.add_job_from_function("Syncing series with Sonarr", is_progress=True,
                                         wait_for_completion=wait_for_completion)
        return

    # Update root folders and update their health status
    check_sonarr_rootfolder()

    # Get shows data from Sonarr
    try:
        series = get_series_from_sonarr_api(apikey_sonarr=settings.sonarr.apikey)
    except Exception as e:
        logging.exception(f"BAZARR Error trying to get series from Sonarr: {e}")
        return
    else:
        # Get current shows in DB
        current_shows_db = [x.sonarrSeriesId for x in
                            database.execute(
                                select(TableShows.sonarrSeriesId))
                            .all()]

        current_shows_sonarr = []

        series_count = len(series)
        skipped_count = 0

        series_monitored = None
        if settings.sonarr.sync_only_monitored_series:
            # Get current series monitored status in DB
            series_monitored = get_series_monitored_table()

        trace(f"Starting sync for {series_count} shows")

        jobs_queue.update_job_progress(job_id=job_id, progress_max=series_count)
        for i, show in enumerate(series, start=1):
            jobs_queue.update_job_progress(job_id=job_id, progress_value=i, progress_message=show['title'])

            if settings.sonarr.sync_only_monitored_series:
                try:
                    monitored_status_db = bool_map[series_monitored[show['id']]]
                except KeyError:
                    monitored_status_db = None
                if monitored_status_db is None:
                    # not in db, need to add
                    pass
                elif monitored_status_db != show['monitored']:
                    # monitored status changed and we don't know about it until now
                    trace(f"{i}: (Monitor Status Mismatch) {show['title']}")
                    # pass
                elif not show['monitored']:
                    # Add unmonitored series in sonarr to current series list, otherwise it will be deleted from db
                    trace(f"{i}: (Skipped Unmonitored) {show['title']}")
                    current_shows_sonarr.append(show['id'])
                    skipped_count += 1
                    continue

            trace(f"{i}: (Processing) {show['title']}")

            # Add shows in Sonarr to current shows list
            current_shows_sonarr.append(show['id'])

            # Update series in DB
            update_one_series(show['id'], action='updated')

            # Update episodes in DB
            sync_episodes(series_id=show['id'])

        # Calculate series to remove from DB
        removed_series = list(set(current_shows_db) - set(current_shows_sonarr))

        for series in removed_series:
            # Remove series from DB
            update_one_series(series, action='deleted')

        if settings.sonarr.sync_only_monitored_series:
            trace(f"skipped {skipped_count} unmonitored series out of {series_count}")

        logging.debug('BAZARR All series synced from Sonarr into database.')

    jobs_queue.update_job_name(job_id=job_id, new_job_name="Synced series with Sonarr")

    gc.collect()


def update_one_series(series_id, action, is_signalr=False):
    logging.debug(f'BAZARR syncing this specific series from Sonarr: {series_id}')

    # Check if there's a row in database for this series ID
    existing_series = database.execute(
        select(TableShows)
        .where(TableShows.sonarrSeriesId == series_id))\
        .first()

    # Delete series from DB
    if action == 'deleted' and existing_series:
        database.execute(
            delete(TableShows)
            .where(TableShows.sonarrSeriesId == int(series_id)))

        event_stream(type='series', action='delete', payload=int(series_id))
        return

    if settings.general.serie_default_enabled is True:
        serie_default_profile = settings.general.serie_default_profile
        if serie_default_profile == '':
            serie_default_profile = None
    else:
        serie_default_profile = None

    audio_profiles = get_profile_list()
    tagsDict = get_tags()
    language_profiles = get_language_profiles()

    try:
        # Get series data from sonarr api
        series_data = get_series_from_sonarr_api(apikey_sonarr=settings.sonarr.apikey, sonarr_series_id=int(series_id))
    except Exception:
        logging.exception(f'BAZARR cannot get series with ID {series_id} from Sonarr API.')
        return
    else:
        if not series_data:
            return
        else:
            if action == 'updated' and existing_series:
                # Update existing series in DB
                series = seriesParser(series_data[0], action='update', tags_dict=tagsDict,
                                      language_profiles=language_profiles,
                                      serie_default_profile=serie_default_profile,
                                      audio_profiles=audio_profiles)
                try:
                    series['updated_at_timestamp'] = datetime.now()
                    database.execute(
                        update(TableShows)
                        .values(series)
                        .where(TableShows.sonarrSeriesId == series['sonarrSeriesId']))
                except IntegrityError as e:
                    logging.error(f"BAZARR cannot update series {series['path']} because of {e}")
                else:
                    if not is_signalr:
                        # Sonarr emit two SignalR events when episodes must be refreshed.
                        # The one that gets there doesn't include the episodeChanged flag.
                        # The episodes are synced only when this function is called from the
                        # frontend sync button in the episodes' page.
                        sync_episodes(series_id=int(series_id))
                    event_stream(type='series', action='update', payload=int(series_id))
                    logging.debug(
                        f'BAZARR updated this series into the database:{path_mappings.path_replace(series["path"])}')
            elif action == 'updated' and not existing_series:
                # Insert new series in DB
                series = seriesParser(series_data[0], action='insert', tags_dict=tagsDict,
                                      language_profiles=language_profiles,
                                      serie_default_profile=serie_default_profile,
                                      audio_profiles=audio_profiles)

                try:
                    series['created_at_timestamp'] = datetime.now()
                    database.execute(
                        insert(TableShows)
                        .values(series))
                except IntegrityError as e:
                    logging.error(f"BAZARR cannot insert series {series['path']} because of {e}")
                else:
                    event_stream(type='series', action='update', payload=int(series_id))
                    logging.debug(
                        f'BAZARR inserted this series into the database:{path_mappings.path_replace(series["path"])}')

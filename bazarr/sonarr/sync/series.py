# coding=utf-8

import logging

from concurrent.futures import ThreadPoolExecutor
from threading import Lock

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

# Thread-safe progress tracking
progress_lock = Lock()
completed = 0

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


def update_series(job_id=None):
    global completed
    completed = 0

    if not job_id:
        jobs_queue.add_job_from_function("Syncing series with Sonarr", is_progress=True)
        return

    check_sonarr_rootfolder()
    apikey_sonarr = settings.sonarr.apikey
    if apikey_sonarr is None:
        return

    serie_default_enabled = settings.general.serie_default_enabled

    if serie_default_enabled is True:
        serie_default_profile = settings.general.serie_default_profile
        if serie_default_profile == '':
            serie_default_profile = None
    else:
        serie_default_profile = None

    # Prevent trying to insert a series with a non-existing languages profileId
    if (serie_default_profile and not database.execute(
            select(TableLanguagesProfiles)
            .where(TableLanguagesProfiles.profileId == serie_default_profile))
            .first()):
        serie_default_profile = None

    audio_profiles = get_profile_list()
    tagsDict = get_tags()
    language_profiles = get_language_profiles()

    # Get shows data from Sonarr
    series = get_series_from_sonarr_api(apikey_sonarr=apikey_sonarr)
    if not isinstance(series, list):
        return

    # Get current shows in DB
    current_shows_db = [x.sonarrSeriesId for x in
                        database.execute(select(TableShows.sonarrSeriesId)).all()]
    current_shows_sonarr = []

    sync_monitored = settings.sonarr.sync_only_monitored_series

    # Filter monitored series if needed
    if sync_monitored:
        series_monitored = get_series_monitored_table()
        series_to_process = []
        skipped_count = 0

        for i, show in series:
            try:
                monitored_status_db = bool_map[series_monitored[show['id']]]
            except (KeyError, AttributeError):
                monitored_status_db = None

            if monitored_status_db is None:
                # not in db, need to add
                trace(f"{i}: (Monitor Status Missing) {show['title']}")
                series_to_process.append(show)
            elif monitored_status_db != show['monitored']:
                # monitored status changed and we don't know about it until now
                trace(f"{i}: (Monitor Status Mismatch) {show['title']}")
                series_to_process.append(show)
            elif not show['monitored']:
                # Add unmonitored series in sonarr to current series list, otherwise it will be deleted from db
                trace(f"{i}: (Skipped Unmonitored) {show['title']}")
                current_shows_sonarr.append(show['id'])
                skipped_count += 1
            else:
                series_to_process.append(show)

        trace(f"Processing {len(series_to_process)} series, skipped {skipped_count} unmonitored")
    else:
        series_to_process = series

    series_count = len(series)
    trace(f"Starting sync for {series_count} shows")

    # Get worker count from settings with 5 default
    # (setting doesn't exist yet, but maybe later?)
    worker_count = getattr(settings.sonarr, 'sonarr_sync_workers', 5)
    # Cap at 10 to avoid overwhelming Sonarr
    worker_count = min(worker_count, 10)

    trace(f"Starting parallel sync with {worker_count} workers for {len(series_to_process)} series")
    jobs_queue.update_job_progress(job_id=job_id, progress_max=len(series_to_process))

    # Process series in parallel
    with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="SonarrSync") as executor:
        futures = {
            executor.submit(
                sync_single_series,
                show, tagsDict, language_profiles, serie_default_profile,
                audio_profiles, current_shows_db, job_id, len(series_to_process)
            ): show
            for show in series_to_process
        }

        # Collect results and track processed series
        for future in futures:
            show = futures[future]
            try:
                series_id, success, error = future.result(timeout=300)  # 5 min timeout per series
                if success:
                    # Add shows in Sonarr to current shows list
                    current_shows_sonarr.append(series_id)
                else:
                    list_missing_subtitles(no=show['id'])
                    logging.error(f"Failed to sync series {show['title']}: {error}")
            except Exception as e:
                logging.exception(f"Exception syncing series {show['title']}: {e}")

    # Remove old series from DB
    removed_series = list(set(current_shows_db) - set(current_shows_sonarr))
    for series_id in removed_series:
        if settings.general.debug:
            series_title = database.execute(
                select(TableShows.title).where(TableShows.sonarrSeriesId == series_id)
            ).first()[0]
            trace(f"Deleting {series_title}")
        database.execute(delete(TableShows).where(TableShows.sonarrSeriesId == series_id))
        event_stream(type='series', action='delete', payload=series_id)

    logging.debug('BAZARR All series synced from Sonarr into database.')
    jobs_queue.update_job_name(job_id=job_id, new_job_name="Synced series with Sonarr")

def sync_single_series(show, tagsDict, language_profiles, serie_default_profile, 
                       audio_profiles, current_shows_db, job_id, total):
    """Process a single series with all its episodes"""
    global completed

    series_id = show['id']
    thread_name = f"Series-{series_id}"

    try:
        trace(f"[{thread_name}] Processing {show['title']}")

        # Determine if update or insert
        if series_id in current_shows_db:
            series_data = seriesParser(show, action='update', tags_dict=tagsDict,
                                      language_profiles=language_profiles,
                                      serie_default_profile=serie_default_profile,
                                      audio_profiles=audio_profiles)

            if not database.execute(select(TableShows).filter_by(**series_data)).first():
                series_data['updated_at_timestamp'] = datetime.now()
                database.execute(
                    update(TableShows)
                    .values(series_data)
                    .where(TableShows.sonarrSeriesId == series_id))
                trace(f"[{thread_name}] Updated {show['title']}")
        else:
            series_data = seriesParser(show, action='insert', tags_dict=tagsDict,
                                      language_profiles=language_profiles,
                                      serie_default_profile=serie_default_profile,
                                      audio_profiles=audio_profiles)

            series_data['created_at_timestamp'] = datetime.now()
            database.execute(insert(TableShows).values(series_data))
            trace(f"[{thread_name}] Inserted {show['title']}")

        # Sync episodes (this is the expensive part)
        sync_episodes(series_id=series_id)

        # Thread-safe progress update
        with progress_lock:
            completed += 1
            jobs_queue.update_job_progress(
                job_id=job_id, 
                progress_value=completed,
                progress_message=f"{show['title']} ({completed}/{total})"
            )

        event_stream(type='series', payload=series_id)
        return series_id, True, None

    except IntegrityError as e:
        logging.error(f"[{thread_name}] Cannot process series {show.get('path', 'unknown')}: {e}")
        return series_id, False, str(e)
    except Exception as e:
        logging.exception(f"[{thread_name}] Unexpected error processing {show['title']}")
        return series_id, False, str(e)

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

    serie_default_enabled = settings.general.serie_default_enabled

    if serie_default_enabled is True:
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
        series = None

        series_data = get_series_from_sonarr_api(apikey_sonarr=settings.sonarr.apikey, sonarr_series_id=int(series_id))

        if not series_data:
            return
        else:
            if action == 'updated' and existing_series:
                series = seriesParser(series_data[0], action='update', tags_dict=tagsDict,
                                      language_profiles=language_profiles,
                                      serie_default_profile=serie_default_profile,
                                      audio_profiles=audio_profiles)
            elif action == 'updated' and not existing_series:
                series = seriesParser(series_data[0], action='insert', tags_dict=tagsDict,
                                      language_profiles=language_profiles,
                                      serie_default_profile=serie_default_profile,
                                      audio_profiles=audio_profiles)
    except Exception:
        logging.exception('BAZARR cannot get series returned by SignalR feed from Sonarr API.')
        return

    # Update existing series in DB
    if action == 'updated' and existing_series:
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
            logging.debug(f'BAZARR updated this series into the database:{path_mappings.path_replace(series["path"])}')

    # Insert new series in DB
    elif action == 'updated' and not existing_series:
        try:
            series['created_at_timestamp'] = datetime.now()
            database.execute(
                insert(TableShows)
                .values(series))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot insert series {series['path']} because of {e}")
        else:
            event_stream(type='series', action='update', payload=int(series_id))
            logging.debug(f'BAZARR inserted this series into the database:{path_mappings.path_replace(series["path"])}')

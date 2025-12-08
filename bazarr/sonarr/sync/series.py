# coding=utf-8

import logging

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


def update_series(job_id=None):
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
    else:
        # Get current shows in DB
        current_shows_db = [x.sonarrSeriesId for x in
                            database.execute(
                                select(TableShows.sonarrSeriesId))
                            .all()]
        current_shows_sonarr = []

        series_count = len(series)
        sync_monitored = settings.sonarr.sync_only_monitored_series
        if sync_monitored:
            series_monitored = get_series_monitored_table()
            skipped_count = 0
        trace(f"Starting sync for {series_count} shows")

        jobs_queue.update_job_progress(job_id=job_id, progress_max=series_count)
        for i, show in enumerate(series, start=1):
            jobs_queue.update_job_progress(job_id=job_id, progress_value=i, progress_message=show['title'])
            if sync_monitored:
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

            if show['id'] in current_shows_db:
                updated_series = seriesParser(show, action='update', tags_dict=tagsDict,
                                              language_profiles=language_profiles,
                                              serie_default_profile=serie_default_profile,
                                              audio_profiles=audio_profiles)

                if not database.execute(
                        select(TableShows)
                        .filter_by(**updated_series))\
                        .first():
                    try:
                        trace(f"Updating {show['title']}")
                        updated_series['updated_at_timestamp'] = datetime.now()
                        database.execute(
                            update(TableShows)
                            .values(updated_series)
                            .where(TableShows.sonarrSeriesId == show['id']))
                    except IntegrityError as e:
                        logging.error(f"BAZARR cannot update series {updated_series['path']} because of {e}")
                        continue

                event_stream(type='series', payload=show['id'])
            else:
                added_series = seriesParser(show, action='insert', tags_dict=tagsDict,
                                            language_profiles=language_profiles,
                                            serie_default_profile=serie_default_profile,
                                            audio_profiles=audio_profiles)

                try:
                    trace(f"Inserting {show['title']}")
                    added_series['created_at_timestamp'] = datetime.now()
                    database.execute(
                        insert(TableShows)
                        .values(added_series))
                except IntegrityError as e:
                    logging.error(f"BAZARR cannot insert series {added_series['path']} because of {e}")
                    continue
                else:
                    list_missing_subtitles(no=show['id'])

                    event_stream(type='series', action='update', payload=show['id'])

            sync_episodes(series_id=show['id'])

        # Remove old series from DB
        removed_series = list(set(current_shows_db) - set(current_shows_sonarr))

        for series in removed_series:
            # try to avoid unnecessary database calls
            if settings.general.debug:
                series_title = database.execute(select(TableShows.title).where(TableShows.sonarrSeriesId == series)).first()[0]
                trace(f"Deleting {series_title}")
            database.execute(
                delete(TableShows)
                .where(TableShows.sonarrSeriesId == series))
            event_stream(type='series', action='delete', payload=series)

        if sync_monitored:
            trace(f"skipped {skipped_count} unmonitored series out of {i}")
        logging.debug('BAZARR All series synced from Sonarr into database.')


def update_one_series(series_id, action, **kwargs):
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

# coding=utf-8

import logging
import os
import operator

from datetime import datetime
from functools import reduce

from app.config import settings
from app.database import (TableMovies, TableLanguagesProfiles, TableRadarrInstances,
                          database, insert, update, delete, select, get_exclusion_clause,
                          get_radarr_instances)
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue
from constants import MINIMUM_VIDEO_SIZE
from radarr.rootfolder import check_radarr_rootfolder
from subtitles.indexer.movies import store_subtitles_movie
from subtitles.mass_download import movies_download_subtitles
from utilities.path_mappings import path_mappings
from subtitles.adaptive_searching import is_search_active

from sqlalchemy.exc import IntegrityError
from .parser import movieParser
from .utils import get_profile_list, get_tags, get_movies_from_radarr_api

# map between booleans and strings in DB
bool_map = {"True": True, "False": False}

FEATURE_PREFIX = "SYNC_MOVIES "


def trace(message):
    if settings.general.debug:
        logging.debug(FEATURE_PREFIX + message)


def get_language_profiles():
    return database.execute(
        select(TableLanguagesProfiles.profileId, TableLanguagesProfiles.name, TableLanguagesProfiles.tag)).all()


def get_movie_file_size_from_db(movie_path):
    try:
        bazarr_file_size = os.path.getsize(path_mappings.path_replace_movie(movie_path))
    except OSError:
        bazarr_file_size = 0
    return bazarr_file_size


# Update movies in DB
def update_movie(updated_movie):
    try:
        updated_movie['updated_at_timestamp'] = datetime.now()
        database.execute(
            update(TableMovies).values(updated_movie)
            .where(TableMovies.radarrId == updated_movie['radarrId'])
            .where(TableMovies.radarr_instance_id == updated_movie['radarr_instance_id']))
    except IntegrityError as e:
        logging.error(f"BAZARR cannot update movie {updated_movie['path']} because of {e}")
    else:
        store_subtitles_movie(updated_movie['path'], path_mappings.path_replace_movie(updated_movie['path']))
        event_stream(type='movie', action='update', payload=updated_movie['radarrId'])


def get_movie_monitored_status(movie_id, radarr_instance_id=1):
    existing_movie_monitored = database.execute(
        select(TableMovies.monitored)
        .where(TableMovies.radarrId == str(movie_id))
        .where(TableMovies.radarr_instance_id == radarr_instance_id))\
        .first()
    if existing_movie_monitored is None:
        return True
    else:
        return bool_map[existing_movie_monitored[0]]


# Insert new movies in DB
def add_movie(added_movie):
    try:
        added_movie['created_at_timestamp'] = datetime.now()
        database.execute(
            insert(TableMovies)
            .values(added_movie))
    except IntegrityError as e:
        logging.error(f"BAZARR cannot insert movie {added_movie['path']} because of {e}")
    else:
        store_subtitles_movie(added_movie['path'], path_mappings.path_replace_movie(added_movie['path']))
        event_stream(type='movie', action='update', payload=int(added_movie['radarrId']))


def _sync_instance_movies(instance, movie_default_profile):
    """Sync movies for a single Radarr instance.

    Args:
        instance: dict from TableRadarrInstances.to_dict()
        movie_default_profile: default language profile ID (or None)
    """
    instance_id = instance['id']
    instance_name = instance.get('name', f'Instance {instance_id}')
    apikey = instance.get('apikey', '')

    logging.debug(f'BAZARR Starting movie sync from Radarr instance "{instance_name}" (id={instance_id}).')

    if not apikey:
        logging.warning(f'BAZARR Skipping Radarr instance "{instance_name}": no API key configured.')
        return

    audio_profiles = get_profile_list(instance=instance)
    tagsDict = get_tags(instance=instance)
    language_profiles = get_language_profiles()

    # Get movies data from radarr
    movies = get_movies_from_radarr_api(apikey_radarr=apikey, instance=instance)
    if not isinstance(movies, list):
        logging.warning(f'BAZARR Could not retrieve movies from Radarr instance "{instance_name}".')
        return

    movies_count = len(movies)

    # Get current movies in DB for this instance
    current_movies_id_db = [x.radarrId for x in
                            database.execute(
                                select(TableMovies.radarrId)
                                .where(TableMovies.radarr_instance_id == instance_id))
                            .all()]
    current_movies_db_kv = [x.items() for x in [y._asdict()['TableMovies'].__dict__ for y in
                                                  database.execute(
                                                      select(TableMovies)
                                                      .where(TableMovies.radarr_instance_id == instance_id))
                                                  .all()]]

    current_movies_radarr = [movie['id'] for movie in movies if movie['hasFile'] and
                             'movieFile' in movie and
                             (movie['movieFile']['size'] > MINIMUM_VIDEO_SIZE or
                              get_movie_file_size_from_db(movie['movieFile']['path']) > MINIMUM_VIDEO_SIZE)]

    # Remove movies from DB that no longer exist in Radarr or don't have a movie file
    movies_to_delete = list(set(current_movies_id_db) - set(current_movies_radarr))
    movies_deleted = []
    if len(movies_to_delete):
        try:
            database.execute(
                delete(TableMovies)
                .where(TableMovies.radarrId.in_(movies_to_delete))
                .where(TableMovies.radarr_instance_id == instance_id))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot delete movies from instance '{instance_name}' because of {e}")
        else:
            for removed_movie in movies_to_delete:
                movies_deleted.append(removed_movie)
                event_stream(type='movie', action='delete', payload=removed_movie)

    # Instance-specific settings
    sync_monitored = bool(instance.get('sync_only_monitored_movies', 0))
    if sync_monitored:
        skipped_count = 0
    files_missing = 0
    movies_added = []
    movies_updated = []

    for i, movie in enumerate(movies, start=1):
        if movie['hasFile'] is True:
            if 'movieFile' in movie:
                if sync_monitored:
                    if get_movie_monitored_status(movie['id'], instance_id) != movie['monitored']:
                        trace(f"{i}: (Monitor Status Mismatch) {movie['title']}")
                    elif not movie['monitored']:
                        trace(f"{i}: (Skipped Unmonitored) {movie['title']}")
                        skipped_count += 1
                        continue

                if (movie['movieFile']['size'] > MINIMUM_VIDEO_SIZE or
                        get_movie_file_size_from_db(movie['movieFile']['path']) > MINIMUM_VIDEO_SIZE):
                    trace(f"{i}: (Processing) {movie['title']}")
                    if movie['id'] in current_movies_id_db:
                        parsed_movie = movieParser(movie, action='update',
                                                   tags_dict=tagsDict,
                                                   language_profiles=language_profiles,
                                                   movie_default_profile=movie_default_profile,
                                                   audio_profiles=audio_profiles,
                                                   radarr_instance_id=instance_id,
                                                   instance=instance)
                        if not any([parsed_movie.items() <= x for x in current_movies_db_kv]):
                            update_movie(parsed_movie)
                            movies_updated.append(parsed_movie['title'])
                    else:
                        parsed_movie = movieParser(movie, action='insert',
                                                   tags_dict=tagsDict,
                                                   language_profiles=language_profiles,
                                                   movie_default_profile=movie_default_profile,
                                                   audio_profiles=audio_profiles,
                                                   radarr_instance_id=instance_id,
                                                   instance=instance)
                        add_movie(parsed_movie)
                        movies_added.append(parsed_movie['title'])
        else:
            trace(f"{i}: (Skipped File Missing) {movie['title']}")
            files_missing += 1

    trace(f"Instance '{instance_name}': Skipped {files_missing} file-missing movies out of {movies_count}")
    if sync_monitored:
        trace(f"Instance '{instance_name}': Skipped {skipped_count} unmonitored movies out of {movies_count}")
    logging.debug(f'BAZARR Synced {len(movies_added)} added, {len(movies_updated)} updated, '
                  f'{len(movies_deleted)} deleted from Radarr instance "{instance_name}".')


def update_movies(job_id=None):
    if not job_id:
        jobs_queue.add_job_from_function("Syncing movies with Radarr", is_progress=True)
        return

    check_radarr_rootfolder()

    movie_default_enabled = settings.general.movie_default_enabled
    if movie_default_enabled is True:
        movie_default_profile = settings.general.movie_default_profile
        if movie_default_profile == '':
            movie_default_profile = None
    else:
        movie_default_profile = None

    # Prevent trying to insert a movie with a non-existing languages profileId
    if (movie_default_profile and not database.execute(
            select(TableLanguagesProfiles)
            .where(TableLanguagesProfiles.profileId == movie_default_profile))
            .first()):
        movie_default_profile = None

    # Sync from all enabled Radarr instances
    instances = get_radarr_instances()
    if not instances:
        logging.warning('BAZARR No enabled Radarr instances found. Skipping movie sync.')
        return

    movies_count = 0
    for instance in instances:
        # Estimate count for progress reporting
        try:
            movies_count += len(get_movies_from_radarr_api(
                apikey_radarr=instance.get('apikey', ''), instance=instance) or [])
        except Exception:
            pass

    jobs_queue.update_job_progress(job_id=job_id, progress_max=max(movies_count, 1))

    for instance in instances:
        try:
            _sync_instance_movies(instance, movie_default_profile)
        except Exception:
            logging.exception(f'BAZARR Exception syncing Radarr instance "{instance.get("name", instance["id"])}"')

    logging.debug('BAZARR All movies synced from all Radarr instances into database.')
    jobs_queue.update_job_name(job_id=job_id, new_job_name="Synced movies with Radarr")


def update_one_movie(movie_id, action, defer_search=False, is_signalr=False,
                     radarr_instance_id=1, instance=None):
    """Sync a single movie from a specific Radarr instance.

    Args:
        movie_id: Radarr movie ID.
        action: 'updated' or 'deleted'.
        defer_search: If True, defer subtitle search to next scheduled run.
        is_signalr: True if called from SignalR feed.
        radarr_instance_id: The instance ID (default=1 for primary).
        instance: Full instance dict. If None, uses primary instance from settings.
    """
    logging.debug(f'BAZARR syncing this specific movie from Radarr instance {radarr_instance_id}: {movie_id}')

    # If no instance dict provided, load it from DB
    if instance is None:
        inst_row = database.execute(
            select(TableRadarrInstances)
            .where(TableRadarrInstances.id == radarr_instance_id)
        ).scalar_one_or_none()
        if inst_row:
            instance = inst_row.to_dict()

    # Check if there's a row in the database for this movie ID + instance
    existing_movie = database.execute(
        select(TableMovies.path)
        .where(TableMovies.radarrId == movie_id)
        .where(TableMovies.radarr_instance_id == radarr_instance_id))\
        .first()

    # Remove movie from DB
    if action == 'deleted':
        if existing_movie:
            try:
                database.execute(
                    delete(TableMovies)
                    .where(TableMovies.radarrId == movie_id)
                    .where(TableMovies.radarr_instance_id == radarr_instance_id))
            except IntegrityError as e:
                logging.error(f"BAZARR cannot delete movie {path_mappings.path_replace_movie(existing_movie.path)} "
                              f"because of {e}")
            else:
                event_stream(type='movie', action='delete', payload=int(movie_id))
                logging.debug(
                    f'BAZARR deleted this movie from the database: '
                    f'{path_mappings.path_replace_movie(existing_movie.path)}')
        return

    movie_default_enabled = settings.general.movie_default_enabled
    if movie_default_enabled is True:
        movie_default_profile = settings.general.movie_default_profile
        if movie_default_profile == '':
            movie_default_profile = None
    else:
        movie_default_profile = None

    apikey = instance.get('apikey', settings.radarr.apikey) if instance else settings.radarr.apikey
    audio_profiles = get_profile_list(instance=instance)
    tagsDict = get_tags(instance=instance)
    language_profiles = get_language_profiles()

    try:
        movie = None
        movie_data = get_movies_from_radarr_api(apikey_radarr=apikey, radarr_id=movie_id, instance=instance)
        if not movie_data:
            return
        else:
            if action == 'updated' and existing_movie:
                movie = movieParser(movie_data, action='update', tags_dict=tagsDict,
                                    language_profiles=language_profiles,
                                    movie_default_profile=movie_default_profile,
                                    audio_profiles=audio_profiles,
                                    radarr_instance_id=radarr_instance_id,
                                    instance=instance)
            elif action == 'updated' and not existing_movie:
                movie = movieParser(movie_data, action='insert', tags_dict=tagsDict,
                                    language_profiles=language_profiles,
                                    movie_default_profile=movie_default_profile,
                                    audio_profiles=audio_profiles,
                                    radarr_instance_id=radarr_instance_id,
                                    instance=instance)
    except Exception:
        logging.exception('BAZARR cannot get movie returned by SignalR feed from Radarr API.')
        return

    # Drop useless events
    if not movie and not existing_movie:
        return

    # Remove movie from DB
    if not movie and existing_movie:
        try:
            database.execute(
                delete(TableMovies)
                .where(TableMovies.radarrId == movie_id)
                .where(TableMovies.radarr_instance_id == radarr_instance_id))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot delete movie {path_mappings.path_replace_movie(existing_movie.path)} because "
                          f"of {e}")
        else:
            event_stream(type='movie', action='delete', payload=int(movie_id))
            logging.debug(
                f'BAZARR deleted this movie from the database:{path_mappings.path_replace_movie(existing_movie.path)}')
        return

    # Update existing movie in DB
    elif movie and existing_movie:
        try:
            movie['updated_at_timestamp'] = datetime.now()
            database.execute(
                update(TableMovies)
                .values(movie)
                .where(TableMovies.radarrId == movie['radarrId'])
                .where(TableMovies.radarr_instance_id == radarr_instance_id))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot update movie {path_mappings.path_replace_movie(movie['path'])} because "
                          f"of {e}")
        else:
            store_subtitles_movie(movie['path'], path_mappings.path_replace_movie(movie['path']))
            event_stream(type='movie', action='update', payload=int(movie_id))
            logging.debug(
                f'BAZARR updated this movie into the database:{path_mappings.path_replace_movie(movie["path"])}')

    # Insert new movie in DB
    elif movie and not existing_movie:
        try:
            movie['created_at_timestamp'] = datetime.now()
            database.execute(
                insert(TableMovies)
                .values(movie))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot insert movie {path_mappings.path_replace_movie(movie['path'])} because "
                          f"of {e}")
        else:
            store_subtitles_movie(movie['path'], path_mappings.path_replace_movie(movie['path']))
            event_stream(type='movie', action='update', payload=int(movie_id))
            logging.debug(
                f'BAZARR inserted this movie into the database:{path_mappings.path_replace_movie(movie["path"])}')

    # Downloading missing subtitles
    if defer_search:
        logging.debug(
            f'BAZARR searching for missing subtitles is deferred until scheduled task execution for this movie: '
            f'{path_mappings.path_replace_movie(movie["path"])}')
    else:
        if os.path.exists(path_mappings.path_replace_movie(movie["path"])):
            logging.debug(f'BAZARR downloading missing subtitles for this movie: {movie["title"]} ({movie["year"]})')
            if _is_there_missing_subtitles(radarr_id=movie_id, radarr_instance_id=radarr_instance_id):
                jobs_queue.feed_jobs_pending_queue(job_name=f'Downloading missing subtitles for {movie["title"]} '
                                                            f'({movie["year"]})',
                                                   module='subtitles.mass_download.movies',
                                                   func='movies_download_subtitles',
                                                   args=[],
                                                   kwargs={'no': movie_id},
                                                   is_signalr=is_signalr)
            else:
                logging.debug(f'BAZARR no missing subtitles for this movie: {movie["title"]} ({movie["year"]})')
        else:
            logging.debug(f'BAZARR cannot find this file yet (Radarr may be slow to import movie between disks?). '
                          f'Searching for missing subtitles is deferred until scheduled task execution for this movie: '
                          f'{movie["title"]} ({movie["year"]})')


def _is_there_missing_subtitles(radarr_id: int, radarr_instance_id: int = 1) -> bool:
    """
    Determines if there are any missing subtitles for a specified movie in the database.
    """
    movies_conditions = [(TableMovies.missing_subtitles.is_not(None)),
                         (TableMovies.missing_subtitles != '[]'),
                         (TableMovies.radarrId == radarr_id),
                         (TableMovies.radarr_instance_id == radarr_instance_id)]
    if not radarr_id:
        return False
    movies_conditions += get_exclusion_clause('movie')
    missing_movies = database.execute(
        select(TableMovies.missing_subtitles, TableMovies.failedAttempts)
        .select_from(TableMovies)
        .where(reduce(operator.and_, movies_conditions))) \
        .all()
    for missing_movie in missing_movies:
        for language in missing_movie.missing_subtitles:
            if is_search_active(desired_language=language, attempt_string=missing_movie.failedAttempts):
                return True
    return False

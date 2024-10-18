# coding=utf-8

import os
import logging
from constants import MINIMUM_VIDEO_SIZE

from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.config import settings
from utilities.path_mappings import path_mappings
from subtitles.indexer.movies import store_subtitles_movie, movies_full_scan_subtitles
from radarr.rootfolder import check_radarr_rootfolder
from subtitles.mass_download import movies_download_subtitles
from app.database import TableMovies, TableLanguagesProfiles, database, insert, update, delete, select
from app.event_handler import event_stream, show_progress, hide_progress

from .utils import get_profile_list, get_tags, get_movies_from_radarr_api
from .parser import movieParser

# map between booleans and strings in DB
bool_map = {"True": True, "False": False}

FEATURE_PREFIX = "SYNC_MOVIES "


def trace(message):
    if settings.general.debug:
        logging.debug(FEATURE_PREFIX + message)


def get_language_profiles():
    return database.execute(
        select(TableLanguagesProfiles.profileId, TableLanguagesProfiles.name, TableLanguagesProfiles.tag)).all()


def update_all_movies():
    movies_full_scan_subtitles()
    logging.info('BAZARR All existing movie subtitles indexed from disk.')


def get_movie_file_size_from_db(movie_path):
    try:
        bazarr_file_size = os.path.getsize(path_mappings.path_replace_movie(movie_path))
    except OSError:
        bazarr_file_size = 0
    return bazarr_file_size


# Update movies in DB
def update_movie(updated_movie, send_event):
    try:
        updated_movie['updated_at_timestamp'] = datetime.now()
        database.execute(
            update(TableMovies).values(updated_movie)
            .where(TableMovies.tmdbId == updated_movie['tmdbId']))
    except IntegrityError as e:
        logging.error(f"BAZARR cannot update movie {updated_movie['path']} because of {e}")
    else:
        store_subtitles_movie(updated_movie['path'], path_mappings.path_replace_movie(updated_movie['path']))

        if send_event:
            event_stream(type='movie', action='update', payload=updated_movie['radarrId'])


def get_movie_monitored_status(movie_id):
    existing_movie_monitored = database.execute(
        select(TableMovies.monitored)
        .where(TableMovies.tmdbId == str(movie_id)))\
        .first()
    if existing_movie_monitored is None:
        return True
    else:
        return bool_map[existing_movie_monitored[0]]


# Insert new movies in DB
def add_movie(added_movie, send_event):
    try:
        added_movie['created_at_timestamp'] = datetime.now()
        database.execute(
            insert(TableMovies)
            .values(added_movie))
    except IntegrityError as e:
        logging.error(f"BAZARR cannot insert movie {added_movie['path']} because of {e}")
    else:
        store_subtitles_movie(added_movie['path'], path_mappings.path_replace_movie(added_movie['path']))

        if send_event:
            event_stream(type='movie', action='update', payload=int(added_movie['radarrId']))


def update_movies(send_event=True):
    check_radarr_rootfolder()
    logging.debug('BAZARR Starting movie sync from Radarr.')
    apikey_radarr = settings.radarr.apikey

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

    if apikey_radarr is None:
        pass
    else:
        audio_profiles = get_profile_list()
        tagsDict = get_tags()
        language_profiles = get_language_profiles()

        # Get movies data from radarr
        movies = get_movies_from_radarr_api(apikey_radarr=apikey_radarr)
        if not isinstance(movies, list):
            return
        else:
            # Get current movies in DB
            current_movies_id_db = [x.tmdbId for x in
                                    database.execute(
                                        select(TableMovies.tmdbId))
                                    .all()]
            current_movies_db_kv = [x.items() for x in [y._asdict()['TableMovies'].__dict__ for y in
                                                        database.execute(
                                                            select(TableMovies))
                                                        .all()]]

            current_movies_radarr = [str(movie['tmdbId']) for movie in movies if movie['hasFile'] and
                                     'movieFile' in movie and
                                     (movie['movieFile']['size'] > MINIMUM_VIDEO_SIZE or
                                      get_movie_file_size_from_db(movie['movieFile']['path']) > MINIMUM_VIDEO_SIZE)]

            # Remove movies from DB that either no longer exist in Radarr or exist and Radarr says do not have a movie file
            movies_to_delete = list(set(current_movies_id_db) - set(current_movies_radarr))
            movies_deleted = []
            if len(movies_to_delete):
                try:
                    database.execute(delete(TableMovies).where(TableMovies.tmdbId.in_(movies_to_delete)))
                except IntegrityError as e:
                    logging.error(f"BAZARR cannot delete movies because of {e}")
                else:
                    for removed_movie in movies_to_delete:
                        movies_deleted.append(removed_movie)
                        if send_event:
                            event_stream(type='movie', action='delete', payload=removed_movie)

            # Add new movies and update movies that Radarr says have media files
            # Any new movies added to Radarr that don't have media files yet will not be added to DB
            movies_count = len(movies)
            sync_monitored = settings.radarr.sync_only_monitored_movies
            if sync_monitored:
                skipped_count = 0
            files_missing = 0
            movies_added = []
            movies_updated = []
            for i, movie in enumerate(movies):
                if send_event:
                    show_progress(id='movies_progress',
                                  header='Syncing movies...',
                                  name=movie['title'],
                                  value=i,
                                  count=movies_count)
                # Only movies that Radarr says have files downloaded will be kept up to date in the DB
                if movie['hasFile'] is True:
                    if 'movieFile' in movie:
                        if sync_monitored:
                            if get_movie_monitored_status(movie['tmdbId']) != movie['monitored']:
                                # monitored status is not the same as our DB
                                trace(f"{i}: (Monitor Status Mismatch) {movie['title']}")
                            elif not movie['monitored']:
                                trace(f"{i}: (Skipped Unmonitored) {movie['title']}")
                                skipped_count += 1
                                continue

                        if (movie['movieFile']['size'] > MINIMUM_VIDEO_SIZE or
                                get_movie_file_size_from_db(movie['movieFile']['path']) > MINIMUM_VIDEO_SIZE):
                            # Add/update movies from Radarr that have a movie file to current movies list
                            trace(f"{i}: (Processing) {movie['title']}")
                            if str(movie['tmdbId']) in current_movies_id_db:
                                parsed_movie = movieParser(movie, action='update',
                                                           tags_dict=tagsDict,
                                                           language_profiles=language_profiles,
                                                           movie_default_profile=movie_default_profile,
                                                           audio_profiles=audio_profiles)
                                if not any([parsed_movie.items() <= x for x in current_movies_db_kv]):
                                    update_movie(parsed_movie, send_event)
                                    movies_updated.append(parsed_movie['title'])
                            else:
                                parsed_movie = movieParser(movie, action='insert',
                                                           tags_dict=tagsDict,
                                                           language_profiles=language_profiles,
                                                           movie_default_profile=movie_default_profile,
                                                           audio_profiles=audio_profiles)
                                add_movie(parsed_movie, send_event)
                                movies_added.append(parsed_movie['title'])
                else:
                    trace(f"{i}: (Skipped File Missing) {movie['title']}")
                    files_missing += 1

            if send_event:
                hide_progress(id='movies_progress')

            trace(f"Skipped {files_missing} file missing movies out of {movies_count}")
            if sync_monitored:
                trace(f"Skipped {skipped_count} unmonitored movies out of {movies_count}")
                trace(f"Processed {movies_count - files_missing - skipped_count} movies out of {movies_count} "
                      f"with {len(movies_added)} added, {len(movies_updated)} updated and "
                      f"{len(movies_deleted)} deleted")
            else:
                trace(f"Processed {movies_count - files_missing} movies out of {movies_count} with {len(movies_added)} added and "
                      f"{len(movies_updated)} updated")

            logging.debug('BAZARR All movies synced from Radarr into database.')


def update_one_movie(movie_id, action, defer_search=False):
    logging.debug(f'BAZARR syncing this specific movie from Radarr: {movie_id}')

    # Check if there's a row in database for this movie ID
    existing_movie = database.execute(
        select(TableMovies.path)
        .where(TableMovies.radarrId == movie_id))\
        .first()

    # Remove movie from DB
    if action == 'deleted':
        if existing_movie:
            try:
                database.execute(
                    delete(TableMovies)
                    .where(TableMovies.radarrId == movie_id))
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

    audio_profiles = get_profile_list()
    tagsDict = get_tags()
    language_profiles = get_language_profiles()

    try:
        # Get movie data from radarr api
        movie = None
        movie_data = get_movies_from_radarr_api(apikey_radarr=settings.radarr.apikey, radarr_id=movie_id)
        if not movie_data:
            return
        else:
            if action == 'updated' and existing_movie:
                movie = movieParser(movie_data, action='update', tags_dict=tagsDict, language_profiles=language_profiles,
                                    movie_default_profile=movie_default_profile, audio_profiles=audio_profiles)
            elif action == 'updated' and not existing_movie:
                movie = movieParser(movie_data, action='insert', tags_dict=tagsDict, language_profiles=language_profiles,
                                    movie_default_profile=movie_default_profile, audio_profiles=audio_profiles)
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
                .where(TableMovies.radarrId == movie_id))
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
                .where(TableMovies.radarrId == movie['radarrId']))
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

    # Storing existing subtitles
    logging.debug(f'BAZARR storing subtitles for this movie: {path_mappings.path_replace_movie(movie["path"])}')
    store_subtitles_movie(movie['path'], path_mappings.path_replace_movie(movie['path']))

    # Downloading missing subtitles
    if defer_search:
        logging.debug(
            f'BAZARR searching for missing subtitles is deferred until scheduled task execution for this movie: '
            f'{path_mappings.path_replace_movie(movie["path"])}')
    else:
        logging.debug(
            f'BAZARR downloading missing subtitles for this movie: {path_mappings.path_replace_movie(movie["path"])}')
        movies_download_subtitles(movie_id)

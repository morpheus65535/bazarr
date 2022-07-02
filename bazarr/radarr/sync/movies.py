# coding=utf-8

import logging

from peewee import IntegrityError

from app.config import settings
from radarr.info import url_radarr
from utilities.path_mappings import path_mappings
from subtitles.indexer.movies import store_subtitles_movie, movies_full_scan_subtitles
from radarr.rootfolder import check_radarr_rootfolder
from subtitles.mass_download import movies_download_subtitles
from app.database import TableMovies
from app.event_handler import event_stream, show_progress, hide_progress

from .utils import get_profile_list, get_tags, get_movies_from_radarr_api
from .parser import movieParser


def update_all_movies():
    movies_full_scan_subtitles()
    logging.info('BAZARR All existing movie subtitles indexed from disk.')


def update_movies(send_event=True):
    check_radarr_rootfolder()
    logging.debug('BAZARR Starting movie sync from Radarr.')
    apikey_radarr = settings.radarr.apikey

    movie_default_enabled = settings.general.getboolean('movie_default_enabled')

    if movie_default_enabled is True:
        movie_default_profile = settings.general.movie_default_profile
        if movie_default_profile == '':
            movie_default_profile = None
    else:
        movie_default_profile = None

    if apikey_radarr is None:
        pass
    else:
        audio_profiles = get_profile_list()
        tagsDict = get_tags()

        # Get movies data from radarr
        movies = get_movies_from_radarr_api(url=url_radarr(), apikey_radarr=apikey_radarr)
        if not movies:
            return
        else:
            # Get current movies in DB
            current_movies_db = TableMovies.select(TableMovies.tmdbId, TableMovies.path, TableMovies.radarrId).dicts()

            current_movies_db_list = [x['tmdbId'] for x in current_movies_db]

            current_movies_radarr = []
            movies_to_update = []
            movies_to_add = []
            altered_movies = []

            # Build new and updated movies
            movies_count = len(movies)
            for i, movie in enumerate(movies):
                if send_event:
                    show_progress(id='movies_progress',
                                  header='Syncing movies...',
                                  name=movie['title'],
                                  value=i,
                                  count=movies_count)

                if movie['hasFile'] is True:
                    if 'movieFile' in movie:
                        if movie['movieFile']['size'] > 20480:
                            # Add movies in radarr to current movies list
                            current_movies_radarr.append(str(movie['tmdbId']))

                            if str(movie['tmdbId']) in current_movies_db_list:
                                movies_to_update.append(movieParser(movie, action='update',
                                                                    tags_dict=tagsDict,
                                                                    movie_default_profile=movie_default_profile,
                                                                    audio_profiles=audio_profiles))
                            else:
                                movies_to_add.append(movieParser(movie, action='insert',
                                                                 tags_dict=tagsDict,
                                                                 movie_default_profile=movie_default_profile,
                                                                 audio_profiles=audio_profiles))

            if send_event:
                hide_progress(id='movies_progress')

            # Remove old movies from DB
            removed_movies = list(set(current_movies_db_list) - set(current_movies_radarr))

            for removed_movie in removed_movies:
                try:
                    TableMovies.delete().where(TableMovies.tmdbId == removed_movie).execute()
                except Exception as e:
                    logging.error(f"BAZARR cannot remove movie tmdbId {removed_movie} because of {e}")
                    continue

            # Update movies in DB
            movies_in_db_list = []
            movies_in_db = TableMovies.select(TableMovies.radarrId,
                                              TableMovies.title,
                                              TableMovies.path,
                                              TableMovies.tmdbId,
                                              TableMovies.overview,
                                              TableMovies.poster,
                                              TableMovies.fanart,
                                              TableMovies.audio_language,
                                              TableMovies.sceneName,
                                              TableMovies.monitored,
                                              TableMovies.sortTitle,
                                              TableMovies.year,
                                              TableMovies.alternativeTitles,
                                              TableMovies.format,
                                              TableMovies.resolution,
                                              TableMovies.video_codec,
                                              TableMovies.audio_codec,
                                              TableMovies.imdbId,
                                              TableMovies.movie_file_id,
                                              TableMovies.tags,
                                              TableMovies.file_size).dicts()

            for item in movies_in_db:
                movies_in_db_list.append(item)

            movies_to_update_list = [i for i in movies_to_update if i not in movies_in_db_list]

            for updated_movie in movies_to_update_list:
                try:
                    TableMovies.update(updated_movie).where(TableMovies.tmdbId == updated_movie['tmdbId']).execute()
                except IntegrityError as e:
                    logging.error(f"BAZARR cannot update movie {updated_movie['path']} because of {e}")
                    continue
                else:
                    altered_movies.append([updated_movie['tmdbId'],
                                           updated_movie['path'],
                                           updated_movie['radarrId'],
                                           updated_movie['monitored']])

            # Insert new movies in DB
            for added_movie in movies_to_add:
                try:
                    result = TableMovies.insert(added_movie).on_conflict(action='IGNORE').execute()
                except IntegrityError as e:
                    logging.error(f"BAZARR cannot insert movie {added_movie['path']} because of {e}")
                    continue
                else:
                    if result > 0:
                        altered_movies.append([added_movie['tmdbId'],
                                               added_movie['path'],
                                               added_movie['radarrId'],
                                               added_movie['monitored']])
                        if send_event:
                            event_stream(type='movie', action='update', payload=int(added_movie['radarrId']))
                    else:
                        logging.debug('BAZARR unable to insert this movie into the database:',
                                      path_mappings.path_replace_movie(added_movie['path']))

            # Store subtitles for added or modified movies
            for i, altered_movie in enumerate(altered_movies, 1):
                store_subtitles_movie(altered_movie[1], path_mappings.path_replace_movie(altered_movie[1]))

            logging.debug('BAZARR All movies synced from Radarr into database.')


def update_one_movie(movie_id, action, defer_search=False):
    logging.debug('BAZARR syncing this specific movie from Radarr: {}'.format(movie_id))

    # Check if there's a row in database for this movie ID
    existing_movie = TableMovies.select(TableMovies.path)\
        .where(TableMovies.radarrId == movie_id)\
        .dicts()\
        .get_or_none()

    # Remove movie from DB
    if action == 'deleted':
        if existing_movie:
            try:
                TableMovies.delete().where(TableMovies.radarrId == movie_id).execute()
            except Exception as e:
                logging.error(f"BAZARR cannot delete movie {existing_movie['path']} because of {e}")
            else:
                event_stream(type='movie', action='delete', payload=int(movie_id))
                logging.debug('BAZARR deleted this movie from the database:{}'.format(path_mappings.path_replace_movie(
                    existing_movie['path'])))
        return

    movie_default_enabled = settings.general.getboolean('movie_default_enabled')

    if movie_default_enabled is True:
        movie_default_profile = settings.general.movie_default_profile
        if movie_default_profile == '':
            movie_default_profile = None
    else:
        movie_default_profile = None

    audio_profiles = get_profile_list()
    tagsDict = get_tags()

    try:
        # Get movie data from radarr api
        movie = None
        movie_data = get_movies_from_radarr_api(url=url_radarr(), apikey_radarr=settings.radarr.apikey,
                                                radarr_id=movie_id)
        if not movie_data:
            return
        else:
            if action == 'updated' and existing_movie:
                movie = movieParser(movie_data, action='update', tags_dict=tagsDict,
                                    movie_default_profile=movie_default_profile, audio_profiles=audio_profiles)
            elif action == 'updated' and not existing_movie:
                movie = movieParser(movie_data, action='insert', tags_dict=tagsDict,
                                    movie_default_profile=movie_default_profile, audio_profiles=audio_profiles)
    except Exception:
        logging.debug('BAZARR cannot get movie returned by SignalR feed from Radarr API.')
        return

    # Drop useless events
    if not movie and not existing_movie:
        return

    # Remove movie from DB
    if not movie and existing_movie:
        try:
            TableMovies.delete().where(TableMovies.radarrId == movie_id).execute()
        except Exception as e:
            logging.error(f"BAZARR cannot insert episode {existing_movie['path']} because of {e}")
        else:
            event_stream(type='movie', action='delete', payload=int(movie_id))
            logging.debug('BAZARR deleted this movie from the database:{}'.format(path_mappings.path_replace_movie(
                existing_movie['path'])))
            return

    # Update existing movie in DB
    elif movie and existing_movie:
        try:
            TableMovies.update(movie).where(TableMovies.radarrId == movie['radarrId']).execute()
        except IntegrityError as e:
            logging.error(f"BAZARR cannot insert episode {movie['path']} because of {e}")
        else:
            event_stream(type='movie', action='update', payload=int(movie_id))
            logging.debug('BAZARR updated this movie into the database:{}'.format(path_mappings.path_replace_movie(
                movie['path'])))

    # Insert new movie in DB
    elif movie and not existing_movie:
        try:
            TableMovies.insert(movie).on_conflict(action='IGNORE').execute()
        except IntegrityError as e:
            logging.error(f"BAZARR cannot insert movie {movie['path']} because of {e}")
        else:
            event_stream(type='movie', action='update', payload=int(movie_id))
            logging.debug('BAZARR inserted this movie into the database:{}'.format(path_mappings.path_replace_movie(
                movie['path'])))

    # Storing existing subtitles
    logging.debug('BAZARR storing subtitles for this movie: {}'.format(path_mappings.path_replace_movie(
            movie['path'])))
    store_subtitles_movie(movie['path'], path_mappings.path_replace_movie(movie['path']))

    # Downloading missing subtitles
    if defer_search:
        logging.debug('BAZARR searching for missing subtitles is deferred until scheduled task execution for this '
                      'movie: {}'.format(path_mappings.path_replace_movie(movie['path'])))
    else:
        logging.debug('BAZARR downloading missing subtitles for this movie: {}'.format(path_mappings.path_replace_movie(
            movie['path'])))
        movies_download_subtitles(movie_id)

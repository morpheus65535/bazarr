# coding=utf-8

import os
import re
import logging
from indexer.tmdb_caching_proxy import tmdb
from database import TableMoviesRootfolder, TableMovies
from event_handler import show_progress, hide_progress
from indexer.video_prop_reader import video_prop_reader
from indexer.tmdb_caching_proxy import tmdb_func_cache
from indexer.utils import normalize_title, VIDEO_EXTENSION
from list_subtitles import store_subtitles_movie
from config import settings


def list_movies_directories(root_dir_id):
    # return the movies subdirectories for a specific root folder ID
    movies_directories = []

    try:
        # get root folder row
        root_dir_path = TableMoviesRootfolder.select(TableMoviesRootfolder.path)\
            .where(TableMoviesRootfolder.rootId == root_dir_id)\
            .dicts()\
            .get()
    except Exception:
        pass
    else:
        if not root_dir_path:
            logging.debug(f'BAZARR cannot find the specified movies root folder: {root_dir_id}')
            return movies_directories
        # get root folder subdirectories (first level). They should be movies parent directories.
        for i, directory_temp in enumerate(os.listdir(root_dir_path['path'])):
            # remove year fo directory name if found
            directory = re.sub(r"\(\b(19|20)\d{2}\b\)", '', directory_temp).rstrip()
            # deal with trailing article
            if directory.endswith(', The'):
                directory = 'The ' + directory.rstrip(', The')
            elif directory.endswith(', A'):
                directory = 'A ' + directory.rstrip(', A')
            # exclude invisible directories and append the directory to the list that will be returned
            if not directory.startswith('.'):
                movies_directories.append(
                    {
                        'id': i,
                        'directory': directory_temp,
                        'rootDir': root_dir_id
                    }
                )
    finally:
        return movies_directories


def get_movies_match(directory):
    # get matching movies from tmdb using the directory name
    directory_temp = directory
    # get year from directory name if available
    year_match = re.search(r"\((\b(19|20)\d{2}\b)\)", directory_temp)
    if year_match:
        year = year_match.group(1)
    else:
        year = None
    # remove year fo directory name if found
    directory = re.sub(r"\(\b(19|20)\d{2}\b\)", '', directory_temp).rstrip()
    if directory.endswith(', The'):
        directory = 'The ' + directory.rstrip(', The')
    elif directory.endswith(', A'):
        directory = 'A ' + directory.rstrip(', A')

    try:
        # get matches from tmdb (potentially from cache)
        movies_temp = tmdb_func_cache(tmdb.Search().movie, query=directory, year=year)
    except Exception as e:
        logging.exception('BAZARR is facing issues indexing movies: {0}'.format(repr(e)))
    else:
        matching_movies = []
        # if there's results, parse them to return matching titles
        if len(movies_temp['results']):
            for item in movies_temp['results']:
                year = None
                if 'release_date' in item:
                    year = item['release_date'][:4]
                matching_movies.append(
                    {
                        'title': item['original_title'],
                        'year': year or 'n/a',
                        'tmdbId': item['id']
                    }
                )
        else:
            logging.debug(f'BAZARR cannot match {directory} with TMDB.')
        return matching_movies


def get_movie_file_from_list(path):
    # simple function to get the path of the biggest file in a directory. We presume it's the movie file.
    max_size = 0
    max_file = None

    for folder, subfolders, files in os.walk(path):
        files.sort()
        for file in files:
            if os.path.splitext(file)[1] in VIDEO_EXTENSION:
                if os.path.exists(os.path.join(folder, file)):
                    size = os.stat(os.path.join(folder, file)).st_size
                    if size > max_size:
                        max_size = size
                        max_file = file

    return max_file


def get_movies_metadata(tmdbid, root_dir_id, dir_name=None, movie_path=None):
    # get the metadata from tmdb for a specific tmdbid
    movies_metadata = {}
    # get root folder row
    root_dir_path = TableMoviesRootfolder.select(TableMoviesRootfolder.path)\
        .where(TableMoviesRootfolder.rootId == root_dir_id)\
        .dicts()\
        .get()
    if tmdbid:
        try:
            # get movie info, alternative titles and external ids from tmdb using cache if available
            movies_info = tmdb_func_cache(tmdb.Movies(tmdbid).info,
                                          append_to_response='alternative_titles,external_ids')
        except Exception as e:
            logging.exception('BAZARR is facing issues indexing movies: {0}'.format(repr(e)))
        else:
            # parse metadata returned by tmdb
            images_url = 'https://image.tmdb.org/t/p/w500{0}'
            movies_metadata = {
                'title': movies_info['title'],
                'sortTitle': normalize_title(movies_info['title']),
                'year': movies_info['release_date'][:4] if movies_info['release_date'] else None,
                'overview': movies_info['overview'],
                'poster': images_url.format(movies_info['poster_path']) if movies_info['poster_path'] else None,
                'fanart': images_url.format(movies_info['backdrop_path']) if movies_info['backdrop_path'] else None,
                'alternativeTitles': [x['title'] for x in movies_info['alternative_titles']['titles']],
                'imdbId': movies_info['external_ids']['imdb_id']
            }

            if dir_name:
                # only for initial import and not update
                movie_dir = os.path.join(root_dir_path['path'], dir_name)
                movie_file = get_movie_file_from_list(movie_dir)

                movies_metadata['rootdir'] = root_dir_id
                movies_metadata['path'] = os.path.join(movie_dir, movie_file) if movie_file else None
                movies_metadata['tmdbId'] = tmdbid

                if movie_file:
                    movies_metadata.update(video_prop_reader(file=os.path.join(movie_dir, movie_file),
                                                             media_type='movie',
                                                             use_cache=False))
            else:
                # otherwise we use only what's required to update the db row
                movies_metadata.update(video_prop_reader(file=movie_path,
                                                         media_type='movie',
                                                         use_cache=settings.movies.getboolean('use_ffprobe_cache')))

        return movies_metadata


def update_indexed_movies():
    # update all movies in db, insert new ones and remove old ones
    root_dir_ids = TableMoviesRootfolder.select(TableMoviesRootfolder.rootId, TableMoviesRootfolder.path).dicts()
    root_dir_ids_len = len(root_dir_ids)
    for i, root_dir_id in enumerate(root_dir_ids):
        show_progress(
            id="m1_indexing_root_dirs",
            header="Indexing movies root folders...",
            name=root_dir_id['path'],
            value=i,
            count=root_dir_ids_len
        )

        # for each root folder, get the existing movies rows
        existing_movies = TableMovies.select(TableMovies.path,
                                             TableMovies.movieId,
                                             TableMovies.tmdbId)\
            .where(TableMovies.rootdir == root_dir_id['rootId'])\
            .order_by(TableMovies.title)\
            .dicts()

        existing_movies_len = len(existing_movies)
        existing_movies_iteration_number = 0
        for existing_movie in existing_movies:
            # delete removed movie form database
            if not os.path.exists(existing_movie['path']):
                TableMovies.delete().where(TableMovies.path == existing_movie['path']).execute()
            # update existing episodes metadata
            else:
                movie_metadata = get_movies_metadata(tmdbid=existing_movie['tmdbId'],
                                                     root_dir_id=root_dir_id['rootId'],
                                                     movie_path=existing_movie['path'])
                if movie_metadata:
                    show_progress(
                        id="m2_updating_existing_subdirectories_movies",
                        header="Updating existing movies...",
                        name=movie_metadata['title'],
                        value=existing_movies_iteration_number,
                        count=existing_movies_len
                    )

                    TableMovies.update(movie_metadata).where(TableMovies.movieId ==
                                                             existing_movie['movieId']).execute()
                    store_subtitles_movie(existing_movie['path'],
                                          use_cache=settings.movies.getboolean('use_ffprobe_cache'))
            existing_movies_iteration_number += 1
        hide_progress(id="m2_updating_existing_subdirectories_movies")

        # add missing movies to database
        root_dir_subdirectories = list_movies_directories(root_dir_id['rootId'])
        # get existing movies paths
        existing_movies_paths = [os.path.dirname(x['path']) for x in existing_movies]
        root_dir_subdirectories_len = len(root_dir_subdirectories) - \
            len(TableMovies.select().where(TableMovies.rootdir == root_dir_id['rootId']))
        root_dir_subdirectories_iteration_number = 0
        for root_dir_subdirectory in root_dir_subdirectories:
            if os.path.join(root_dir_id['path'], root_dir_subdirectory['directory']) in existing_movies_paths:
                # movie is already in db so we'll skip it
                root_dir_subdirectories_iteration_number += 1
                continue
            else:
                # new movie, let's get matches for it
                root_dir_match = get_movies_match(root_dir_subdirectory['directory'])
                if root_dir_match:
                    # now that we have at least a match, we'll assume the first one is the good one and get metadata
                    directory_metadata = get_movies_metadata(root_dir_match[0]['tmdbId'], root_dir_id['rootId'],
                                                             root_dir_subdirectory['directory'])
                    if directory_metadata and directory_metadata['path']:
                        show_progress(
                            id="m2_adding_new_subdirectories_movies",
                            header="Adding new movies...",
                            name=directory_metadata['title'],
                            value=root_dir_subdirectories_iteration_number,
                            count=root_dir_subdirectories_len
                        )

                        try:
                            # let's insert this movie into the db
                            result = TableMovies.insert(directory_metadata).execute()
                        except Exception as e:
                            logging.error(f'BAZARR is unable to insert this movie to the database: '
                                          f'"{directory_metadata["path"]}". The exception encountered is "{e}".')
                        else:
                            if result:
                                # once added to the db, we'll index existing subtitles and calculate the missing ones
                                store_subtitles_movie(directory_metadata['path'], use_cache=False)
            root_dir_subdirectories_iteration_number += 1
        hide_progress(id="m2_adding_new_subdirectories_movies")
    hide_progress(id="m1_indexing_root_dirs")


def update_specific_movie(movieId, use_cache=True):
    # update a specific movieId using the ffprobe cache
    movie_metadata = TableMovies.select().where(TableMovies.movieId == movieId).dicts().get()
    # get metadata for this movie
    directory_metadata = get_movies_metadata(movie_metadata['tmdbId'], movie_metadata['rootdir'],
                                             movie_path=movie_metadata['path'])
    if directory_metadata:
        try:
            # update the db
            result = TableMovies.update(directory_metadata).where(TableMovies.movieId == movieId).execute()
        except Exception as e:
            logging.error(f'BAZARR is unable to update this movie to the database: '
                          f'"{movie_metadata["path"]}". The exception encountered is "{e}".')
        else:
            if result:
                # index existing subtitles and calculate missing ones
                store_subtitles_movie(movie_metadata['path'], use_cache=use_cache)

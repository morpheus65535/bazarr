# coding=utf-8

import os
import re
import logging
from indexer.tmdb_caching_proxy import tmdb
from database import TableMoviesRootfolder, TableMovies
from indexer.video_prop_reader import VIDEO_EXTENSION, video_prop_reader
from indexer.tmdb_caching_proxy import tmdb_func_cache
from list_subtitles import store_subtitles_movie

WordDelimiterRegex = re.compile(r"(\s|\.|,|_|-|=|\|)+")
PunctuationRegex = re.compile(r"[^\w\s]")
CommonWordRegex = re.compile(r"\b(a|an|the|and|or|of)\b\s?")
DuplicateSpacesRegex = re.compile(r"\s{2,}")


def list_movies_directories(root_dir):
    movies_directories = []

    try:
        root_dir_path = TableMoviesRootfolder.select(TableMoviesRootfolder.path)\
            .where(TableMoviesRootfolder.rootId == root_dir)\
            .dicts()\
            .get()
    except:
        pass
    else:
        if not root_dir_path:
            logging.debug(f'BAZARR cannot find the specified movies root folder: {root_dir}')
            return movies_directories
        for i, directory_temp in enumerate(os.listdir(root_dir_path['path'])):
            directory_original = re.sub(r"\(\b(19|20)\d{2}\b\)", '', directory_temp).rstrip()
            directory = re.sub(r"\s\b(19|20)\d{2}\b", '', directory_original).rstrip()
            if directory.endswith(', The'):
                directory = 'The ' + directory.rstrip(', The')
            elif directory.endswith(', A'):
                directory = 'A ' + directory.rstrip(', A')
            if not directory.startswith('.'):
                movies_directories.append(
                    {
                        'id': i,
                        'directory': directory_temp,
                        'rootDir': root_dir
                    }
                )
    finally:
        return movies_directories


def get_movies_match(directory):
    directory_temp = directory
    directory_original = re.sub(r"\(\b(19|20)\d{2}\b\)", '', directory_temp).rstrip()
    directory = re.sub(r"\s\b(19|20)\d{2}\b", '', directory_original).rstrip()

    try:
        movies_temp = tmdb_func_cache(tmdb.Search().movie, query=directory)
    except Exception as e:
        logging.exception('BAZARR is facing issues indexing movies: {0}'.format(repr(e)))
    else:
        matching_movies = []
        if movies_temp['total_results']:
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
        return matching_movies


def get_movie_file_from_list(path):
    max_size = 0
    max_file = None

    for folder, subfolders, files in os.walk(path):
        for file in files:
            if os.path.splitext(file)[1] in VIDEO_EXTENSION:
                if os.path.exists(os.path.join(folder, file)):
                    size = os.stat(os.path.join(folder, file)).st_size
                    if size > max_size:
                        max_size = size
                        max_file = file

    return max_file


def get_movies_metadata(tmdbid, root_dir_id, dir_name=None, movie_path=None):
    movies_metadata = {}
    root_dir_path = TableMoviesRootfolder.select(TableMoviesRootfolder.path)\
        .where(TableMoviesRootfolder.rootId == root_dir_id)\
        .dicts()\
        .get()
    if tmdbid:
        try:
            movies_info = tmdb_func_cache(tmdb.Movies(tmdbid).info)
            alternative_titles = tmdb_func_cache(tmdb.Movies(tmdbid).alternative_titles)
            external_ids = tmdb_func_cache(tmdb.Movies(tmdbid).external_ids)
        except Exception as e:
            logging.exception('BAZARR is facing issues indexing movies: {0}'.format(repr(e)))
        else:
            images_url = 'https://image.tmdb.org/t/p/w500{0}'
            movies_metadata = {
                'title': movies_info['title'],
                'sortTitle': normalize_title(movies_info['title']),
                'year': movies_info['release_date'][:4] if movies_info['release_date'] else None,
                'overview': movies_info['overview'],
                'poster': images_url.format(movies_info['poster_path']) if movies_info['poster_path'] else None,
                'fanart': images_url.format(movies_info['backdrop_path']) if movies_info['backdrop_path'] else None,
                'alternativeTitles': [x['title'] for x in alternative_titles['titles']],
                'imdbId': external_ids['imdb_id']
            }

            # only for initial import and not update
            if dir_name:
                movie_dir = os.path.join(root_dir_path['path'], dir_name)
                movie_file = get_movie_file_from_list(movie_dir)

                movies_metadata['rootdir'] = root_dir_id
                movies_metadata['path'] = os.path.join(movie_dir, movie_file) if movie_file else None
                movies_metadata['tmdbId'] = tmdbid

                if movie_file:
                    movies_metadata.update(video_prop_reader(os.path.join(movie_dir, movie_file)))
            else:
                movies_metadata.update(video_prop_reader(movie_path))

        return movies_metadata


def normalize_title(title):
    title = title.lower()

    title = re.sub(WordDelimiterRegex, " ", title)
    title = re.sub(PunctuationRegex, "", title)
    title = re.sub(CommonWordRegex, "", title)
    title = re.sub(DuplicateSpacesRegex, " ", title)

    return title.strip()


def update_indexed_movies():
    root_dir_ids = TableMoviesRootfolder.select(TableMoviesRootfolder.rootId, TableMoviesRootfolder.path).dicts()
    for root_dir_id in root_dir_ids:
        existing_movies = TableMovies.select(TableMovies.path,
                                             TableMovies.movieId,
                                             TableMovies.tmdbId)\
            .where(TableMovies.rootdir == root_dir_id['rootId'])\
            .dicts()

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
                    TableMovies.update(movie_metadata).where(TableMovies.movieId ==
                                                             existing_movie['movieId']).execute()
                    store_subtitles_movie(existing_movie['path'], use_cache=True)

        # add missing movies to database
        root_dir_subdirectories = list_movies_directories(root_dir_id['rootId'])
        existing_movies_paths = [os.path.dirname(x['path']) for x in existing_movies]
        for root_dir_subdirectory in root_dir_subdirectories:
            if os.path.join(root_dir_id['path'], root_dir_subdirectory['directory']) in existing_movies_paths:
                continue
            else:
                root_dir_match = get_movies_match(root_dir_subdirectory['directory'])
                if root_dir_match:
                    directory_metadata = get_movies_metadata(root_dir_match[0]['tmdbId'], root_dir_id['rootId'],
                                                             root_dir_subdirectory['directory'])
                    if directory_metadata and directory_metadata['path']:
                        try:
                            result = TableMovies.insert(directory_metadata).execute()
                        except Exception as e:
                            logging.error(f'BAZARR is unable to insert this movie to the database: '
                                          f'"{directory_metadata["path"]}". The exception encountered is "{e}".')
                        else:
                            if result:
                                store_subtitles_movie(directory_metadata['path'], use_cache=False)


def update_specific_movie(movieId, use_cache=True):
    movie_metadata = TableMovies.select().where(TableMovies.movieId == movieId).dicts().get()
    directory_metadata = get_movies_metadata(movie_metadata['tmdbId'], movie_metadata['rootdir'],
                                             movie_path=movie_metadata['path'])
    if directory_metadata:
        try:
            result = TableMovies.update(directory_metadata).where(TableMovies.movieId == movieId).execute()
        except Exception as e:
            logging.error(f'BAZARR is unable to update this movie to the database: '
                          f'"{movie_metadata["path"]}". The exception encountered is "{e}".')
        else:
            if result:
                store_subtitles_movie(movie_metadata['path'], use_cache=use_cache)

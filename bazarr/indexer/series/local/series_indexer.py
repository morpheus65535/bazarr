# coding=utf-8
# pylama:ignore=W0611
# TODO unignore and fix W0611

import os
import re
import logging
from indexer.tmdb_caching_proxy import tmdb
from database import TableShowsRootfolder, TableShows
from indexer.tmdb_caching_proxy import tmdb_func_cache
from .episodes_indexer import update_series_episodes
from event_handler import show_progress, hide_progress

WordDelimiterRegex = re.compile(r"(\s|\.|,|_|-|=|\|)+")
PunctuationRegex = re.compile(r"[^\w\s]")
CommonWordRegex = re.compile(r"\b(a|an|the|and|or|of)\b\s?")
DuplicateSpacesRegex = re.compile(r"\s{2,}")


def list_series_directories(root_dir):
    series_directories = []

    try:
        root_dir_path = TableShowsRootfolder.select(TableShowsRootfolder.path)\
            .where(TableShowsRootfolder.rootId == root_dir)\
            .dicts()\
            .get()
    except Exception:
        pass
    else:
        if not root_dir_path:
            logging.debug(f'BAZARR cannot find the specified series root folder: {root_dir}')
            return series_directories
        for i, directory_temp in enumerate(os.listdir(root_dir_path['path'])):
            directory_original = re.sub(r"\(\b(19|20)\d{2}\b\)", '', directory_temp).rstrip()
            directory = re.sub(r"\s\b(19|20)\d{2}\b", '', directory_original).rstrip()
            if directory.endswith(', The'):
                directory = 'The ' + directory.rstrip(', The')
            elif directory.endswith(', A'):
                directory = 'A ' + directory.rstrip(', A')
            if not directory.startswith('.'):
                series_directories.append(
                    {
                        'id': i,
                        'directory': directory_temp,
                        'rootDir': root_dir
                    }
                )
    finally:
        return series_directories


def get_series_match(directory):
    directory_temp = directory
    directory_original = re.sub(r"\(\b(19|20)\d{2}\b\)", '', directory_temp).rstrip()
    directory = re.sub(r"\s\b(19|20)\d{2}\b", '', directory_original).rstrip()

    try:
        series_temp = tmdb_func_cache(tmdb.Search().tv, query=directory)
    except Exception as e:
        logging.exception('BAZARR is facing issues indexing series: {0}'.format(repr(e)))
    else:
        matching_series = []
        if series_temp['total_results']:
            for item in series_temp['results']:
                year = None
                if 'first_air_date' in item:
                    year = item['first_air_date'][:4]
                matching_series.append(
                    {
                        'title': item['original_name'],
                        'year': year or 'n/a',
                        'tmdbId': item['id']
                    }
                )
        return matching_series


def get_series_metadata(tmdbid, root_dir_id, dir_name=None):
    series_metadata = {}
    root_dir_path = TableShowsRootfolder.select(TableShowsRootfolder.path)\
        .where(TableShowsRootfolder.rootId == root_dir_id)\
        .dicts()\
        .get()
    if tmdbid:
        try:
            series_info = tmdb_func_cache(tmdb.TV(tmdbid).info)
            alternative_titles = tmdb_func_cache(tmdb.TV(tmdbid).alternative_titles)
            external_ids = tmdb_func_cache(tmdb.TV(tmdbid).external_ids)
        except Exception as e:
            logging.exception('BAZARR is facing issues indexing series: {0}'.format(repr(e)))
        else:
            images_url = 'https://image.tmdb.org/t/p/w500{0}'

            series_metadata = {
                'title': series_info['original_name'],
                'sortTitle': normalize_title(series_info['original_name']),
                'year': series_info['first_air_date'][:4] if series_info['first_air_date'] else None,
                'overview': series_info['overview'],
                'poster': images_url.format(series_info['poster_path']) if series_info['poster_path'] else None,
                'fanart': images_url.format(series_info['backdrop_path'])if series_info['backdrop_path'] else None,
                'alternateTitles': [x['title'] for x in alternative_titles['results']],
                'imdbId': external_ids['imdb_id']
            }

            # only for initial import and not update
            if dir_name:
                series_metadata['rootdir'] = root_dir_id
                series_metadata['path'] = os.path.join(root_dir_path['path'], dir_name)
                series_metadata['tmdbId'] = tmdbid

        return series_metadata


def normalize_title(title):
    title = title.lower()

    title = re.sub(WordDelimiterRegex, " ", title)
    title = re.sub(PunctuationRegex, "", title)
    title = re.sub(CommonWordRegex, "", title)
    title = re.sub(DuplicateSpacesRegex, " ", title)

    return title.strip()


def update_indexed_series():
    root_dir_ids = TableShowsRootfolder.select(TableShowsRootfolder.rootId, TableShowsRootfolder.path).dicts()
    for root_dir_id in root_dir_ids:
        root_dir_subdirectories = list_series_directories(root_dir_id['rootId'])
        existing_subdirectories = [x['path'] for x in
                                   TableShows.select(TableShows.path)
                                   .where(TableShows.rootdir == root_dir_id['rootId'])
                                   .dicts()]

        for existing_subdirectory in existing_subdirectories:
            # delete removed series from database
            if not os.path.exists(existing_subdirectory):
                TableShows.delete().where(TableShows.path == existing_subdirectory).execute()
            # update existing series metadata
            else:
                show_metadata = TableShows.select().where(TableShows.path == existing_subdirectory).dicts().get()
                directory_metadata = get_series_metadata(show_metadata['tmdbId'], root_dir_id['rootId'])
                if directory_metadata:
                    result = TableShows.update(directory_metadata)\
                        .where(TableShows.tmdbId == show_metadata['tmdbId'])\
                        .execute()
                    if result:
                        update_series_episodes(seriesId=show_metadata['seriesId'], use_cache=True)

        # add missing series to database
        for root_dir_subdirectory in root_dir_subdirectories:
            if os.path.join(root_dir_id['path'], root_dir_subdirectory['directory']) in existing_subdirectories:
                continue
            else:
                root_dir_match = get_series_match(root_dir_subdirectory['directory'])
                if root_dir_match:
                    directory_metadata = get_series_metadata(root_dir_match[0]['tmdbId'], root_dir_id['rootId'],
                                                             root_dir_subdirectory['directory'])
                    if directory_metadata:
                        try:
                            series_id = TableShows.insert(directory_metadata).execute()
                        except Exception as e:
                            logging.error(f'BAZARR is unable to insert this series to the database: '
                                          f'"{directory_metadata["path"]}". The exception encountered is "{e}".')
                        else:
                            if series_id:
                                update_series_episodes(seriesId=series_id, use_cache=False)


def update_specific_series(seriesId):
    show_metadata = TableShows.select().where(TableShows.seriesId == seriesId).dicts().get()
    directory_metadata = get_series_metadata(show_metadata['tmdbId'], show_metadata['rootdir'])
    if directory_metadata:
        result = TableShows.update(directory_metadata) \
            .where(TableShows.tmdbId == show_metadata['tmdbId']) \
            .execute()
        if result:
            update_series_episodes(seriesId=show_metadata['seriesId'], use_cache=True)

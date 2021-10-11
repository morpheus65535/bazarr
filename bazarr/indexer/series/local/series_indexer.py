# coding=utf-8

import os
import re
import logging
from indexer.tmdb_caching_proxy import tmdb
from database import TableShowsRootfolder, TableShows
from event_handler import event_stream, show_progress, hide_progress
from indexer.tmdb_caching_proxy import tmdb_func_cache
from indexer.utils import normalize_title
from .episodes_indexer import update_series_episodes
from config import settings


def list_series_directories(root_dir):
    # get the series directories for a specific root folder id
    series_directories = []

    try:
        # get root folder row
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
            # iterate over each directories under the root folder path and strip year if present
            directory = re.sub(r"\(\b(19|20)\d{2}\b\)", '', directory_temp).rstrip()
            # deal with trailing article
            if directory.endswith(', The'):
                directory = 'The ' + directory.rstrip(', The')
            elif directory.endswith(', A'):
                directory = 'A ' + directory.rstrip(', A')
            # exclude invisible directories and append the directory to the list that will be returned
            if not directory.startswith('.'):
                series_directories.append(
                    {
                        'id': i,
                        'directory': directory_temp,
                        'rootDir': root_dir
                    }
                )
    finally:
        return sorted(series_directories, key=lambda d: d['directory'])


def get_series_match(directory):
    # get matching series from tmdb using the directory name
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
        series_temp = tmdb_func_cache(tmdb.Search().tv, query=directory, year=year)
    except Exception as e:
        logging.exception('BAZARR is facing issues indexing series: {0}'.format(repr(e)))
    else:
        matching_series = []
        # if there's results, parse them to return matching titles
        if len(series_temp['results']):
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
        else:
            logging.debug(f'BAZARR cannot match {directory} with TMDB.')
        return matching_series


def get_series_metadata(tmdbid, root_dir_id, dir_name=None):
    # get the metadata from tmdb for a specific tmdbid
    series_metadata = {}
    # get root folder row
    root_dir_path = TableShowsRootfolder.select(TableShowsRootfolder.path)\
        .where(TableShowsRootfolder.rootId == root_dir_id)\
        .dicts()\
        .get()
    if tmdbid:
        try:
            # get series info, alternative titles and external ids from tmdb using cache if available
            series_info = tmdb_func_cache(tmdb.TV(tmdbid).info, append_to_response='alternative_titles,external_ids')
        except Exception as e:
            logging.exception('BAZARR is facing issues indexing series: {0}'.format(repr(e)))
        else:
            # parse metadata returned by tmdb
            images_url = 'https://image.tmdb.org/t/p/w500{0}'
            series_metadata = {
                'title': series_info['original_name'],
                'sortTitle': normalize_title(series_info['original_name']),
                'year': series_info['first_air_date'][:4] if series_info['first_air_date'] else None,
                'overview': series_info['overview'],
                'poster': images_url.format(series_info['poster_path']) if series_info['poster_path'] else None,
                'fanart': images_url.format(series_info['backdrop_path'])if series_info['backdrop_path'] else None,
                'alternateTitles': [x['title'] for x in series_info['alternative_titles']['results']],
                'imdbId': series_info['external_ids']['imdb_id']
            }

            # only for initial import and not update
            if dir_name:
                series_metadata['rootdir'] = root_dir_id
                series_metadata['path'] = os.path.join(root_dir_path['path'], dir_name)
                series_metadata['tmdbId'] = tmdbid

        return series_metadata


def update_indexed_series():
    # update all series in db, insert new ones and remove old ones
    root_dir_ids = TableShowsRootfolder.select(TableShowsRootfolder.rootId, TableShowsRootfolder.path).dicts()
    root_dir_ids_len = len(root_dir_ids)
    for i, root_dir_id in enumerate(root_dir_ids):
        show_progress(
            id="s1_indexing_root_dirs",
            header="Indexing series root folders...",
            name=root_dir_id['path'],
            value=i,
            count=root_dir_ids_len
        )
        # for each root folder, get the existing series rows
        root_dir_subdirectories = list_series_directories(root_dir_id['rootId'])
        existing_subdirectories = [x['path'] for x in
                                   TableShows.select(TableShows.path)
                                   .where(TableShows.rootdir == root_dir_id['rootId'])
                                   .order_by(TableShows.title)
                                   .dicts()]

        existing_subdirectories_len = len(existing_subdirectories)
        existing_subdirectories_iteration_number = 0
        for existing_subdirectory in existing_subdirectories:
            show_metadata = TableShows.select().where(TableShows.path == existing_subdirectory).dicts().get()

            # delete removed series from database
            if not os.path.exists(existing_subdirectory):
                TableShows.delete().where(TableShows.path == existing_subdirectory).execute()
                event_stream(type='series', action='delete', payload=show_metadata['seriesId'])
            # update existing series metadata
            else:
                directory_metadata = get_series_metadata(show_metadata['tmdbId'], root_dir_id['rootId'])
                if directory_metadata:
                    show_progress(
                        id="s2_updating_existing_subdirectories",
                        header="Updating existing series...",
                        name=directory_metadata['title'],
                        value=existing_subdirectories_iteration_number,
                        count=existing_subdirectories_len
                    )

                    result = TableShows.update(directory_metadata)\
                        .where(TableShows.tmdbId == show_metadata['tmdbId'])\
                        .execute()
                    if result:
                        event_stream(type='series', action='update', payload=show_metadata['seriesId'])
                        update_series_episodes(seriesId=show_metadata['seriesId'],
                                               use_cache=settings.series.getboolean('use_ffprobe_cache'))
            existing_subdirectories_iteration_number += 1
        hide_progress(id="s2_updating_existing_subdirectories")

        # add missing series to database
        new_subdirectories_len = len(root_dir_subdirectories) - len(TableShows.select(TableShows.path)
                                                                    .where(TableShows.rootdir == root_dir_id['rootId']))
        new_directories_iteration_number = 0
        for root_dir_subdirectory in root_dir_subdirectories:
            if os.path.join(root_dir_id['path'], root_dir_subdirectory['directory']) in existing_subdirectories:
                # series is already in db so we'll skip it
                new_directories_iteration_number += 1
                continue
            else:
                # new series, let's get matches for it
                root_dir_match = get_series_match(root_dir_subdirectory['directory'])
                if root_dir_match:
                    # now that we have at least a match, we'll assume the first one is the good one and get metadata
                    directory_metadata = get_series_metadata(root_dir_match[0]['tmdbId'], root_dir_id['rootId'],
                                                             root_dir_subdirectory['directory'])
                    show_progress(
                        id="s2_adding_new_subdirectories",
                        header="Adding new series...",
                        name=directory_metadata['title'],
                        value=new_directories_iteration_number,
                        count=new_subdirectories_len
                    )
                    if directory_metadata:
                        try:
                            # let's insert this series into the db
                            series_id = TableShows.insert(directory_metadata).execute()
                        except Exception as e:
                            logging.error(f'BAZARR is unable to insert this series to the database: '
                                          f'"{directory_metadata["path"]}". The exception encountered is "{e}".')
                        else:
                            if series_id:
                                event_stream(type='series', action='update', payload=series_id)
                                # once added to the db, we'll check for episodes for this series
                                update_series_episodes(seriesId=series_id, use_cache=False)
            new_directories_iteration_number += 1
        hide_progress(id="s2_adding_new_subdirectories")
    hide_progress(id="s1_indexing_root_dirs")


def update_specific_series(seriesId):
    # update a specific series in db
    # get series row
    show_metadata = TableShows.select().where(TableShows.seriesId == seriesId).dicts().get()
    # get metadata for this series
    directory_metadata = get_series_metadata(show_metadata['tmdbId'], show_metadata['rootdir'])
    if directory_metadata:
        # if we get metadata, we update the db
        result = TableShows.update(directory_metadata) \
            .where(TableShows.tmdbId == show_metadata['tmdbId']) \
            .execute()
        if result:
            # if db updated, we check for episodes for this series
            update_series_episodes(seriesId=show_metadata['seriesId'], use_cache=False)

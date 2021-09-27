# coding=utf-8
# pylama:ignore=W0611
# TODO unignore and fix W0611

import os
import re
import logging
from indexer.tmdb_caching_proxy import tmdb
from guessit import guessit
from requests.exceptions import HTTPError
from database import TableShowsRootfolder, TableShows, TableEpisodes
from indexer.video_prop_reader import video_prop_reader
from indexer.tmdb_caching_proxy import tmdb_func_cache
from indexer.utils import VIDEO_EXTENSION
from list_subtitles import store_subtitles


def get_series_episodes(series_directory):
    # return, for a specific series path, all the video files that can be recursively found
    episodes_path = []
    for root, dirs, files in os.walk(series_directory):
        for filename in files:
            if os.path.splitext(filename)[1] in VIDEO_EXTENSION and filename[0] != '.':
                if os.path.exists(os.path.join(root, filename)):
                    episodes_path.append(os.path.join(root, filename))

    return episodes_path


def get_episode_metadata(file, tmdbid, series_id, update=False):
    # get specific episode file path metadata from tmdb
    episode_metadata = {}
    episode_info = {}
    # guess season an episode number from filename
    guessed = guessit(file)
    if 'season' in guessed and 'episode' in guessed:
        if isinstance(guessed['episode'], int):
            # single episode file
            episode_number = guessed['episode']
        else:
            # for multiple episode file, we use the first one. ex.: S01E01-02 will be added as episode 1
            episode_number = guessed['episode'][0]
        try:
            # get episode metadata from tmdb
            episode_info = tmdb_func_cache(tmdb.TV_Episodes(tv_id=tmdbid, season_number=guessed['season'],
                                                            episode_number=episode_number).info)
        except HTTPError:
            logging.debug(f"BAZARR can't find this episode on TMDB: {file}")
            # if we don't find the episode on tmdb, we add the episode with "TBA" as title
            episode_info['name'] = 'TBA'
        except Exception:
            logging.exception(f'BAZARR is facing issues indexing this episodes: {file}')
            return False
        else:
            episode_metadata = {
                'title': episode_info['name'],
                'season': guessed['season'],
                'episode': episode_number
            }
            if not update:
                episode_metadata['seriesId'] = series_id
                episode_metadata['path'] = file
            # we now get the video file metadata using ffprobe
            episode_metadata.update(video_prop_reader(file))

    return episode_metadata


def update_series_episodes(seriesId=None, use_cache=True):
    # update all episodes for all or a specific series
    if seriesId:
        # make sure that we work from a list of series even if there's only one
        series_ids = [seriesId]
    else:
        series_ids = [x['seriesId'] for x in TableShows.select(TableShows.seriesId).dicts()]

    for series_id in series_ids:
        # getting episodes from db for that series
        existing_series_episodes = TableEpisodes.select(TableEpisodes.path,
                                                        TableEpisodes.seriesId,
                                                        TableEpisodes.episodeId,
                                                        TableShows.tmdbId)\
            .join(TableShows)\
            .where(TableEpisodes.seriesId == series_id)\
            .dicts()

        for existing_series_episode in existing_series_episodes:
            # delete removed episodes form database
            if not os.path.exists(existing_series_episode['path']):
                TableEpisodes.delete().where(TableEpisodes.path == existing_series_episode['path']).execute()
            # update existing episodes metadata
            else:
                # get metadata for that episode from tmdb
                episode_metadata = get_episode_metadata(file=existing_series_episode['path'],
                                                        tmdbid=existing_series_episode['tmdbId'],
                                                        series_id=existing_series_episode['seriesId'],
                                                        update=True)
                if episode_metadata:
                    # updating db
                    TableEpisodes.update(episode_metadata).where(TableEpisodes.episodeId ==
                                                                 existing_series_episode['episodeId']).execute()
                    # indexing existing subtitles and missing ones.
                    store_subtitles(existing_series_episode['path'], use_cache=use_cache)

        # add missing episodes to database
        try:
            # get series row from db
            series_metadata = TableShows.select(TableShows.path,
                                                TableShows.tmdbId) \
                .where(TableShows.seriesId == series_id) \
                .dicts() \
                .get()
        except TableShows.DoesNotExist:
            # this show doesn't exists? duh...
            continue
        # get all the episodes for that series
        episodes = get_series_episodes(series_metadata['path'])
        # make it a list of paths
        existing_episodes = [x['path'] for x in existing_series_episodes]
        for episode in episodes:
            if episode in existing_episodes:
                # skip episode if it's already in DB (been updated earlier)
                continue
            else:
                # get episode metadata form tmdb
                episode_metadata = get_episode_metadata(episode, series_metadata['tmdbId'], series_id, update=False)
                if episode_metadata:
                    try:
                        # insert episod eto db
                        result = TableEpisodes.insert(episode_metadata).execute()
                    except Exception as e:
                        logging.error(f'BAZARR is unable to insert this episode to the database: '
                                      f'"{episode_metadata["path"]}". The exception encountered is "{e}".')
                    else:
                        if result:
                            # index existing subtitles and missing ones
                            store_subtitles(episode, use_cache=use_cache)

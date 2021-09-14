# coding=utf-8

import os
import re
import logging
from indexer.tmdb_caching_proxy import tmdb
from guessit import guessit
from requests.exceptions import HTTPError
from database import TableShowsRootfolder, TableShows, TableEpisodes
from indexer.video_prop_reader import VIDEO_EXTENSION, video_prop_reader
from indexer.tmdb_caching_proxy import tmdb_func_cache
from list_subtitles import store_subtitles


def get_series_episodes(series_directory):
    episodes_path = []
    for root, dirs, files in os.walk(series_directory):
        for filename in files:
            if os.path.splitext(filename)[1] in VIDEO_EXTENSION and filename[0] != '.':
                if os.path.exists(os.path.join(root, filename)):
                    episodes_path.append(os.path.join(root, filename))

    return episodes_path


def get_episode_metadata(file, tmdbid, series_id, update=False):
    episode_metadata = {}
    episode_info = {}
    guessed = guessit(file)
    if 'season' in guessed and 'episode' in guessed:
        if isinstance(guessed['episode'], int):
            episode_number = guessed['episode']
        else:
            episode_number = guessed['episode'][0]
        try:
            episode_info = tmdb_func_cache(tmdb.TV_Episodes(tv_id=tmdbid, season_number=guessed['season'],
                                                            episode_number=episode_number).info)
        except HTTPError:
            logging.debug(f"BAZARR can't find this episode on TMDB: {file}")
            episode_info['name'] = 'TBA'
        except Exception as e:
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
            episode_metadata.update(video_prop_reader(file))

    return episode_metadata


def update_series_episodes(seriesId=None, use_cache=True):
    if seriesId:
        series_ids = [seriesId]
    else:
        series_ids = [x['seriesId'] for x in TableShows.select(TableShows.seriesId).dicts()]

    for series_id in series_ids:
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
                episode_metadata = get_episode_metadata(file=existing_series_episode['path'],
                                                        tmdbid=existing_series_episode['tmdbId'],
                                                        series_id=existing_series_episode['seriesId'],
                                                        update=True)
                if episode_metadata:
                    TableEpisodes.update(episode_metadata).where(TableEpisodes.episodeId ==
                                                                 existing_series_episode['episodeId']).execute()
                    store_subtitles(existing_series_episode['path'], use_cache=use_cache)

        # add missing episodes to database
        try:
            series_metadata = TableShows.select(TableShows.path,
                                                TableShows.tmdbId) \
                .where(TableShows.seriesId == series_id) \
                .dicts() \
                .get()
        except TableShows.DoesNotExist:
            continue
        episodes = get_series_episodes(series_metadata['path'])
        existing_episodes = [x['path'] for x in existing_series_episodes]
        for episode in episodes:
            if episode in existing_episodes:
                continue
            else:
                episode_metadata = get_episode_metadata(episode, series_metadata['tmdbId'], series_id, update=False)
                if episode_metadata:
                    try:
                        result = TableEpisodes.insert(episode_metadata).execute()
                    except Exception as e:
                        logging.error(f'BAZARR is unable to insert this episode to the database: '
                                      f'"{episode_metadata["path"]}". The exception encountered is "{e}".')
                    else:
                        if result:
                            store_subtitles(episode, use_cache=use_cache)

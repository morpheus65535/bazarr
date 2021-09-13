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
                episodes_path.append(os.path.join(root, filename))

    return episodes_path


def get_episode_metadata(file, tmdbid, series_id):
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
                'seriesId': series_id,
                'title': episode_info['name'],
                'season': guessed['season'],
                'episode': episode_number,
                'path': file
            }
            episode_metadata.update(video_prop_reader(file))

    return episode_metadata


def index_all_episodes():
    TableEpisodes.delete().execute()
    series_ids = TableShows.select(TableShows.seriesId, TableShows.path, TableShows.tmdbId).dicts()
    for series_id in series_ids:
        episodes = get_series_episodes(series_id['path'])
        for episode in episodes:
            episode_metadata = get_episode_metadata(episode, series_id['tmdbId'], series_id['seriesId'])
            if episode_metadata:
                try:
                    result = TableEpisodes.insert(episode_metadata).execute()
                except Exception as e:
                    logging.error(f'BAZARR is unable to insert this episode to the database: '
                                  f'"{episode_metadata["path"]}". The exception encountered is "{e}".')
                else:
                    if result:
                        store_subtitles(episode)

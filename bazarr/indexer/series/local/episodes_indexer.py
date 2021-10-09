# coding=utf-8

import os
import logging
from indexer.tmdb_caching_proxy import tmdb
from guessit import guessit
from requests.exceptions import HTTPError
from database import TableShows, TableEpisodes
from event_handler import show_progress, hide_progress
from indexer.video_prop_reader import video_prop_reader
from indexer.tmdb_caching_proxy import tmdb_func_cache
from indexer.utils import VIDEO_EXTENSION
from list_subtitles import store_subtitles
from config import settings


def get_series_episodes(series_directory):
    # return, for a specific series path, all the video files that can be recursively found
    episodes_path = []
    for root, dirs, files in os.walk(series_directory):
        files.sort()
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
        if isinstance(guessed['season'], int):
            # single season file
            season_number = guessed['season']
        else:
            # for multiple season file, we use the first one. This one is really strange but I've run into it during
            # development...
            season_number = guessed['season'][0]

        if isinstance(guessed['episode'], int):
            # single episode file
            episode_number = guessed['episode']
        else:
            # for multiple episode file, we use the first one. ex.: S01E01-02 will be added as episode 1
            episode_number = guessed['episode'][0]

        try:
            # get episode metadata from tmdb
            episode_info = tmdb_func_cache(tmdb.TV_Episodes(tv_id=tmdbid, season_number=season_number,
                                                            episode_number=episode_number).info)
        except HTTPError:
            logging.debug(f"BAZARR can't find this episode on TMDB: {file}")
            # if we don't find the episode on tmdb, we add the episode with "TBA" as title
            episode_info['name'] = 'TBA'
        except Exception:
            logging.exception(f'BAZARR is facing issues indexing this episodes: {file}')
            return False
        finally:
            episode_metadata = {
                'title': episode_info['name'],
                'season': season_number,
                'episode': episode_number
            }
            if not update:
                episode_metadata['seriesId'] = series_id
                episode_metadata['path'] = file
                episode_metadata['monitored'] = "False"
                # we make sure the episode reflect it's series monitored state
                try:
                    series_monitored_state = TableShows.select(TableShows.monitored)\
                        .where(TableShows.seriesId == series_id)\
                        .dicts()\
                        .get()
                except TableShows.DoesNotExist:
                    pass
                else:
                    episode_metadata['monitored'] = series_monitored_state['monitored']
            # we now get the video file metadata using ffprobe
            episode_metadata.update(video_prop_reader(file=file, media_type='episode',
                                                      use_cache=settings.series.getboolean('use_ffprobe_cache')))

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
                                                        TableShows.tmdbId,
                                                        TableEpisodes.title.alias('episodeTitle'),
                                                        TableEpisodes.season,
                                                        TableEpisodes.episode,
                                                        TableShows.title.alias('seriesTitle'))\
            .join(TableShows)\
            .where(TableEpisodes.seriesId == series_id)\
            .order_by(TableEpisodes.season, TableEpisodes.episode)\
            .dicts()

        existing_series_episodes_len = len(existing_series_episodes)
        existing_series_episodes_iteration_number = 0
        for existing_series_episode in existing_series_episodes:
            show_progress(
                id="s3_series_episodes_update",
                header=f"Updating {existing_series_episode['seriesTitle']} episodes...",
                name=f"S{existing_series_episode['season']:02d}E{existing_series_episode['episode']:02d} - "
                     f"{existing_series_episode['episodeTitle']}",
                value=existing_series_episodes_iteration_number,
                count=existing_series_episodes_len
            )

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

            existing_series_episodes_iteration_number += 1

        hide_progress(id="s3_series_episodes_update")

        # add missing episodes to database
        try:
            # get series row from db
            series_metadata = TableShows.select(TableShows.path,
                                                TableShows.title,
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
        existing_episodes = [x['path'] for x in
                             TableEpisodes.select().where(TableEpisodes.seriesId == series_id).dicts()]
        existing_episodes_len = len(episodes) - len(existing_episodes)
        existing_episodes_iteration_number = 0
        for episode in episodes:
            if episode in existing_episodes:
                # skip episode if it's already in DB (been updated earlier)
                existing_episodes_iteration_number += 1
                continue
            else:
                # get episode metadata form tmdb
                episode_metadata = get_episode_metadata(episode, series_metadata['tmdbId'], series_id, update=False)
                if episode_metadata:
                    show_progress(
                        id="s3_series_episodes_add",
                        header=f"Adding {series_metadata['title']} episodes...",
                        name=f"S{episode_metadata['season']:02d}E{episode_metadata['episode']:02d} - "
                             f"{episode_metadata['title']}",
                        value=existing_episodes_iteration_number,
                        count=existing_episodes_len
                    )

                    try:
                        # insert episod eto db
                        result = TableEpisodes.insert(episode_metadata).execute()
                    except Exception as e:
                        logging.error(f'BAZARR is unable to insert this episode to the database: '
                                      f'"{episode_metadata["path"]}". The exception encountered is "{e}".')
                    else:
                        if result:
                            # index existing subtitles and missing ones
                            store_subtitles(episode, use_cache=False)
            existing_episodes_iteration_number += 1
        hide_progress(id="s3_series_episodes_add")

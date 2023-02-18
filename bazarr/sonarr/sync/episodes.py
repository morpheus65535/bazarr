# coding=utf-8

import os
import logging

from peewee import IntegrityError

from app.database import TableEpisodes
from app.config import settings
from utilities.path_mappings import path_mappings
from subtitles.indexer.series import store_subtitles, series_full_scan_subtitles
from subtitles.mass_download import episode_download_subtitles
from app.event_handler import event_stream, show_progress, hide_progress
from sonarr.info import get_sonarr_info, url_sonarr

from .parser import episodeParser
from .utils import get_series_from_sonarr_api, get_episodes_from_sonarr_api, get_episodesFiles_from_sonarr_api


def update_all_episodes():
    series_full_scan_subtitles()
    logging.info('BAZARR All existing episode subtitles indexed from disk.')


def sync_episodes(series_id=None, send_event=True):
    logging.debug('BAZARR Starting episodes sync from Sonarr.')
    apikey_sonarr = settings.sonarr.apikey

    # Get current episodes id in DB
    current_episodes_db = TableEpisodes.select(TableEpisodes.sonarrEpisodeId)\
        .where((TableEpisodes.sonarrSeriesId == series_id) if series_id else None)\
        .dicts()

    current_episodes_db_list = [x['sonarrEpisodeId'] for x in current_episodes_db]

    current_episodes_sonarr = []
    episodes_to_update = []
    episodes_to_add = []
    altered_episodes = []

    # Get sonarrId for each series from database
    seriesIdList = get_series_from_sonarr_api(url=url_sonarr(), apikey_sonarr=apikey_sonarr, sonarr_series_id=series_id)

    series_count = len(seriesIdList)
    for i, seriesId in enumerate(seriesIdList):
        if send_event:
            show_progress(id='episodes_progress',
                          header='Syncing episodes...',
                          name=seriesId['title'],
                          value=i,
                          count=series_count)

        # Get episodes data for a series from Sonarr
        episodes = get_episodes_from_sonarr_api(url=url_sonarr(), apikey_sonarr=apikey_sonarr,
                                                series_id=seriesId['id'])
        if not episodes:
            continue
        else:
            # For Sonarr v3, we need to update episodes to integrate the episodeFile API endpoint results
            if not get_sonarr_info.is_legacy():
                episodeFiles = get_episodesFiles_from_sonarr_api(url=url_sonarr(), apikey_sonarr=apikey_sonarr,
                                                                 series_id=seriesId['id'])
                for episode in episodes:
                    if episode['hasFile']:
                        item = [x for x in episodeFiles if x['id'] == episode['episodeFileId']]
                        if item:
                            episode['episodeFile'] = item[0]

            for episode in episodes:
                parsed_episode = episodeParser(episode)
                if parsed_episode:
                    # Add episodes in sonarr to current episode list
                    current_episodes_sonarr.append(episode['id'])
                    # Parse episode data
                    if episode['id'] in current_episodes_db_list:
                        update_episode(parsed_episode)
                    else:
                        add_episode(parsed_episode, send_event)

    if send_event:
        hide_progress(id='episodes_progress')

    # Remove old episodes from DB
    removed_episodes = list(set(current_episodes_db_list) - set(current_episodes_sonarr))
    remove_old_episodes(removed_episodes, send_event)

    logging.debug('BAZARR All episodes synced from Sonarr into database.')


def sync_one_episode(episode_id, defer_search=False):
    logging.debug('BAZARR syncing this specific episode from Sonarr: {}'.format(episode_id))
    url = url_sonarr()
    apikey_sonarr = settings.sonarr.apikey

    # Check if there's a row in database for this episode ID
    existing_episode = TableEpisodes.select(TableEpisodes.path, TableEpisodes.episode_file_id)\
        .where(TableEpisodes.sonarrEpisodeId == episode_id)\
        .dicts()\
        .get_or_none()

    try:
        # Get episode data from sonarr api
        episode = None
        episode_data = get_episodes_from_sonarr_api(url=url, apikey_sonarr=apikey_sonarr,
                                                    episode_id=episode_id)
        if not episode_data:
            return

        else:
            # For Sonarr v3, we need to update episodes to integrate the episodeFile API endpoint results
            if not get_sonarr_info.is_legacy() and existing_episode and episode_data['hasFile']:
                episode_data['episodeFile'] = \
                    get_episodesFiles_from_sonarr_api(url=url, apikey_sonarr=apikey_sonarr,
                                                      episode_file_id=episode_data['episodeFileId'])
            episode = episodeParser(episode_data)
    except Exception:
        logging.exception('BAZARR cannot get episode returned by SignalR feed from Sonarr API.')
        return

    # Drop useless events
    if not episode and not existing_episode:
        return

    # Remove episode from DB
    if not episode and existing_episode:
        try:
            TableEpisodes.delete().where(TableEpisodes.sonarrEpisodeId == episode_id).execute()
        except Exception as e:
            logging.error(f"BAZARR cannot delete episode {existing_episode['path']} because of {e}")
        else:
            event_stream(type='episode', action='delete', payload=int(episode_id))
            logging.debug('BAZARR deleted this episode from the database:{}'.format(path_mappings.path_replace(
                existing_episode['path'])))
            return

    # Update existing episodes in DB
    elif episode and existing_episode:
        try:
            TableEpisodes.update(episode).where(TableEpisodes.sonarrEpisodeId == episode_id).execute()
        except IntegrityError as e:
            logging.error(f"BAZARR cannot update episode {episode['path']} because of {e}")
        else:
            event_stream(type='episode', action='update', payload=int(episode_id))
            logging.debug('BAZARR updated this episode into the database:{}'.format(path_mappings.path_replace(
                episode['path'])))

    # Insert new episodes in DB
    elif episode and not existing_episode:
        try:
            TableEpisodes.insert(episode).on_conflict(action='IGNORE').execute()
        except IntegrityError as e:
            logging.error(f"BAZARR cannot insert episode {episode['path']} because of {e}")
        else:
            event_stream(type='episode', action='update', payload=int(episode_id))
            logging.debug('BAZARR inserted this episode into the database:{}'.format(path_mappings.path_replace(
                episode['path'])))

    # Storing existing subtitles
    logging.debug('BAZARR storing subtitles for this episode: {}'.format(path_mappings.path_replace(
            episode['path'])))
    store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))

    # Downloading missing subtitles
    if defer_search:
        logging.debug('BAZARR searching for missing subtitles is deferred until scheduled task execution for this '
                      'episode: {}'.format(path_mappings.path_replace(episode['path'])))
    else:
        logging.debug('BAZARR downloading missing subtitles for this episode: {}'.format(path_mappings.path_replace(
            episode['path'])))
        episode_download_subtitles(episode_id)


def remove_old_episodes(removed_episodes, send_event):
    logging.debug('BAZARR removing old episodes from database.')
    for episode in removed_episodes:
        try:
            TableEpisodes.delete().where(TableEpisodes.sonarrEpisodeId == episode).execute()
        except Exception as e:
            logging.exception(f"BAZARR cannot delete episode {episode} because of {e}")
        else:
            if send_event:
                event_stream(type='episode', action='delete', payload=int(episode))
            logging.debug(f'BAZARR deleted this episode from the database:{episode}')
    return


def update_episode(episode):
    if not TableEpisodes.need_update(episode):
        return
    try:
        TableEpisodes.update(episode).where(TableEpisodes.sonarrEpisodeId == episode['sonarrEpisodeId']).execute()
    except Exception as e:
        logging.exception(f"BAZARR cannot update episode {episode['path']} because of {e}")
    else:
        store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))
        logging.debug(f'BAZARR updated this episode into the database:{episode["path"]}')
    return


def add_episode(episode, send_event=True):
    try:
        TableEpisodes.insert(episode).on_conflict_ignore().execute()
    except Exception as e:
        logging.exception(f"BAZARR cannot insert episode {episode['path']} because of {e}")
    else:
        store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))
        if send_event:
            event_stream(type='episode', payload=episode['sonarrEpisodeId'])
        logging.debug(f'BAZARR inserted this episode into the database:{episode["path"]}')
    return

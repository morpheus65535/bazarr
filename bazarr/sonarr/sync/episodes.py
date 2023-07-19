# coding=utf-8

import os
import logging

from sqlalchemy.exc import IntegrityError

from app.database import database, TableEpisodes, delete, update, insert, select
from app.config import settings
from utilities.path_mappings import path_mappings
from subtitles.indexer.series import store_subtitles, series_full_scan_subtitles
from subtitles.mass_download import episode_download_subtitles
from app.event_handler import event_stream
from sonarr.info import get_sonarr_info, url_sonarr

from .parser import episodeParser
from .utils import get_episodes_from_sonarr_api, get_episodesFiles_from_sonarr_api


def update_all_episodes():
    series_full_scan_subtitles()
    logging.info('BAZARR All existing episode subtitles indexed from disk.')


def sync_episodes(series_id, send_event=True):
    logging.debug('BAZARR Starting episodes sync from Sonarr.')
    apikey_sonarr = settings.sonarr.apikey

    # Get current episodes id in DB
    if series_id:
        current_episodes_db_list = [row.sonarrEpisodeId for row in
                                    database.execute(
                                        select(TableEpisodes.sonarrEpisodeId,
                                               TableEpisodes.path,
                                               TableEpisodes.sonarrSeriesId)
                                        .where(TableEpisodes.sonarrSeriesId == series_id)).all()]
    else:
        return

    current_episodes_sonarr = []
    episodes_to_update = []
    episodes_to_add = []
    altered_episodes = []

    # Get episodes data for a series from Sonarr
    episodes = get_episodes_from_sonarr_api(url=url_sonarr(), apikey_sonarr=apikey_sonarr,
                                            series_id=series_id)
    if episodes:
        # For Sonarr v3, we need to update episodes to integrate the episodeFile API endpoint results
        if not get_sonarr_info.is_legacy():
            episodeFiles = get_episodesFiles_from_sonarr_api(url=url_sonarr(), apikey_sonarr=apikey_sonarr,
                                                             series_id=series_id)
            for episode in episodes:
                if episodeFiles and episode['hasFile']:
                    item = [x for x in episodeFiles if x['id'] == episode['episodeFileId']]
                    if item:
                        episode['episodeFile'] = item[0]

        for episode in episodes:
            if 'hasFile' in episode:
                if episode['hasFile'] is True:
                    if 'episodeFile' in episode:
                        try:
                            bazarr_file_size = \
                                os.path.getsize(path_mappings.path_replace(episode['episodeFile']['path']))
                        except OSError:
                            bazarr_file_size = 0
                        if episode['episodeFile']['size'] > 20480 or bazarr_file_size > 20480:
                            # Add episodes in sonarr to current episode list
                            current_episodes_sonarr.append(episode['id'])

                            # Parse episode data
                            if episode['id'] in current_episodes_db_list:
                                episodes_to_update.append(episodeParser(episode))
                            else:
                                episodes_to_add.append(episodeParser(episode))

    # Remove old episodes from DB
    removed_episodes = list(set(current_episodes_db_list) - set(current_episodes_sonarr))

    stmt = select(TableEpisodes.path,
                  TableEpisodes.sonarrSeriesId,
                  TableEpisodes.sonarrEpisodeId)
    for removed_episode in removed_episodes:
        episode_to_delete = database.execute(stmt.where(TableEpisodes.sonarrEpisodeId == removed_episode)).first()
        if not episode_to_delete:
            continue
        try:
            database.execute(
                delete(TableEpisodes)
                .where(TableEpisodes.sonarrEpisodeId == removed_episode))
        except Exception as e:
            logging.error(f"BAZARR cannot delete episode {episode_to_delete.path} because of {e}")
            continue
        else:
            if send_event:
                event_stream(type='episode', action='delete', payload=episode_to_delete.sonarrEpisodeId)

    # Update existing episodes in DB
    for updated_episode in episodes_to_update:
        if database.execute(
                select(TableEpisodes)
                .filter_by(**updated_episode))\
                .first():
            continue
        else:
            try:
                database.execute(
                    update(TableEpisodes)
                    .values(updated_episode)
                    .where(TableEpisodes.sonarrEpisodeId == updated_episode['sonarrEpisodeId']))
            except IntegrityError as e:
                logging.error(f"BAZARR cannot update episode {updated_episode['path']} because of {e}")
                continue
            else:
                altered_episodes.append([updated_episode['sonarrEpisodeId'],
                                         updated_episode['path'],
                                         updated_episode['sonarrSeriesId']])
                if send_event:
                    event_stream(type='episode', action='update', payload=updated_episode['sonarrEpisodeId'])

    # Insert new episodes in DB
    for added_episode in episodes_to_add:
        try:
            database.execute(
                insert(TableEpisodes)
                .values(added_episode))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot insert episode {added_episode['path']} because of {e}")
            continue
        else:
            altered_episodes.append([added_episode['sonarrEpisodeId'],
                                     added_episode['path'],
                                     added_episode['monitored']])
            if send_event:
                event_stream(type='episode', payload=added_episode['sonarrEpisodeId'])

    # Store subtitles for added or modified episodes
    for i, altered_episode in enumerate(altered_episodes, 1):
        store_subtitles(altered_episode[1], path_mappings.path_replace(altered_episode[1]))

    logging.debug('BAZARR All episodes synced from Sonarr into database.')


def sync_one_episode(episode_id, defer_search=False):
    logging.debug('BAZARR syncing this specific episode from Sonarr: {}'.format(episode_id))
    url = url_sonarr()
    apikey_sonarr = settings.sonarr.apikey

    # Check if there's a row in database for this episode ID
    existing_episode = database.execute(
        select(TableEpisodes.path, TableEpisodes.episode_file_id)
        .where(TableEpisodes.sonarrEpisodeId == episode_id)) \
        .first()

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
        database.execute(
            delete(TableEpisodes)
            .where(TableEpisodes.sonarrEpisodeId == episode_id))

        event_stream(type='episode', action='delete', payload=int(episode_id))
        logging.debug('BAZARR deleted this episode from the database:{}'.format(path_mappings.path_replace(
            existing_episode['path'])))
        return

    # Update existing episodes in DB
    elif episode and existing_episode:
        try:
            database.execute(
                update(TableEpisodes)
                .values(episode)
                .where(TableEpisodes.sonarrEpisodeId == episode_id))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot update episode {episode['path']} because of {e}")
        else:
            event_stream(type='episode', action='update', payload=int(episode_id))
            logging.debug('BAZARR updated this episode into the database:{}'.format(path_mappings.path_replace(
                episode['path'])))

    # Insert new episodes in DB
    elif episode and not existing_episode:
        try:
            database.execute(
                insert(TableEpisodes)
                .values(episode))
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

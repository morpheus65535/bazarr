# coding=utf-8

import os
import logging
from constants import MINIMUM_VIDEO_SIZE

from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.database import database, TableShows, TableEpisodes, delete, update, insert, select
from app.config import settings
from utilities.path_mappings import path_mappings
from subtitles.indexer.series import store_subtitles, series_full_scan_subtitles
from subtitles.mass_download import episode_download_subtitles
from app.event_handler import event_stream
from sonarr.info import get_sonarr_info

from .parser import episodeParser
from .utils import get_episodes_from_sonarr_api, get_episodesFiles_from_sonarr_api

# map between booleans and strings in DB
bool_map = {"True": True, "False": False}

FEATURE_PREFIX = "SYNC_EPISODES "


def trace(message):
    if settings.general.debug:
        logging.debug(FEATURE_PREFIX + message)


def get_episodes_monitored_table(series_id):
    episodes_monitored = database.execute(
        select(TableEpisodes.episode_file_id, TableEpisodes.monitored)
        .where(TableEpisodes.sonarrSeriesId == series_id))\
        .all()
    episode_dict = dict((x, y) for x, y in episodes_monitored)
    return episode_dict


def update_all_episodes():
    series_full_scan_subtitles()
    logging.info('BAZARR All existing episode subtitles indexed from disk.')


def sync_episodes(series_id, send_event=True, defer_search=False):
    logging.debug(f'BAZARR Starting episodes sync from Sonarr for series ID {series_id}.')
    apikey_sonarr = settings.sonarr.apikey

    # Get current episodes id in DB
    if series_id:
        current_episodes_id_db_list = [row.sonarrEpisodeId for row in
                                       database.execute(
                                           select(TableEpisodes.sonarrEpisodeId,
                                                  TableEpisodes.path,
                                                  TableEpisodes.sonarrSeriesId)
                                           .where(TableEpisodes.sonarrSeriesId == series_id)).all()]
        current_episodes_db_kv = [x.items() for x in [y._asdict()['TableEpisodes'].__dict__ for y in
                                                      database.execute(
                                                          select(TableEpisodes)
                                                          .where(TableEpisodes.sonarrSeriesId == series_id))
                                                      .all()]]
    else:
        return

    current_episodes_sonarr = []
    episodes_to_update = []
    episodes_to_add = []

    # Get episodes data for a series from Sonarr
    episodes = get_episodes_from_sonarr_api(apikey_sonarr=apikey_sonarr, series_id=series_id)
    if episodes:
        # For Sonarr v3, we need to update episodes to integrate the episodeFile API endpoint results
        if not get_sonarr_info.is_legacy():
            episodeFiles = get_episodesFiles_from_sonarr_api(apikey_sonarr=apikey_sonarr, series_id=series_id)
            for episode in episodes:
                if episodeFiles and episode['hasFile']:
                    item = [x for x in episodeFiles if x['id'] == episode['episodeFileId']]
                    if item:
                        episode['episodeFile'] = item[0]

        sync_monitored = settings.sonarr.sync_only_monitored_series and settings.sonarr.sync_only_monitored_episodes
        if sync_monitored:
            episodes_monitored = get_episodes_monitored_table(series_id)
            skipped_count = 0

        for episode in episodes:
            if 'hasFile' in episode:
                if episode['hasFile'] is True:
                    if 'episodeFile' in episode:
                        # monitored_status_db = get_episodes_monitored_status(episode['episodeFileId'])
                        if sync_monitored:
                            try:
                                monitored_status_db = bool_map[episodes_monitored[episode['episodeFileId']]]
                            except KeyError:
                                monitored_status_db = None

                            if monitored_status_db is None:
                                # not in db, might need to add, if we have a file on disk
                                pass
                            elif monitored_status_db != episode['monitored']:
                                # monitored status changed and we don't know about it until now
                                trace(f"(Monitor Status Mismatch) {episode['title']}")
                                # pass
                            elif not episode['monitored']:
                                # Add unmonitored episode in sonarr to current episode list, otherwise it will be deleted from db
                                current_episodes_sonarr.append(episode['id'])
                                skipped_count += 1
                                continue

                        try:
                            bazarr_file_size = \
                                os.path.getsize(path_mappings.path_replace(episode['episodeFile']['path']))
                        except OSError:
                            bazarr_file_size = 0
                        if episode['episodeFile']['size'] > MINIMUM_VIDEO_SIZE or bazarr_file_size > MINIMUM_VIDEO_SIZE:
                            # Add episodes in sonarr to current episode list
                            current_episodes_sonarr.append(episode['id'])

                            # Parse episode data
                            if episode['id'] in current_episodes_id_db_list:
                                parsed_episode = episodeParser(episode)
                                if not any([parsed_episode.items() <= x for x in current_episodes_db_kv]):
                                    episodes_to_update.append(parsed_episode)
                            else:
                                episodes_to_add.append(episodeParser(episode))
    else:
        return

    if sync_monitored:
        # try to avoid unnecessary database calls
        if settings.general.debug:
            series_title = database.execute(select(TableShows.title).where(TableShows.sonarrSeriesId == series_id)).first()[0]
            trace(f"Skipped {skipped_count} unmonitored episodes out of {len(episodes)} for {series_title}")

    # Remove old episodes from DB
    episodes_to_delete = list(set(current_episodes_id_db_list) - set(current_episodes_sonarr))

    if len(episodes_to_delete):
        try:
            database.execute(delete(TableEpisodes).where(TableEpisodes.sonarrEpisodeId.in_(episodes_to_delete)))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot delete episodes because of {e}")
        else:
            for removed_episode in episodes_to_delete:
                if send_event:
                    event_stream(type='episode', action='delete', payload=removed_episode)

    # Insert new episodes in DB
    if len(episodes_to_add):
        for added_episode in episodes_to_add:
            try:
                added_episode['created_at_timestamp'] = datetime.now()
                database.execute(insert(TableEpisodes).values(added_episode))
            except IntegrityError as e:
                logging.error(f"BAZARR cannot insert episodes because of {e}. We'll try to update it instead.")
                del added_episode['created_at_timestamp']
                episodes_to_update.append(added_episode)
            else:
                store_subtitles(added_episode['path'], path_mappings.path_replace(added_episode['path']))

                if send_event:
                    event_stream(type='episode', payload=added_episode['sonarrEpisodeId'])

    # Update existing episodes in DB
    if len(episodes_to_update):
        for updated_episode in episodes_to_update:
            try:
                updated_episode['updated_at_timestamp'] = datetime.now()
                database.execute(update(TableEpisodes)
                                 .values(updated_episode)
                                 .where(TableEpisodes.sonarrEpisodeId == updated_episode['sonarrEpisodeId']))
            except IntegrityError as e:
                logging.error(f"BAZARR cannot update episodes because of {e}")
            else:
                store_subtitles(updated_episode['path'], path_mappings.path_replace(updated_episode['path']))

                if send_event:
                    event_stream(type='episode', action='update', payload=updated_episode['sonarrEpisodeId'])

    # Downloading missing subtitles
    for episode in episodes_to_add + episodes_to_update:
        episode_id = episode['sonarrEpisodeId']
        if defer_search:
            logging.debug(
                f'BAZARR searching for missing subtitles is deferred until scheduled task execution for this episode: '
                f'{path_mappings.path_replace(episode["path"])}')
        else:
            mapped_episode_path = path_mappings.path_replace(episode["path"])
            if os.path.exists(mapped_episode_path):
                logging.debug(f'BAZARR downloading missing subtitles for this episode: {mapped_episode_path}')
                episode_download_subtitles(episode_id, send_progress=True)
            else:
                logging.debug(
                    f'BAZARR cannot find this file yet (Sonarr may be slow to import episode between disks?). '
                    f'Searching for missing subtitles is deferred until scheduled task execution for this episode'
                    f': {mapped_episode_path}')

    logging.debug(f'BAZARR All episodes from series ID {series_id} synced from Sonarr into database.')


def sync_one_episode(episode_id, defer_search=False):
    logging.debug(f'BAZARR syncing this specific episode from Sonarr: {episode_id}')
    apikey_sonarr = settings.sonarr.apikey

    # Check if there's a row in database for this episode ID
    existing_episode = database.execute(
        select(TableEpisodes.path, TableEpisodes.episode_file_id)
        .where(TableEpisodes.sonarrEpisodeId == episode_id)) \
        .first()

    try:
        # Get episode data from sonarr api
        episode = None
        episode_data = get_episodes_from_sonarr_api(apikey_sonarr=apikey_sonarr, episode_id=episode_id)
        if not episode_data:
            return

        else:
            # For Sonarr v3, we need to update episodes to integrate the episodeFile API endpoint results
            if not get_sonarr_info.is_legacy() and existing_episode and episode_data['hasFile']:
                episode_data['episodeFile'] = \
                    get_episodesFiles_from_sonarr_api(apikey_sonarr=apikey_sonarr,
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
            database.execute(
                delete(TableEpisodes)
                .where(TableEpisodes.sonarrEpisodeId == episode_id))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot delete episode {existing_episode.path} because of {e}")
        else:
            event_stream(type='episode', action='delete', payload=int(episode_id))
            logging.debug(
                f'BAZARR deleted this episode from the database:{path_mappings.path_replace(existing_episode["path"])}')
        return

    # Update existing episodes in DB
    elif episode and existing_episode:
        try:
            episode['updated_at_timestamp'] = datetime.now()
            database.execute(
                update(TableEpisodes)
                .values(episode)
                .where(TableEpisodes.sonarrEpisodeId == episode_id))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot update episode {episode['path']} because of {e}")
        else:
            store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))
            event_stream(type='episode', action='update', payload=int(episode_id))
            logging.debug(
                f'BAZARR updated this episode into the database:{path_mappings.path_replace(episode["path"])}')

    # Insert new episodes in DB
    elif episode and not existing_episode:
        try:
            episode['created_at_timestamp'] = datetime.now()
            database.execute(
                insert(TableEpisodes)
                .values(episode))
        except IntegrityError as e:
            logging.error(f"BAZARR cannot insert episode {episode['path']} because of {e}")
        else:
            store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))
            event_stream(type='episode', action='update', payload=int(episode_id))
            logging.debug(
                f'BAZARR inserted this episode into the database:{path_mappings.path_replace(episode["path"])}')

    # Downloading missing subtitles
    if defer_search:
        logging.debug(
            f'BAZARR searching for missing subtitles is deferred until scheduled task execution for this episode: '
            f'{path_mappings.path_replace(episode["path"])}')
    else:
        mapped_episode_path = path_mappings.path_replace(episode["path"])
        if os.path.exists(mapped_episode_path):
            logging.debug(f'BAZARR downloading missing subtitles for this episode: {mapped_episode_path}')
            episode_download_subtitles(episode_id, send_progress=True)
        else:
            logging.debug(f'BAZARR cannot find this file yet (Sonarr may be slow to import episode between disks?). '
                          f'Searching for missing subtitles is deferred until scheduled task execution for this episode'
                          f': {mapped_episode_path}')

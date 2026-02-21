# coding=utf-8

import os
import logging
import operator
import semver

from sqlalchemy.exc import IntegrityError
from datetime import datetime
from functools import reduce

from constants import MINIMUM_VIDEO_SIZE
from app.database import database, TableShows, TableEpisodes, delete, update, insert, select, get_exclusion_clause
from app.config import settings
from utilities.path_mappings import path_mappings
from subtitles.indexer.series import store_subtitles, series_full_scan_subtitles
from subtitles.mass_download import episode_download_subtitles
from app.event_handler import event_stream
from sonarr.info import get_sonarr_info
from app.jobs_queue import jobs_queue
from subtitles.adaptive_searching import is_search_active

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


def check_actual_file_size(original_episode_path):
    try:
        bazarr_file_size = \
            os.path.getsize(path_mappings.path_replace(original_episode_path))
    except OSError:
        bazarr_file_size = 0

    return bazarr_file_size > MINIMUM_VIDEO_SIZE


def sync_episodes(series_id, defer_search=False, is_signalr=False):
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
        current_episodes_in_db_row_as_dict = {row[0].sonarrEpisodeId: row[0].to_dict() for row in
                                              database.execute(
                                                  select(TableEpisodes)
                                                  .where(TableEpisodes.sonarrSeriesId == series_id))
                                              .all()}
    else:
        return

    current_episodes_sonarr = []
    episodes_to_update = []
    episodes_to_add = []

    # Get episodes data for a series from Sonarr
    episodes = get_episodes_from_sonarr_api(apikey_sonarr=apikey_sonarr, series_id=series_id)
    if episodes:
        if get_sonarr_info.is_legacy():
            # We skip this for legacy versions of Sonarr since it already have episodeFile structure included
            pass
        elif get_sonarr_info.semver() >= semver.Version(*(4, 0, 9, 2421)):
            # We skip this if the episodes already contain an episodeFile structure (added with Sonarr v4.0.9.2421)
            pass
        else:
            # For Sonarr v3 or greater but lower than 4.0.9.2421, we need to update episodes to integrate the
            # episodeFile API endpoint results
            episodeFiles = get_episodesFiles_from_sonarr_api(apikey_sonarr=apikey_sonarr, series_id=series_id)
            if episodeFiles:
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
            if 'hasFile' in episode and episode['hasFile'] and 'episodeFile' in episode:
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

                if (episode['episodeFile']['size'] > MINIMUM_VIDEO_SIZE or
                        check_actual_file_size(episode['episodeFile']['path']) or
                        (settings.general.enable_strm_support and episode['episodeFile']['path'].lower().endswith('.strm'))):
                    # Add episodes in sonarr to current episode list
                    current_episodes_sonarr.append(episode['id'])

                    # Parse episode data
                    if episode['id'] in current_episodes_in_db_row_as_dict:
                        parsed_episode = episodeParser(episode)
                        if not set(parsed_episode.items()).issubset(set(current_episodes_in_db_row_as_dict[episode['id']].items())):
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
                event_stream(type='episode', action='update', payload=updated_episode['sonarrEpisodeId'])

    # Downloading missing subtitles
    series_data = database.execute(
        select(TableShows.title,
               TableShows.year,
               TableShows.path)
        .where(TableShows.sonarrSeriesId == series_id)
    ).first()
    if not series_data:
        pass
    else:
        if defer_search:
            logging.debug(
                f'BAZARR searching for missing subtitles is deferred until scheduled task execution for this series: '
                f'{series_data.title} ({series_data.year})')
        else:
            for episode in episodes_to_update + episodes_to_add:
                episode_title = (f'{series_data.title} - S{episode["season"]:02d}E{episode["episode"]:02d} '
                                 f'- {episode["title"]}')
                if _is_there_missing_subtitles(episode_id=episode['sonarrEpisodeId']):
                    if os.path.exists(path_mappings.path_replace(episode['path'])):
                        logging.debug(f'BAZARR downloading missing subtitles for this episode: {episode_title}')
                        jobs_queue.feed_jobs_pending_queue(job_name=f'Downloading missing subtitles for '
                                                                    f'{episode_title}',
                                                           module='subtitles.mass_download.series',
                                                           func='episode_download_subtitles',
                                                           args=[],
                                                           kwargs={'no': episode['sonarrEpisodeId']},
                                                           is_signalr=is_signalr)
                    else:
                        logging.debug(f'BAZARR cannot find this episode file yet (Sonarr may be slow to import episode '
                                      f'between disks?). Searching for missing subtitles is deferred until scheduled '
                                      f'task execution for this episode: {episode_title}')
                else:
                    logging.debug(f'BAZARR no missing subtitles for this episode: {episode_title}')

    logging.debug(f'BAZARR All episodes from series ID {series_id} synced from Sonarr into database.')


def sync_one_episode(episode_id, defer_search=False, is_signalr=False):
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
                f'BAZARR deleted this episode from the database:{path_mappings.path_replace(existing_episode.path)}')
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
        series_title = database.execute(
            select(TableShows.title)
            .where(TableShows.sonarrSeriesId == episode["sonarrSeriesId"])
        ).first()[0]
        episode_full_title = (f'{series_title} - S{episode["season"]:02d}E{episode["episode"]:02d} - '
                              f'{episode["title"]}')

        if os.path.exists(path_mappings.path_replace(episode["path"])):
            logging.debug(f'BAZARR downloading missing subtitles for this episode: {episode_full_title}')
            if _is_there_missing_subtitles(episode_id=episode_id):
                jobs_queue.feed_jobs_pending_queue(job_name=f'Downloading missing subtitles for {series_title}',
                                                   module='subtitles.mass_download.series',
                                                   func='episode_download_subtitles',
                                                   args=[],
                                                   kwargs={'no': episode_id},
                                                   is_signalr=is_signalr)
            else:
                logging.debug(f'BAZARR no missing subtitles for this episode: {episode_full_title}')
        else:
            logging.debug(f'BAZARR cannot find this file yet (Sonarr may be slow to import episode between disks?). '
                          f'Searching for missing subtitles is deferred until scheduled task execution for this episode'
                          f': {episode_full_title}')


def _is_there_missing_subtitles(series_id: int = None, episode_id: int = None) -> bool:
    """
    Determines whether there are missing subtitles for a given series or episode.

    This function checks if there are missing subtitles based on the given
    series ID or episode ID. If both `series_id` and `episode_id` are provided,
    or if neither is provided, the function returns False. Otherwise, it evaluates
    the specified conditions to determine if subtitles are missing for the
    requested series or episode.

    :param series_id: The ID of the series to check for missing subtitles.
        Optional, defaults to None.
    :param episode_id: The ID of the episode to check for missing subtitles.
        Optional, defaults to None.
    :return: Boolean indicating whether there are missing subtitles (`True`)
        or not (`False`).
    :rtype: bool
    """
    episodes_conditions = [(TableEpisodes.missing_subtitles.is_not(None)),
                           (TableEpisodes.missing_subtitles != '[]')]
    if all([series_id, episode_id]) or not any([series_id, episode_id]):
        return False
    elif series_id:
        episodes_conditions.append(TableEpisodes.sonarrSeriesId == series_id)
    elif episode_id:
        episodes_conditions.append(TableEpisodes.sonarrEpisodeId == episode_id)
    episodes_conditions += get_exclusion_clause('series')
    missing_episodes = database.execute(
        select(TableEpisodes.missing_subtitles, TableEpisodes.failedAttempts)
        .select_from(TableEpisodes)
        .join(TableShows)
        .where(reduce(operator.and_, episodes_conditions))) \
        .all()
    for missing_episode in missing_episodes:
        for language in missing_episode.missing_subtitles:
            if is_search_active(desired_language=language, attempt_string=missing_episode.failedAttempts):
                return True
    return False

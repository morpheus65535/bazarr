# coding=utf-8

import logging

from app.database import TableEpisodes
from app.event_handler import event_stream, hide_progress
from sonarr.info import get_sonarr_info, url_sonarr
from subtitles.indexer.series import store_subtitles, series_full_scan_subtitles
from subtitles.mass_download import episode_download_subtitles
from utilities.path_mappings import path_mappings
from .parser import episodeParser
from .utils import get_episodes_from_sonarr_api, get_episodes_files_from_sonarr_api


def update_all_episodes():
    series_full_scan_subtitles()
    logging.info('BAZARR All existing episode subtitles indexed from disk.')


def sync_episodes(serie_id: int = None) -> None:
    logging.debug(f'BAZARR Starting episodes sync for serie_id={serie_id}.')

    # Get current episodes id in DB
    current_episodes_db = TableEpisodes.select(TableEpisodes.sonarrEpisodeId) \
        .where((TableEpisodes.sonarrSeriesId == serie_id) if serie_id else None) \
        .dicts()

    current_episodes_db_list = [x['sonarrEpisodeId'] for x in current_episodes_db]

    current_episodes_sonarr = []

    # Get episodes data for a series from Sonarr
    episodes = get_episodes_from_sonarr_api(series_id=serie_id)
    if not episodes:
        return
    # For Sonarr v3, we need to update episodes to integrate the episodeFile API endpoint results
    if not get_sonarr_info.is_legacy():
        episodeFiles = get_episodes_files_from_sonarr_api(series_id=serie_id)
        for episode in episodes:
            if episode['hasFile']:
                item = [x for x in episodeFiles if x['id'] == episode['episodeFileId']]
                if item:
                    episode['episodeFile'] = item[0]
    episodes_to_update = []
    for episode in episodes:
        parsed_episode = episodeParser(episode)
        if parsed_episode:
            # Add episodes in sonarr to current episode list
            current_episodes_sonarr.append(episode['id'])
            # Parse episode data
            if episode['id'] in current_episodes_db_list:
                episodes_to_update.append(parsed_episode)
            else:
                add_episode(parsed_episode, send_event=False)

    if episodes_to_update:
        update_episode(episodes_to_update)


    # Remove old episodes from DB
    removed_episodes = list(set(current_episodes_db_list) - set(current_episodes_sonarr))
    remove_old_episodes(removed_episodes)

    logging.debug('BAZARR All episodes synced from Sonarr into database.')


def sync_one_episode(episode_id, defer_search=False):
    logging.debug(
        f'BAZARR syncing this specific episode from Sonarr: {episode_id}'
    )

    try:
        # Get episode data from sonarr api
        episode_data = get_episodes_from_sonarr_api(episode_id=episode_id)
        if not episode_data:
            return

        # For Sonarr v3, we need to update episodes to integrate the episodeFile API endpoint results
        if not get_sonarr_info.is_legacy() and episode_data['hasFile']:
            episode_data['episodeFile'] = \
                get_episodes_files_from_sonarr_api(episode_file_id=episode_data['episodeFileId'])
        episode = episodeParser(episode_data)
    except Exception:
        logging.exception('BAZARR cannot get episode returned by SignalR feed from Sonarr API.')
        raise

    # Remove episode from DB
    if not episode:
        remove_old_episodes([episode_id])
        logging.debug(f'BAZARR deleted this episode from the database:{episode_id}')
        return

    add_episode(episode)

    # Storing existing subtitles
    logging.debug(
        f"BAZARR storing subtitles for this episode: {path_mappings.path_replace(episode['path'])}"
    )
    store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))

    # Downloading missing subtitles
    if defer_search:
        logging.debug(
            f"BAZARR searching for missing subtitles is deferred until scheduled task execution for this episode: {path_mappings.path_replace(episode['path'])}"
        )
    else:
        logging.debug(
            f"BAZARR downloading missing subtitles for this episode: {path_mappings.path_replace(episode['path'])}"
        )
        episode_download_subtitles(episode_id)


def remove_old_episodes(removed_episodes):
    logging.debug('BAZARR removing old episodes from database.')
    for episode in removed_episodes:
        try:
            TableEpisodes.delete().where(TableEpisodes.sonarrEpisodeId == episode).execute()
        except Exception as e:
            logging.exception(f"BAZARR cannot delete episode {episode} because of {e}")
        else:
            event_stream(type='episode', action='delete', payload=int(episode))
            logging.debug(f'BAZARR deleted this episode from the database:{episode}')
    return


def update_episode(episodes_to_update):
    list_of_episodes_ids = [x['sonarrEpisodeId'] for x in episodes_to_update]
    episodes_in_db = TableEpisodes.select(TableEpisodes.sonarrSeriesId,
                                          TableEpisodes.sonarrEpisodeId,
                                          TableEpisodes.title,
                                          TableEpisodes.path,
                                          TableEpisodes.season,
                                          TableEpisodes.episode,
                                          TableEpisodes.sceneName,
                                          TableEpisodes.monitored,
                                          TableEpisodes.format,
                                          TableEpisodes.resolution,
                                          TableEpisodes.video_codec,
                                          TableEpisodes.audio_codec,
                                          TableEpisodes.episode_file_id,
                                          TableEpisodes.audio_language,
                                          TableEpisodes.file_size).where(
        TableEpisodes.sonarrEpisodeId.in_(list_of_episodes_ids)).dicts()
    episode_in_db_list = list(episodes_in_db)
    episodes_to_update_list = [i for i in episodes_to_update if i not in episode_in_db_list]
    for episode in episodes_to_update_list:
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
        TableEpisodes.insert(episode).on_conflict_replace().execute()
    except Exception as e:
        logging.exception(f"BAZARR cannot insert episode {episode['path']} because of {e}")
    else:
        store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))
        if send_event:
            event_stream(type='episode', payload=episode['sonarrEpisodeId'])
        logging.debug(f'BAZARR inserted this episode into the database:{episode["path"]}')
    return

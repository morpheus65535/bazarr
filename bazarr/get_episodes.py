# coding=utf-8

import os
import requests
import logging
from gevent import sleep
from peewee import DoesNotExist

from database import get_exclusion_clause, TableEpisodes, TableShows
from config import settings, url_sonarr
from helper import path_mappings
from list_subtitles import store_subtitles, series_full_scan_subtitles
from get_subtitle import episode_download_subtitles
from event_handler import event_stream, show_progress, hide_progress
from utils import get_sonarr_info

headers = {"User-Agent": os.environ["SZ_USER_AGENT"]}


def update_all_episodes():
    series_full_scan_subtitles()
    logging.info('BAZARR All existing episode subtitles indexed from disk.')


def sync_episodes(series_id=None, send_event=True):
    logging.debug('BAZARR Starting episodes sync from Sonarr.')
    apikey_sonarr = settings.sonarr.apikey

    # Get current episodes id in DB
    current_episodes_db = TableEpisodes.select(TableEpisodes.sonarrEpisodeId,
                                               TableEpisodes.path,
                                               TableEpisodes.sonarrSeriesId)\
        .where((TableEpisodes.sonarrSeriesId == series_id) if series_id else None)\
        .dicts()

    current_episodes_db_list = [x['sonarrEpisodeId'] for x in current_episodes_db]

    current_episodes_sonarr = []
    episodes_to_update = []
    episodes_to_add = []
    altered_episodes = []

    # Get sonarrId for each series from database
    seriesIdList = get_series_from_sonarr_api(series_id=series_id, url=url_sonarr(), apikey_sonarr=apikey_sonarr,)

    series_count = len(seriesIdList)
    for i, seriesId in enumerate(seriesIdList):
        sleep()
        if send_event:
            show_progress(id='episodes_progress',
                          header='Syncing episodes...',
                          name=seriesId['title'],
                          value=i,
                          count=series_count)

        # Get episodes data for a series from Sonarr
        episodes = get_episodes_from_sonarr_api(url=url_sonarr(), apikey_sonarr=apikey_sonarr,
                                                series_id=seriesId['sonarrSeriesId'])
        if not episodes:
            continue
        else:
            # For Sonarr v3, we need to update episodes to integrate the episodeFile API endpoint results
            if not get_sonarr_info.is_legacy():
                episodeFiles = get_episodesFiles_from_sonarr_api(url=url_sonarr(), apikey_sonarr=apikey_sonarr,
                                                                 series_id=seriesId['sonarrSeriesId'])
                for episode in episodes:
                    if episode['hasFile']:
                        item = [x for x in episodeFiles if x['id'] == episode['episodeFileId']]
                        if item:
                            episode['episodeFile'] = item[0]

            for episode in episodes:
                sleep()
                if 'hasFile' in episode:
                    if episode['hasFile'] is True:
                        if 'episodeFile' in episode:
                            if episode['episodeFile']['size'] > 20480:
                                # Add episodes in sonarr to current episode list
                                current_episodes_sonarr.append(episode['id'])

                                # Parse episode data
                                if episode['id'] in current_episodes_db_list:
                                    episodes_to_update.append(episodeParser(episode))
                                else:
                                    episodes_to_add.append(episodeParser(episode))

    if send_event:
        hide_progress(id='episodes_progress')

    # Remove old episodes from DB
    removed_episodes = list(set(current_episodes_db_list) - set(current_episodes_sonarr))

    for removed_episode in removed_episodes:
        sleep()
        episode_to_delete = TableEpisodes.select(TableEpisodes.sonarrSeriesId, TableEpisodes.sonarrEpisodeId)\
            .where(TableEpisodes.sonarrEpisodeId == removed_episode)\
            .dicts()\
            .get()
        TableEpisodes.delete().where(TableEpisodes.sonarrEpisodeId == removed_episode).execute()
        if send_event:
            event_stream(type='episode', action='delete', payload=episode_to_delete['sonarrEpisodeId'])

    # Update existing episodes in DB
    episode_in_db_list = []
    episodes_in_db = TableEpisodes.select(TableEpisodes.sonarrSeriesId,
                                          TableEpisodes.sonarrEpisodeId,
                                          TableEpisodes.title,
                                          TableEpisodes.path,
                                          TableEpisodes.season,
                                          TableEpisodes.episode,
                                          TableEpisodes.scene_name,
                                          TableEpisodes.monitored,
                                          TableEpisodes.format,
                                          TableEpisodes.resolution,
                                          TableEpisodes.video_codec,
                                          TableEpisodes.audio_codec,
                                          TableEpisodes.episode_file_id,
                                          TableEpisodes.audio_language,
                                          TableEpisodes.file_size).dicts()

    for item in episodes_in_db:
        episode_in_db_list.append(item)

    episodes_to_update_list = [i for i in episodes_to_update if i not in episode_in_db_list]

    for updated_episode in episodes_to_update_list:
        sleep()
        TableEpisodes.update(updated_episode).where(TableEpisodes.sonarrEpisodeId ==
                                                    updated_episode['sonarrEpisodeId']).execute()
        altered_episodes.append([updated_episode['sonarrEpisodeId'],
                                 updated_episode['path'],
                                 updated_episode['sonarrSeriesId']])

    # Insert new episodes in DB
    for added_episode in episodes_to_add:
        sleep()
        result = TableEpisodes.insert(added_episode).on_conflict(action='IGNORE').execute()
        if result > 0:
            altered_episodes.append([added_episode['sonarrEpisodeId'],
                                     added_episode['path'],
                                     added_episode['monitored']])
            if send_event:
                event_stream(type='episode', payload=added_episode['sonarrEpisodeId'])
        else:
            logging.debug('BAZARR unable to insert this episode into the database:{}'.format(
                path_mappings.path_replace(added_episode['path'])))

    # Store subtitles for added or modified episodes
    for i, altered_episode in enumerate(altered_episodes, 1):
        sleep()
        store_subtitles(altered_episode[1], path_mappings.path_replace(altered_episode[1]))

    logging.debug('BAZARR All episodes synced from Sonarr into database.')


def sync_one_episode(episode_id):
    logging.debug('BAZARR syncing this specific episode from Sonarr: {}'.format(episode_id))
    url = url_sonarr()
    apikey_sonarr = settings.sonarr.apikey

    # Check if there's a row in database for this episode ID
    try:
        existing_episode = TableEpisodes.select(TableEpisodes.path, TableEpisodes.episode_file_id)\
            .where(TableEpisodes.sonarrEpisodeId == episode_id)\
            .dicts()\
            .get()
    except DoesNotExist:
        existing_episode = None

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
                                                      episode_file_id=existing_episode['episode_file_id'])
            episode = episodeParser(episode_data)
    except Exception:
        logging.debug('BAZARR cannot get episode returned by SignalR feed from Sonarr API.')
        return

    # Drop useless events
    if not episode and not existing_episode:
        return

    # Remove episode from DB
    if not episode and existing_episode:
        TableEpisodes.delete().where(TableEpisodes.sonarrEpisodeId == episode_id).execute()
        event_stream(type='episode', action='delete', payload=int(episode_id))
        logging.debug('BAZARR deleted this episode from the database:{}'.format(path_mappings.path_replace(
            existing_episode['path'])))
        return

    # Update existing episodes in DB
    elif episode and existing_episode:
        TableEpisodes.update(episode).where(TableEpisodes.sonarrEpisodeId == episode_id).execute()
        event_stream(type='episode', action='update', payload=int(episode_id))
        logging.debug('BAZARR updated this episode into the database:{}'.format(path_mappings.path_replace(
            episode['path'])))

    # Insert new episodes in DB
    elif episode and not existing_episode:
        TableEpisodes.insert(episode).on_conflict(action='IGNORE').execute()
        event_stream(type='episode', action='update', payload=int(episode_id))
        logging.debug('BAZARR inserted this episode into the database:{}'.format(path_mappings.path_replace(
            episode['path'])))

    # Storing existing subtitles
    logging.debug('BAZARR storing subtitles for this episode: {}'.format(path_mappings.path_replace(
            episode['path'])))
    store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))

    # Downloading missing subtitles
    logging.debug('BAZARR downloading missing subtitles for this episode: {}'.format(path_mappings.path_replace(
        episode['path'])))
    episode_download_subtitles(episode_id)


def SonarrFormatAudioCodec(audio_codec):
    if audio_codec == 'AC-3':
        return 'AC3'
    if audio_codec == 'E-AC-3':
        return 'EAC3'
    if audio_codec == 'MPEG Audio':
        return 'MP3'

    return audio_codec


def SonarrFormatVideoCodec(video_codec):
    if video_codec == 'x264' or video_codec == 'AVC':
        return 'h264'
    elif video_codec == 'x265' or video_codec == 'HEVC':
        return 'h265'
    elif video_codec.startswith('XviD'):
        return 'XviD'
    elif video_codec.startswith('DivX'):
        return 'DivX'
    elif video_codec == 'MPEG-1 Video':
        return 'Mpeg'
    elif video_codec == 'MPEG-2 Video':
        return 'Mpeg2'
    elif video_codec == 'MPEG-4 Video':
        return 'Mpeg4'
    elif video_codec == 'VC-1':
        return 'VC1'
    elif video_codec.endswith('VP6'):
        return 'VP6'
    elif video_codec.endswith('VP7'):
        return 'VP7'
    elif video_codec.endswith('VP8'):
        return 'VP8'
    elif video_codec.endswith('VP9'):
        return 'VP9'
    else:
        return video_codec


def episodeParser(episode):
    if 'hasFile' in episode:
        if episode['hasFile'] is True:
            if 'episodeFile' in episode:
                if episode['episodeFile']['size'] > 20480:
                    if 'sceneName' in episode['episodeFile']:
                        sceneName = episode['episodeFile']['sceneName']
                    else:
                        sceneName = None

                    audio_language = []
                    if 'language' in episode['episodeFile'] and len(episode['episodeFile']['language']):
                        item = episode['episodeFile']['language']
                        if isinstance(item, dict):
                            if 'name' in item:
                                audio_language.append(item['name'])
                    else:
                        audio_language = TableShows.get(TableShows.sonarrSeriesId == episode['seriesId']).audio_language

                    if 'mediaInfo' in episode['episodeFile']:
                        if 'videoCodec' in episode['episodeFile']['mediaInfo']:
                            videoCodec = episode['episodeFile']['mediaInfo']['videoCodec']
                            videoCodec = SonarrFormatVideoCodec(videoCodec)
                        else:
                            videoCodec = None

                        if 'audioCodec' in episode['episodeFile']['mediaInfo']:
                            audioCodec = episode['episodeFile']['mediaInfo']['audioCodec']
                            audioCodec = SonarrFormatAudioCodec(audioCodec)
                        else:
                            audioCodec = None
                    else:
                        videoCodec = None
                        audioCodec = None

                    try:
                        video_format, video_resolution = episode['episodeFile']['quality']['quality']['name'].split('-')
                    except Exception:
                        video_format = episode['episodeFile']['quality']['quality']['name']
                        try:
                            video_resolution = str(episode['episodeFile']['quality']['quality']['resolution']) + 'p'
                        except Exception:
                            video_resolution = None

                    return {'sonarrSeriesId': episode['seriesId'],
                            'sonarrEpisodeId': episode['id'],
                            'title': episode['title'],
                            'path': episode['episodeFile']['path'],
                            'season': episode['seasonNumber'],
                            'episode': episode['episodeNumber'],
                            'scene_name': sceneName,
                            'monitored': str(bool(episode['monitored'])),
                            'format': video_format,
                            'resolution': video_resolution,
                            'video_codec': videoCodec,
                            'audio_codec': audioCodec,
                            'episode_file_id': episode['episodeFile']['id'],
                            'audio_language': str(audio_language),
                            'file_size': episode['episodeFile']['size']}


def get_series_from_sonarr_api(series_id, url, apikey_sonarr):
    if series_id:
        url_sonarr_api_series = url + "/api/{0}series/{1}?apikey={2}".format(
            '' if get_sonarr_info.is_legacy() else 'v3/', series_id, apikey_sonarr)
    else:
        url_sonarr_api_series = url + "/api/{0}series?apikey={1}".format(
            '' if get_sonarr_info.is_legacy() else 'v3/', apikey_sonarr)
    try:
        r = requests.get(url_sonarr_api_series, timeout=60, verify=False, headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code:
            raise requests.exceptions.HTTPError
        logging.exception("BAZARR Error trying to get series from Sonarr. Http error.")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get series from Sonarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get series from Sonarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get series from Sonarr.")
        return
    else:
        series_json = []
        if series_id:
            series_json.append(r.json())
        else:
            series_json = r.json()
        series_list = []
        for series in series_json:
            series_list.append({'sonarrSeriesId': series['id'], 'title': series['title']})
        return series_list


def get_episodes_from_sonarr_api(url, apikey_sonarr, series_id=None, episode_id=None):
    if series_id:
        url_sonarr_api_episode = url + "/api/{0}episode?seriesId={1}&apikey={2}".format(
            '' if get_sonarr_info.is_legacy() else 'v3/', series_id, apikey_sonarr)
    elif episode_id:
        url_sonarr_api_episode = url + "/api/{0}episode/{1}?apikey={2}".format(
            '' if get_sonarr_info.is_legacy() else 'v3/', episode_id, apikey_sonarr)
    else:
        return

    try:
        r = requests.get(url_sonarr_api_episode, timeout=60, verify=False, headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        logging.exception("BAZARR Error trying to get episodes from Sonarr. Http error.")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get episodes from Sonarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get episodes from Sonarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get episodes from Sonarr.")
        return
    else:
        return r.json()


def get_episodesFiles_from_sonarr_api(url, apikey_sonarr, series_id=None, episode_file_id=None):
    if series_id:
        url_sonarr_api_episodeFiles = url + "/api/v3/episodeFile?seriesId={0}&apikey={1}".format(series_id,
                                                                                                 apikey_sonarr)
    elif episode_file_id:
        url_sonarr_api_episodeFiles = url + "/api/v3/episodeFile/{0}?apikey={1}".format(episode_file_id, apikey_sonarr)
    else:
        return

    try:
        r = requests.get(url_sonarr_api_episodeFiles, timeout=60, verify=False, headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        logging.exception("BAZARR Error trying to get episodeFiles from Sonarr. Http error.")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get episodeFiles from Sonarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get episodeFiles from Sonarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get episodeFiles from Sonarr.")
        return
    else:
        return r.json()

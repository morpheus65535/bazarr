# coding=utf-8

import os
import requests
import logging
from database import database, dict_converter, get_exclusion_clause

from config import settings, url_sonarr
from helper import path_mappings
from list_subtitles import store_subtitles, series_full_scan_subtitles
from get_subtitle import episode_download_subtitles
from event_handler import event_stream, show_progress, hide_progress

headers = {"User-Agent": os.environ["SZ_USER_AGENT"]}


def update_all_episodes():
    series_full_scan_subtitles()
    logging.info('BAZARR All existing episode subtitles indexed from disk.')


def sync_episodes(send_event=True):
    logging.debug('BAZARR Starting episodes sync from Sonarr.')
    apikey_sonarr = settings.sonarr.apikey
    
    # Get current episodes id in DB
    current_episodes_db = database.execute("SELECT sonarrEpisodeId, path, sonarrSeriesId FROM table_episodes")

    current_episodes_db_list = [x['sonarrEpisodeId'] for x in current_episodes_db]

    current_episodes_sonarr = []
    episodes_to_update = []
    episodes_to_add = []
    altered_episodes = []
    
    # Get sonarrId for each series from database
    seriesIdList = get_series_from_sonarr_api(url=url_sonarr(), apikey_sonarr=apikey_sonarr)

    series_count = len(seriesIdList)
    for i, seriesId in enumerate(seriesIdList, 1):
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
            for episode in episodes:
                if 'hasFile' in episode:
                    if episode['hasFile'] is True:
                        if 'episodeFile' in episode:
                            if episode['episodeFile']['size'] > 20480:
                                # Add episodes in sonarr to current episode list
                                current_episodes_sonarr.append(episode['id'])

                                # Parse episdoe data
                                if episode['id'] in current_episodes_db_list:
                                    episodes_to_update.append(episodeParser(episode))
                                else:
                                    episodes_to_add.append(episodeParser(episode))

    show_progress(id='episodes_progress',
                  header='Syncing episodes...',
                  name='Completed successfully',
                  value=series_count,
                  count=series_count)

    hide_progress(id='episodes_progress')

    # Remove old episodes from DB
    removed_episodes = list(set(current_episodes_db_list) - set(current_episodes_sonarr))

    for removed_episode in removed_episodes:
        episode_to_delete = database.execute("SELECT sonarrSeriesId, sonarrEpisodeId FROM table_episodes WHERE "
                                             "sonarrEpisodeId=?", (removed_episode,), only_one=True)
        database.execute("DELETE FROM table_episodes WHERE sonarrEpisodeId=?", (removed_episode,))
        event_stream(type='episode', action='delete', payload=episode_to_delete['sonarrEpisodeId'])

    # Update existing episodes in DB
    episode_in_db_list = []
    episodes_in_db = database.execute("SELECT sonarrSeriesId, sonarrEpisodeId, title, path, season, episode, "
                                      "scene_name, monitored, format, resolution, video_codec, audio_codec, "
                                      "episode_file_id, audio_language, file_size FROM table_episodes")

    for item in episodes_in_db:
        episode_in_db_list.append(item)

    episodes_to_update_list = [i for i in episodes_to_update if i not in episode_in_db_list]

    for updated_episode in episodes_to_update_list:
        query = dict_converter.convert(updated_episode)
        database.execute('''UPDATE table_episodes SET ''' + query.keys_update + ''' WHERE sonarrEpisodeId = ?''',
                         query.values + (updated_episode['sonarrEpisodeId'],))
        altered_episodes.append([updated_episode['sonarrEpisodeId'],
                                 updated_episode['path'],
                                 updated_episode['sonarrSeriesId']])

    # Insert new episodes in DB
    for added_episode in episodes_to_add:
        query = dict_converter.convert(added_episode)
        result = database.execute(
            '''INSERT OR IGNORE INTO table_episodes(''' + query.keys_insert + ''') VALUES(''' + query.question_marks +
            ''')''', query.values)
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
        store_subtitles(altered_episode[1], path_mappings.path_replace(altered_episode[1]))

    logging.debug('BAZARR All episodes synced from Sonarr into database.')


def sync_one_episode(episode_id):
    logging.debug('BAZARR syncing this specific episode from Sonarr: {}'.format(episode_id))

    # Check if there's a row in database for this episode ID
    existing_episode = database.execute('SELECT path FROM table_episodes WHERE sonarrEpisodeId = ?', (episode_id,),
                                        only_one=True)

    try:
        # Get episode data from sonarr api
        episode = None
        episode_data = get_episodes_from_sonarr_api(url=url_sonarr(), apikey_sonarr=settings.sonarr.apikey,
                                                    episode_id=episode_id)
        if not episode_data:
            return
        else:
            episode = episodeParser(episode_data)
    except Exception:
        logging.debug('BAZARR cannot get episode returned by SignalR feed from Sonarr API.')
        return

    # Drop useless events
    if not episode and not existing_episode:
        return

    # Remove episode from DB
    if not episode and existing_episode:
        database.execute("DELETE FROM table_episodes WHERE sonarrEpisodeId=?", (episode_id,))
        event_stream(type='episode', action='delete', payload=int(episode_id))
        logging.debug('BAZARR deleted this episode from the database:{}'.format(path_mappings.path_replace(
            existing_episode['path'])))
        return

    # Update existing episodes in DB
    elif episode and existing_episode:
        query = dict_converter.convert(episode)
        database.execute('''UPDATE table_episodes SET ''' + query.keys_update + ''' WHERE sonarrEpisodeId = ?''',
                         query.values + (episode['sonarrEpisodeId'],))
        event_stream(type='episode', action='update', payload=int(episode_id))
        logging.debug('BAZARR updated this episode into the database:{}'.format(path_mappings.path_replace(
            episode['path'])))

    # Insert new episodes in DB
    elif episode and not existing_episode:
        query = dict_converter.convert(episode)
        database.execute('''INSERT OR IGNORE INTO table_episodes(''' + query.keys_insert + ''') VALUES(''' +
                         query.question_marks + ''')''', query.values)
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
                        audio_language = database.execute("SELECT audio_language FROM table_shows WHERE "
                                                          "sonarrSeriesId=?", (episode['seriesId'],),
                                                          only_one=True)['audio_language']

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
                    except:
                        video_format = episode['episodeFile']['quality']['quality']['name']
                        try:
                            video_resolution = str(episode['episodeFile']['quality']['quality']['resolution']) + 'p'
                        except:
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


def get_series_from_sonarr_api(url, apikey_sonarr):
    url_sonarr_api_series = url + "/api/series?apikey=" + apikey_sonarr
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
        series_list = []
        for series in r.json():
            series_list.append({'sonarrSeriesId': series['id'], 'title': series['title']})
        return series_list


def get_episodes_from_sonarr_api(url, apikey_sonarr, series_id=None, episode_id=None):
    if series_id:
        url_sonarr_api_episode = url + "/api/episode?seriesId={}&apikey=".format(series_id) + apikey_sonarr
    elif episode_id:
        url_sonarr_api_episode = url + "/api/episode/{}?apikey=".format(episode_id) + apikey_sonarr
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

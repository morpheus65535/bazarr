# coding=utf-8
import os
import requests
import logging
import re
from queueconfig import notifications
from database import database, dict_converter

from get_args import args
from config import settings, url_sonarr
from helper import path_replace
from list_subtitles import list_missing_subtitles, store_subtitles, series_full_scan_subtitles
from get_subtitle import episode_download_subtitles


def update_all_episodes():
    series_full_scan_subtitles()
    logging.info('BAZARR All existing episode subtitles indexed from disk.')


def sync_episodes():
    notifications.write(msg='Episodes sync from Sonarr started...', queue='get_episodes')
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
    seriesIdList = database.execute("SELECT sonarrSeriesId, title FROM table_shows")
    
    seriesIdListLength = len(seriesIdList)
    for i, seriesId in enumerate(seriesIdList, 1):
        notifications.write(msg='Getting episodes data from Sonarr...', queue='get_episodes', item=i, length=seriesIdListLength)
        # Get episodes data for a series from Sonarr
        url_sonarr_api_episode = url_sonarr() + "/api/episode?seriesId=" + str(seriesId['sonarrSeriesId']) + "&apikey=" + apikey_sonarr
        try:
            r = requests.get(url_sonarr_api_episode, timeout=60, verify=False)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logging.exception("BAZARR Error trying to get episodes from Sonarr. Http error.")
            return
        except requests.exceptions.ConnectionError as errc:
            logging.exception("BAZARR Error trying to get episodes from Sonarr. Connection Error.")
            return
        except requests.exceptions.Timeout as errt:
            logging.exception("BAZARR Error trying to get episodes from Sonarr. Timeout Error.")
            return
        except requests.exceptions.RequestException as err:
            logging.exception("BAZARR Error trying to get episodes from Sonarr.")
            return
        else:
            for episode in r.json():
                if 'hasFile' in episode:
                    if episode['hasFile'] is True:
                        if 'episodeFile' in episode:
                            if episode['episodeFile']['size'] > 20480:
                                # Add shows in Sonarr to current shows list
                                if 'sceneName' in episode['episodeFile']:
                                    sceneName = episode['episodeFile']['sceneName']
                                else:
                                    sceneName = None

                                try:
                                    format, resolution = episode['episodeFile']['quality']['quality']['name'].split('-')
                                except:
                                    format = episode['episodeFile']['quality']['quality']['name']
                                    try:
                                        resolution = str(episode['episodeFile']['quality']['quality']['resolution']) + 'p'
                                    except:
                                        resolution = None

                                if 'mediaInfo' in episode['episodeFile']:
                                    if 'videoCodec' in episode['episodeFile']['mediaInfo']:
                                        videoCodec = episode['episodeFile']['mediaInfo']['videoCodec']
                                        videoCodec = SonarrFormatVideoCodec(videoCodec)
                                    else: videoCodec = None

                                    if 'audioCodec' in episode['episodeFile']['mediaInfo']:
                                        audioCodec = episode['episodeFile']['mediaInfo']['audioCodec']
                                        audioCodec = SonarrFormatAudioCodec(audioCodec)
                                    else: audioCodec = None
                                else:
                                    videoCodec = None
                                    audioCodec = None

                                # Add episodes in sonarr to current episode list
                                current_episodes_sonarr.append(episode['id'])
                                
                                if episode['id'] in current_episodes_db_list:
                                    episodes_to_update.append({'sonarrSeriesId': episode['seriesId'],
                                                               'sonarrEpisodeId': episode['id'],
                                                               'title': episode['title'],
                                                               'path': episode['episodeFile']['path'],
                                                               'season': episode['seasonNumber'],
                                                               'episode': episode['episodeNumber'],
                                                               'scene_name': sceneName,
                                                               'monitored': str(bool(episode['monitored'])),
                                                               'format': format,
                                                               'resolution': resolution,
                                                               'video_codec': videoCodec,
                                                               'audio_codec': audioCodec,
                                                               'episode_file_id': episode['episodeFile']['id']})
                                else:
                                    episodes_to_add.append({'sonarrSeriesId': episode['seriesId'],
                                                            'sonarrEpisodeId': episode['id'],
                                                            'title': episode['title'],
                                                            'path': episode['episodeFile']['path'],
                                                            'season': episode['seasonNumber'],
                                                            'episode': episode['episodeNumber'],
                                                            'scene_name': sceneName,
                                                            'monitored': str(bool(episode['monitored'])),
                                                            'format': format,
                                                            'resolution': resolution,
                                                            'video_codec': videoCodec,
                                                            'audio_codec': audioCodec,
                                                            'episode_file_id': episode['episodeFile']['id']})

    # Remove old episodes from DB
    removed_episodes = list(set(current_episodes_db_list) - set(current_episodes_sonarr))

    for removed_episode in removed_episodes:
        database.execute("DELETE FROM table_episodes WHERE sonarrEpisodeId=?", (removed_episode,))

    # Update existing episodes in DB
    episode_in_db_list = []
    episodes_in_db = database.execute("SELECT sonarrSeriesId, sonarrEpisodeId, title, path, season, episode, "
                                      "scene_name, monitored, format, resolution, video_codec, audio_codec, "
                                      "episode_file_id FROM table_episodes")

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
            altered_episodes.append([added_episode['sonarrEpisodeId'], added_episode['path']])
        else:
            logging.debug('BAZARR unable to insert this episode into the database:',
                          path_replace(added_episode['path']))

    # Store subtitles for added or modified episodes
    for i, altered_episode in enumerate(altered_episodes, 1):
        notifications.write(msg='Indexing episodes embedded subtitles...', queue='get_episodes', item=i,
                            length=len(altered_episodes))
        store_subtitles(path_replace(altered_episode[1]))

    logging.debug('BAZARR All episodes synced from Sonarr into database.')

    # Search for desired subtitles if no more than 5 episodes have been added.
    if len(altered_episodes) <= 5:
        logging.debug("BAZARR No more than 5 episodes were added during this sync then we'll search for subtitles.")
        for altered_episode in altered_episodes:
            episode_download_subtitles(altered_episode[0])
    else:
        logging.debug("BAZARR More than 5 episodes were added during this sync then we wont search for subtitles right now.")


def SonarrFormatAudioCodec(audioCodec):
    if audioCodec == 'AC-3': return 'AC3'
    if audioCodec == 'E-AC-3': return 'EAC3'
    if audioCodec == 'MPEG Audio': return 'MP3'

    return audioCodec


def SonarrFormatVideoCodec(videoCodec):
    if videoCodec == 'x264' or videoCodec == 'AVC': return 'h264'
    if videoCodec == 'x265' or videoCodec == 'HEVC': return 'h265'
    if videoCodec.startswith('XviD'): return 'XviD'
    if videoCodec.startswith('DivX'): return 'DivX'
    if videoCodec == 'MPEG-1 Video': return 'Mpeg'
    if videoCodec == 'MPEG-2 Video': return 'Mpeg2'
    if videoCodec == 'MPEG-4 Video': return 'Mpeg4'
    if videoCodec == 'VC-1': return 'VC1'
    if videoCodec.endswith('VP6'): return 'VP6'
    if videoCodec.endswith('VP7'): return 'VP7'
    if videoCodec.endswith('VP8'): return 'VP8'
    if videoCodec.endswith('VP9'): return 'VP9'

    return videoCodec

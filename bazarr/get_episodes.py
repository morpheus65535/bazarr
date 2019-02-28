# coding=utf-8
import os
import sqlite3
import requests
import logging
import re
from queueconfig import notifications

from get_args import args
from config import settings, url_sonarr
from helper import path_replace
from list_subtitles import list_missing_subtitles, store_subtitles, series_full_scan_subtitles, \
    movies_full_scan_subtitles


def update_all_episodes():
    series_full_scan_subtitles()
    logging.info('BAZARR All existing episode subtitles indexed from disk.')
    list_missing_subtitles()
    logging.info('BAZARR All missing episode subtitles updated in database.')


def update_all_movies():
    movies_full_scan_subtitles()
    logging.info('BAZARR All existing movie subtitles indexed from disk.')
    list_missing_subtitles()
    logging.info('BAZARR All missing movie subtitles updated in database.')


def sync_episodes():
    notifications.write(msg='Episodes sync from Sonarr started...', queue='get_episodes')
    logging.debug('BAZARR Starting episodes sync from Sonarr.')
    apikey_sonarr = settings.sonarr.apikey
    
    # Open database connection
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    
    # Get current episodes id in DB
    current_episodes_db = c.execute('SELECT sonarrEpisodeId, path FROM table_episodes').fetchall()

    current_episodes_db_list = [x[0] for x in current_episodes_db]
    current_episodes_sonarr = []
    episodes_to_update = []
    episodes_to_add = []
    
    # Get sonarrId for each series from database
    seriesIdList = c.execute("SELECT sonarrSeriesId, title FROM table_shows").fetchall()
    
    # Close database connection
    c.close()
    
    for seriesId in seriesIdList:
        notifications.write(msg='Getting episodes data for this show: ' + seriesId[1], queue='get_episodes')
        # Get episodes data for a series from Sonarr
        url_sonarr_api_episode = url_sonarr + "/api/episode?seriesId=" + str(seriesId[0]) + "&apikey=" + apikey_sonarr
        try:
            r = requests.get(url_sonarr_api_episode, timeout=15, verify=False)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logging.exception("BAZARR Error trying to get episodes from Sonarr. Http error.")
        except requests.exceptions.ConnectionError as errc:
            logging.exception("BAZARR Error trying to get episodes from Sonarr. Connection Error.")
        except requests.exceptions.Timeout as errt:
            logging.exception("BAZARR Error trying to get episodes from Sonarr. Timeout Error.")
        except requests.exceptions.RequestException as err:
            logging.exception("BAZARR Error trying to get episodes from Sonarr.")
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
                                    resolution = str(episode['episodeFile']['quality']['quality']['resolution']) + 'p'

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
                                    episodes_to_update.append((episode['title'], episode['episodeFile']['path'],
                                                               episode['seasonNumber'], episode['episodeNumber'],
                                                               sceneName, str(bool(episode['monitored'])),
                                                               format, resolution,
                                                               videoCodec, audioCodec, episode['id']))
                                else:
                                    episodes_to_add.append((episode['seriesId'], episode['id'], episode['title'],
                                                            episode['episodeFile']['path'], episode['seasonNumber'],
                                                            episode['episodeNumber'], sceneName,
                                                            str(bool(episode['monitored'])), format, resolution,
                                                            videoCodec, audioCodec))
    
    removed_episodes = list(set(current_episodes_db_list) - set(current_episodes_sonarr))
    
    # Update or insert movies in DB
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    
    updated_result = c.executemany(
        '''UPDATE table_episodes SET title = ?, path = ?, season = ?, episode = ?, scene_name = ?, monitored = ?, format = ?, resolution = ?, video_codec = ?, audio_codec = ? WHERE sonarrEpisodeId = ?''',
        episodes_to_update)
    db.commit()
    
    added_result = c.executemany(
        '''INSERT OR IGNORE INTO table_episodes(sonarrSeriesId, sonarrEpisodeId, title, path, season, episode, scene_name, monitored, format, resolution, video_codec, audio_codec) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        episodes_to_add)
    db.commit()
    
    for removed_episode in removed_episodes:
        c.execute('DELETE FROM table_episodes WHERE sonarrEpisodeId = ?', (removed_episode,))
        db.commit()

    # Get episodes list after INSERT and UPDATE
    episodes_now_in_db = c.execute('SELECT sonarrEpisodeId, path FROM table_episodes').fetchall()

    # Close database connection
    c.close()

    # Get only episodes added or modified and store subtitles for them
    altered_episodes = set(episodes_now_in_db).difference(set(current_episodes_db))
    for altered_episode in altered_episodes:
        store_subtitles(path_replace(altered_episode[1]))

    logging.debug('BAZARR All episodes synced from Sonarr into database.')
    
    list_missing_subtitles()
    logging.debug('BAZARR All missing subtitles updated in database.')
    
    notifications.write(msg='Episodes sync from Sonarr ended.', queue='get_episodes')


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

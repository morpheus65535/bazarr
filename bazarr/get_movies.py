# coding=utf-8

import os
import sqlite3
import requests
import logging
from queueconfig import q4ws

from get_args import args
from config import settings, url_radarr
from helper import path_replace_movie
from list_subtitles import store_subtitles_movie, list_missing_subtitles_movies


def update_movies():
    q4ws.append("Update movies list from Radarr is running...")
    logging.debug('BAZARR Starting movie sync from Radarr.')
    apikey_radarr = settings.radarr.apikey
    movie_default_enabled = settings.general.getboolean('movie_default_enabled')
    movie_default_language = settings.general.movie_default_language
    movie_default_hi = settings.general.movie_default_hi
    
    if apikey_radarr is None:
        pass
    else:
        get_profile_list()
        
        # Get movies data from radarr
        url_radarr_api_movies = url_radarr + "/api/movie?apikey=" + apikey_radarr
        try:
            r = requests.get(url_radarr_api_movies, timeout=15, verify=False)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logging.exception("BAZARR Error trying to get movies from Radarr. Http error.")
        except requests.exceptions.ConnectionError as errc:
            logging.exception("BAZARR Error trying to get movies from Radarr. Connection Error.")
        except requests.exceptions.Timeout as errt:
            logging.exception("BAZARR Error trying to get movies from Radarr. Timeout Error.")
        except requests.exceptions.RequestException as err:
            logging.exception("BAZARR Error trying to get movies from Radarr.")
        else:
            # Get current movies in DB
            db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
            c = db.cursor()
            current_movies_db = c.execute('SELECT tmdbId, path FROM table_movies').fetchall()
            db.close()
            
            current_movies_db_list = [x[0] for x in current_movies_db]
            current_movies_radarr = []
            movies_to_update = []
            movies_to_add = []
            
            for movie in r.json():
                q4ws.append("Getting data for this movie: " + movie['title'])
                if movie['hasFile'] is True:
                    if 'movieFile' in movie:
                        if movie["path"] != None and movie['movieFile']['relativePath'] != None:
                            try:
                                overview = unicode(movie['overview'])
                            except:
                                overview = ""
                            try:
                                poster_big = movie['images'][0]['url']
                                poster = os.path.splitext(poster_big)[0] + '-500' + os.path.splitext(poster_big)[1]
                            except:
                                poster = ""
                            try:
                                fanart = movie['images'][1]['url']
                            except:
                                fanart = ""
                            
                            if 'sceneName' in movie['movieFile']:
                                sceneName = movie['movieFile']['sceneName']
                            else:
                                sceneName = None

                            if movie['alternativeTitles'] != None:
                                alternativeTitles = str([item['title'] for item in movie['alternativeTitles']])

                            if 'imdbId' in movie: imdbId = movie['imdbId']
                            else: imdbId = None

                            try:
                                format, resolution = movie['movieFile']['quality']['quality']['name'].split('-')
                            except:
                                format = movie['movieFile']['quality']['quality']['name']
                                resolution = movie['movieFile']['quality']['quality']['resolution'].lstrip('r').lower()

                            if 'mediaInfo' in movie['movieFile']:
                                videoFormat = videoCodecID = videoProfile = videoCodecLibrary = None
                                if 'videoFormat' in movie['movieFile']['mediaInfo']: videoFormat = movie['movieFile']['mediaInfo']['videoFormat']
                                if 'videoCodecID' in movie['movieFile']['mediaInfo']: videoCodecID = movie['movieFile']['mediaInfo']['videoCodecID']
                                if 'videoProfile' in movie['movieFile']['mediaInfo']: videoProfile = movie['movieFile']['mediaInfo']['videoProfile']
                                if 'videoCodecLibrary' in movie['movieFile']['mediaInfo']: videoCodecLibrary = movie['movieFile']['mediaInfo']['videoCodecLibrary']
                                videoCodec = RadarrFormatVideoCodec(videoFormat, videoCodecID, videoProfile, videoCodecLibrary)

                                audioFormat = audioCodec = audioProfile = audioAdditionalFeatures = None
                                if 'audioFormat' in movie['movieFile']['mediaInfo']: audioFormat = movie['movieFile']['mediaInfo']['audioFormat']
                                if 'audioCodecID' in movie['movieFile']['mediaInfo']: audioCodecID = movie['movieFile']['mediaInfo']['audioCodecID']
                                if 'audioProfile' in movie['movieFile']['mediaInfo']: audioProfile = movie['movieFile']['mediaInfo']['audioProfile']
                                if 'audioAdditionalFeatures' in movie['movieFile']['mediaInfo']: audioAdditionalFeatures = movie['movieFile']['mediaInfo']['audioAdditionalFeatures']
                                audioCodec = RadarrFormatAudioCodec(audioFormat, audioCodecID, audioProfile, audioAdditionalFeatures)
                            else:
                                videoCodec = None
                                audioCodec = None

                            # Add movies in radarr to current movies list
                            current_movies_radarr.append(unicode(movie['tmdbId']))
                            
                            # Detect file separator
                            if movie['path'][0] == "/":
                                separator = "/"
                            else:
                                separator = "\\"
                            
                            if unicode(movie['tmdbId']) in current_movies_db_list:
                                movies_to_update.append((movie["title"],
                                                         movie["path"] + separator + movie['movieFile']['relativePath'],
                                                         movie["tmdbId"], movie["id"], overview, poster, fanart,
                                                         profile_id_to_language(movie['qualityProfileId']), sceneName,
                                                         unicode(bool(movie['monitored'])), movie['sortTitle'],
                                                         movie['year'], alternativeTitles, format, resolution,
                                                         videoCodec, audioCodec, imdbId, movie["tmdbId"]))
                            else:
                                if movie_default_enabled is True:
                                    movies_to_add.append((movie["title"],
                                                          movie["path"] + separator + movie['movieFile']['relativePath'],
                                                          movie["tmdbId"], movie_default_language, '[]', movie_default_hi,
                                                          movie["id"], overview, poster, fanart,
                                                          profile_id_to_language(movie['qualityProfileId']), sceneName,
                                                          unicode(bool(movie['monitored'])), movie['sortTitle'],
                                                          movie['year'], alternativeTitles, format, resolution,
                                                          videoCodec, audioCodec, imdbId))
                                else:
                                    movies_to_add.append((movie["title"],
                                                          movie["path"] + separator + movie['movieFile'][
                                                              'relativePath'], movie["tmdbId"], movie["tmdbId"],
                                                          movie["tmdbId"], movie["id"], overview, poster, fanart,
                                                          profile_id_to_language(movie['qualityProfileId']), sceneName,
                                                          unicode(bool(movie['monitored'])), movie['sortTitle'],
                                                          movie['year'], alternativeTitles, format, resolution,
                                                          videoCodec, audioCodec, imdbId))
                        else:
                            logging.error(
                                'BAZARR Radarr returned a movie without a file path: ' + movie["path"] + separator +
                                movie['movieFile']['relativePath'])
            
            # Update or insert movies in DB
            db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
            c = db.cursor()
            
            updated_result = c.executemany(
                '''UPDATE table_movies SET title = ?, path = ?, tmdbId = ?, radarrId = ?, overview = ?, poster = ?, fanart = ?, `audio_language` = ?, sceneName = ?, monitored = ?, sortTitle = ?, year = ?, alternativeTitles = ?, format = ?, resolution = ?, video_codec = ?, audio_codec = ?, imdbId = ? WHERE tmdbid = ?''',
                movies_to_update)
            db.commit()
            
            if movie_default_enabled is True:
                added_result = c.executemany(
                    '''INSERT OR IGNORE INTO table_movies(title, path, tmdbId, languages, subtitles,`hearing_impaired`, radarrId, overview, poster, fanart, `audio_language`, sceneName, monitored, sortTitle, year, alternativeTitles, format, resolution, video_codec, audio_codec, imdbId) VALUES (?,?,?,?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    movies_to_add)
                db.commit()
            else:
                added_result = c.executemany(
                    '''INSERT OR IGNORE INTO table_movies(title, path, tmdbId, languages, subtitles,`hearing_impaired`, radarrId, overview, poster, fanart, `audio_language`, sceneName, monitored, sortTitle, year, alternativeTitles, format, resolution, video_codec, audio_codec, imdbId) VALUES (?,?,?,(SELECT languages FROM table_movies WHERE tmdbId = ?), '[]',(SELECT `hearing_impaired` FROM table_movies WHERE tmdbId = ?), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    movies_to_add)
                db.commit()

            removed_movies = list(set(current_movies_db_list) - set(current_movies_radarr))

            for removed_movie in removed_movies:
                c.execute('DELETE FROM table_movies WHERE tmdbId = ?', (removed_movie,))
                db.commit()

            # Get movies list after INSERT and UPDATE
            movies_now_in_db = c.execute('SELECT tmdbId, path FROM table_movies').fetchall()

            # Close database connection
            db.close()

            # Get only movies added or modified and store subtitles for them
            altered_movies = set(movies_now_in_db).difference(set(current_movies_db))
            for altered_movie in altered_movies:
                store_subtitles_movie(path_replace_movie(altered_movie[1]))

    logging.debug('BAZARR All movies synced from Radarr into database.')
    
    list_missing_subtitles_movies()
    logging.debug('BAZARR All movie missing subtitles updated in database.')
    
    q4ws.append("Update movies list from Radarr is ended.")


def get_profile_list():
    apikey_radarr = settings.radarr.apikey
    
    # Get profiles data from radarr
    global profiles_list
    profiles_list = []
    
    url_radarr_api_movies = url_radarr + "/api/profile?apikey=" + apikey_radarr
    try:
        profiles_json = requests.get(url_radarr_api_movies, timeout=15, verify=False)
    except requests.exceptions.ConnectionError as errc:
        logging.exception("BAZARR Error trying to get profiles from Radarr. Connection Error.")
    except requests.exceptions.Timeout as errt:
        logging.exception("BAZARR Error trying to get profiles from Radarr. Timeout Error.")
    except requests.exceptions.RequestException as err:
        logging.exception("BAZARR Error trying to get profiles from Radarr.")
    else:
        # Parsing data returned from radarr
        for profile in profiles_json.json():
            profiles_list.append([profile['id'], profile['language'].capitalize()])


def profile_id_to_language(id):
    for profile in profiles_list:
        if id == profile[0]:
            return profile[1]


def RadarrFormatAudioCodec(audioFormat, audioCodecID, audioProfile, audioAdditionalFeatures):
    if audioFormat == "AC-3": return "AC3"
    if audioFormat == "E-AC-3": return "EAC3"
    if audioFormat == "AAC":
        if audioCodecID == "A_AAC/MPEG4/LC/SBR":
            return "HE-AAC"
        else:
            return "AAC"
    if audioFormat.strip() == "mp3": return "MP3"
    if audioFormat == "MPEG Audio":
        if audioCodecID == "55" or audioCodecID == "A_MPEG/L3" or audioProfile == "Layer 3": return "MP3"
        if audioCodecID == "A_MPEG/L2" or audioProfile == "Layer 2": return "MP2"
    if audioFormat == "MLP FBA":
        if audioAdditionalFeatures == "16-ch":
            return "TrueHD Atmos"
        else:
            return "TrueHD"

    return audioFormat


def RadarrFormatVideoCodec(videoFormat, videoCodecID, videoProfile, videoCodecLibrary):
    if videoFormat == "x264": return "h264"
    if videoFormat == "AVC" or videoFormat == "V.MPEG4/ISO/AVC": return "h264"
    if videoFormat == "HEVC" or videoFormat == "V_MPEGH/ISO/HEVC":
        if videoCodecLibrary.startswith("x265"): return "h265"
    if videoFormat == "MPEG Video":
        if videoCodecID == "2" or videoCodecID == "V_MPEG2":
            return "Mpeg2"
        else:
            return "Mpeg"
    if videoFormat == "MPEG-1 Video": return "Mpeg"
    if videoFormat == "MPEG-2 Video": return "Mpeg2"
    if videoFormat == "MPEG-4 Visual":
        if videoCodecID.endswith("XVID") or videoCodecLibrary.startswith("XviD"): return "XviD"
        if videoCodecID.endswith("DIV3") or videoCodecID.endswith("DIVX") or videoCodecID.endswith(
            "DX50") or videoCodecLibrary.startswith("DivX"): return "DivX"
    if videoFormat == "VC-1": return "VC1"
    if videoFormat == "WMV2":
        return "WMV"
    if videoFormat == "DivX" or videoFormat == "div3":
        return "DivX"

    return videoFormat


if __name__ == '__main__':
    update_movies()

# coding=utf-8

import os
import requests
import logging
from queueconfig import notifications

from get_args import args
from config import settings, url_radarr
from helper import path_replace_movie
from utils import get_radarr_version
from list_subtitles import store_subtitles_movie, list_missing_subtitles_movies, movies_full_scan_subtitles

from get_subtitle import movies_download_subtitles
from database import database, dict_converter


def update_all_movies():
    movies_full_scan_subtitles()
    logging.info('BAZARR All existing movie subtitles indexed from disk.')


def update_movies():
    logging.debug('BAZARR Starting movie sync from Radarr.')
    apikey_radarr = settings.radarr.apikey
    movie_default_enabled = settings.general.getboolean('movie_default_enabled')
    movie_default_language = settings.general.movie_default_language
    movie_default_hi = settings.general.movie_default_hi
    movie_default_forced = settings.general.movie_default_forced
    
    if apikey_radarr is None:
        pass
    else:
        audio_profiles = get_profile_list()
        
        # Get movies data from radarr
        url_radarr_api_movies = url_radarr() + "/api/movie?apikey=" + apikey_radarr
        try:
            r = requests.get(url_radarr_api_movies, timeout=60, verify=False)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logging.exception("BAZARR Error trying to get movies from Radarr. Http error.")
            return
        except requests.exceptions.ConnectionError as errc:
            logging.exception("BAZARR Error trying to get movies from Radarr. Connection Error.")
            return
        except requests.exceptions.Timeout as errt:
            logging.exception("BAZARR Error trying to get movies from Radarr. Timeout Error.")
            return
        except requests.exceptions.RequestException as err:
            logging.exception("BAZARR Error trying to get movies from Radarr.")
            return
        else:
            # Get current movies in DB
            current_movies_db = database.execute("SELECT tmdbId, path, radarrId FROM table_movies")
            
            current_movies_db_list = [x['tmdbId'] for x in current_movies_db]

            current_movies_radarr = []
            movies_to_update = []
            movies_to_add = []
            altered_movies = []

            moviesIdListLength = len(r.json())
            for i, movie in enumerate(r.json(), 1):
                notifications.write(msg="Getting movies data from Radarr...", queue='get_movies', item=i,
                                    length=moviesIdListLength)
                if movie['hasFile'] is True:
                    if 'movieFile' in movie:
                        # Detect file separator
                        if movie['path'][0] == "/":
                            separator = "/"
                        else:
                            separator = "\\"

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

                            if 'alternativeTitles' in movie:
                                alternativeTitles = str([item['title'] for item in movie['alternativeTitles']])
                            else:
                                alternativeTitles = None

                            if 'imdbId' in movie: imdbId = movie['imdbId']
                            else: imdbId = None

                            try:
                                format, resolution = movie['movieFile']['quality']['quality']['name'].split('-')
                            except:
                                format = movie['movieFile']['quality']['quality']['name']
                            try:
                                resolution = movie['movieFile']['quality']['quality']['resolution'].lstrip('r').lower()
                            except:
                                resolution = None

                            if 'mediaInfo' in movie['movieFile']:
                                videoFormat = videoCodecID = videoProfile = videoCodecLibrary = None
                                if 'videoFormat' in movie['movieFile']['mediaInfo']: videoFormat = movie['movieFile']['mediaInfo']['videoFormat']
                                if 'videoCodecID' in movie['movieFile']['mediaInfo']: videoCodecID = movie['movieFile']['mediaInfo']['videoCodecID']
                                if 'videoProfile' in movie['movieFile']['mediaInfo']: videoProfile = movie['movieFile']['mediaInfo']['videoProfile']
                                if 'videoCodecLibrary' in movie['movieFile']['mediaInfo']: videoCodecLibrary = movie['movieFile']['mediaInfo']['videoCodecLibrary']
                                videoCodec = RadarrFormatVideoCodec(videoFormat, videoCodecID, videoProfile, videoCodecLibrary)

                                audioFormat = audioCodecID = audioProfile = audioAdditionalFeatures = None
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
                            
                            if unicode(movie['tmdbId']) in current_movies_db_list:
                                movies_to_update.append({'radarrId': movie["id"],
                                                         'title': unicode(movie["title"]),
                                                         'path': unicode(movie["path"] + separator + movie['movieFile']['relativePath']),
                                                         'tmdbId': unicode(movie["tmdbId"]),
                                                         'poster': unicode(poster),
                                                         'fanart': unicode(fanart),
                                                         'audio_language': unicode(profile_id_to_language(movie['qualityProfileId'], audio_profiles)),
                                                         'sceneName': sceneName,
                                                         'monitored': unicode(bool(movie['monitored'])),
                                                         'year': unicode(movie['year']),
                                                         'sortTitle': unicode(movie['sortTitle']),
                                                         'alternativeTitles': unicode(alternativeTitles),
                                                         'format': unicode(format),
                                                         'resolution': unicode(resolution),
                                                         'video_codec': unicode(videoCodec),
                                                         'audio_codec': unicode(audioCodec),
                                                         'overview': unicode(overview),
                                                         'imdbId': unicode(imdbId),
                                                         'movie_file_id': movie['movieFile']['id']})
                            else:
                                if movie_default_enabled is True:
                                    movies_to_add.append({'radarrId': movie["id"],
                                                          'title': movie["title"],
                                                          'path': movie["path"] + separator + movie['movieFile']['relativePath'],
                                                          'tmdbId': movie["tmdbId"],
                                                          'languages': movie_default_language,
                                                          'subtitles': '[]',
                                                          'hearing_impaired': movie_default_hi,
                                                          'overview': overview,
                                                          'poster': poster,
                                                          'fanart': fanart,
                                                          'audio_language': profile_id_to_language(movie['qualityProfileId'], audio_profiles),
                                                          'sceneName': sceneName,
                                                          'monitored': unicode(bool(movie['monitored'])),
                                                          'sortTitle': movie['sortTitle'],
                                                          'year': movie['year'],
                                                          'alternativeTitles': alternativeTitles,
                                                          'format': format,
                                                          'resolution': resolution,
                                                          'video_codec': videoCodec,
                                                          'audio_codec': audioCodec,
                                                          'imdbId': imdbId,
                                                          'forced': movie_default_forced,
                                                          'movie_file_id': movie['movieFile']['id']})
                                else:
                                    movies_to_add.append({'radarrId': movie["id"],
                                                          'title': movie["title"],
                                                          'path': movie["path"] + separator + movie['movieFile']['relativePath'],
                                                          'tmdbId': movie["tmdbId"],
                                                          'languages': None,
                                                          'subtitles': '[]',
                                                          'hearing_impaired': None,
                                                          'overview': overview,
                                                          'poster': poster,
                                                          'fanart': fanart,
                                                          'audio_language': profile_id_to_language(movie['qualityProfileId'], audio_profiles),
                                                          'sceneName': sceneName,
                                                          'monitored': unicode(bool(movie['monitored'])),
                                                          'sortTitle': movie['sortTitle'],
                                                          'year': movie['year'],
                                                          'alternativeTitles': alternativeTitles,
                                                          'format': format,
                                                          'resolution': resolution,
                                                          'video_codec': videoCodec,
                                                          'audio_codec': audioCodec,
                                                          'imdbId': imdbId,
                                                          'forced': None,
                                                          'movie_file_id': movie['movieFile']['id']})
                        else:
                            logging.error(
                                'BAZARR Radarr returned a movie without a file path: ' + movie["path"] + separator +
                                movie['movieFile']['relativePath'])

            # Remove old movies from DB
            removed_movies = list(set(current_movies_db_list) - set(current_movies_radarr))

            for removed_movie in removed_movies:
                database.execute("DELETE FROM table_movies WHERE tmdbId=?", (removed_movie,))

            # Update movies in DB
            movies_in_db_list = []
            movies_in_db = database.execute("SELECT radarrId, title, path, tmdbId, overview, poster, fanart, "
                                            "audio_language, sceneName, monitored, sortTitle, year, "
                                            "alternativeTitles, format, resolution, video_codec, audio_codec, imdbId,"
                                            "movie_file_id FROM table_movies")

            for item in movies_in_db:
                movies_in_db_list.append(item)

            movies_to_update_list = [i for i in movies_to_update if i not in movies_in_db_list]

            for updated_movie in movies_to_update_list:
                query = dict_converter.convert(updated_movie)
                database.execute('''UPDATE table_movies SET ''' + query.keys_update + ''' WHERE radarrId = ?''',
                                 query.values + (updated_movie['radarrId'],))
                altered_movies.append([updated_movie['tmdbId'],
                                       updated_movie['path'],
                                       updated_movie['radarrId'],
                                       updated_movie['monitored']])

            # Insert new movies in DB
            for added_movie in movies_to_add:
                query = dict_converter.convert(added_movie)
                result = database.execute(
                    '''INSERT OR IGNORE INTO table_movies(''' + query.keys_insert + ''') VALUES(''' +
                    query.question_marks + ''')''', query.values)
                if result > 0:
                    altered_movies.append([added_movie['tmdbId'],
                                           added_movie['path'],
                                           added_movie['radarrId'],
                                           added_movie['monitored']])
                else:
                    logging.debug('BAZARR unable to insert this movie into the database:',
                                  path_replace_movie(added_movie['path']))

            # Store subtitles for added or modified movies
            for i, altered_movie in enumerate(altered_movies, 1):
                notifications.write(msg='Indexing movies embedded subtitles...', queue='get_movies', item=i,
                                    length=len(altered_movies))
                store_subtitles_movie(path_replace_movie(altered_movie[1]))

            logging.debug('BAZARR All movies synced from Radarr into database.')

            # Search for desired subtitles if no more than 5 movies have been added.
            if len(altered_movies) <= 5:
                logging.debug("BAZARR No more than 5 movies were added during this sync then we'll search for subtitles.")
                for altered_movie in altered_movies:
                    if settings.radarr.getboolean('only_monitored'):
                        if altered_movie[3] == 'True':
                            movies_download_subtitles(altered_movie[2])
                    else:
                        movies_download_subtitles(altered_movie[2])
            else:
                logging.debug("BAZARR More than 5 movies were added during this sync then we wont search for subtitles.")


def get_profile_list():
    apikey_radarr = settings.radarr.apikey
    radarr_version = get_radarr_version()
    profiles_list = []
    # Get profiles data from radarr

    url_radarr_api_movies = url_radarr() + "/api/profile?apikey=" + apikey_radarr
    try:
        profiles_json = requests.get(url_radarr_api_movies, timeout=60, verify=False)
    except requests.exceptions.ConnectionError as errc:
        logging.exception("BAZARR Error trying to get profiles from Radarr. Connection Error.")
    except requests.exceptions.Timeout as errt:
        logging.exception("BAZARR Error trying to get profiles from Radarr. Timeout Error.")
    except requests.exceptions.RequestException as err:
        logging.exception("BAZARR Error trying to get profiles from Radarr.")
    else:
        # Parsing data returned from radarr
        if radarr_version.startswith('0'):
            for profile in profiles_json.json():
                profiles_list.append([profile['id'], profile['language'].capitalize()])
        elif radarr_version.startswith('2'):
            for profile in profiles_json.json():
                profiles_list.append([profile['id'], profile['language']['name'].capitalize()])

        return profiles_list

    return None


def profile_id_to_language(id, profiles):
    for profile in profiles:
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

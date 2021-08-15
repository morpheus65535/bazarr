# coding=utf-8

import os
import requests
import logging
import operator
from functools import reduce
from gevent import sleep
from peewee import DoesNotExist

from config import settings, url_radarr
from helper import path_mappings
from utils import get_radarr_info
from list_subtitles import store_subtitles_movie, movies_full_scan_subtitles
from get_rootfolder import check_radarr_rootfolder

from get_subtitle import movies_download_subtitles
from database import get_exclusion_clause, TableMovies
from event_handler import event_stream, show_progress, hide_progress

headers = {"User-Agent": os.environ["SZ_USER_AGENT"]}


def update_all_movies():
    movies_full_scan_subtitles()
    logging.info('BAZARR All existing movie subtitles indexed from disk.')


def update_movies(send_event=True):
    check_radarr_rootfolder()
    logging.debug('BAZARR Starting movie sync from Radarr.')
    apikey_radarr = settings.radarr.apikey

    movie_default_enabled = settings.general.getboolean('movie_default_enabled')

    if movie_default_enabled is True:
        movie_default_profile = settings.general.movie_default_profile
        if movie_default_profile == '':
            movie_default_profile = None
    else:
        movie_default_profile = None

    if apikey_radarr is None:
        pass
    else:
        audio_profiles = get_profile_list()
        tagsDict = get_tags()
        
        # Get movies data from radarr
        movies = get_movies_from_radarr_api(url=url_radarr(), apikey_radarr=apikey_radarr)
        if not movies:
            return
        else:
            # Get current movies in DB
            current_movies_db = TableMovies.select(TableMovies.tmdbId, TableMovies.path, TableMovies.radarrId).dicts()
            
            current_movies_db_list = [x['tmdbId'] for x in current_movies_db]

            current_movies_radarr = []
            movies_to_update = []
            movies_to_add = []
            altered_movies = []

            # Build new and updated movies
            movies_count = len(movies)
            for i, movie in enumerate(movies, 1):
                sleep()
                if send_event:
                    show_progress(id='movies_progress',
                                  header='Syncing movies...',
                                  name=movie['title'],
                                  value=i,
                                  count=movies_count)

                if movie['hasFile'] is True:
                    if 'movieFile' in movie:
                        if movie['movieFile']['size'] > 20480:
                            # Add movies in radarr to current movies list
                            current_movies_radarr.append(str(movie['tmdbId']))

                            if str(movie['tmdbId']) in current_movies_db_list:
                                movies_to_update.append(movieParser(movie, action='update',
                                                                    tags_dict=tagsDict,
                                                                    movie_default_profile=movie_default_profile,
                                                                    audio_profiles=audio_profiles))
                            else:
                                movies_to_add.append(movieParser(movie, action='insert',
                                                                 tags_dict=tagsDict,
                                                                 movie_default_profile=movie_default_profile,
                                                                 audio_profiles=audio_profiles))
 
            if send_event:
                hide_progress(id='movies_progress')

            # Remove old movies from DB
            removed_movies = list(set(current_movies_db_list) - set(current_movies_radarr))

            for removed_movie in removed_movies:
                sleep()
                TableMovies.delete().where(TableMovies.tmdbId == removed_movie).execute()

            # Update movies in DB
            movies_in_db_list = []
            movies_in_db = TableMovies.select(TableMovies.radarrId,
                                              TableMovies.title,
                                              TableMovies.path,
                                              TableMovies.tmdbId,
                                              TableMovies.overview,
                                              TableMovies.poster,
                                              TableMovies.fanart,
                                              TableMovies.audio_language,
                                              TableMovies.sceneName,
                                              TableMovies.monitored,
                                              TableMovies.sortTitle,
                                              TableMovies.year,
                                              TableMovies.alternativeTitles,
                                              TableMovies.format,
                                              TableMovies.resolution,
                                              TableMovies.video_codec,
                                              TableMovies.audio_codec,
                                              TableMovies.imdbId,
                                              TableMovies.movie_file_id,
                                              TableMovies.tags,
                                              TableMovies.file_size).dicts()

            for item in movies_in_db:
                movies_in_db_list.append(item)

            movies_to_update_list = [i for i in movies_to_update if i not in movies_in_db_list]

            for updated_movie in movies_to_update_list:
                sleep()
                TableMovies.update(updated_movie).where(TableMovies.tmdbId == updated_movie['tmdbId']).execute()
                altered_movies.append([updated_movie['tmdbId'],
                                       updated_movie['path'],
                                       updated_movie['radarrId'],
                                       updated_movie['monitored']])

            # Insert new movies in DB
            for added_movie in movies_to_add:
                sleep()
                result = TableMovies.insert(added_movie).on_conflict(action='IGNORE').execute()
                if result > 0:
                    altered_movies.append([added_movie['tmdbId'],
                                           added_movie['path'],
                                           added_movie['radarrId'],
                                           added_movie['monitored']])
                    if send_event:
                        event_stream(type='movie', action='update', payload=int(added_movie['radarrId']))
                else:
                    logging.debug('BAZARR unable to insert this movie into the database:',
                                  path_mappings.path_replace_movie(added_movie['path']))

            # Store subtitles for added or modified movies
            for i, altered_movie in enumerate(altered_movies, 1):
                sleep()
                store_subtitles_movie(altered_movie[1], path_mappings.path_replace_movie(altered_movie[1]))

            logging.debug('BAZARR All movies synced from Radarr into database.')


def update_one_movie(movie_id, action):
    logging.debug('BAZARR syncing this specific movie from Radarr: {}'.format(movie_id))

    # Check if there's a row in database for this movie ID
    try:
        existing_movie = TableMovies.select(TableMovies.path)\
            .where(TableMovies.radarrId == movie_id)\
            .dicts()\
            .get()
    except DoesNotExist:
        existing_movie = None

    # Remove movie from DB
    if action == 'deleted':
        if existing_movie:
            TableMovies.delete().where(TableMovies.radarrId == movie_id).execute()
            event_stream(type='movie', action='delete', payload=int(movie_id))
            logging.debug('BAZARR deleted this movie from the database:{}'.format(path_mappings.path_replace_movie(
                existing_movie['path'])))
        return

    movie_default_enabled = settings.general.getboolean('movie_default_enabled')

    if movie_default_enabled is True:
        movie_default_profile = settings.general.movie_default_profile
        if movie_default_profile == '':
            movie_default_profile = None
    else:
        movie_default_profile = None

    audio_profiles = get_profile_list()
    tagsDict = get_tags()

    try:
        # Get movie data from radarr api
        movie = None
        movie_data = get_movies_from_radarr_api(url=url_radarr(), apikey_radarr=settings.radarr.apikey,
                                                radarr_id=movie_id)
        if not movie_data:
            return
        else:
            if action == 'updated' and existing_movie:
                movie = movieParser(movie_data, action='update', tags_dict=tagsDict, 
                                    movie_default_profile=movie_default_profile, audio_profiles=audio_profiles)
            elif action == 'updated' and not existing_movie:
                movie = movieParser(movie_data, action='insert', tags_dict=tagsDict, 
                                    movie_default_profile=movie_default_profile, audio_profiles=audio_profiles)
    except Exception:
        logging.debug('BAZARR cannot get movie returned by SignalR feed from Radarr API.')
        return

    # Drop useless events
    if not movie and not existing_movie:
        return

    # Remove movie from DB
    if not movie and existing_movie:
        TableMovies.delete().where(TableMovies.radarrId == movie_id).execute()
        event_stream(type='movie', action='delete', payload=int(movie_id))
        logging.debug('BAZARR deleted this movie from the database:{}'.format(path_mappings.path_replace_movie(
            existing_movie['path'])))
        return

    # Update existing movie in DB
    elif movie and existing_movie:
        TableMovies.update(movie).where(TableMovies.radarrId == movie['radarrId']).execute()
        event_stream(type='movie', action='update', payload=int(movie_id))
        logging.debug('BAZARR updated this movie into the database:{}'.format(path_mappings.path_replace_movie(
            movie['path'])))

    # Insert new movie in DB
    elif movie and not existing_movie:
        TableMovies.insert(movie).on_conflict(action='IGNORE').execute()
        event_stream(type='movie', action='update', payload=int(movie_id))
        logging.debug('BAZARR inserted this movie into the database:{}'.format(path_mappings.path_replace_movie(
            movie['path'])))

    # Storing existing subtitles
    logging.debug('BAZARR storing subtitles for this movie: {}'.format(path_mappings.path_replace_movie(
            movie['path'])))
    store_subtitles_movie(movie['path'], path_mappings.path_replace_movie(movie['path']))

    # Downloading missing subtitles
    logging.debug('BAZARR downloading missing subtitles for this movie: {}'.format(path_mappings.path_replace_movie(
        movie['path'])))
    movies_download_subtitles(movie_id)


def get_profile_list():
    apikey_radarr = settings.radarr.apikey
    profiles_list = []
    # Get profiles data from radarr
    if get_radarr_info.is_legacy():
        url_radarr_api_movies = url_radarr() + "/api/profile?apikey=" + apikey_radarr
    else:
        url_radarr_api_movies = url_radarr() + "/api/v3/qualityprofile?apikey=" + apikey_radarr

    try:
        profiles_json = requests.get(url_radarr_api_movies, timeout=60, verify=False, headers=headers)
    except requests.exceptions.ConnectionError as errc:
        logging.exception("BAZARR Error trying to get profiles from Radarr. Connection Error.")
    except requests.exceptions.Timeout as errt:
        logging.exception("BAZARR Error trying to get profiles from Radarr. Timeout Error.")
    except requests.exceptions.RequestException as err:
        logging.exception("BAZARR Error trying to get profiles from Radarr.")
    else:
        # Parsing data returned from radarr
        if get_radarr_info.is_legacy():
            for profile in profiles_json.json():
                profiles_list.append([profile['id'], profile['language'].capitalize()])
        else:
            for profile in profiles_json.json():
                profiles_list.append([profile['id'], profile['language']['name'].capitalize()])

        return profiles_list

    return None


def profile_id_to_language(id, profiles):
    for profile in profiles:
        profiles_to_return = []
        if id == profile[0]:
            profiles_to_return.append(profile[1])
    return profiles_to_return


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


def RadarrFormatVideoCodec(videoFormat, videoCodecID, videoCodecLibrary):
    if videoFormat == "x264": return "h264"
    if videoFormat == "AVC" or videoFormat == "V.MPEG4/ISO/AVC": return "h264"
    if videoCodecLibrary and (videoFormat == "HEVC" or videoFormat == "V_MPEGH/ISO/HEVC"):
        if videoCodecLibrary.startswith("x265"): return "h265"
    if videoCodecID and videoFormat == "MPEG Video":
        if videoCodecID == "2" or videoCodecID == "V_MPEG2":
            return "Mpeg2"
        else:
            return "Mpeg"
    if videoFormat == "MPEG-1 Video": return "Mpeg"
    if videoFormat == "MPEG-2 Video": return "Mpeg2"
    if videoCodecLibrary and videoCodecID and videoFormat == "MPEG-4 Visual":
        if videoCodecID.endswith("XVID") or videoCodecLibrary.startswith("XviD"): return "XviD"
        if videoCodecID.endswith("DIV3") or videoCodecID.endswith("DIVX") or videoCodecID.endswith(
            "DX50") or videoCodecLibrary.startswith("DivX"): return "DivX"
    if videoFormat == "VC-1": return "VC1"
    if videoFormat == "WMV2":
        return "WMV"
    if videoFormat == "DivX" or videoFormat == "div3":
        return "DivX"

    return videoFormat


def get_tags():
    apikey_radarr = settings.radarr.apikey
    tagsDict = []

    # Get tags data from Radarr
    if get_radarr_info.is_legacy():
        url_radarr_api_series = url_radarr() + "/api/tag?apikey=" + apikey_radarr
    else:
        url_radarr_api_series = url_radarr() + "/api/v3/tag?apikey=" + apikey_radarr

    try:
        tagsDict = requests.get(url_radarr_api_series, timeout=60, verify=False, headers=headers)
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get tags from Radarr. Connection Error.")
        return []
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get tags from Radarr. Timeout Error.")
        return []
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get tags from Radarr.")
        return []
    else:
        return tagsDict.json()


def movieParser(movie, action, tags_dict, movie_default_profile, audio_profiles):
    if 'movieFile' in movie:
        # Detect file separator
        if movie['path'][0] == "/":
            separator = "/"
        else:
            separator = "\\"

        try:
            overview = str(movie['overview'])
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

        alternativeTitles = None
        if get_radarr_info.is_legacy():
            if 'alternativeTitles' in movie:
                alternativeTitles = str([item['title'] for item in movie['alternativeTitles']])
        else:
            if 'alternateTitles' in movie:
                alternativeTitles = str([item['title'] for item in movie['alternateTitles']])

        if 'imdbId' in movie:
            imdbId = movie['imdbId']
        else:
            imdbId = None

        try:
            format, resolution = movie['movieFile']['quality']['quality']['name'].split('-')
        except:
            format = movie['movieFile']['quality']['quality']['name']
            try:
                resolution = str(movie['movieFile']['quality']['quality']['resolution']) + 'p'
            except:
                resolution = None

        if 'mediaInfo' in movie['movieFile']:
            videoFormat = videoCodecID = videoProfile = videoCodecLibrary = None
            if get_radarr_info.is_legacy():
                if 'videoFormat' in movie['movieFile']['mediaInfo']: videoFormat = \
                movie['movieFile']['mediaInfo']['videoFormat']
            else:
                if 'videoCodec' in movie['movieFile']['mediaInfo']: videoFormat = \
                movie['movieFile']['mediaInfo']['videoCodec']
            if 'videoCodecID' in movie['movieFile']['mediaInfo']: videoCodecID = \
            movie['movieFile']['mediaInfo']['videoCodecID']
            if 'videoProfile' in movie['movieFile']['mediaInfo']: videoProfile = \
            movie['movieFile']['mediaInfo']['videoProfile']
            if 'videoCodecLibrary' in movie['movieFile']['mediaInfo']: videoCodecLibrary = \
            movie['movieFile']['mediaInfo']['videoCodecLibrary']
            videoCodec = RadarrFormatVideoCodec(videoFormat, videoCodecID, videoCodecLibrary)

            audioFormat = audioCodecID = audioProfile = audioAdditionalFeatures = None
            if get_radarr_info.is_legacy():
                if 'audioFormat' in movie['movieFile']['mediaInfo']: audioFormat = \
                movie['movieFile']['mediaInfo']['audioFormat']
            else:
                if 'audioCodec' in movie['movieFile']['mediaInfo']: audioFormat = \
                movie['movieFile']['mediaInfo']['audioCodec']
            if 'audioCodecID' in movie['movieFile']['mediaInfo']: audioCodecID = \
            movie['movieFile']['mediaInfo']['audioCodecID']
            if 'audioProfile' in movie['movieFile']['mediaInfo']: audioProfile = \
            movie['movieFile']['mediaInfo']['audioProfile']
            if 'audioAdditionalFeatures' in movie['movieFile']['mediaInfo']: audioAdditionalFeatures = \
            movie['movieFile']['mediaInfo']['audioAdditionalFeatures']
            audioCodec = RadarrFormatAudioCodec(audioFormat, audioCodecID, audioProfile,
                                                audioAdditionalFeatures)
        else:
            videoCodec = None
            audioCodec = None

        audio_language = []
        if get_radarr_info.is_legacy():
            if 'mediaInfo' in movie['movieFile']:
                if 'audioLanguages' in movie['movieFile']['mediaInfo']:
                    audio_languages_list = movie['movieFile']['mediaInfo']['audioLanguages'].split('/')
                    if len(audio_languages_list):
                        for audio_language_list in audio_languages_list:
                            audio_language.append(audio_language_list.strip())
            if not audio_language:
                audio_language = profile_id_to_language(movie['qualityProfileId'], audio_profiles)
        else:
            if 'languages' in movie['movieFile'] and len(movie['movieFile']['languages']):
                for item in movie['movieFile']['languages']:
                    if isinstance(item, dict):
                        if 'name' in item:
                            audio_language.append(item['name'])

        tags = [d['label'] for d in tags_dict if d['id'] in movie['tags']]

        if action == 'update':
             return {'radarrId': int(movie["id"]),
                     'title': movie["title"],
                     'path': movie["path"] + separator + movie['movieFile']['relativePath'],
                     'tmdbId': str(movie["tmdbId"]),
                     'poster': poster,
                     'fanart': fanart,
                     'audio_language': str(audio_language),
                     'sceneName': sceneName,
                     'monitored': str(bool(movie['monitored'])),
                     'year': str(movie['year']),
                     'sortTitle': movie['sortTitle'],
                     'alternativeTitles': alternativeTitles,
                     'format': format,
                     'resolution': resolution,
                     'video_codec': videoCodec,
                     'audio_codec': audioCodec,
                     'overview': overview,
                     'imdbId': imdbId,
                     'movie_file_id': int(movie['movieFile']['id']),
                     'tags': str(tags),
                     'file_size': movie['movieFile']['size']}
        else:
            return {'radarrId': int(movie["id"]),
                    'title': movie["title"],
                    'path': movie["path"] + separator + movie['movieFile']['relativePath'],
                    'tmdbId': str(movie["tmdbId"]),
                    'subtitles': '[]',
                    'overview': overview,
                    'poster': poster,
                    'fanart': fanart,
                    'audio_language': str(audio_language),
                    'sceneName': sceneName,
                    'monitored': str(bool(movie['monitored'])),
                    'sortTitle': movie['sortTitle'],
                    'year': str(movie['year']),
                    'alternativeTitles': alternativeTitles,
                    'format': format,
                    'resolution': resolution,
                    'video_codec': videoCodec,
                    'audio_codec': audioCodec,
                    'imdbId': imdbId,
                    'movie_file_id': int(movie['movieFile']['id']),
                    'tags': str(tags),
                    'profileId': movie_default_profile,
                    'file_size': movie['movieFile']['size']}


def get_movies_from_radarr_api(url, apikey_radarr, radarr_id=None):
    if get_radarr_info.is_legacy():
        url_radarr_api_movies = url + "/api/movie" + ("/{}".format(radarr_id) if radarr_id else "") + "?apikey=" + \
                                apikey_radarr
    else:
        url_radarr_api_movies = url + "/api/v3/movie" + ("/{}".format(radarr_id) if radarr_id else "") + "?apikey=" + \
                                apikey_radarr

    try:
        r = requests.get(url_radarr_api_movies, timeout=60, verify=False, headers=headers)
        if r.status_code == 404:
            return
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
        return r.json()

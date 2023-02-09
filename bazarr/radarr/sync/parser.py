# coding=utf-8

import os

from radarr.info import get_radarr_info
from utilities.video_analyzer import embedded_audio_reader
from utilities.path_mappings import path_mappings

from .converter import RadarrFormatAudioCodec, RadarrFormatVideoCodec


def movieParser(movie, action, tags_dict, movie_default_profile, audio_profiles):
    if 'movieFile' in movie:
        # Detect file separator
        if movie['path'][0] == "/":
            separator = "/"
        else:
            separator = "\\"

        try:
            overview = str(movie['overview'])
        except Exception:
            overview = ""
        try:
            poster_big = movie['images'][0]['url']
            poster = os.path.splitext(poster_big)[0] + '-500' + os.path.splitext(poster_big)[1]
        except Exception:
            poster = ""
        try:
            fanart = movie['images'][1]['url']
        except Exception:
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
        except Exception:
            format = movie['movieFile']['quality']['quality']['name']
            try:
                resolution = str(movie['movieFile']['quality']['quality']['resolution']) + 'p'
            except Exception:
                resolution = None

        if 'mediaInfo' in movie['movieFile']:
            videoFormat = videoCodecID = videoCodecLibrary = None
            if get_radarr_info.is_legacy():
                if 'videoFormat' in movie['movieFile']['mediaInfo']:
                    videoFormat = movie['movieFile']['mediaInfo']['videoFormat']
            else:
                if 'videoCodec' in movie['movieFile']['mediaInfo']:
                    videoFormat = movie['movieFile']['mediaInfo']['videoCodec']
            if 'videoCodecID' in movie['movieFile']['mediaInfo']:
                videoCodecID = movie['movieFile']['mediaInfo']['videoCodecID']
            if 'videoCodecLibrary' in movie['movieFile']['mediaInfo']:
                videoCodecLibrary = movie['movieFile']['mediaInfo']['videoCodecLibrary']
            videoCodec = RadarrFormatVideoCodec(videoFormat, videoCodecID, videoCodecLibrary)

            audioFormat = audioCodecID = audioProfile = audioAdditionalFeatures = None
            if get_radarr_info.is_legacy():
                if 'audioFormat' in movie['movieFile']['mediaInfo']:
                    audioFormat = movie['movieFile']['mediaInfo']['audioFormat']
            else:
                if 'audioCodec' in movie['movieFile']['mediaInfo']:
                    audioFormat = movie['movieFile']['mediaInfo']['audioCodec']
            if 'audioCodecID' in movie['movieFile']['mediaInfo']:
                audioCodecID = movie['movieFile']['mediaInfo']['audioCodecID']
            if 'audioProfile' in movie['movieFile']['mediaInfo']:
                audioProfile = movie['movieFile']['mediaInfo']['audioProfile']
            if 'audioAdditionalFeatures' in movie['movieFile']['mediaInfo']:
                audioAdditionalFeatures = movie['movieFile']['mediaInfo']['audioAdditionalFeatures']
            audioCodec = RadarrFormatAudioCodec(audioFormat, audioCodecID, audioProfile, audioAdditionalFeatures)
        else:
            videoCodec = None
            audioCodec = None

        audio_language = embedded_audio_reader(path_mappings.path_replace_movie(movie['movieFile']['path']),
                                               file_size=movie['movieFile']['size'],
                                               movie_file_id=movie['movieFile']['id'],
                                               use_cache=True)

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


def profile_id_to_language(id, profiles):
    for profile in profiles:
        profiles_to_return = []
        if id == profile[0]:
            profiles_to_return.append(profile[1])
    return profiles_to_return

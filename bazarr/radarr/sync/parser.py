# coding=utf-8

import os

from radarr.info import get_radarr_info
from languages.get_languages import language_from_alpha2

from .converter import RadarrFormatAudioCodec, RadarrFormatVideoCodec


def movieParser(movie, action, tags_dict, movie_default_profile, audio_profiles):
    if 'movieFile' not in movie:
        return
        # Detect file separator
    separator = "/" if movie['path'][0] == "/" else "\\"
    try:
        overview = str(movie['overview'])
    except Exception:
        overview = ""
    try:
        poster_big = movie['images'][0]['url']
        poster = f'{os.path.splitext(poster_big)[0]}-500{os.path.splitext(poster_big)[1]}'

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
    elif 'alternateTitles' in movie:
        alternativeTitles = str([item['title'] for item in movie['alternateTitles']])

    imdbId = movie['imdbId'] if 'imdbId' in movie else None
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
        elif 'videoCodec' in movie['movieFile']['mediaInfo']:
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
        elif 'audioCodec' in movie['movieFile']['mediaInfo']:
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

    audio_language = []
    if get_radarr_info.is_legacy():
        if 'mediaInfo' in movie['movieFile'] and 'audioLanguages' in movie['movieFile']['mediaInfo']:
            audio_languages_list = movie['movieFile']['mediaInfo']['audioLanguages'].split('/')
            if len(audio_languages_list):
                audio_language.extend(audio_language_list.strip() for audio_language_list in audio_languages_list)

        if not audio_language:
            audio_language = profile_id_to_language(movie['qualityProfileId'], audio_profiles)
    elif 'languages' in movie['movieFile'] and len(movie['movieFile']['languages']):
        for item in movie['movieFile']['languages']:
            if isinstance(item, dict) and 'name' in item:
                language = item['name']
                if language == 'Portuguese (Brazil)':
                    language = language_from_alpha2('pb')
                audio_language.append(language)

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

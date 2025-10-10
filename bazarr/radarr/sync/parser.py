# coding=utf-8

import os

from app.config import settings
from languages.get_languages import audio_language_from_name
from radarr.info import get_radarr_info
from utilities.video_analyzer import embedded_audio_reader
from utilities.path_mappings import path_mappings

from .converter import RadarrFormatAudioCodec, RadarrFormatVideoCodec


def get_matching_profile(tags, language_profiles):
    matching_profile = None
    if len(tags) > 0:
        for profileId, name, tag in language_profiles:
            if tag in tags:
                matching_profile = profileId
                break
    return matching_profile


def movieParser(movie, action, tags_dict, language_profiles, movie_default_profile, audio_profiles):
    if 'movieFile' in movie:
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
                resolution = f'{movie["movieFile"]["quality"]["quality"]["resolution"]}p'
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

        if settings.general.parse_embedded_audio_track:
            audio_language = embedded_audio_reader(path_mappings.path_replace_movie(movie['movieFile']['path']),
                                                   file_size=movie['movieFile']['size'],
                                                   movie_file_id=movie['movieFile']['id'],
                                                   use_cache=True)
        else:
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
                        if isinstance(item, dict) and 'name' in item:
                                language = audio_language_from_name(item['name'])
                                audio_language.append(language)

        tags = [d['label'] for d in tags_dict if d['id'] in movie['tags']]

        parsed_movie = {'radarrId': int(movie["id"]),
                        'title': movie["title"],
                        'path': movie['movieFile']['path'],
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

        if action == 'insert':
            parsed_movie['subtitles'] = '[]'
            parsed_movie['profileId'] = movie_default_profile

        if settings.general.movie_tag_enabled:
            tag_profile = get_matching_profile(tags, language_profiles)
            if tag_profile:
                parsed_movie['profileId'] = tag_profile
            remove_profile_tags_list = settings.general.remove_profile_tags
            if len(remove_profile_tags_list) > 0:
                if set(tags) & set(remove_profile_tags_list):
                    parsed_movie['profileId'] = None

        return parsed_movie


def profile_id_to_language(id, profiles):
    profiles_to_return = []
    for profile in profiles:
        if id == profile[0]:
            profiles_to_return.append(profile[1])
    return profiles_to_return

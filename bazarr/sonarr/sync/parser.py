# coding=utf-8

import os

from app.config import settings
from app.database import TableShows
from utilities.path_mappings import path_mappings
from utilities.video_analyzer import embedded_audio_reader
from sonarr.info import get_sonarr_info

from .converter import SonarrFormatVideoCodec, SonarrFormatAudioCodec


def seriesParser(show, action, tags_dict, serie_default_profile, audio_profiles):
    overview = show['overview'] if 'overview' in show else ''
    poster = ''
    fanart = ''
    for image in show['images']:
        if image['coverType'] == 'poster':
            poster_big = image['url'].split('?')[0]
            poster = os.path.splitext(poster_big)[0] + '-250' + os.path.splitext(poster_big)[1]

        if image['coverType'] == 'fanart':
            fanart = image['url'].split('?')[0]

    alternate_titles = None
    if show['alternateTitles'] is not None:
        alternate_titles = str([item['title'] for item in show['alternateTitles']])

    tags = [d['label'] for d in tags_dict if d['id'] in show['tags']]

    imdbId = show['imdbId'] if 'imdbId' in show else None

    audio_language = []
    if not settings.general.getboolean('parse_embedded_audio_track'):
        if get_sonarr_info.is_legacy():
            audio_language = profile_id_to_language(show['qualityProfileId'], audio_profiles)
        else:
            if 'languageProfileId' in show:
                audio_language = profile_id_to_language(show['languageProfileId'], audio_profiles)
            else:
                audio_language = []

    if action == 'update':
        return {'title': show["title"],
                'path': show["path"],
                'tvdbId': int(show["tvdbId"]),
                'sonarrSeriesId': int(show["id"]),
                'overview': overview,
                'poster': poster,
                'fanart': fanart,
                'audio_language': str(audio_language),
                'sortTitle': show['sortTitle'],
                'year': str(show['year']),
                'alternativeTitles': alternate_titles,
                'tags': str(tags),
                'seriesType': show['seriesType'],
                'imdbId': imdbId,
                'monitored': str(bool(show['monitored']))}
    else:
        return {'title': show["title"],
                'path': show["path"],
                'tvdbId': show["tvdbId"],
                'sonarrSeriesId': show["id"],
                'overview': overview,
                'poster': poster,
                'fanart': fanart,
                'audio_language': str(audio_language),
                'sortTitle': show['sortTitle'],
                'year': str(show['year']),
                'alternativeTitles': alternate_titles,
                'tags': str(tags),
                'seriesType': show['seriesType'],
                'imdbId': imdbId,
                'profileId': serie_default_profile,
                'monitored': str(bool(show['monitored']))}


def profile_id_to_language(id_, profiles):
    profiles_to_return = []
    for profile in profiles:
        if id_ == profile[0]:
            profiles_to_return.append(profile[1])
    return profiles_to_return


def episodeParser(episode):
    if 'hasFile' in episode:
        if episode['hasFile'] is True:
            if 'episodeFile' in episode:
                try:
                    bazarr_file_size = os.path.getsize(path_mappings.path_replace(episode['episodeFile']['path']))
                except OSError:
                    bazarr_file_size = 0
                if episode['episodeFile']['size'] > 20480 or bazarr_file_size > 20480:
                    if 'sceneName' in episode['episodeFile']:
                        sceneName = episode['episodeFile']['sceneName']
                    else:
                        sceneName = None

                    if settings.general.getboolean('parse_embedded_audio_track'):
                        audio_language = embedded_audio_reader(path_mappings.path_replace(episode['episodeFile']
                                                                                          ['path']),
                                                               file_size=episode['episodeFile']['size'],
                                                               episode_file_id=episode['episodeFile']['id'],
                                                               use_cache=True)
                    else:
                        audio_language = []
                        if 'language' in episode['episodeFile'] and len(episode['episodeFile']['language']):
                            item = episode['episodeFile']['language']
                            if isinstance(item, dict):
                                if 'name' in item:
                                    audio_language.append(item['name'])
                        elif 'languages' in episode['episodeFile'] and len(episode['episodeFile']['languages']):
                            items = episode['episodeFile']['languages']
                            if isinstance(items, list):
                                for item in items:
                                    if 'name' in item:
                                        audio_language.append(item['name'])
                        else:
                            audio_language = TableShows.get(
                                TableShows.sonarrSeriesId == episode['seriesId']).audio_language

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
                            'sceneName': sceneName,
                            'monitored': str(bool(episode['monitored'])),
                            'format': video_format,
                            'resolution': video_resolution,
                            'video_codec': videoCodec,
                            'audio_codec': audioCodec,
                            'episode_file_id': episode['episodeFile']['id'],
                            'audio_language': str(audio_language),
                            'file_size': episode['episodeFile']['size']}
    return

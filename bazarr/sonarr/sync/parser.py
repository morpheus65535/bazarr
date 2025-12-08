# coding=utf-8

import os

from dateutil import parser

from app.config import settings
from app.database import TableShows, database, select
from constants import MINIMUM_VIDEO_SIZE
from languages.get_languages import audio_language_from_name
from utilities.path_mappings import path_mappings
from utilities.video_analyzer import embedded_audio_reader
from sonarr.info import get_sonarr_info

from .converter import SonarrFormatVideoCodec, SonarrFormatAudioCodec


def get_matching_profile(tags, language_profiles):
    matching_profile = None
    if len(tags) > 0:
        for profileId, name, tag in language_profiles:
            if tag in tags:
                matching_profile = profileId
                break
    return matching_profile


def seriesParser(show, action, tags_dict, language_profiles, serie_default_profile, audio_profiles):
    overview = show['overview'] if 'overview' in show else ''
    poster = ''
    fanart = ''
    for image in show['images']:
        if image['coverType'] == 'poster':
            poster_big = image['url'].split('?')[0]
            poster = f'{os.path.splitext(poster_big)[0]}-250{os.path.splitext(poster_big)[1]}'

        if image['coverType'] == 'fanart':
            fanart = image['url'].split('?')[0]

    if show['alternateTitles'] is not None:
        alternate_titles = [item['title'] for item in show['alternateTitles'] if 'title' in item and item['title'] not
                            in [None, ''] and item["title"] != show["title"]]
    else:
        alternate_titles = []

    tags = [d['label'] for d in tags_dict if d['id'] in show['tags']]

    imdbId = show['imdbId'] if 'imdbId' in show else None

    ended = 'True' if 'ended' in show and show['ended'] else 'False'

    lastAired = parser.parse(show['lastAired']).strftime("%Y-%m-%d") if 'lastAired' in show and show['lastAired'] else None

    audio_language = []
    if not settings.general.parse_embedded_audio_track:
        if get_sonarr_info.is_legacy():
            audio_language = profile_id_to_language(show['qualityProfileId'], audio_profiles)
        else:
            if 'languageProfileId' in show:
                audio_language = profile_id_to_language(show['languageProfileId'], audio_profiles)
            else:
                audio_language = []

    parsed_series = {
        'title': show["title"],
        'path': show["path"],
        'tvdbId': int(show["tvdbId"]),
        'sonarrSeriesId': int(show["id"]),
        'overview': overview,
        'poster': poster,
        'fanart': fanart,
        'audio_language': str(audio_language),
        'sortTitle': show['sortTitle'],
        'year': str(show['year']),
        'alternativeTitles': str(alternate_titles),
        'tags': str(tags),
        'seriesType': show['seriesType'],
        'imdbId': imdbId,
        'monitored': str(bool(show['monitored'])),
        'ended': ended,
        'lastAired': lastAired,
    }

    if action == 'insert':
        parsed_series['profileId'] = serie_default_profile
    
    if settings.general.serie_tag_enabled:
        tag_profile = get_matching_profile(tags, language_profiles)
        if tag_profile:
            parsed_series['profileId'] = tag_profile
        remove_profile_tags_list = settings.general.remove_profile_tags
        if len(remove_profile_tags_list) > 0:
            if set(tags) & set(remove_profile_tags_list):
                parsed_series['profileId'] = None

    return parsed_series


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
                if episode['episodeFile']['size'] > MINIMUM_VIDEO_SIZE or bazarr_file_size > MINIMUM_VIDEO_SIZE:
                    if 'sceneName' in episode['episodeFile']:
                        sceneName = episode['episodeFile']['sceneName']
                    else:
                        sceneName = None

                    if settings.general.parse_embedded_audio_track:
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
                                if isinstance(item, dict) and 'name' in item:
                                    audio_language.append(audio_language_from_name(item['name']))
                        elif 'languages' in episode['episodeFile'] and len(episode['episodeFile']['languages']):
                            items = episode['episodeFile']['languages']
                            if isinstance(items, list):
                                for item in items:
                                    if isinstance(item, dict) and 'name' in item:
                                        audio_language.append(audio_language_from_name(item['name']))
                        else:
                            audio_language = database.execute(
                                select(TableShows.audio_language)
                                .where(TableShows.sonarrSeriesId == episode['seriesId']))\
                                .first().audio_language

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
                            video_resolution = f'{episode["episodeFile"]["quality"]["quality"]["resolution"]}p'
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
                            'file_size': episode['episodeFile']['size'],
                            'absoluteEpisode': episode.get('absoluteEpisodeNumber')}

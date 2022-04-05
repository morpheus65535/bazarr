# coding=utf-8

import os
import logging
import requests

from .utils import headers
from .converter import SonarrFormatVideoCodec, SonarrFormatAudioCodec
from bazarr.database import TableShows
from bazarr.sonarr.info import get_sonarr_info


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

    audio_language = []
    if get_sonarr_info.is_legacy():
        audio_language = profile_id_to_language(show['qualityProfileId'], audio_profiles)
    else:
        audio_language = profile_id_to_language(show['languageProfileId'], audio_profiles)

    tags = [d['label'] for d in tags_dict if d['id'] in show['tags']]

    imdbId = show['imdbId'] if 'imdbId' in show else None

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
                'alternateTitles': alternate_titles,
                'tags': str(tags),
                'seriesType': show['seriesType'],
                'imdbId': imdbId}
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
                'alternateTitles': alternate_titles,
                'tags': str(tags),
                'seriesType': show['seriesType'],
                'imdbId': imdbId,
                'profileId': serie_default_profile}


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
                if episode['episodeFile']['size'] > 20480:
                    if 'sceneName' in episode['episodeFile']:
                        sceneName = episode['episodeFile']['sceneName']
                    else:
                        sceneName = None

                    audio_language = []
                    if 'language' in episode['episodeFile'] and len(episode['episodeFile']['language']):
                        item = episode['episodeFile']['language']
                        if isinstance(item, dict):
                            if 'name' in item:
                                audio_language.append(item['name'])
                    else:
                        audio_language = TableShows.get(TableShows.sonarrSeriesId == episode['seriesId']).audio_language

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
                            'scene_name': sceneName,
                            'monitored': str(bool(episode['monitored'])),
                            'format': video_format,
                            'resolution': video_resolution,
                            'video_codec': videoCodec,
                            'audio_codec': audioCodec,
                            'episode_file_id': episode['episodeFile']['id'],
                            'audio_language': str(audio_language),
                            'file_size': episode['episodeFile']['size']}


def get_series_from_sonarr_api(series_id, url, apikey_sonarr):
    if series_id:
        url_sonarr_api_series = url + "/api/{0}series/{1}?apikey={2}".format(
            '' if get_sonarr_info.is_legacy() else 'v3/', series_id, apikey_sonarr)
    else:
        url_sonarr_api_series = url + "/api/{0}series?apikey={1}".format(
            '' if get_sonarr_info.is_legacy() else 'v3/', apikey_sonarr)
    try:
        r = requests.get(url_sonarr_api_series, timeout=60, verify=False, headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code:
            raise requests.exceptions.HTTPError
        logging.exception("BAZARR Error trying to get series from Sonarr. Http error.")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get series from Sonarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get series from Sonarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get series from Sonarr.")
        return
    else:
        series_json = []
        if series_id:
            series_json.append(r.json())
        else:
            series_json = r.json()
        series_list = []
        for series in series_json:
            series_list.append({'sonarrSeriesId': series['id'], 'title': series['title']})
        return series_list

# coding=utf-8

import ast

from functools import wraps
from flask import request, abort
from operator import itemgetter

from config import settings, base_url
from get_languages import language_from_alpha2, alpha3_from_alpha2
from database import get_audio_profile_languages, get_desired_languages
from helper import path_mappings

None_Keys = ['null', 'undefined', '', None]

False_Keys = ['False', 'false', '0']


def authenticate(actual_method):
    @wraps(actual_method)
    def wrapper(*args, **kwargs):
        apikey_settings = settings.auth.apikey
        apikey_get = request.args.get('apikey')
        apikey_post = request.form.get('apikey')
        apikey_header = None
        if 'X-API-KEY' in request.headers:
            apikey_header = request.headers['X-API-KEY']

        if apikey_settings in [apikey_get, apikey_post, apikey_header]:
            return actual_method(*args, **kwargs)

        return abort(401)

    return wrapper


def postprocess(item):
    # Remove ffprobe_cache
    if 'ffprobe_cache' in item:
        del (item['ffprobe_cache'])

    # Parse tags
    if 'tags' in item:
        if item['tags'] is None:
            item['tags'] = []
        else:
            item['tags'] = ast.literal_eval(item['tags'])

    if 'monitored' in item:
        if item['monitored'] is None:
            item['monitored'] = False
        else:
            item['monitored'] = item['monitored'] == 'True'

    if 'hearing_impaired' in item and item['hearing_impaired'] is not None:
        if item['hearing_impaired'] is None:
            item['hearing_impaired'] = False
        else:
            item['hearing_impaired'] = item['hearing_impaired'] == 'True'

    if 'language' in item:
        if item['language'] == 'None':
            item['language'] = None
        elif item['language'] is not None:
            splitted_language = item['language'].split(':')
            item['language'] = {"name": language_from_alpha2(splitted_language[0]),
                                "code2": splitted_language[0],
                                "code3": alpha3_from_alpha2(splitted_language[0]),
                                "forced": True if item['language'].endswith(':forced') else False,
                                "hi": True if item['language'].endswith(':hi') else False}


def postprocessSeries(item):
    postprocess(item)
    # Parse audio language
    if 'audio_language' in item and item['audio_language'] is not None:
        item['audio_language'] = get_audio_profile_languages(series_id=item['sonarrSeriesId'])

    if 'alternateTitles' in item:
        if item['alternateTitles'] is None:
            item['alternativeTitles'] = []
        else:
            item['alternativeTitles'] = ast.literal_eval(item['alternateTitles'])
        del item["alternateTitles"]

    # Parse seriesType
    if 'seriesType' in item and item['seriesType'] is not None:
        item['seriesType'] = item['seriesType'].capitalize()

    if 'path' in item:
        item['path'] = path_mappings.path_replace(item['path'])

    # map poster and fanart to server proxy
    if 'poster' in item:
        poster = item['poster']
        item['poster'] = f"{base_url}/images/series{poster}" if poster else None

    if 'fanart' in item:
        fanart = item['fanart']
        item['fanart'] = f"{base_url}/images/series{fanart}" if fanart else None


def postprocessEpisode(item):
    postprocess(item)
    if 'audio_language' in item and item['audio_language'] is not None:
        item['audio_language'] = get_audio_profile_languages(episode_id=item['sonarrEpisodeId'])

    if 'subtitles' in item:
        if item['subtitles'] is None:
            raw_subtitles = []
        else:
            raw_subtitles = ast.literal_eval(item['subtitles'])
        subtitles = []

        for subs in raw_subtitles:
            subtitle = subs[0].split(':')
            sub = {"name": language_from_alpha2(subtitle[0]),
                   "code2": subtitle[0],
                   "code3": alpha3_from_alpha2(subtitle[0]),
                   "path": path_mappings.path_replace(subs[1]),
                   "forced": False,
                   "hi": False}
            if len(subtitle) > 1:
                sub["forced"] = True if subtitle[1] == 'forced' else False
                sub["hi"] = True if subtitle[1] == 'hi' else False

            subtitles.append(sub)

        item.update({"subtitles": subtitles})

    # Parse missing subtitles
    if 'missing_subtitles' in item:
        if item['missing_subtitles'] is None:
            item['missing_subtitles'] = []
        else:
            item['missing_subtitles'] = ast.literal_eval(item['missing_subtitles'])
        for i, subs in enumerate(item['missing_subtitles']):
            subtitle = subs.split(':')
            item['missing_subtitles'][i] = {"name": language_from_alpha2(subtitle[0]),
                                            "code2": subtitle[0],
                                            "code3": alpha3_from_alpha2(subtitle[0]),
                                            "forced": False,
                                            "hi": False}
            if len(subtitle) > 1:
                item['missing_subtitles'][i].update({
                    "forced": True if subtitle[1] == 'forced' else False,
                    "hi": True if subtitle[1] == 'hi' else False
                })

    if 'scene_name' in item:
        item["sceneName"] = item["scene_name"]
        del item["scene_name"]

    if 'path' in item and item['path']:
        # Provide mapped path
        item['path'] = path_mappings.path_replace(item['path'])


# TODO: Move
def postprocessMovie(item):
    postprocess(item)
    # Parse audio language
    if 'audio_language' in item and item['audio_language'] is not None:
        item['audio_language'] = get_audio_profile_languages(movie_id=item['radarrId'])

    # Parse alternate titles
    if 'alternativeTitles' in item:
        if item['alternativeTitles'] is None:
            item['alternativeTitles'] = []
        else:
            item['alternativeTitles'] = ast.literal_eval(item['alternativeTitles'])

    # Parse failed attempts
    if 'failedAttempts' in item:
        if item['failedAttempts']:
            item['failedAttempts'] = ast.literal_eval(item['failedAttempts'])

    # Parse subtitles
    if 'subtitles' in item:
        if item['subtitles'] is None:
            item['subtitles'] = []
        else:
            item['subtitles'] = ast.literal_eval(item['subtitles'])
        for i, subs in enumerate(item['subtitles']):
            language = subs[0].split(':')
            item['subtitles'][i] = {"path": path_mappings.path_replace_movie(subs[1]),
                                    "name": language_from_alpha2(language[0]),
                                    "code2": language[0],
                                    "code3": alpha3_from_alpha2(language[0]),
                                    "forced": False,
                                    "hi": False}
            if len(language) > 1:
                item['subtitles'][i].update({
                    "forced": True if language[1] == 'forced' else False,
                    "hi": True if language[1] == 'hi' else False
                })

        if settings.general.getboolean('embedded_subs_show_desired'):
            desired_lang_list = get_desired_languages(item['profileId'])
            item['subtitles'] = [x for x in item['subtitles'] if x['code2'] in desired_lang_list or x['path']]

        if item['subtitles']:
            item['subtitles'] = sorted(item['subtitles'], key=itemgetter('name', 'forced'))

    # Parse missing subtitles
    if 'missing_subtitles' in item:
        if item['missing_subtitles'] is None:
            item['missing_subtitles'] = []
        else:
            item['missing_subtitles'] = ast.literal_eval(item['missing_subtitles'])
        for i, subs in enumerate(item['missing_subtitles']):
            language = subs.split(':')
            item['missing_subtitles'][i] = {"name": language_from_alpha2(language[0]),
                                            "code2": language[0],
                                            "code3": alpha3_from_alpha2(language[0]),
                                            "forced": False,
                                            "hi": False}
            if len(language) > 1:
                item['missing_subtitles'][i].update({
                    "forced": True if language[1] == 'forced' else False,
                    "hi": True if language[1] == 'hi' else False
                })

    # Provide mapped path
    if 'path' in item:
        if item['path']:
            item['path'] = path_mappings.path_replace_movie(item['path'])

    if 'subtitles_path' in item:
        # Provide mapped subtitles path
        item['subtitles_path'] = path_mappings.path_replace_movie(item['subtitles_path'])

    # map poster and fanart to server proxy
    if 'poster' in item:
        poster = item['poster']
        item['poster'] = f"{base_url}/images/movies{poster}" if poster else None

    if 'fanart' in item:
        fanart = item['fanart']
        item['fanart'] = f"{base_url}/images/movies{fanart}" if fanart else None

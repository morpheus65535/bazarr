# coding=utf-8

import ast

from functools import wraps
from flask import request, abort
from operator import itemgetter

from app.config import settings, base_url
from languages.get_languages import language_from_alpha2, alpha3_from_alpha2
from app.database import get_audio_profile_languages, get_desired_languages
from utilities.path_mappings import path_mappings

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
    if item.get('radarrId'):
        path_replace = path_mappings.path_replace_movie
    else:
        path_replace = path_mappings.path_replace
    if item.get('ffprobe_cache'):
        del item['ffprobe_cache']

    # Parse audio language
    if item.get('audio_language'):
        item['audio_language'] = get_audio_profile_languages(item['audio_language'])

    # Make sure profileId is a valid None value
    if item.get('profileId') in None_Keys:
        item['profileId'] = None

    # Parse alternate titles
    if item.get('alternativeTitles'):
        item['alternativeTitles'] = ast.literal_eval(item['alternativeTitles'])
    else:
        item['alternativeTitles'] = []

    # Parse subtitles
    if item.get('subtitles'):
        item['subtitles'] = ast.literal_eval(item['subtitles'])
        for i, subs in enumerate(item['subtitles']):
            language = subs[0].split(':')
            file_size = subs[2] if len(subs) > 2 else 0
            item['subtitles'][i] = {"path": path_replace(subs[1]),
                                    "name": language_from_alpha2(language[0]),
                                    "code2": language[0],
                                    "code3": alpha3_from_alpha2(language[0]),
                                    "forced": False,
                                    "hi": False,
                                    "file_size": file_size}
            if len(language) > 1:
                item['subtitles'][i].update(
                    {
                        "forced": language[1].lower() == 'forced',
                        "hi": language[1].lower() == 'hi',
                    }
                )
        if settings.general.embedded_subs_show_desired and item.get('profileId'):
            desired_lang_list = get_desired_languages(item['profileId'])
            item['subtitles'] = [x for x in item['subtitles'] if x['code2'] in desired_lang_list or x['path']]
        item['subtitles'] = sorted(item['subtitles'], key=itemgetter('name', 'forced'))
    else:
        item['subtitles'] = []

    # Parse missing subtitles
    if item.get('missing_subtitles'):
        item['missing_subtitles'] = ast.literal_eval(item['missing_subtitles'])
        for i, subs in enumerate(item['missing_subtitles']):
            language = subs.split(':')
            item['missing_subtitles'][i] = {"name": language_from_alpha2(language[0]),
                                            "code2": language[0],
                                            "code3": alpha3_from_alpha2(language[0]),
                                            "forced": False,
                                            "hi": False}
            if len(language) > 1:
                item['missing_subtitles'][i].update(
                    {
                        "forced": language[1] == 'forced',
                        "hi": language[1] == 'hi',
                    }
                )
    else:
        item['missing_subtitles'] = []

    # Parse tags
    if item.get('tags') is not None:
        item['tags'] = ast.literal_eval(item.get('tags', '[]'))
    else:
        item['tags'] = []
    if item.get('monitored'):
        item['monitored'] = item.get('monitored') == 'True'
    else:
        item['monitored'] = False
    if item.get('hearing_impaired'):
        item['hearing_impaired'] = item.get('hearing_impaired') == 'True'
    else:
        item['hearing_impaired'] = False

    if item.get('language'):
        if item['language'] == 'None':
            item['language'] = None
        if item['language'] is not None:
            splitted_language = item['language'].split(':')
            item['language'] = {
                "name": language_from_alpha2(splitted_language[0]),
                "code2": splitted_language[0],
                "code3": alpha3_from_alpha2(splitted_language[0]),
                "forced": bool(item['language'].endswith(':forced')),
                "hi": bool(item['language'].endswith(':hi')),
            }

    if item.get('path'):
        item['path'] = path_replace(item['path'])

    if item.get('video_path'):
        # Provide mapped video path for history
        item['video_path'] = path_replace(item['video_path'])

    if item.get('subtitles_path'):
        # Provide mapped subtitles path
        item['subtitles_path'] = path_replace(item['subtitles_path'])

    if item.get('external_subtitles'):
        # Provide mapped external subtitles paths for history
        if isinstance(item['external_subtitles'], str):
            item['external_subtitles'] = ast.literal_eval(item['external_subtitles'])
        for i, subs in enumerate(item['external_subtitles']):
            item['external_subtitles'][i] = path_replace(subs)

    # map poster and fanart to server proxy
    if item.get('poster') is not None:
        poster = item['poster']
        item['poster'] = f"{base_url}/images/{'movies' if item.get('radarrId') else 'series'}{poster}" if poster else None

    if item.get('fanart') is not None:
        fanart = item['fanart']
        item['fanart'] = f"{base_url}/images/{'movies' if item.get('radarrId') else 'series'}{fanart}" if fanart else None

    return item

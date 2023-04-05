# coding=utf-8

import ast

from functools import wraps
from flask import request, abort
from operator import itemgetter

from app.config import settings, base_url
from languages.get_languages import language_from_alpha2, alpha3_from_alpha2
from app.database import get_audio_profile_languages, get_desired_languages, Base
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
    # flatten Table object as a single level dictionary
    item_dict = {}
    if not isinstance(item, dict):
        item = item.__dict__
    for key, value in item.items():
        if isinstance(value, Base):
            for child_key, child_value in value.__dict__.items():
                if child_key not in ['_sa_instance_state']:
                    item_dict[child_key] = child_value
        else:
            if key not in ['_sa_instance_state']:
                item_dict[key] = value

    # Remove ffprobe_cache
    if item_dict.get('movie_file_id'):
        path_replace = path_mappings.path_replace_movie
    else:
        path_replace = path_mappings.path_replace
    if item_dict.get('ffprobe_cache'):
        del item_dict['ffprobe_cache']

    # Parse audio language
    if item_dict.get('audio_language'):
        item_dict['audio_language'] = get_audio_profile_languages(item_dict['audio_language'])

    # Make sure profileId is a valid None value
    if item_dict.get('profileId') in None_Keys:
        item_dict['profileId'] = None

    # Parse alternate titles
    if item_dict.get('alternativeTitles'):
        item_dict['alternativeTitles'] = ast.literal_eval(item_dict['alternativeTitles'])
    else:
        item_dict['alternativeTitles'] = []

    # Parse failed attempts
    if item_dict.get('failedAttempts'):
        item_dict['failedAttempts'] = ast.literal_eval(item_dict['failedAttempts'])
    else:
        item_dict['failedAttempts'] = []

    # Parse subtitles
    if item_dict.get('subtitles'):
        item_dict['subtitles'] = ast.literal_eval(item_dict['subtitles'])
        for i, subs in enumerate(item_dict['subtitles']):
            language = subs[0].split(':')
            item_dict['subtitles'][i] = {"path": path_replace(subs[1]),
                                         "name": language_from_alpha2(language[0]),
                                         "code2": language[0],
                                         "code3": alpha3_from_alpha2(language[0]),
                                         "forced": False,
                                         "hi": False}
            if len(language) > 1:
                item_dict['subtitles'][i].update(
                    {
                        "forced": language[1] == 'forced',
                        "hi": language[1] == 'hi',
                    }
                )
        if settings.general.getboolean('embedded_subs_show_desired') and item_dict.get('profileId'):
            desired_lang_list = get_desired_languages(item_dict['profileId'])
            item_dict['subtitles'] = [x for x in item_dict['subtitles'] if x['code2'] in desired_lang_list or x['path']]
        item_dict['subtitles'] = sorted(item_dict['subtitles'], key=itemgetter('name', 'forced'))
    else:
        item_dict['subtitles'] = []

    # Parse missing subtitles
    if item_dict.get('missing_subtitles'):
        item_dict['missing_subtitles'] = ast.literal_eval(item_dict['missing_subtitles'])
        for i, subs in enumerate(item_dict['missing_subtitles']):
            language = subs.split(':')
            item_dict['missing_subtitles'][i] = {"name": language_from_alpha2(language[0]),
                                            "code2": language[0],
                                            "code3": alpha3_from_alpha2(language[0]),
                                            "forced": False,
                                            "hi": False}
            if len(language) > 1:
                item_dict['missing_subtitles'][i].update(
                    {
                        "forced": language[1] == 'forced',
                        "hi": language[1] == 'hi',
                    }
                )
    else:
        item_dict['missing_subtitles'] = []

    # Parse tags
    if item_dict.get('tags') is not None:
        item_dict['tags'] = ast.literal_eval(item_dict.get('tags', '[]'))
    else:
        item_dict['tags'] = []
    if item_dict.get('monitored'):
        item_dict['monitored'] = item_dict.get('monitored') == 'True'
    else:
        item_dict['monitored'] = False
    if item_dict.get('hearing_impaired'):
        item_dict['hearing_impaired'] = item_dict.get('hearing_impaired') == 'True'
    else:
        item_dict['hearing_impaired'] = False

    if item_dict.get('language'):
        if item_dict['language'] == 'None':
            item_dict['language'] = None
        if item_dict['language'] is not None:
            splitted_language = item_dict['language'].split(':')
            item_dict['language'] = {
                "name": language_from_alpha2(splitted_language[0]),
                "code2": splitted_language[0],
                "code3": alpha3_from_alpha2(splitted_language[0]),
                "forced": bool(item_dict['language'].endswith(':forced')),
                "hi": bool(item_dict['language'].endswith(':hi')),
            }

    if item_dict.get('path'):
        item_dict['path'] = path_replace(item_dict['path'])

    if item_dict.get('subtitles_path'):
        # Provide mapped subtitles path
        item_dict['subtitles_path'] = path_replace(item_dict['subtitles_path'])

    # map poster and fanart to server proxy
    if item_dict.get('poster') is not None:
        poster = item_dict['poster']
        item_dict['poster'] = f"{base_url}/images/{'movies' if item_dict.get('movie_file_id') else 'series'}{poster}" if poster else None

    if item_dict.get('fanart') is not None:
        fanart = item_dict['fanart']
        item_dict['fanart'] = f"{base_url}/images/{'movies' if item_dict.get('movie_file_id') else 'series'}{fanart}" if fanart else None

    return item_dict

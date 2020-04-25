# coding=utf-8
import hashlib
import os

from simpleconfigparser import simpleconfigparser

from get_args import args

defaults = {
    'general': {
        'ip': '0.0.0.0',
        'port': '6767',
        'base_url': '',
        'path_mappings': '[]',
        'debug': 'False',
        'branch': 'master',
        'auto_update': 'True',
        'single_language': 'False',
        'minimum_score': '90',
        'use_scenename': 'True',
        'use_postprocessing': 'False',
        'postprocessing_cmd': '',
        'use_sonarr': 'False',
        'use_radarr': 'False',
        'path_mappings_movie': '[]',
        'serie_default_enabled': 'False',
        'serie_default_language': '[]',
        'serie_default_hi': 'False',
        'serie_default_forced': 'False',
        'movie_default_enabled': 'False',
        'movie_default_language': '[]',
        'movie_default_hi': 'False',
        'movie_default_forced': 'False',
        'page_size': '25',
        'page_size_manual_search': '5',
        'minimum_score_movie': '70',
        'use_embedded_subs': 'True',
        'utf8_encode': 'True',
        'ignore_pgs_subs': 'False',
        'adaptive_searching': 'False',
        'enabled_providers': '',
        'throtteled_providers': '{}',
        'multithreading': 'True',
        'chmod_enabled': 'False',
        'chmod': '0640',
        'subfolder': 'current',
        'subfolder_custom': '',
        'update_restart': 'True',
        'upgrade_subs': 'True',
        'upgrade_frequency': '12',
        'days_to_upgrade_subs': '7',
        'upgrade_manual': 'True',
        'anti_captcha_provider': 'None',
        'wanted_search_frequency': '3'
    },
    'auth': {
        'type': 'None',
        'username': '',
        'password': ''
    },
    'sonarr': {
        'ip': '127.0.0.1',
        'port': '8989',
        'base_url': '/',
        'ssl': 'False',
        'apikey': '',
        'full_update': 'Daily',
        'full_update_day': '6',
        'full_update_hour': '4',
        'only_monitored': 'False',
    },
    'radarr': {
        'ip': '127.0.0.1',
        'port': '7878',
        'base_url': '/',
        'ssl': 'False',
        'apikey': '',
        'full_update': 'Daily',
        'full_update_day': '6',
        'full_update_hour': '5',
        'only_monitored': 'False',
    },
    'proxy': {
        'type': 'None',
        'url': '',
        'port': '',
        'username': '',
        'password': '',
        'exclude': 'localhost,127.0.0.1'
    },
    'opensubtitles': {
        'username': '',
        'password': '',
        'use_tag_search': 'False',
        'vip': 'False',
        'ssl': 'False',
        'timeout': '15',
        'skip_wrong_fps': 'False'
    },
    'addic7ed': {
        'username': '',
        'password': '',
        'random_agents': 'True'
    },
    'legendasdivx': {
        'username': '',
        'password': ''
    },
    'legendastv': {
        'username': '',
        'password': ''
    },
    'xsubs': {
        'username': '',
        'password': ''
    },
    'assrt': {
        'token': ''
    },
    'anticaptcha': {
        'anti_captcha_key': ''
    },
    'deathbycaptcha': {
        'username': '',
        'password': ''
    },
    'napisy24': {
        'username': '',
        'password': ''
    },
    'subscene': {
        'username': '',
        'password': ''
    },
    'betaseries': {
        'token': ''
    },
    'analytics': {
        'enabled': 'True'
    },
    'titlovi': {
        'username': '',
        'password': ''
    }
}

settings = simpleconfigparser(defaults=defaults, interpolation=None)
settings.read(os.path.join(args.config_dir, 'config', 'config.ini'))

settings.general.base_url = settings.general.base_url if settings.general.base_url else '/'
base_url = settings.general.base_url


def save_settings(settings_items):
    from database import database
    for key, value in settings_items:
        # Intercept database stored settings
        if key == 'enabled_languages':
            database.execute("UPDATE table_settings_languages SET enabled=0")
            for item in value:
                database.execute("UPDATE table_settings_languages SET enabled=1 WHERE code2=?", (item,))
            continue

        # Make sure that text based form values aren't pass as list
        if isinstance(value, list) and len(value) == 1:
            value = value[0]

        settings_keys = key.split('-')

        if value == 'true':
            value = 'True'
        elif value == 'false':
            value = 'False'

        if key == 'settings-auth-password':
            value = hashlib.md5(value.encode('utf-8')).hexdigest()

        if settings_keys[0] == 'settings':
            settings[settings_keys[1]][settings_keys[2]] = str(value)

    with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
        settings.write(handle)



def url_sonarr():
    if settings.sonarr.getboolean('ssl'):
        protocol_sonarr = "https"
    else:
        protocol_sonarr = "http"

    if settings.sonarr.base_url == '':
        settings.sonarr.base_url = "/"
    if not settings.sonarr.base_url.startswith("/"):
        settings.sonarr.base_url = "/" + settings.sonarr.base_url
    if settings.sonarr.base_url.endswith("/"):
        settings.sonarr.base_url = settings.sonarr.base_url[:-1]

    return protocol_sonarr + "://" + settings.sonarr.ip + ":" + settings.sonarr.port + settings.sonarr.base_url


def url_sonarr_short():
    if settings.sonarr.getboolean('ssl'):
        protocol_sonarr = "https"
    else:
        protocol_sonarr = "http"

    if settings.sonarr.base_url == '':
        settings.sonarr.base_url = "/"
    if not settings.sonarr.base_url.startswith("/"):
        settings.sonarr.base_url = "/" + settings.sonarr.base_url
    if settings.sonarr.base_url.endswith("/"):
        settings.sonarr.base_url = settings.sonarr.base_url[:-1]
    return protocol_sonarr + "://" + settings.sonarr.ip + ":" + settings.sonarr.port


def url_radarr():
    if settings.radarr.getboolean('ssl'):
        protocol_radarr = "https"
    else:
        protocol_radarr = "http"

    if settings.radarr.base_url == '':
        settings.radarr.base_url = "/"
    if not settings.radarr.base_url.startswith("/"):
        settings.radarr.base_url = "/" + settings.radarr.base_url
    if settings.radarr.base_url.endswith("/"):
        settings.radarr.base_url = settings.radarr.base_url[:-1]

    return protocol_radarr + "://" + settings.radarr.ip + ":" + settings.radarr.port + settings.radarr.base_url


def url_radarr_short():
    if settings.radarr.getboolean('ssl'):
        protocol_radarr = "https"
    else:
        protocol_radarr = "http"

    if settings.radarr.base_url == '':
        settings.radarr.base_url = "/"
    if not settings.radarr.base_url.startswith("/"):
        settings.radarr.base_url = "/" + settings.radarr.base_url
    if settings.radarr.base_url.endswith("/"):
        settings.radarr.base_url = settings.radarr.base_url[:-1]

    return protocol_radarr + "://" + settings.radarr.ip + ":" + settings.radarr.port

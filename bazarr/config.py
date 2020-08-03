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
        'postprocessing_threshold': '90',
        'use_postprocessing_threshold': 'False',
        'postprocessing_threshold_movie': '70',
        'use_postprocessing_threshold_movie': 'False',
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
        'page_size_manual_search': '10',
        'minimum_score_movie': '70',
        'use_embedded_subs': 'True',
        'embedded_subs_show_desired': 'True',
        'utf8_encode': 'True',
        'ignore_pgs_subs': 'False',
        'ignore_vobsub_subs': 'False',
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
        'wanted_search_frequency': '3',
        'wanted_search_frequency_movie': '3',
        'subzero_mods': '',
        'dont_notify_manual_actions': 'False'
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
        'series_sync': '1',
        'episodes_sync': '5',
        'excluded_tags': '[]',
        'excluded_series_types': '[]'
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
        'movies_sync': '5',
        'excluded_tags': '[]'
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
        'password': ''
    },
    'legendasdivx': {
        'username': '',
        'password': '',
        'skip_wrong_fps': 'False'
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
    },
    'subsync': {
        'use_subsync': 'False',
        'use_subsync_threshold': 'False',
        'subsync_threshold': '90',
        'use_subsync_movie_threshold': 'False',
        'subsync_movie_threshold': '70'
    }
}

settings = simpleconfigparser(defaults=defaults, interpolation=None)
settings.read(os.path.join(args.config_dir, 'config', 'config.ini'))

settings.general.base_url = settings.general.base_url if settings.general.base_url else '/'
base_url = settings.general.base_url


def save_settings(settings_items):
    from database import database

    configure_debug = False
    configure_captcha = False
    update_schedule = False
    update_path_map = False
    configure_proxy = False

    for key, value in settings_items:
        # Intercept database stored settings
        if key == 'enabled_languages':
            database.execute("UPDATE table_settings_languages SET enabled=0")
            for item in value:
                database.execute("UPDATE table_settings_languages SET enabled=1 WHERE code2=?", (item,))
            continue

        # Make sure that text based form values aren't pass as list unless they are language list
        if isinstance(value, list) and len(value) == 1 and key not in ['settings-general-serie_default_language',
                                                                       'settings-general-movie_default_language']:
            value = value[0]

        # Make sure empty language list are stored correctly due to bug in bootstrap-select
        if key in ['settings-general-serie_default_language', 'settings-general-movie_default_language'] and value == ['null']:
            value = []

        settings_keys = key.split('-')

        if value == 'true':
            value = 'True'
        elif value == 'false':
            value = 'False'

        if key == 'settings-auth-password':
            value = hashlib.md5(value.encode('utf-8')).hexdigest()

        if key == 'settings-general-debug':
            configure_debug = True

        if key in ['settings-general-anti_captcha_provider', 'settings-anticaptcha-anti_captcha_key',
                   'settings-deathbycaptcha-username', 'settings-deathbycaptcha-password']:
            configure_captcha = True

        if key in ['update_schedule', 'settings-general-use_sonarr', 'settings-general-use_radarr',
                   'settings-general-auto_update', 'settings-general-upgrade_subs']:
            update_schedule = True

        if key in ['settings-general-path_mappings', 'settings-general-path_mappings_movie']:
            update_path_map = True

        if key in ['settings-proxy-type', 'settings-proxy-url', 'settings-proxy-port', 'settings-proxy-username',
                   'settings-proxy-password']:
            configure_proxy = True

        if settings_keys[0] == 'settings':
            settings[settings_keys[1]][settings_keys[2]] = str(value)

    with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
        settings.write(handle)

    # Reconfigure Bazarr to reflect changes
    if configure_debug:
        from logger import configure_logging
        configure_logging(settings.general.getboolean('debug') or args.debug)

    if configure_captcha:
        configure_captcha_func()

    if update_schedule:
        from api import scheduler
        scheduler.update_configurable_tasks()

    if update_path_map:
        from helper import path_mappings
        path_mappings.update()

    if configure_proxy:
        configure_proxy_func()


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


def configure_captcha_func():
    # set anti-captcha provider and key
    if settings.general.anti_captcha_provider == 'anti-captcha' and settings.anticaptcha.anti_captcha_key != "":
        os.environ["ANTICAPTCHA_CLASS"] = 'AntiCaptchaProxyLess'
        os.environ["ANTICAPTCHA_ACCOUNT_KEY"] = str(settings.anticaptcha.anti_captcha_key)
    elif settings.general.anti_captcha_provider == 'death-by-captcha' and settings.deathbycaptcha.username != "" and \
            settings.deathbycaptcha.password != "":
        os.environ["ANTICAPTCHA_CLASS"] = 'DeathByCaptchaProxyLess'
        os.environ["ANTICAPTCHA_ACCOUNT_KEY"] = str(':'.join(
            {settings.deathbycaptcha.username, settings.deathbycaptcha.password}))
    else:
        os.environ["ANTICAPTCHA_CLASS"] = ''


def configure_proxy_func():
    if settings.proxy.type != 'None':
        if settings.proxy.username != '' and settings.proxy.password != '':
            proxy = settings.proxy.type + '://' + settings.proxy.username + ':' + settings.proxy.password + '@' + \
                    settings.proxy.url + ':' + settings.proxy.port
        else:
            proxy = settings.proxy.type + '://' + settings.proxy.url + ':' + settings.proxy.port
        os.environ['HTTP_PROXY'] = str(proxy)
        os.environ['HTTPS_PROXY'] = str(proxy)
        os.environ['NO_PROXY'] = str(settings.proxy.exclude)

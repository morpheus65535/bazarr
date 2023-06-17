# coding=utf-8

import hashlib
import os
import ast

from urllib.parse import quote_plus
from subliminal.cache import region
from dynaconf import Dynaconf
from dynaconf.loaders.yaml_loader import write

from .get_args import args


def base_url_slash_cleaner(uri):
    while "//" in uri:
        uri = uri.replace("//", "/")
    return uri


defaults = {
    'general': {
        'ip': '0.0.0.0',
        'port': 6767,
        'base_url': '',
        'path_mappings': [],
        'debug': False,
        'branch': 'master',
        'auto_update': True,
        'single_language': False,
        'minimum_score': 90,
        'use_scenename': True,
        'use_postprocessing': False,
        'postprocessing_cmd': '',
        'postprocessing_threshold': 90,
        'use_postprocessing_threshold': False,
        'postprocessing_threshold_movie': 70,
        'use_postprocessing_threshold_movie': False,
        'use_sonarr': False,
        'use_radarr': False,
        'path_mappings_movie': [],
        'serie_default_enabled': False,
        'serie_default_profile': '',
        'movie_default_enabled': False,
        'movie_default_profile': '',
        'page_size': 25,
        'theme': 'auto',
        'page_size_manual_search': 10,
        'minimum_score_movie': 70,
        'use_embedded_subs': True,
        'embedded_subs_show_desired': True,
        'utf8_encode': True,
        'ignore_pgs_subs': False,
        'ignore_vobsub_subs': False,
        'ignore_ass_subs': False,
        'adaptive_searching': False,
        'adaptive_searching_delay': '3w',
        'adaptive_searching_delta': '1w',
        'enabled_providers': [],
        'multithreading': True,
        'chmod_enabled': False,
        'chmod': '0640',
        'subfolder': 'current',
        'subfolder_custom': '',
        'upgrade_subs': True,
        'upgrade_frequency': 12,
        'days_to_upgrade_subs': 7,
        'upgrade_manual': True,
        'anti_captcha_provider': None,
        'wanted_search_frequency': 6,
        'wanted_search_frequency_movie': 6,
        'subzero_mods': '',
        'dont_notify_manual_actions': False,
        'hi_extension': 'hi',
        'embedded_subtitles_parser': 'ffprobe',
        'default_und_audio_lang': '',
        'default_und_embedded_subtitles_lang': '',
        'parse_embedded_audio_track': False,
        'skip_hashing': False,
        'language_equals': [],
    },
    'auth': {
        'type': None,
        'username': '',
        'password': ''
    },
    'cors': {
        'enabled': False
    },
    'backup': {
        'folder': os.path.join(args.config_dir, 'backup'),
        'retention': 31,
        'frequency': 'Weekly',
        'day': 6,
        'hour': 3
    },
    'sonarr': {
        'ip': '127.0.0.1',
        'port': 8989,
        'base_url': '/',
        'ssl': False,
        'http_timeout': 60,
        'apikey': '',
        'full_update': 'Daily',
        'full_update_day': 6,
        'full_update_hour': 4,
        'only_monitored': False,
        'series_sync': 60,
        'episodes_sync': 60,
        'excluded_tags': [],
        'excluded_series_types': [],
        'use_ffprobe_cache': True,
        'exclude_season_zero': False,
        'defer_search_signalr': False
    },
    'radarr': {
        'ip': '127.0.0.1',
        'port': 7878,
        'base_url': '/',
        'ssl': False,
        'http_timeout': 60,
        'apikey': '',
        'full_update': 'Daily',
        'full_update_day': 6,
        'full_update_hour': 5,
        'only_monitored': False,
        'movies_sync': 60,
        'excluded_tags': [],
        'use_ffprobe_cache': True,
        'defer_search_signalr': False
    },
    'proxy': {
        'type': None,
        'url': '',
        'port': '',
        'username': '',
        'password': '',
        'exclude': ["localhost", "127.0.0.1"]
    },
    'opensubtitles': {
        'username': '',
        'password': '',
        'use_tag_search': False,
        'vip': False,
        'ssl': False,
        'timeout': 15,
        'skip_wrong_fps': False
    },
    'opensubtitlescom': {
        'username': '',
        'password': '',
        'use_hash': True
    },
    'addic7ed': {
        'username': '',
        'password': '',
        'cookies': '',
        'user_agent': '',
        'vip': False
    },
    'podnapisi': {
        'verify_ssl': True
    },
    'subf2m': {
        'verify_ssl': True,
        'user_agent': ''
    },
    'whisperai': {
        'endpoint': 'http://127.0.0.1:9000',
        'timeout': 3600
    },
    'legendasdivx': {
        'username': '',
        'password': '',
        'skip_wrong_fps': False
    },
    'ktuvit': {
        'email': '',
        'hashed_password': ''
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
        'enabled': True
    },
    'titlovi': {
        'username': '',
        'password': ''
    },
    'titulky': {
        'username': '',
        'password': '',
        'approved_only': False
    },
    'embeddedsubtitles': {
        'included_codecs': [],
        'hi_fallback': False,
        'timeout': 600,
        'unknown_as_english': False,
    },
    'karagarga': {
        'username': '',
        'password': '',
        'f_username': '',
        'f_password': '',
    },
    'subsync': {
        'use_subsync': False,
        'use_subsync_threshold': False,
        'subsync_threshold': 90,
        'use_subsync_movie_threshold': False,
        'subsync_movie_threshold': 70,
        'debug': False,
        'force_audio': False
    },
    'series_scores': {
        "hash": 359,
        "series": 180,
        "year": 90,
        "season": 30,
        "episode": 30,
        "release_group": 14,
        "source": 7,
        "audio_codec": 3,
        "resolution": 2,
        "video_codec": 2,
        "streaming_service": 1,
        "hearing_impaired": 1,
    },
    'movie_scores': {
        "hash": 119,
        "title": 60,
        "year": 30,
        "release_group": 13,
        "source": 7,
        "audio_codec": 3,
        "resolution": 2,
        "video_codec": 2,
        "streaming_service": 1,
        "edition": 1,
        "hearing_impaired": 1,
    },
    'postgresql': {
        'enabled': False,
        'host': 'localhost',
        'port': 5432,
        'database': '',
        'username': '',
        'password': '',
    },
}


def convert_ini_to_yaml(config_file):
    import configparser
    import yaml
    config_object = configparser.ConfigParser()
    file = open(config_file, "r")
    config_object.read_file(file)
    output_dict = dict()
    sections = config_object.sections()
    for section in sections:
        items = config_object.items(section)
        output_dict[section] = dict()
        for item in items:
            try:
                output_dict[section].update({item[0]: ast.literal_eval(item[1])})
            except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
                output_dict[section].update({item[0]: item[1]})
    with open(os.path.join(os.path.dirname(config_file), 'config.yaml'), 'w') as file:
        yaml.dump(output_dict, file)


config_yaml_file = os.path.join(args.config_dir, 'config', 'config.yaml')
config_ini_file = os.path.join(args.config_dir, 'config', 'config.ini')
if not os.path.exists(config_yaml_file):
    convert_ini_to_yaml(config_ini_file)

settings = Dynaconf(
    settings_files=config_yaml_file,
)


def write_config():
    write(settings_path=config_yaml_file,
          settings_data={k.lower(): v for k, v in settings.as_dict().items()},
          merge=False)


settings.general.base_url = settings.general.base_url if settings.general.base_url else '/'
base_url = settings.general.base_url.rstrip('/')

array_keys = ['excluded_tags',
              'exclude',
              'included_codecs',
              'subzero_mods',
              'excluded_series_types',
              'enabled_providers',
              'path_mappings',
              'path_mappings_movie',
              'language_equals']

empty_values = ['', 'None', 'null', 'undefined', None, []]

# Increase Sonarr and Radarr sync interval since we now use SignalR feed to update in real time
if int(settings.sonarr.series_sync) < 15:
    settings.sonarr.series_sync = "60"
if int(settings.sonarr.episodes_sync) < 15:
    settings.sonarr.episodes_sync = "60"
if int(settings.radarr.movies_sync) < 15:
    settings.radarr.movies_sync = "60"

# Make sure to get of double slashes in base_url
settings.general.base_url = base_url_slash_cleaner(uri=settings.general.base_url)
settings.sonarr.base_url = base_url_slash_cleaner(uri=settings.sonarr.base_url)
settings.radarr.base_url = base_url_slash_cleaner(uri=settings.radarr.base_url)

# fixing issue with improper page_size value
if settings.general.page_size not in ['25', '50', '100', '250', '500', '1000']:
    settings.general.page_size = defaults['general']['page_size']

# increase delay between searches to reduce impact on providers
if settings.general.wanted_search_frequency == 3:
    settings.general.wanted_search_frequency = 6
if settings.general.wanted_search_frequency_movie == 3:
    settings.general.wanted_search_frequency_movie = 6

# save updated settings to file
write_config()


def get_settings():
    # return {k.lower(): v for k, v in settings.as_dict().items()}
    settings_to_return = {}
    for k, v in settings.as_dict().items():
        k = k.lower()
        settings_to_return[k] = dict({k: v})
        for subk, subv in v.items():
            if subv in empty_values and subk.lower() in array_keys:
                settings_to_return[k].update({subk: []})
            elif subk == 'subzero_mods':
                settings_to_return[k].update({subk: get_array_from(subv)})
            else:
                settings_to_return[k].update({subk: subv})
    return settings_to_return


def save_settings(settings_items):
    configure_debug = False
    configure_captcha = False
    update_schedule = False
    sonarr_changed = False
    radarr_changed = False
    update_path_map = False
    configure_proxy = False
    exclusion_updated = False
    sonarr_exclusion_updated = False
    radarr_exclusion_updated = False
    use_embedded_subs_changed = False
    undefined_audio_track_default_changed = False
    undefined_subtitles_track_default_changed = False
    audio_tracks_parsing_changed = False

    # Subzero Mods
    update_subzero = False
    subzero_mods = get_array_from(settings.general.subzero_mods)

    if len(subzero_mods) == 1 and subzero_mods[0] == '':
        subzero_mods = []

    for key, value in settings_items:

        settings_keys = key.split('-')

        # Make sure that text based form values aren't pass as list
        if isinstance(value, list) and len(value) == 1 and settings_keys[-1] not in array_keys:
            value = value[0]
            if value in empty_values and value != '':
                value = None

        # Make sure empty language list are stored correctly
        if settings_keys[-1] in array_keys and value[0] in empty_values:
            value = []

        if value == 'true':
            value = True
        elif value == 'false':
            value = False

        if key in ['settings-general-use_embedded_subs', 'settings-general-ignore_pgs_subs',
                   'settings-general-ignore_vobsub_subs', 'settings-general-ignore_ass_subs']:
            use_embedded_subs_changed = True

        if key == 'settings-general-default_und_audio_lang':
            undefined_audio_track_default_changed = True

        if key == 'settings-general-parse_embedded_audio_track':
            audio_tracks_parsing_changed = True

        if key == 'settings-general-default_und_embedded_subtitles_lang':
            undefined_subtitles_track_default_changed = True

        if key in ['settings-general-base_url', 'settings-sonarr-base_url', 'settings-radarr-base_url']:
            value = base_url_slash_cleaner(value)

        if key == 'settings-auth-password':
            if value != settings.auth.password and value is not None:
                value = hashlib.md5(value.encode('utf-8')).hexdigest()

        if key == 'settings-general-debug':
            configure_debug = True

        if key == 'settings-general-hi_extension':
            os.environ["SZ_HI_EXTENSION"] = str(value)

        if key in ['settings-general-anti_captcha_provider', 'settings-anticaptcha-anti_captcha_key',
                   'settings-deathbycaptcha-username', 'settings-deathbycaptcha-password']:
            configure_captcha = True

        if key in ['update_schedule', 'settings-general-use_sonarr', 'settings-general-use_radarr',
                   'settings-general-auto_update', 'settings-general-upgrade_subs',
                   'settings-sonarr-series_sync', 'settings-sonarr-episodes_sync', 'settings-radarr-movies_sync',
                   'settings-sonarr-full_update', 'settings-sonarr-full_update_day', 'settings-sonarr-full_update_hour',
                   'settings-radarr-full_update', 'settings-radarr-full_update_day', 'settings-radarr-full_update_hour',
                   'settings-general-wanted_search_frequency', 'settings-general-wanted_search_frequency_movie',
                   'settings-general-upgrade_frequency', 'settings-backup-frequency', 'settings-backup-day',
                   'settings-backup-hour']:
            update_schedule = True

        if key in ['settings-general-use_sonarr', 'settings-sonarr-ip', 'settings-sonarr-port',
                   'settings-sonarr-base_url', 'settings-sonarr-ssl', 'settings-sonarr-apikey']:
            sonarr_changed = True

        if key in ['settings-general-use_radarr', 'settings-radarr-ip', 'settings-radarr-port',
                   'settings-radarr-base_url', 'settings-radarr-ssl', 'settings-radarr-apikey']:
            radarr_changed = True

        if key in ['settings-general-path_mappings', 'settings-general-path_mappings_movie']:
            update_path_map = True

        if key in ['settings-proxy-type', 'settings-proxy-url', 'settings-proxy-port', 'settings-proxy-username',
                   'settings-proxy-password']:
            configure_proxy = True

        if key in ['settings-sonarr-excluded_tags', 'settings-sonarr-only_monitored',
                   'settings-sonarr-excluded_series_types', 'settings-sonarr-exclude_season_zero',
                   'settings.radarr.excluded_tags', 'settings-radarr-only_monitored']:
            exclusion_updated = True

        if key in ['settings-sonarr-excluded_tags', 'settings-sonarr-only_monitored',
                   'settings-sonarr-excluded_series_types', 'settings-sonarr-exclude_season_zero']:
            sonarr_exclusion_updated = True

        if key in ['settings.radarr.excluded_tags', 'settings-radarr-only_monitored']:
            radarr_exclusion_updated = True

        if key == 'settings-addic7ed-username':
            if key != settings.addic7ed.username:
                region.delete('addic7ed_data')
        elif key == 'settings-addic7ed-password':
            if key != settings.addic7ed.password:
                region.delete('addic7ed_data')

        if key == 'settings-legendasdivx-username':
            if key != settings.legendasdivx.username:
                region.delete('legendasdivx_cookies2')
        elif key == 'settings-legendasdivx-password':
            if key != settings.legendasdivx.password:
                region.delete('legendasdivx_cookies2')

        if key == 'settings-opensubtitles-username':
            if key != settings.opensubtitles.username:
                region.delete('os_token')
        elif key == 'settings-opensubtitles-password':
            if key != settings.opensubtitles.password:
                region.delete('os_token')

        if key == 'settings-opensubtitlescom-username':
            if key != settings.opensubtitlescom.username:
                region.delete('oscom_token')
        elif key == 'settings-opensubtitlescom-password':
            if key != settings.opensubtitlescom.password:
                region.delete('oscom_token')

        if key == 'settings-subscene-username':
            if key != settings.subscene.username:
                region.delete('subscene_cookies2')
        elif key == 'settings-subscene-password':
            if key != settings.subscene.password:
                region.delete('subscene_cookies2')

        if key == 'settings-titlovi-username':
            if key != settings.titlovi.username:
                region.delete('titlovi_token')
        elif key == 'settings-titlovi-password':
            if key != settings.titlovi.password:
                region.delete('titlovi_token')

        if settings_keys[0] == 'settings':
            settings[settings_keys[1]][settings_keys[2]] = value

        if settings_keys[0] == 'subzero':
            mod = settings_keys[1]
            if mod in subzero_mods and not value:
                subzero_mods.remove(mod)
            elif value:
                subzero_mods.append(mod)

            # Handle color
            if mod == 'color':
                previous = None
                for exist_mod in subzero_mods:
                    if exist_mod.startswith('color'):
                        previous = exist_mod
                        break
                if previous is not None:
                    subzero_mods.remove(previous)
                if value not in empty_values:
                    subzero_mods.append(value)

            update_subzero = True

    if use_embedded_subs_changed or undefined_audio_track_default_changed:
        from .scheduler import scheduler
        from subtitles.indexer.series import list_missing_subtitles
        from subtitles.indexer.movies import list_missing_subtitles_movies
        if settings.general.use_sonarr:
            scheduler.add_job(list_missing_subtitles, kwargs={'send_event': True})
        if settings.general.use_radarr:
            scheduler.add_job(list_missing_subtitles_movies, kwargs={'send_event': True})

    if undefined_subtitles_track_default_changed:
        from .scheduler import scheduler
        from subtitles.indexer.series import series_full_scan_subtitles
        from subtitles.indexer.movies import movies_full_scan_subtitles
        if settings.general.use_sonarr:
            scheduler.add_job(series_full_scan_subtitles, kwargs={'use_cache': True})
        if settings.general.use_radarr:
            scheduler.add_job(movies_full_scan_subtitles, kwargs={'use_cache': True})

    if audio_tracks_parsing_changed:
        from .scheduler import scheduler
        if settings.general.use_sonarr:
            from sonarr.sync.series import update_series
            scheduler.add_job(update_series, kwargs={'send_event': True}, max_instances=1)
        if settings.general.use_radarr:
            from radarr.sync.movies import update_movies
            scheduler.add_job(update_movies, kwargs={'send_event': True}, max_instances=1)

    if update_subzero:
        settings.general.subzero_mods = ','.join(subzero_mods)

    write_config()

    # Reconfigure Bazarr to reflect changes
    if configure_debug:
        from .logger import configure_logging
        configure_logging(settings.general.debug or args.debug)

    if configure_captcha:
        configure_captcha_func()

    if update_schedule:
        from .scheduler import scheduler
        from .event_handler import event_stream
        scheduler.update_configurable_tasks()
        event_stream(type='task')

    if sonarr_changed:
        from .signalr_client import sonarr_signalr_client
        try:
            sonarr_signalr_client.restart()
        except Exception:
            pass

    if radarr_changed:
        from .signalr_client import radarr_signalr_client
        try:
            radarr_signalr_client.restart()
        except Exception:
            pass

    if update_path_map:
        from utilities.path_mappings import path_mappings
        path_mappings.update()

    if configure_proxy:
        configure_proxy_func()

    if exclusion_updated:
        from .event_handler import event_stream
        event_stream(type='badges')
        if sonarr_exclusion_updated:
            event_stream(type='reset-episode-wanted')
        if radarr_exclusion_updated:
            event_stream(type='reset-movie-wanted')


def get_array_from(property):
    if property:
        if '[' in property:
            return ast.literal_eval(property)
        elif ',' in property:
            return property.split(',')
        else:
            return [property]
    else:
        return []


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
    if settings.proxy.type:
        if settings.proxy.username != '' and settings.proxy.password != '':
            proxy = settings.proxy.type + '://' + quote_plus(settings.proxy.username) + ':' + \
                    quote_plus(settings.proxy.password) + '@' + settings.proxy.url + ':' + settings.proxy.port
        else:
            proxy = settings.proxy.type + '://' + settings.proxy.url + ':' + settings.proxy.port
        os.environ['HTTP_PROXY'] = str(proxy)
        os.environ['HTTPS_PROXY'] = str(proxy)
        exclude = ','.join(settings.proxy.exclude)
        os.environ['NO_PROXY'] = exclude


def get_scores():
    settings = get_settings()
    return {"movie": settings["movie_scores"], "episode": settings["series_scores"]}

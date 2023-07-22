# coding=utf-8

import hashlib
import os
import ast

from urllib.parse import quote_plus
from subliminal.cache import region
from dynaconf import Dynaconf, Validator
from dynaconf.loaders.yaml_loader import write
from dynaconf.validator import ValidationError
from ipaddress import ip_address
from binascii import hexlify

from .get_args import args


def base_url_slash_cleaner(uri):
    while "//" in uri:
        uri = uri.replace("//", "/")
    return uri


def validate_ip_address(ip_string):
    try:
        ip_address(ip_string)
        return True
    except ValueError:
        return False


validators = [
    # general section
    Validator('general.flask_secret_key', must_exist=True, default=hexlify(os.urandom(16)).decode()),
    Validator('general.ip', must_exist=True, default='0.0.0.0', condition=validate_ip_address),
    Validator('general.port', must_exist=True, default=6767, gte=1, lte=65535),
    Validator('general.base_url', must_exist=True, default=''),
    Validator('general.path_mappings', must_exist=True, default=[]),
    Validator('general.debug', must_exist=True, default=False),
    Validator('general.branch', must_exist=True, default='master', is_in=['master', 'development']),
    Validator('general.auto_update', must_exist=True, default=True),
    Validator('general.single_language', must_exist=True, default=False),
    Validator('general.minimum_score', must_exist=True, default=90, gte=0, lte=100),
    Validator('general.use_scenename', must_exist=True, default=True),
    Validator('general.use_postprocessing', must_exist=True, default=False),
    Validator('general.postprocessing_cmd', must_exist=True, default=''),
    Validator('general.postprocessing_threshold', must_exist=True, default=90, gte=0, lte=100),
    Validator('general.use_postprocessing_threshold', must_exist=True, default=False),
    Validator('general.postprocessing_threshold_movie', must_exist=True, default=70, gte=0, lte=100),
    Validator('general.use_postprocessing_threshold_movie', must_exist=True, default=False),
    Validator('general.use_sonarr', must_exist=True, default=False),
    Validator('general.use_radarr', must_exist=True, default=False),
    Validator('general.path_mappings_movie', must_exist=True, default=[]),
    Validator('general.serie_default_enabled', must_exist=True, default=False),
    Validator('general.serie_default_profile', must_exist=True, default=''),
    Validator('general.movie_default_enabled', must_exist=True, default=False),
    Validator('general.movie_default_profile', must_exist=True, default=''),
    Validator('general.page_size', must_exist=True, default=25, is_in=[25, 50, 100, 250, 500, 1000]),
    Validator('general.theme', must_exist=True, default='auto', is_in=['auto', 'light', 'dark']),
    Validator('general.minimum_score_movie', must_exist=True, default=70, gte=0, lte=100),
    Validator('general.use_embedded_subs', must_exist=True, default=True),
    Validator('general.embedded_subs_show_desired', must_exist=True, default=True),
    Validator('general.utf8_encode', must_exist=True, default=True),
    Validator('general.ignore_pgs_subs', must_exist=True, default=False),
    Validator('general.ignore_vobsub_subs', must_exist=True, default=False),
    Validator('general.ignore_ass_subs', must_exist=True, default=False),
    Validator('general.adaptive_searching', must_exist=True, default=False),
    Validator('general.adaptive_searching_delay', must_exist=True, default='3w', is_in=['1w', '2w', '3w', '4']),
    Validator('general.adaptive_searching_delta', must_exist=True, default='1w', is_in=['3d', '1w', '2w', '3w', '4']),
    Validator('general.enabled_providers', must_exist=True, default=[]),
    Validator('general.multithreading', must_exist=True, default=True),
    Validator('general.chmod_enabled', must_exist=True, default=False),
    Validator('general.chmod', must_exist=True, default='0640'),
    Validator('general.subfolder', must_exist=True, default='current'),
    Validator('general.subfolder_custom', must_exist=True, default=''),
    Validator('general.upgrade_subs', must_exist=True, default=True),
    Validator('general.upgrade_frequency', must_exist=True, default=12, is_in=[6, 12, 24]),
    Validator('general.days_to_upgrade_subs', must_exist=True, default=7, gte=0, lte=30),
    Validator('general.upgrade_manual', must_exist=True, default=True),
    Validator('general.anti_captcha_provider', must_exist=True, default=None),
    Validator('general.wanted_search_frequency', must_exist=True, default=6, is_in=[6, 12, 24]),
    Validator('general.wanted_search_frequency_movie', must_exist=True, default=6, is_in=[6, 12, 24]),
    Validator('general.subzero_mods', must_exist=True, default=''),
    Validator('general.dont_notify_manual_actions', must_exist=True, default=False),
    Validator('general.hi_extension', must_exist=True, default='hi', is_in=['hi', 'cc', 'sdh']),
    Validator('general.embedded_subtitles_parser', must_exist=True, default='ffprobe', is_in=['ffprobe', 'mediainfo']),
    Validator('general.default_und_audio_lang', must_exist=True, default=''),
    Validator('general.default_und_embedded_subtitles_lang', must_exist=True, default=''),
    Validator('general.parse_embedded_audio_track', must_exist=True, default=False),
    Validator('general.skip_hashing', must_exist=True, default=False),
    Validator('general.language_equals', must_exist=True, default=[]),

    # auth section
    Validator('auth.apikey', must_exist=True, default=hexlify(os.urandom(16)).decode()),
    Validator('auth.type', must_exist=True, default=None, is_in=[None, 'basic', 'form']),
    Validator('auth.username', must_exist=True, default=''),
    Validator('auth.password', must_exist=True, default=''),

    # cors section
    Validator('cors.enabled', must_exist=True, default=False),

    # backup section
    Validator('backup.folder', must_exist=True, default=os.path.join(args.config_dir, 'backup')),
    Validator('backup.retention', must_exist=True, default=31, gte=0),
    Validator('backup.frequency', must_exist=True, default='Weekly', is_in=['Manually', 'Daily', 'Weekly']),
    Validator('backup.day', must_exist=True, default=6, gte=0, lte=6),
    Validator('backup.hour', must_exist=True, default=3, gte=0, lte=23),

    # sonarr section
    Validator('sonarr.ip', must_exist=True, default='127.0.0.1'),
    Validator('sonarr.port', must_exist=True, default=8989, gte=1, lte=65535),
    Validator('sonarr.base_url', must_exist=True, default='/'),
    Validator('sonarr.ssl', must_exist=True, default=False),
    Validator('sonarr.http_timeout', must_exist=True, default=60, is_in=[60, 120, 180, 240, 300, 600]),
    Validator('sonarr.apikey', must_exist=True, default=''),
    Validator('sonarr.full_update', must_exist=True, default='Daily', is_in=['Manually', 'Daily', 'Weekly']),
    Validator('sonarr.full_update_day', must_exist=True, default=6, gte=0, lte=6),
    Validator('sonarr.full_update_hour', must_exist=True, default=4, gte=0, lte=23),
    Validator('sonarr.only_monitored', must_exist=True, default=False),
    Validator('sonarr.series_sync', must_exist=True, default=60, is_in=[15, 60, 180, 360, 720, 1440]),
    Validator('sonarr.episodes_sync', must_exist=True, default=60, is_in=[15, 60, 180, 360, 720, 1440]),
    Validator('sonarr.excluded_tags', must_exist=True, default=[]),
    Validator('sonarr.excluded_series_types', must_exist=True, default=[]),
    Validator('sonarr.use_ffprobe_cache', must_exist=True, default=True),
    Validator('sonarr.exclude_season_zero', must_exist=True, default=False),
    Validator('sonarr.defer_search_signalr', must_exist=True, default=False),

    # radarr section
    Validator('radarr.ip', must_exist=True, default='127.0.0.1'),
    Validator('radarr.port', must_exist=True, default=7878, gte=1, lte=65535),
    Validator('radarr.base_url', must_exist=True, default='/'),
    Validator('radarr.ssl', must_exist=True, default=False),
    Validator('radarr.http_timeout', must_exist=True, default=60, is_in=[60, 120, 180, 240, 300, 600]),
    Validator('radarr.apikey', must_exist=True, default=''),
    Validator('radarr.full_update', must_exist=True, default='Daily', is_in=['Manually', 'Daily', 'Weekly']),
    Validator('radarr.full_update_day', must_exist=True, default=6, gte=0, lte=6),
    Validator('radarr.full_update_hour', must_exist=True, default=4, gte=0, lte=23),
    Validator('radarr.only_monitored', must_exist=True, default=False),
    Validator('radarr.movies_sync', must_exist=True, default=60, is_in=[15, 60, 180, 360, 720, 1440]),
    Validator('radarr.excluded_tags', must_exist=True, default=[]),
    Validator('radarr.use_ffprobe_cache', must_exist=True, default=True),
    Validator('radarr.defer_search_signalr', must_exist=True, default=False),

    # proxy section
    Validator('proxy.type', must_exist=True, default=None, is_in=[None, 'socks5', 'http']),
    Validator('proxy.url', must_exist=True, default=''),
    Validator('proxy.port', must_exist=True, default=''),
    Validator('proxy.username', must_exist=True, default=''),
    Validator('proxy.password', must_exist=True, default=''),
    Validator('proxy.exclude', must_exist=True, default=["localhost", "127.0.0.1"]),

    # opensubtitles.org section
    Validator('opensubtitles.username', must_exist=True, default=''),
    Validator('opensubtitles.password', must_exist=True, default=''),
    Validator('opensubtitles.use_tag_search', must_exist=True, default=False),
    Validator('opensubtitles.vip', must_exist=True, default=False),
    Validator('opensubtitles.ssl', must_exist=True, default=False),
    Validator('opensubtitles.timeout', must_exist=True, default=15, gte=0),
    Validator('opensubtitles.skip_wrong_fps', must_exist=True, default=False),

    # opensubtitles.com section
    Validator('opensubtitlescom.username', must_exist=True, default=''),
    Validator('opensubtitlescom.password', must_exist=True, default=''),
    Validator('opensubtitlescom.use_hash', must_exist=True, default=True),

    # addic7ed section
    Validator('addic7ed.username', must_exist=True, default=''),
    Validator('addic7ed.password', must_exist=True, default=''),
    Validator('addic7ed.cookies', must_exist=True, default=''),
    Validator('addic7ed.user_agent', must_exist=True, default=''),
    Validator('addic7ed.vip', must_exist=True, default=False),

    # podnapisi section
    Validator('podnapisi.verify_ssl', must_exist=True, default=True),

    # subf2m section
    Validator('subf2m.verify_ssl', must_exist=True, default=True),
    Validator('subf2m.user_agent', must_exist=True, default=''),

    # whisperai section
    Validator('whisperai.endpoint', must_exist=True, default='http://127.0.0.1:9000'),
    Validator('whisperai.timeout', must_exist=True, default=3600, gte=0),

    # legendasdivx section
    Validator('legendasdivx.username', must_exist=True, default=''),
    Validator('legendasdivx.password', must_exist=True, default=''),
    Validator('legendasdivx.skip_wrong_fps', must_exist=True, default=False),

    # ktuvit section
    Validator('ktuvit.email', must_exist=True, default=''),
    Validator('ktuvit.hashed_password', must_exist=True, default=''),

    # xsubs section
    Validator('xsubs.username', must_exist=True, default=''),
    Validator('xsubs.password', must_exist=True, default=''),

    # assrt section
    Validator('assrt.token', must_exist=True, default=''),

    # anticaptcha section
    Validator('anticaptcha.anti_captcha_key', must_exist=True, default=''),

    # deathbycaptcha section
    Validator('deathbycaptcha.username', must_exist=True, default=''),
    Validator('deathbycaptcha.password', must_exist=True, default=''),

    # napisy24 section
    Validator('napisy24.username', must_exist=True, default=''),
    Validator('napisy24.password', must_exist=True, default=''),

    # subscene section
    Validator('subscene.username', must_exist=True, default=''),
    Validator('subscene.password', must_exist=True, default=''),

    # betaseries section
    Validator('betaseries.token', must_exist=True, default=''),

    # analytics section
    Validator('analytics.enabled', must_exist=True, default=True),

    # titlovi section
    Validator('titlovi.username', must_exist=True, default=''),
    Validator('titlovi.password', must_exist=True, default=''),

    # titulky section
    Validator('titulky.username', must_exist=True, default=''),
    Validator('titulky.password', must_exist=True, default=''),
    Validator('titulky.approved_only', must_exist=True, default=False),

    # embeddedsubtitles section
    Validator('embeddedsubtitles.included_codecs', must_exist=True, default=[]),
    Validator('embeddedsubtitles.hi_fallback', must_exist=True, default=False),
    Validator('embeddedsubtitles.timeout', must_exist=True, default=600, gte=0),
    Validator('embeddedsubtitles.unknown_as_english', must_exist=True, default=False),

    # karagarga section
    Validator('karagarga.username', must_exist=True, default=''),
    Validator('karagarga.password', must_exist=True, default=''),
    Validator('karagarga.f_username', must_exist=True, default=''),
    Validator('karagarga.f_password', must_exist=True, default=''),

    # subsync section
    Validator('subsync.use_subsync', must_exist=True, default=False),
    Validator('subsync.use_subsync_threshold', must_exist=True, default=False),
    Validator('subsync.subsync_threshold', must_exist=True, default=90, gte=0, lte=100),
    Validator('subsync.use_subsync_movie_threshold', must_exist=True, default=False),
    Validator('subsync.subsync_movie_threshold', must_exist=True, default=70, gte=0, lte=100),
    Validator('subsync.debug', must_exist=True, default=False),
    Validator('subsync.force_audio', must_exist=True, default=False),

    # series_scores section
    Validator('series_scores.hash', must_exist=True, default=359),
    Validator('series_scores.series', must_exist=True, default=180),
    Validator('series_scores.year', must_exist=True, default=90),
    Validator('series_scores.season', must_exist=True, default=30),
    Validator('series_scores.episode', must_exist=True, default=30),
    Validator('series_scores.release_group', must_exist=True, default=14),
    Validator('series_scores.source', must_exist=True, default=7),
    Validator('series_scores.audio_codec', must_exist=True, default=3),
    Validator('series_scores.resolution', must_exist=True, default=2),
    Validator('series_scores.video_codec', must_exist=True, default=2),
    Validator('series_scores.streaming_service', must_exist=True, default=1),
    Validator('series_scores.hearing_impaired', must_exist=True, default=1),

    # movie_scores section
    Validator('movie_scores.hash', must_exist=True, default=119),
    Validator('movie_scores.title', must_exist=True, default=60),
    Validator('movie_scores.year', must_exist=True, default=30),
    Validator('movie_scores.release_group', must_exist=True, default=13),
    Validator('movie_scores.source', must_exist=True, default=7),
    Validator('movie_scores.audio_codec', must_exist=True, default=3),
    Validator('movie_scores.resolution', must_exist=True, default=2),
    Validator('movie_scores.video_codec', must_exist=True, default=2),
    Validator('movie_scores.streaming_service', must_exist=True, default=1),
    Validator('movie_scores.edition', must_exist=True, default=1),
    Validator('movie_scores.hearing_impaired', must_exist=True, default=1),

    # postgresql section
    Validator('postgresql.enabled', must_exist=True, default=False),
    Validator('postgresql.host', must_exist=True, default='localhost'),
    Validator('postgresql.port', must_exist=True, default=5432, gte=0, lte=65535),
    Validator('postgresql.database', must_exist=True, default=''),
    Validator('postgresql.username', must_exist=True, default=''),
    Validator('postgresql.password', must_exist=True, default=''),
]


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
    os.rename(config_file, config_file + '.old')


config_yaml_file = os.path.join(args.config_dir, 'config', 'config.yaml')
config_ini_file = os.path.join(args.config_dir, 'config', 'config.ini')
if os.path.exists(config_ini_file) and not os.path.exists(config_yaml_file):
    convert_ini_to_yaml(config_ini_file)
elif not os.path.exists(config_yaml_file):
    if not os.path.isdir(os.path.dirname(config_yaml_file)):
        os.makedirs(os.path.dirname(config_yaml_file))
    open(config_yaml_file, mode='w').close()

settings = Dynaconf(
    settings_file=config_yaml_file,
    core_loaders=['YAML'],
    validators=validators,
    validate_on_update=True,
    apply_default_on_none=True,
)


def write_config():
    write(settings_path=config_yaml_file,
          settings_data={k.lower(): v for k, v in settings.as_dict().items()},
          merge=False)


base_url = settings.general.base_url.rstrip('/')

ignore_keys = ['flask_secret_key']

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
        if isinstance(v, dict):
            k = k.lower()
            settings_to_return[k] = dict()
            for subk, subv in v.items():
                if subk.lower() in ignore_keys:
                    continue
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
    reset_providers = False

    # Subzero Mods
    update_subzero = False
    subzero_mods = get_array_from(settings.general.subzero_mods)

    if len(subzero_mods) == 1 and subzero_mods[0] == '':
        subzero_mods = []

    for key, value in settings_items:

        settings_keys = key.split('-')

        # Make sure list of lists based form values are stored as list
        if isinstance(value, list) and settings_keys[-1] in array_keys:
            value = [x.split(',') for x in value if isinstance(x, str)]

        # Make sure that text based form values aren't passed as list
        if isinstance(value, list) and len(value) == 1 and settings_keys[-1] not in array_keys:
            value = value[0]
            if value in empty_values and value != '':
                value = None

        # try to cast string as integer
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                pass

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
                reset_providers = True
                region.delete('addic7ed_data')
        elif key == 'settings-addic7ed-password':
            if key != settings.addic7ed.password:
                reset_providers = True
                region.delete('addic7ed_data')

        if key == 'settings-legendasdivx-username':
            if key != settings.legendasdivx.username:
                reset_providers = True
                region.delete('legendasdivx_cookies2')
        elif key == 'settings-legendasdivx-password':
            if key != settings.legendasdivx.password:
                reset_providers = True
                region.delete('legendasdivx_cookies2')

        if key == 'settings-opensubtitles-username':
            if key != settings.opensubtitles.username:
                reset_providers = True
                region.delete('os_token')
        elif key == 'settings-opensubtitles-password':
            if key != settings.opensubtitles.password:
                reset_providers = True
                region.delete('os_token')

        if key == 'settings-opensubtitlescom-username':
            if key != settings.opensubtitlescom.username:
                reset_providers = True
                region.delete('oscom_token')
        elif key == 'settings-opensubtitlescom-password':
            if key != settings.opensubtitlescom.password:
                reset_providers = True
                region.delete('oscom_token')

        if key == 'settings-subscene-username':
            if key != settings.subscene.username:
                reset_providers = True
                region.delete('subscene_cookies2')
        elif key == 'settings-subscene-password':
            if key != settings.subscene.password:
                reset_providers = True
                region.delete('subscene_cookies2')

        if key == 'settings-titlovi-username':
            if key != settings.titlovi.username:
                reset_providers = True
                region.delete('titlovi_token')
        elif key == 'settings-titlovi-password':
            if key != settings.titlovi.password:
                reset_providers = True
                region.delete('titlovi_token')

        if reset_providers:
            from .get_providers import reset_throttled_providers
            reset_throttled_providers(only_auth_or_conf_error=True)

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

    try:
        settings.validators.validate_all()
    except ValidationError:
        settings.reload()
        raise
    else:
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

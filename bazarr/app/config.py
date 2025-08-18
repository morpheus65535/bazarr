# coding=utf-8

import hashlib
import os
import ast
import logging
import re
import secrets
import threading
import time
import configparser
import yaml

from urllib.parse import quote_plus
from utilities.binaries import BinaryNotFound, get_binary
from literals import EXIT_VALIDATION_ERROR
from utilities.central import stop_bazarr
from subliminal.cache import region
from dynaconf import Dynaconf, Validator as OriginalValidator
from dynaconf.loaders.yaml_loader import write
from dynaconf.validator import ValidationError
from dynaconf.utils.functional import empty
from ipaddress import ip_address
from binascii import hexlify
from types import MappingProxyType
from shutil import move

from .get_args import args

NoneType = type(None)


def base_url_slash_cleaner(uri):
    while "//" in uri:
        uri = uri.replace("//", "/")
    return uri


def validate_ip_address(ip_string):
    if ip_string == '*':
        return True
    try:
        ip_address(ip_string)
        return True
    except ValueError:
        return False

def validate_tags(tags):
    if not tags:
        return True

    return all(re.match( r'^[a-z0-9_-]+$', item) for item in tags)


ONE_HUNDRED_YEARS_IN_MINUTES = 52560000
ONE_HUNDRED_YEARS_IN_HOURS = 876000


class Validator(OriginalValidator):
    # Give the ability to personalize messages sent by the original dynasync Validator class.
    default_messages = MappingProxyType(
        {
            "must_exist_true": "{name} is required",
            "must_exist_false": "{name} cannot exists",
            "condition": "{name} invalid for {function}({value})",
            "operations": "{name} must {operation} {op_value} but it is {value}",
            "combined": "combined validators failed {errors}",
        }
    )


def check_parser_binary(value):
    try:
        get_binary(value)
    except BinaryNotFound:
        raise ValidationError(f"Executable '{value}' not found in search path. Please install before making this selection.")
    return True


validators = [
    # general section
    Validator('general.flask_secret_key', must_exist=True, default=hexlify(os.urandom(16)).decode(),
              is_type_of=str),
    Validator('general.ip', must_exist=True, default='*', is_type_of=str, condition=validate_ip_address),
    Validator('general.port', must_exist=True, default=6767, is_type_of=int, gte=1, lte=65535),
    Validator('general.base_url', must_exist=True, default='', is_type_of=str),
    Validator('general.path_mappings', must_exist=True, default=[], is_type_of=list),
    Validator('general.debug', must_exist=True, default=False, is_type_of=bool),
    Validator('general.branch', must_exist=True, default='master', is_type_of=str,
              is_in=['master', 'development']),
    Validator('general.auto_update', must_exist=True, default=True, is_type_of=bool),
    Validator('general.single_language', must_exist=True, default=False, is_type_of=bool),
    Validator('general.minimum_score', must_exist=True, default=90, is_type_of=int, gte=0, lte=100),
    Validator('general.use_scenename', must_exist=True, default=True, is_type_of=bool),
    Validator('general.use_postprocessing', must_exist=True, default=False, is_type_of=bool),
    Validator('general.postprocessing_cmd', must_exist=True, default='', is_type_of=str),
    Validator('general.postprocessing_threshold', must_exist=True, default=90, is_type_of=int, gte=0, lte=100),
    Validator('general.use_postprocessing_threshold', must_exist=True, default=False, is_type_of=bool),
    Validator('general.postprocessing_threshold_movie', must_exist=True, default=70, is_type_of=int, gte=0,
              lte=100),
    Validator('general.use_postprocessing_threshold_movie', must_exist=True, default=False, is_type_of=bool),
    Validator('general.use_sonarr', must_exist=True, default=False, is_type_of=bool),
    Validator('general.use_radarr', must_exist=True, default=False, is_type_of=bool),
    Validator('general.use_plex', must_exist=True, default=False, is_type_of=bool),
    Validator('general.path_mappings_movie', must_exist=True, default=[], is_type_of=list),
    Validator('general.serie_tag_enabled', must_exist=True, default=False, is_type_of=bool),
    Validator('general.movie_tag_enabled', must_exist=True, default=False, is_type_of=bool),
    Validator('general.remove_profile_tags', must_exist=True, default=[], is_type_of=list, condition=validate_tags),
    Validator('general.serie_default_enabled', must_exist=True, default=False, is_type_of=bool),
    Validator('general.serie_default_profile', must_exist=True, default='', is_type_of=(int, str)),
    Validator('general.movie_default_enabled', must_exist=True, default=False, is_type_of=bool),
    Validator('general.movie_default_profile', must_exist=True, default='', is_type_of=(int, str)),
    Validator('general.page_size', must_exist=True, default=25, is_type_of=int,
              is_in=[25, 50, 100, 250, 500, 1000]),
    Validator('general.theme', must_exist=True, default='auto', is_type_of=str,
              is_in=['auto', 'light', 'dark']),
    Validator('general.minimum_score_movie', must_exist=True, default=70, is_type_of=int, gte=0, lte=100),
    Validator('general.use_embedded_subs', must_exist=True, default=True, is_type_of=bool),
    Validator('general.embedded_subs_show_desired', must_exist=True, default=True, is_type_of=bool),
    Validator('general.utf8_encode', must_exist=True, default=True, is_type_of=bool),
    Validator('general.ignore_pgs_subs', must_exist=True, default=False, is_type_of=bool),
    Validator('general.ignore_vobsub_subs', must_exist=True, default=False, is_type_of=bool),
    Validator('general.ignore_ass_subs', must_exist=True, default=False, is_type_of=bool),
    Validator('general.adaptive_searching', must_exist=True, default=True, is_type_of=bool),
    Validator('general.adaptive_searching_delay', must_exist=True, default='3w', is_type_of=str,
              is_in=['1w', '2w', '3w', '4w']),
    Validator('general.adaptive_searching_delta', must_exist=True, default='1w', is_type_of=str,
              is_in=['3d', '1w', '2w', '3w', '4w']),
    Validator('general.enabled_providers', must_exist=True, default=[], is_type_of=list),
    Validator('general.enabled_integrations', must_exist=True, default=[], is_type_of=list),
    Validator('general.multithreading', must_exist=True, default=True, is_type_of=bool),
    Validator('general.chmod_enabled', must_exist=True, default=False, is_type_of=bool),
    Validator('general.chmod', must_exist=True, default='0640', is_type_of=str),
    Validator('general.subfolder', must_exist=True, default='current', is_type_of=str),
    Validator('general.subfolder_custom', must_exist=True, default='', is_type_of=str),
    Validator('general.upgrade_subs', must_exist=True, default=True, is_type_of=bool),
    Validator('general.upgrade_frequency', must_exist=True, default=12, is_type_of=int,
              is_in=[6, 12, 24, 168, ONE_HUNDRED_YEARS_IN_HOURS]),
    Validator('general.days_to_upgrade_subs', must_exist=True, default=7, is_type_of=int, gte=0, lte=30),
    Validator('general.upgrade_manual', must_exist=True, default=True, is_type_of=bool),
    Validator('general.anti_captcha_provider', must_exist=True, default=None, is_type_of=(NoneType, str),
              is_in=[None, 'anti-captcha', 'death-by-captcha']),
    Validator('general.wanted_search_frequency', must_exist=True, default=6, is_type_of=int, 
              is_in=[6, 12, 24, 168, ONE_HUNDRED_YEARS_IN_HOURS]),
    Validator('general.wanted_search_frequency_movie', must_exist=True, default=6, is_type_of=int,
              is_in=[6, 12, 24, 168, ONE_HUNDRED_YEARS_IN_HOURS]),
    Validator('general.subzero_mods', must_exist=True, default='', is_type_of=str),
    Validator('general.dont_notify_manual_actions', must_exist=True, default=False, is_type_of=bool),
    Validator('general.hi_extension', must_exist=True, default='hi', is_type_of=str, is_in=['hi', 'cc', 'sdh']),
    Validator('general.embedded_subtitles_parser', must_exist=True, default='ffprobe', is_type_of=str,
              is_in=['ffprobe', 'mediainfo'], condition=check_parser_binary),
    Validator('general.default_und_audio_lang', must_exist=True, default='', is_type_of=str),
    Validator('general.default_und_embedded_subtitles_lang', must_exist=True, default='', is_type_of=str),
    Validator('general.parse_embedded_audio_track', must_exist=True, default=False, is_type_of=bool),
    Validator('general.skip_hashing', must_exist=True, default=False, is_type_of=bool),
    Validator('general.language_equals', must_exist=True, default=[], is_type_of=list),

    # log section
    Validator('log.include_filter', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('log.exclude_filter', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('log.ignore_case', must_exist=True, default=False, is_type_of=bool),
    Validator('log.use_regex', must_exist=True, default=False, is_type_of=bool),

    # auth section
    Validator('auth.apikey', must_exist=True, default=hexlify(os.urandom(16)).decode(), is_type_of=str),
    Validator('auth.type', must_exist=True, default=None, is_type_of=(NoneType, str),
              is_in=[None, 'basic', 'form']),
    Validator('auth.username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('auth.password', must_exist=True, default='', is_type_of=str, cast=str),

    # cors section
    Validator('cors.enabled', must_exist=True, default=False, is_type_of=bool),

    # backup section
    Validator('backup.folder', must_exist=True, default=os.path.join(args.config_dir, 'backup'),
              is_type_of=str),
    Validator('backup.retention', must_exist=True, default=31, is_type_of=int, gte=0),
    Validator('backup.frequency', must_exist=True, default='Weekly', is_type_of=str,
              is_in=['Manually', 'Daily', 'Weekly']),
    Validator('backup.day', must_exist=True, default=6, is_type_of=int, gte=0, lte=6),
    Validator('backup.hour', must_exist=True, default=3, is_type_of=int, gte=0, lte=23),

    # translating section
    Validator('translator.gemini_key', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('translator.gemini_model', must_exist=True, default='gemini-2.0-flash', is_type_of=str, cast=str),
    Validator('translator.translator_info', must_exist=True, default=True, is_type_of=bool),
    Validator('translator.translator_type', must_exist=True, default='google_translate', is_type_of=str, cast=str),
    Validator('translator.lingarr_url', must_exist=True, default='http://lingarr:9876', is_type_of=str),

    # sonarr section
    Validator('sonarr.ip', must_exist=True, default='127.0.0.1', is_type_of=str),
    Validator('sonarr.port', must_exist=True, default=8989, is_type_of=int, gte=1, lte=65535),
    Validator('sonarr.base_url', must_exist=True, default='/', is_type_of=str),
    Validator('sonarr.ssl', must_exist=True, default=False, is_type_of=bool),
    Validator('sonarr.http_timeout', must_exist=True, default=60, is_type_of=int,
              is_in=[60, 120, 180, 240, 300, 600]),
    Validator('sonarr.apikey', must_exist=True, default='', is_type_of=str),
    Validator('sonarr.full_update', must_exist=True, default='Daily', is_type_of=str,
              is_in=['Manually', 'Daily', 'Weekly']),
    Validator('sonarr.full_update_day', must_exist=True, default=6, is_type_of=int, gte=0, lte=6),
    Validator('sonarr.full_update_hour', must_exist=True, default=4, is_type_of=int, gte=0, lte=23),
    Validator('sonarr.only_monitored', must_exist=True, default=False, is_type_of=bool),
    Validator('sonarr.series_sync', must_exist=True, default=60, is_type_of=int,
              is_in=[15, 60, 180, 360, 720, 1440, 10080, ONE_HUNDRED_YEARS_IN_MINUTES]),
    Validator('sonarr.excluded_tags', must_exist=True, default=[], is_type_of=list, condition=validate_tags),
    Validator('sonarr.excluded_series_types', must_exist=True, default=[], is_type_of=list),
    Validator('sonarr.use_ffprobe_cache', must_exist=True, default=True, is_type_of=bool),
    Validator('sonarr.exclude_season_zero', must_exist=True, default=False, is_type_of=bool),
    Validator('sonarr.defer_search_signalr', must_exist=True, default=False, is_type_of=bool),
    Validator('sonarr.sync_only_monitored_series', must_exist=True, default=False, is_type_of=bool),
    Validator('sonarr.sync_only_monitored_episodes', must_exist=True, default=False, is_type_of=bool),

    # radarr section
    Validator('radarr.ip', must_exist=True, default='127.0.0.1', is_type_of=str),
    Validator('radarr.port', must_exist=True, default=7878, is_type_of=int, gte=1, lte=65535),
    Validator('radarr.base_url', must_exist=True, default='/', is_type_of=str),
    Validator('radarr.ssl', must_exist=True, default=False, is_type_of=bool),
    Validator('radarr.http_timeout', must_exist=True, default=60, is_type_of=int,
              is_in=[60, 120, 180, 240, 300, 600]),
    Validator('radarr.apikey', must_exist=True, default='', is_type_of=str),
    Validator('radarr.full_update', must_exist=True, default='Daily', is_type_of=str,
              is_in=['Manually', 'Daily', 'Weekly']),
    Validator('radarr.full_update_day', must_exist=True, default=6, is_type_of=int, gte=0, lte=6),
    Validator('radarr.full_update_hour', must_exist=True, default=4, is_type_of=int, gte=0, lte=23),
    Validator('radarr.only_monitored', must_exist=True, default=False, is_type_of=bool),
    Validator('radarr.movies_sync', must_exist=True, default=60, is_type_of=int,
              is_in=[15, 60, 180, 360, 720, 1440, 10080, ONE_HUNDRED_YEARS_IN_MINUTES]),
    Validator('radarr.excluded_tags', must_exist=True, default=[], is_type_of=list, condition=validate_tags),
    Validator('radarr.use_ffprobe_cache', must_exist=True, default=True, is_type_of=bool),
    Validator('radarr.defer_search_signalr', must_exist=True, default=False, is_type_of=bool),
    Validator('radarr.sync_only_monitored_movies', must_exist=True, default=False, is_type_of=bool),

    # plex section
    Validator('plex.ip', must_exist=True, default='127.0.0.1', is_type_of=str),
    Validator('plex.port', must_exist=True, default=32400, is_type_of=int, gte=1, lte=65535),
    Validator('plex.ssl', must_exist=True, default=False, is_type_of=bool),
    Validator('plex.apikey', must_exist=True, default='', is_type_of=str),
    Validator('plex.movie_library', must_exist=True, default='', is_type_of=str),
    Validator('plex.series_library', must_exist=True, default='', is_type_of=str),
    Validator('plex.set_movie_added', must_exist=True, default=False, is_type_of=bool),
    Validator('plex.set_episode_added', must_exist=True, default=False, is_type_of=bool),
    Validator('plex.update_movie_library', must_exist=True, default=False, is_type_of=bool),
    Validator('plex.update_series_library', must_exist=True, default=False, is_type_of=bool),
    # OAuth fields
    Validator('plex.token', must_exist=True, default='', is_type_of=str),
    Validator('plex.username', must_exist=True, default='', is_type_of=str),
    Validator('plex.email', must_exist=True, default='', is_type_of=str),
    Validator('plex.user_id', must_exist=True, default='', is_type_of=str),
    Validator('plex.auth_method', must_exist=True, default='apikey', is_type_of=str, is_in=['apikey', 'oauth']),
    Validator('plex.encryption_key', must_exist=True, default='', is_type_of=str),
    Validator('plex.server_machine_id', must_exist=True, default='', is_type_of=str),
    Validator('plex.server_name', must_exist=True, default='', is_type_of=str),
    Validator('plex.server_url', must_exist=True, default='', is_type_of=str),
    Validator('plex.server_local', must_exist=True, default=False, is_type_of=bool),

    # proxy section
    Validator('proxy.type', must_exist=True, default=None, is_type_of=(NoneType, str),
              is_in=[None, 'socks5', 'socks5h', 'http']),
    Validator('proxy.url', must_exist=True, default='', is_type_of=str),
    Validator('proxy.port', must_exist=True, default='', is_type_of=(str, int)),
    Validator('proxy.username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('proxy.password', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('proxy.exclude', must_exist=True, default=["localhost", "127.0.0.1"], is_type_of=list),

    # opensubtitles.org section
    Validator('opensubtitles.username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('opensubtitles.password', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('opensubtitles.use_tag_search', must_exist=True, default=False, is_type_of=bool),
    Validator('opensubtitles.vip', must_exist=True, default=False, is_type_of=bool),
    Validator('opensubtitles.ssl', must_exist=True, default=False, is_type_of=bool),
    Validator('opensubtitles.timeout', must_exist=True, default=15, is_type_of=int, gte=1),
    Validator('opensubtitles.skip_wrong_fps', must_exist=True, default=False, is_type_of=bool),

    # opensubtitles.com section
    Validator('opensubtitlescom.username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('opensubtitlescom.password', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('opensubtitlescom.use_hash', must_exist=True, default=True, is_type_of=bool),
    Validator('opensubtitlescom.include_ai_translated', must_exist=True, default=False, is_type_of=bool),

    # napiprojekt section
    Validator('napiprojekt.only_authors', must_exist=True, default=False, is_type_of=bool),
    Validator('napiprojekt.only_real_names', must_exist=True, default=False, is_type_of=bool),

    # addic7ed section
    Validator('addic7ed.username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('addic7ed.password', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('addic7ed.cookies', must_exist=True, default='', is_type_of=str),
    Validator('addic7ed.user_agent', must_exist=True, default='', is_type_of=str),
    Validator('addic7ed.vip', must_exist=True, default=False, is_type_of=bool),

    # animetosho section
    Validator('animetosho.search_threshold', must_exist=True, default=6, is_type_of=int, gte=1, lte=15),
    Validator('animetosho.anidb_api_client', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('animetosho.anidb_api_client_ver', must_exist=True, default=1, is_type_of=int, gte=1, lte=9),

    # avistaz section
    Validator('avistaz.cookies', must_exist=True, default='', is_type_of=str),
    Validator('avistaz.user_agent', must_exist=True, default='', is_type_of=str),

    # cinemaz section
    Validator('cinemaz.cookies', must_exist=True, default='', is_type_of=str),
    Validator('cinemaz.user_agent', must_exist=True, default='', is_type_of=str),

    # podnapisi section
    Validator('podnapisi.verify_ssl', must_exist=True, default=True, is_type_of=bool),

    # subf2m section
    Validator('subf2m.verify_ssl', must_exist=True, default=True, is_type_of=bool),
    Validator('subf2m.user_agent', must_exist=True, default='', is_type_of=str),

    # hdbits section
    Validator('hdbits.username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('hdbits.passkey', must_exist=True, default='', is_type_of=str, cast=str),

    # whisperai section
    Validator('whisperai.endpoint', must_exist=True, default='http://127.0.0.1:9000', is_type_of=str),
    Validator('whisperai.response', must_exist=True, default=5, is_type_of=int, gte=1),
    Validator('whisperai.timeout', must_exist=True, default=3600, is_type_of=int, gte=1),
    Validator('whisperai.pass_video_name', must_exist=True, default=False, is_type_of=bool),
    Validator('whisperai.loglevel', must_exist=True, default='INFO', is_type_of=str,
              is_in=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),

    # legendasdivx section
    Validator('legendasdivx.username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('legendasdivx.password', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('legendasdivx.skip_wrong_fps', must_exist=True, default=False, is_type_of=bool),

    # legendasnet section
    Validator('legendasnet.username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('legendasnet.password', must_exist=True, default='', is_type_of=str, cast=str),

    # ktuvit section
    Validator('ktuvit.email', must_exist=True, default='', is_type_of=str),
    Validator('ktuvit.hashed_password', must_exist=True, default='', is_type_of=str, cast=str),

    # xsubs section
    Validator('xsubs.username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('xsubs.password', must_exist=True, default='', is_type_of=str, cast=str),

    # assrt section
    Validator('assrt.token', must_exist=True, default='', is_type_of=str, cast=str),

    # anticaptcha section
    Validator('anticaptcha.anti_captcha_key', must_exist=True, default='', is_type_of=str),

    # deathbycaptcha section
    Validator('deathbycaptcha.username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('deathbycaptcha.password', must_exist=True, default='', is_type_of=str, cast=str),

    # napisy24 section
    Validator('napisy24.username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('napisy24.password', must_exist=True, default='', is_type_of=str, cast=str),

    # betaseries section
    Validator('betaseries.token', must_exist=True, default='', is_type_of=str, cast=str),

    # analytics section
    Validator('analytics.enabled', must_exist=True, default=True, is_type_of=bool),
    
    # jimaku section
    Validator('jimaku.api_key', must_exist=True, default='', is_type_of=str),
    Validator('jimaku.enable_name_search_fallback', must_exist=True, default=True, is_type_of=bool),
    Validator('jimaku.enable_archives_download', must_exist=True, default=False, is_type_of=bool),
    Validator('jimaku.enable_ai_subs', must_exist=True, default=False, is_type_of=bool),

    # titlovi section
    Validator('titlovi.username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('titlovi.password', must_exist=True, default='', is_type_of=str, cast=str),

    # titulky section
    Validator('titulky.username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('titulky.password', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('titulky.approved_only', must_exist=True, default=False, is_type_of=bool),
    Validator('titulky.skip_wrong_fps', must_exist=True, default=False, is_type_of=bool),

    # embeddedsubtitles section
    Validator('embeddedsubtitles.included_codecs', must_exist=True, default=[], is_type_of=list),
    Validator('embeddedsubtitles.hi_fallback', must_exist=True, default=False, is_type_of=bool),
    Validator('embeddedsubtitles.timeout', must_exist=True, default=600, is_type_of=int, gte=1),
    Validator('embeddedsubtitles.unknown_as_fallback', must_exist=True, default=False, is_type_of=bool),
    Validator('embeddedsubtitles.fallback_lang', must_exist=True, default='en', is_type_of=str, cast=str),

    # karagarga section
    Validator('karagarga.username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('karagarga.password', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('karagarga.f_username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('karagarga.f_password', must_exist=True, default='', is_type_of=str, cast=str),

    # subdl section
    Validator('subdl.api_key', must_exist=True, default='', is_type_of=str, cast=str),

    # turkcealtyaziorg section
    Validator('turkcealtyaziorg.cookies', must_exist=True, default='', is_type_of=str),
    Validator('turkcealtyaziorg.user_agent', must_exist=True, default='', is_type_of=str),

    # subsync section
    Validator('subsync.use_subsync', must_exist=True, default=False, is_type_of=bool),
    Validator('subsync.use_subsync_threshold', must_exist=True, default=False, is_type_of=bool),
    Validator('subsync.subsync_threshold', must_exist=True, default=90, is_type_of=int, gte=0, lte=100),
    Validator('subsync.use_subsync_movie_threshold', must_exist=True, default=False, is_type_of=bool),
    Validator('subsync.subsync_movie_threshold', must_exist=True, default=70, is_type_of=int, gte=0, lte=100),
    Validator('subsync.debug', must_exist=True, default=False, is_type_of=bool),
    Validator('subsync.force_audio', must_exist=True, default=False, is_type_of=bool),
    Validator('subsync.checker', must_exist=True, default={}, is_type_of=dict),
    Validator('subsync.checker.blacklisted_providers', must_exist=True, default=[], is_type_of=list),
    Validator('subsync.checker.blacklisted_languages', must_exist=True, default=[], is_type_of=list),
    Validator('subsync.no_fix_framerate', must_exist=True, default=True, is_type_of=bool),
    Validator('subsync.gss', must_exist=True, default=True, is_type_of=bool),
    Validator('subsync.max_offset_seconds', must_exist=True, default=60, is_type_of=int,
              is_in=[60, 120, 300, 600]),

    # series_scores section
    Validator('series_scores.hash', must_exist=True, default=359, is_type_of=int),
    Validator('series_scores.series', must_exist=True, default=180, is_type_of=int),
    Validator('series_scores.year', must_exist=True, default=90, is_type_of=int),
    Validator('series_scores.season', must_exist=True, default=30, is_type_of=int),
    Validator('series_scores.episode', must_exist=True, default=30, is_type_of=int),
    Validator('series_scores.release_group', must_exist=True, default=14, is_type_of=int),
    Validator('series_scores.source', must_exist=True, default=7, is_type_of=int),
    Validator('series_scores.audio_codec', must_exist=True, default=3, is_type_of=int),
    Validator('series_scores.resolution', must_exist=True, default=2, is_type_of=int),
    Validator('series_scores.video_codec', must_exist=True, default=2, is_type_of=int),
    Validator('series_scores.streaming_service', must_exist=True, default=1, is_type_of=int),
    Validator('series_scores.hearing_impaired', must_exist=True, default=1, is_type_of=int),

    # movie_scores section
    Validator('movie_scores.hash', must_exist=True, default=119, is_type_of=int),
    Validator('movie_scores.title', must_exist=True, default=60, is_type_of=int),
    Validator('movie_scores.year', must_exist=True, default=30, is_type_of=int),
    Validator('movie_scores.release_group', must_exist=True, default=13, is_type_of=int),
    Validator('movie_scores.source', must_exist=True, default=7, is_type_of=int),
    Validator('movie_scores.audio_codec', must_exist=True, default=3, is_type_of=int),
    Validator('movie_scores.resolution', must_exist=True, default=2, is_type_of=int),
    Validator('movie_scores.video_codec', must_exist=True, default=2, is_type_of=int),
    Validator('movie_scores.streaming_service', must_exist=True, default=1, is_type_of=int),
    Validator('movie_scores.edition', must_exist=True, default=1, is_type_of=int),
    Validator('movie_scores.hearing_impaired', must_exist=True, default=1, is_type_of=int),

    # postgresql section
    Validator('postgresql.enabled', must_exist=True, default=False, is_type_of=bool),
    Validator('postgresql.host', must_exist=True, default='localhost', is_type_of=str),
    Validator('postgresql.port', must_exist=True, default=5432, is_type_of=int, gte=1, lte=65535),
    Validator('postgresql.database', must_exist=True, default='', is_type_of=str),
    Validator('postgresql.username', must_exist=True, default='', is_type_of=str, cast=str),
    Validator('postgresql.password', must_exist=True, default='', is_type_of=str, cast=str),

    # anidb section
    Validator('anidb.api_client', must_exist=True, default='', is_type_of=str),
    Validator('anidb.api_client_ver', must_exist=True, default=1, is_type_of=int),
]


def convert_ini_to_yaml(config_file):
    config_object = configparser.RawConfigParser()
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
    os.replace(config_file, f'{config_file}.old')


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
    apply_default_on_none=True,
)

settings.validators.register(*validators)

failed_validator = True
while failed_validator:
    try:
        settings.validators.validate_all()
        failed_validator = False
    except ValidationError as e:
        current_validator_details = e.details[0][0]
        logging.error(f"Validator failed for {current_validator_details.names[0]}: {e}")
        if hasattr(current_validator_details, 'default') and current_validator_details.default is not empty:
            old_value = settings.get(current_validator_details.names[0], 'undefined')
            settings[current_validator_details.names[0]] = current_validator_details.default
            logging.info(f"VALIDATOR RESET: {current_validator_details.names[0]} from '{old_value}' to '{current_validator_details.default}'")
        else:
            logging.critical(f"Value for {current_validator_details.names[0]} doesn't pass validation and there's no "
                             f"default value. This issue must be reported to and fixed by the development team. "
                             f"Bazarr won't work until it's been fixed.")
            stop_bazarr(EXIT_VALIDATION_ERROR)


def write_config():
    if settings.as_dict() == Dynaconf(
        settings_file=config_yaml_file,
        core_loaders=['YAML']
    ).as_dict():
        logging.debug("Nothing changed when comparing to config file. Skipping write to file.")
    else:
        try:
            write(settings_path=config_yaml_file + '.tmp',
                  settings_data={k.lower(): v for k, v in settings.as_dict().items()},
                  merge=False)
        except Exception as error:
            logging.exception(f"Exception raised while trying to save temporary settings file: {error}")
        else:
            try:
                move(config_yaml_file + '.tmp', config_yaml_file)
            except Exception as error:
                logging.exception(f"Exception raised while trying to overwrite settings file with temporary settings "
                                  f"file: {error}")


base_url = settings.general.base_url.rstrip('/')

ignore_keys = ['flask_secret_key']

array_keys = ['excluded_tags',
              'exclude',
              'included_codecs',
              'subzero_mods',
              'excluded_series_types',
              'enabled_providers',
              'enabled_integrations',
              'path_mappings',
              'path_mappings_movie',
              'remove_profile_tags',
              'language_equals',
              'blacklisted_languages',
              'blacklisted_providers']

empty_values = ['', 'None', 'null', 'undefined', None, []]

str_keys = ['chmod', 'log_include_filter', 'log_exclude_filter', 'password', 'f_password', 'hashed_password']

# Increase Sonarr and Radarr sync interval since we now use SignalR feed to update in real time
if settings.sonarr.series_sync < 15:
    settings.sonarr.series_sync = 60
if settings.radarr.movies_sync < 15:
    settings.radarr.movies_sync = 60

# Make sure to get of double slashes in base_url
settings.general.base_url = base_url_slash_cleaner(uri=settings.general.base_url)
settings.sonarr.base_url = base_url_slash_cleaner(uri=settings.sonarr.base_url)
settings.radarr.base_url = base_url_slash_cleaner(uri=settings.radarr.base_url)

# increase delay between searches to reduce impact on providers
if settings.general.wanted_search_frequency == 3:
    settings.general.wanted_search_frequency = 6
if settings.general.wanted_search_frequency_movie == 3:
    settings.general.wanted_search_frequency_movie = 6

# backward compatibility embeddedsubtitles provider
if hasattr(settings.embeddedsubtitles, 'unknown_as_english'):
    if settings.embeddedsubtitles.unknown_as_english:
        settings.embeddedsubtitles.unknown_as_fallback = True
        settings.embeddedsubtitles.fallback_lang = 'en'
    del settings.embeddedsubtitles.unknown_as_english
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


def validate_log_regex():
    # handle bug in dynaconf that changes strings to numbers, so change them back to str
    if not isinstance(settings.log.include_filter, str):
        settings.log.include_filter = str(settings.log.include_filter)
    if not isinstance(settings.log.exclude_filter, str):
        settings.log.exclude_filter = str(settings.log.exclude_filter)

    if settings.log.use_regex:
        # compile any regular expressions specified to see if they are valid
        # if invalid, tell the user which one
        try:
            re.compile(settings.log.include_filter)
        except Exception:
            raise ValidationError(f"Include filter: invalid regular expression: {settings.log.include_filter}")
        try:
            re.compile(settings.log.exclude_filter)
        except Exception:
            raise ValidationError(f"Exclude filter: invalid regular expression: {settings.log.exclude_filter}")


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

        # Make sure that text based form values aren't passed as list
        if isinstance(value, list) and len(value) == 1 and settings_keys[-1] not in array_keys:
            value = value[0]
            if value in empty_values and value != '':
                value = None

        # try to cast string as integer
        if isinstance(value, str) and settings_keys[-1] not in str_keys:
            try:
                value = int(value)
            except ValueError:
                pass

        # Make sure empty language list are stored correctly
        if settings_keys[-1] in array_keys and value[0] in empty_values:
            value = []

        # Handle path mappings settings since they are array in array
        if settings_keys[-1] in ['path_mappings', 'path_mappings_movie']:
            value = [x.split(',') for x in value if isinstance(x, str)]

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
                value = hashlib.md5(f"{value}".encode('utf-8')).hexdigest()

        if key == 'settings-general-debug':
            configure_debug = True

        if key == 'settings-general-hi_extension':
            os.environ["SZ_HI_EXTENSION"] = str(value)

        if key in ['settings-general-anti_captcha_provider', 'settings-anticaptcha-anti_captcha_key',
                   'settings-deathbycaptcha-username', 'settings-deathbycaptcha-password']:
            configure_captcha = True

        if key in ['update_schedule', 'settings-general-use_sonarr', 'settings-general-use_radarr',
                   'settings-general-auto_update', 'settings-general-upgrade_subs',
                   'settings-sonarr-series_sync', 'settings-radarr-movies_sync',
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
            if len(settings_keys) == 3:
                settings[settings_keys[1]][settings_keys[2]] = value
            elif len(settings_keys) == 4:
                settings[settings_keys[1]][settings_keys[2]][settings_keys[3]] = value

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
        settings.validators.validate()
        validate_log_regex()
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
            proxy = (f'{settings.proxy.type}://{quote_plus(settings.proxy.username)}:'
                     f'{quote_plus(settings.proxy.password)}@{settings.proxy.url}:{settings.proxy.port}')
        else:
            proxy = f'{settings.proxy.type}://{settings.proxy.url}:{settings.proxy.port}'
        os.environ['HTTP_PROXY'] = str(proxy)
        os.environ['HTTPS_PROXY'] = str(proxy)
        exclude = ','.join(settings.proxy.exclude)
        os.environ['NO_PROXY'] = exclude


def get_scores():
    settings = get_settings()
    return {"movie": settings["movie_scores"], "episode": settings["series_scores"]}


def sync_checker(subtitle):
    " This function can be extended with settings. It only takes a Subtitle argument"

    logging.debug("Checker data [%s] for %s", settings.subsync.checker, subtitle)

    bl_providers = settings.subsync.checker.blacklisted_providers

    # TODO
    # bl_languages = settings.subsync.checker.blacklisted_languages

    verdicts = set()

    # You can add more inner checkers. The following is a verfy basic one for providers,
    # but you can make your own functions, etc to handle more complex stuff. You have
    # subtitle data to compare.

    verdicts.add(subtitle.provider_name not in bl_providers)

    met = False not in verdicts

    if met is True:
        logging.debug("BAZARR Sync checker passed.")
        return True
    else:
        logging.debug("BAZARR Sync checker not passed. Won't sync.")
        return False


# Plex OAuth Migration Functions
def migrate_plex_config():
    # Generate encryption key if not exists or is empty
    existing_key = settings.plex.get('encryption_key')
    if not existing_key or existing_key.strip() == "":
        logging.info("Generating new encryption key for Plex token storage")
        key = secrets.token_urlsafe(32)
        settings.plex.encryption_key = key
        write_config()
        logging.info("Plex encryption key generated")


def initialize_plex():
    """
    Initialize Plex configuration on startup.
    Call this from your main application initialization.
    """
    # Run migration
    migrate_plex_config()
    
    # Start cache cleanup if OAuth is enabled
    if settings.general.use_plex and settings.plex.get('auth_method') == 'oauth':
        try:
            from api.plex.security import pin_cache
            
            def cleanup_task():
                while True:
                    time.sleep(300)  # 5 minutes
                    try:
                        pin_cache.cleanup_expired()
                    except Exception:
                        pass
            
            cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
            cleanup_thread.start()
            logging.info("Plex cache cleanup started")
        except ImportError:
            logging.warning("Could not start Plex cache cleanup - module not found")
    
    logging.info("Plex configuration initialized")

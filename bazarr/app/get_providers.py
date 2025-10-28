# coding=utf-8

import os
import datetime
import pytz
import logging
import subliminal_patch
import pretty
import time
import socket
import requests
import traceback
import re

from requests import ConnectionError
from subzero.language import Language
from subliminal_patch.exceptions import TooManyRequests, APIThrottled, ParseResponseError, IPAddressBlocked, \
    MustGetBlacklisted, SearchLimitReached, ProviderError, ForbiddenError
from subliminal.providers.opensubtitles import DownloadLimitReached, PaymentRequired, Unauthorized
from subliminal.exceptions import DownloadLimitExceeded, ServiceUnavailable, AuthenticationError, ConfigurationError
from subliminal import region as subliminal_cache_region
from subliminal_patch.extensions import provider_registry

from app.get_args import args
from app.config import settings
from languages.get_languages import CustomLanguage
from app.event_handler import event_stream
from utilities.binaries import get_binary
from radarr.blacklist import blacklist_log_movie
from sonarr.blacklist import blacklist_log
from utilities.analytics import event_tracker

_TRACEBACK_RE = re.compile(r'File "(.*?providers[\\/].*?)", line (\d+)')


def time_until_midnight(timezone):
    # type: (datetime.datetime) -> datetime.timedelta
    """
    Get timedelta until midnight.
    """
    now_in_tz = datetime.datetime.now(tz=timezone)
    midnight = now_in_tz.replace(hour=0, minute=0, second=0, microsecond=0) + \
               datetime.timedelta(days=1)
    return midnight - now_in_tz


# Titulky resets its download limits at the start of a new day from its perspective - the Europe/Prague timezone
# Needs to convert to offset-naive dt
def titulky_limit_reset_timedelta():
    return time_until_midnight(timezone=pytz.timezone('Europe/Prague'))


# LegendasDivx reset its searches limit at approximately midnight, Lisbon time, every day. We wait 1 more hours just
# to be sure.
def legendasdivx_limit_reset_timedelta():
    return time_until_midnight(timezone=pytz.timezone('Europe/Lisbon')) + datetime.timedelta(minutes=60)


VALID_THROTTLE_EXCEPTIONS = (TooManyRequests, DownloadLimitExceeded, ServiceUnavailable, APIThrottled,
                             ParseResponseError, IPAddressBlocked)
VALID_COUNT_EXCEPTIONS = ('TooManyRequests', 'ServiceUnavailable', 'APIThrottled', requests.exceptions.Timeout,
                          requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, socket.timeout)


def provider_throttle_map():
    return {
        "default": {
            TooManyRequests: (datetime.timedelta(hours=1), "1 hour"),
            DownloadLimitExceeded: (datetime.timedelta(hours=3), "3 hours"),
            ServiceUnavailable: (datetime.timedelta(minutes=20), "20 minutes"),
            APIThrottled: (datetime.timedelta(minutes=10), "10 minutes"),
            ParseResponseError: (datetime.timedelta(hours=6), "6 hours"),
            requests.exceptions.Timeout: (datetime.timedelta(hours=1), "1 hour"),
            socket.timeout: (datetime.timedelta(hours=1), "1 hour"),
            requests.exceptions.ConnectTimeout: (datetime.timedelta(hours=1), "1 hour"),
            requests.exceptions.ReadTimeout: (datetime.timedelta(hours=1), "1 hour"),
            ConfigurationError: (datetime.timedelta(hours=12), "12 hours"),
            PermissionError: (datetime.timedelta(hours=12), "12 hours"),
            requests.exceptions.ProxyError: (datetime.timedelta(hours=1), "1 hour"),
            AuthenticationError: (datetime.timedelta(hours=12), "12 hours"),
        },
        "opensubtitles": {
            TooManyRequests: (datetime.timedelta(hours=3), "3 hours"),
            DownloadLimitExceeded: (datetime.timedelta(hours=6), "6 hours"),
            DownloadLimitReached: (datetime.timedelta(hours=6), "6 hours"),
            PaymentRequired: (datetime.timedelta(hours=12), "12 hours"),
            Unauthorized: (datetime.timedelta(hours=12), "12 hours"),
            APIThrottled: (datetime.timedelta(seconds=15), "15 seconds"),
            ServiceUnavailable: (datetime.timedelta(hours=1), "1 hour"),
        },
        "opensubtitlescom": {
            TooManyRequests: (datetime.timedelta(minutes=1), "1 minute"),
            DownloadLimitExceeded: (datetime.timedelta(hours=6), "6 hours"),
        },
        "addic7ed": {
            DownloadLimitExceeded: (datetime.timedelta(hours=3), "3 hours"),
            TooManyRequests: (datetime.timedelta(minutes=5), "5 minutes"),
            IPAddressBlocked: (datetime.timedelta(hours=1), "1 hours"),
        },
        "titlovi": {
            TooManyRequests: (datetime.timedelta(minutes=5), "5 minutes"),
        },
        "titrari": {
            TooManyRequests: (datetime.timedelta(minutes=10), "10 minutes"),
        },
        "titulky": {
            DownloadLimitExceeded: (
                titulky_limit_reset_timedelta(),
                f"{titulky_limit_reset_timedelta().seconds // 3600 + 1} hours")
        },
        "legendasdivx": {
            TooManyRequests: (datetime.timedelta(hours=3), "3 hours"),
            DownloadLimitExceeded: (
                legendasdivx_limit_reset_timedelta(),
                f"{legendasdivx_limit_reset_timedelta().seconds // 3600 + 1} hours"),
            IPAddressBlocked: (
                legendasdivx_limit_reset_timedelta(),
                f"{legendasdivx_limit_reset_timedelta().seconds // 3600 + 1} hours"),
            SearchLimitReached: (
                legendasdivx_limit_reset_timedelta(),
                f"{legendasdivx_limit_reset_timedelta().seconds // 3600 + 1} hours"),
        },
        "whisperai": {
            ConnectionError: (datetime.timedelta(hours=24), "24 hours"),
        },
        "regielive": {
            APIThrottled: (datetime.timedelta(hours=1), "1 hour"),
            TooManyRequests: (datetime.timedelta(minutes=5), "5 minutes"),
            ProviderError: (datetime.timedelta(minutes=10), "10 minutes"),
        },
        "subsource": {
            APIThrottled: (datetime.timedelta(minutes=10), "10 minutes"),
            AuthenticationError: (datetime.timedelta(hours=1), "1 hour"),
            ForbiddenError: (datetime.timedelta(minutes=15), "15 minutes"),
            TooManyRequests: (datetime.timedelta(hours=1), "1 hour"),
        },
    }


PROVIDERS_FORCED_OFF = ["addic7ed", "tvsubtitles", "legendasdivx", "napiprojekt", "shooter",
                        "hosszupuska", "supersubtitles", "titlovi", "assrt"]

throttle_count = {}


def provider_pool():
    if settings.general.multithreading:
        return subliminal_patch.core.SZAsyncProviderPool
    return subliminal_patch.core.SZProviderPool


def _lang_from_str(content: str):
    " Formats: es-MX en@hi es-MX@forced "
    extra_info = content.split("@")
    if len(extra_info) > 1:
        kwargs = {extra_info[-1]: True}
    else:
        kwargs = {}

    content = extra_info[0]

    try:
        code, country = content.split("-")
    except ValueError:
        lang = CustomLanguage.from_value(content)
        if lang is not None:
            lang = lang.subzero_language()
            return lang.rebuild(lang, **kwargs)

        code, country = content, None

    return subliminal_patch.core.Language(code, country, **kwargs)


def get_language_equals(settings_=None):
    settings_ = settings_ or settings

    equals = settings_.general.language_equals
    if not equals:
        return []

    items = []
    for equal in equals:
        try:
            from_, to_ = equal.split(":")
            from_, to_ = _lang_from_str(from_), _lang_from_str(to_)
        except Exception as error:
            logging.info("Invalid equal value: '%s' [%s]", equal, error)
        else:
            items.append((from_, to_))

    return items


def get_providers():
    providers_list = []
    existing_providers = provider_registry.names()
    providers = [x for x in settings.general.enabled_providers if x in existing_providers]
    for provider in providers:
        reason, until, throttle_desc = tp.get(provider, (None, None, None))
        providers_list.append(provider)

        if reason:
            now = datetime.datetime.now()
            if now < until:
                logging.debug("Not using %s until %s, because of: %s", provider,
                              until.strftime("%y/%m/%d %H:%M"), reason)
                providers_list.remove(provider)
            else:
                logging.info("Using %s again after %s, (disabled because: %s)", provider, throttle_desc, reason)
                del tp[provider]
                set_throttled_providers(str(tp))
        # if forced only is enabled: # fixme: Prepared for forced only implementation to remove providers with don't support forced only subtitles
        #     for provider in providers_list:
        #         if provider in PROVIDERS_FORCED_OFF:
        #             providers_list.remove(provider)

    if not providers_list:
        providers_list = None

    return providers_list


def get_enabled_providers():
    # return enabled provider including those who can be throttled
    if isinstance(settings.general.enabled_providers, list):
        return settings.general.enabled_providers
    else:
        return []


_FFPROBE_BINARY = get_binary("ffprobe")
_FFMPEG_BINARY = get_binary("ffmpeg")


def get_providers_auth():
    return {
        'addic7ed': {
            'username': settings.addic7ed.username,
            'password': settings.addic7ed.password,
            'cookies': settings.addic7ed.cookies,
            'user_agent': settings.addic7ed.user_agent,
            'is_vip': settings.addic7ed.vip,
        },
        'avistaz': {
            'cookies': settings.avistaz.cookies,
            'user_agent': settings.avistaz.user_agent,
        },
        'cinemaz': {
            'cookies': settings.cinemaz.cookies,
            'user_agent': settings.cinemaz.user_agent,
        },
        'opensubtitles': {
            'username': settings.opensubtitles.username,
            'password': settings.opensubtitles.password,
            'use_tag_search': settings.opensubtitles.use_tag_search,
            'only_foreign': False,  # fixme
            'also_foreign': False,  # fixme
            'is_vip': settings.opensubtitles.vip,
            'use_ssl': settings.opensubtitles.ssl,
            'timeout': int(settings.opensubtitles.timeout) or 15,
            'skip_wrong_fps': settings.opensubtitles.skip_wrong_fps,
        },
        'opensubtitlescom': {'username': settings.opensubtitlescom.username,
                             'password': settings.opensubtitlescom.password,
                             'use_hash': settings.opensubtitlescom.use_hash,
                             'include_ai_translated': settings.opensubtitlescom.include_ai_translated,
                             'api_key': 's38zmzVlW7IlYruWi7mHwDYl2SfMQoC1'
                             },
        'napiprojekt': {'only_authors': settings.napiprojekt.only_authors,
                        'only_real_names': settings.napiprojekt.only_real_names},
        'podnapisi': {
            'only_foreign': False,  # fixme
            'also_foreign': False,  # fixme
            'verify_ssl': settings.podnapisi.verify_ssl
        },
        'legendasdivx': {
            'username': settings.legendasdivx.username,
            'password': settings.legendasdivx.password,
            'skip_wrong_fps': settings.legendasdivx.skip_wrong_fps,
        },
        'legendasnet': {
            'username': settings.legendasnet.username,
            'password': settings.legendasnet.password,
        },
        'xsubs': {
            'username': settings.xsubs.username,
            'password': settings.xsubs.password,
        },
        'assrt': {
            'token': settings.assrt.token,
        },
        'napisy24': {
            'username': settings.napisy24.username,
            'password': settings.napisy24.password,
        },
        'betaseries': {'token': settings.betaseries.token},
        'titulky': {
            'username': settings.titulky.username,
            'password': settings.titulky.password,
            'approved_only': settings.titulky.approved_only,
            'skip_wrong_fps': settings.titulky.skip_wrong_fps,
        },
        'titlovi': {
            'username': settings.titlovi.username,
            'password': settings.titlovi.password,
        },
        'jimaku': {
            'api_key': settings.jimaku.api_key,
            'enable_name_search_fallback': settings.jimaku.enable_name_search_fallback,
            'enable_archives_download': settings.jimaku.enable_archives_download,
            'enable_ai_subs': settings.jimaku.enable_ai_subs,
        },
        'ktuvit': {
            'email': settings.ktuvit.email,
            'hashed_password': settings.ktuvit.hashed_password,
        },
        'embeddedsubtitles': {
            'included_codecs': settings.embeddedsubtitles.included_codecs,
            'hi_fallback': settings.embeddedsubtitles.hi_fallback,
            'cache_dir': os.path.join(args.config_dir, "cache"),
            'ffprobe_path': _FFPROBE_BINARY,
            'ffmpeg_path': _FFMPEG_BINARY,
            'timeout': settings.embeddedsubtitles.timeout,
            'unknown_as_fallback': settings.embeddedsubtitles.unknown_as_fallback,
            'fallback_lang': settings.embeddedsubtitles.fallback_lang,
        },
        'karagarga': {
            'username': settings.karagarga.username,
            'password': settings.karagarga.password,
            'f_username': settings.karagarga.f_username,
            'f_password': settings.karagarga.f_password,
        },
        'hdbits': {
            'username': settings.hdbits.username,
            'passkey': settings.hdbits.passkey,
        },
        'subf2m': {
            'verify_ssl': settings.subf2m.verify_ssl,
            'user_agent': settings.subf2m.user_agent,
        },
        'whisperai': {
            'endpoint': settings.whisperai.endpoint,
            'response': settings.whisperai.response,
            'timeout': settings.whisperai.timeout,
            'ffmpeg_path': _FFMPEG_BINARY,
            'loglevel': settings.whisperai.loglevel,
            'pass_video_name': settings.whisperai.pass_video_name,
        },
        "animetosho": {
            'search_threshold': settings.animetosho.search_threshold,
        },
        "subdl": {
            'api_key': settings.subdl.api_key,
        },
        'turkcealtyaziorg': {
            'cookies': settings.turkcealtyaziorg.cookies,
            'user_agent': settings.turkcealtyaziorg.user_agent,
        },
        'subsource': {
            'api_key': settings.subsource.apikey,
        },
        'animesubinfo': {}
    }


def _handle_mgb(name, exception, ids, language):
    if language.forced:
        language_str = f'{language.basename}:forced'
    elif language.hi:
        language_str = f'{language.basename}:hi'
    else:
        language_str = language.basename

    if ids:
        if exception.media_type == "series":
            if 'sonarrSeriesId' in ids and 'sonarrEpsiodeId' in ids:
                blacklist_log(ids['sonarrSeriesId'], ids['sonarrEpisodeId'], name, exception.id, language_str)
        else:
            blacklist_log_movie(ids['radarrId'], name, exception.id, language_str)


def provider_throttle(name, exception, ids=None, language=None):
    if isinstance(exception, MustGetBlacklisted) and isinstance(ids, dict) and isinstance(language, Language):
        return _handle_mgb(name, exception, ids, language)

    cls = getattr(exception, "__class__")
    cls_name = getattr(cls, "__name__")
    if cls not in VALID_THROTTLE_EXCEPTIONS:
        for valid_cls in VALID_THROTTLE_EXCEPTIONS:
            if isinstance(cls, valid_cls):
                cls = valid_cls

    throttle_data = provider_throttle_map().get(name, provider_throttle_map()["default"]).get(cls, None) or \
                    provider_throttle_map()["default"].get(cls, None)

    if throttle_data:
        throttle_delta, throttle_description = throttle_data
    else:
        throttle_delta, throttle_description = datetime.timedelta(minutes=10), "10 minutes"

    throttle_until = datetime.datetime.now() + throttle_delta

    if cls_name not in VALID_COUNT_EXCEPTIONS or throttled_count(name):
        if cls_name == 'ValueError' and isinstance(exception.args, tuple) and len(exception.args) and exception.args[
            0].startswith('unsupported pickle protocol'):
            for fn in subliminal_cache_region.backend.all_filenames:
                try:
                    os.remove(fn)
                except (IOError, OSError):
                    logging.debug("Couldn't remove cache file: %s", os.path.basename(fn))
        else:
            tp[name] = (cls_name, throttle_until, throttle_description)
            set_throttled_providers(str(tp))

            trac_info = _get_traceback_info(exception)

            logging.info("Throttling %s for %s, until %s, because of: %s. Exception info: %r", name,
                         throttle_description, throttle_until.strftime("%y/%m/%d %H:%M"), cls_name, trac_info)
            event_tracker.track_throttling(provider=name, exception_name=cls_name, exception_info=trac_info)

    update_throttled_provider()


def _get_traceback_info(exc: Exception):
    traceback_str = " ".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    clean_msg = str(exc).replace("\n", " ").strip()

    line_info = _TRACEBACK_RE.findall(traceback_str)

    # Value info max chars len is 100

    if not line_info:
        return clean_msg[:100]

    line_info = line_info[-1]
    file_, line = line_info

    extra = f"' ~ {os.path.basename(file_)}@{line}"[:90]
    message = f"'{clean_msg}"[:100 - len(extra)]

    return message + extra


def throttled_count(name):
    global throttle_count
    if name in list(throttle_count.keys()):
        if 'count' in list(throttle_count[name].keys()):
            for key, value in throttle_count[name].items():
                if key == 'count':
                    value += 1
                    throttle_count[name]['count'] = value
        else:
            throttle_count[name] = {"count": 1, "time": (datetime.datetime.now() + datetime.timedelta(seconds=120))}

    else:
        throttle_count[name] = {"count": 1, "time": (datetime.datetime.now() + datetime.timedelta(seconds=120))}

    if throttle_count[name]['count'] >= 5:
        return True
    if throttle_count[name]['time'] <= datetime.datetime.now():
        throttle_count[name] = {"count": 1, "time": (datetime.datetime.now() + datetime.timedelta(seconds=120))}
    logging.info("Provider %s throttle count %s of 5, waiting 5sec and trying again", name,
                 throttle_count[name]['count'])
    time.sleep(5)
    return False


def update_throttled_provider():
    existing_providers = provider_registry.names()
    providers_list = [x for x in settings.general.enabled_providers if x in existing_providers]

    for provider in list(tp):
        if provider not in providers_list:
            del tp[provider]
            set_throttled_providers(str(tp))

        reason, until, throttle_desc = tp.get(provider, (None, None, None))

        if reason:
            now = datetime.datetime.now()
            if now < until:
                pass
            else:
                logging.info("Using %s again after %s, (disabled because: %s)", provider, throttle_desc, reason)
                del tp[provider]
                set_throttled_providers(str(tp))

            reason, until, throttle_desc = tp.get(provider, (None, None, None))

            if reason:
                now = datetime.datetime.now()
                if now >= until:
                    logging.info("Using %s again after %s, (disabled because: %s)", provider, throttle_desc, reason)
                    del tp[provider]
                    set_throttled_providers(str(tp))

    event_stream(type='badges')


def list_throttled_providers():
    update_throttled_provider()
    throttled_providers = []
    existing_providers = provider_registry.names()
    providers = [x for x in settings.general.enabled_providers if x in existing_providers]
    for provider in providers:
        reason, until, throttle_desc = tp.get(provider, (None, None, None))
        throttled_providers.append([provider, reason, pretty.date(until)])
    return throttled_providers


def reset_throttled_providers(only_auth_or_conf_error=False):
    for provider in list(tp):
        if only_auth_or_conf_error and tp[provider][0] not in ['AuthenticationError', 'ConfigurationError',
                                                               'PaymentRequired']:
            continue
        del tp[provider]
    set_throttled_providers(str(tp))
    update_throttled_provider()
    if only_auth_or_conf_error:
        logging.info('BAZARR throttled providers have been reset (only AuthenticationError, ConfigurationError and '
                     'PaymentRequired).')
    else:
        logging.info('BAZARR throttled providers have been reset.')


def get_throttled_providers():
    providers = {}
    try:
        if os.path.exists(os.path.join(args.config_dir, 'config', 'throttled_providers.dat')):
            with open(os.path.normpath(os.path.join(args.config_dir, 'config', 'throttled_providers.dat')), 'r') as \
                    handle:
                providers = eval(handle.read())
    except Exception:
        # set empty content in throttled_providers.dat
        logging.error("Invalid content in throttled_providers.dat. Resetting")
        set_throttled_providers(str(providers))
    finally:
        return providers


def set_throttled_providers(data):
    with open(os.path.normpath(os.path.join(args.config_dir, 'config', 'throttled_providers.dat')), 'w+') as handle:
        handle.write(data)


tp = get_throttled_providers()
if not isinstance(tp, dict):
    raise ValueError('tp should be a dict')

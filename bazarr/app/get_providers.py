# coding=utf-8

import ast
import os
import datetime
import pytz
import logging
import subliminal_patch
import pretty
import time
import socket
import requests

from subliminal_patch.exceptions import TooManyRequests, APIThrottled, ParseResponseError, IPAddressBlocked, \
    MustGetBlacklisted, SearchLimitReached
from subliminal.providers.opensubtitles import DownloadLimitReached
from subliminal.exceptions import DownloadLimitExceeded, ServiceUnavailable
from subliminal import region as subliminal_cache_region
from subliminal_patch.extensions import provider_registry

from app.get_args import args
from app.config import settings, get_array_from
from app.event_handler import event_stream
from utilities.binaries import get_binary
from radarr.blacklist import blacklist_log_movie
from sonarr.blacklist import blacklist_log


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
        },
        "opensubtitles": {
            TooManyRequests: (datetime.timedelta(hours=3), "3 hours"),
            DownloadLimitExceeded: (datetime.timedelta(hours=6), "6 hours"),
            DownloadLimitReached: (datetime.timedelta(hours=6), "6 hours"),
            APIThrottled: (datetime.timedelta(seconds=15), "15 seconds"),
        },
        "opensubtitlescom": {
            TooManyRequests: (datetime.timedelta(minutes=1), "1 minute"),
            DownloadLimitExceeded: (datetime.timedelta(hours=24), "24 hours"),
        },
        "addic7ed": {
            DownloadLimitExceeded: (datetime.timedelta(hours=3), "3 hours"),
            TooManyRequests: (datetime.timedelta(minutes=5), "5 minutes"),
            IPAddressBlocked: (datetime.timedelta(hours=1), "1 hours"),
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
        }
    }


PROVIDERS_FORCED_OFF = ["addic7ed", "tvsubtitles", "legendasdivx", "legendastv", "napiprojekt", "shooter",
                        "hosszupuska", "supersubtitles", "titlovi", "argenteam", "assrt", "subscene"]

throttle_count = {}


def provider_pool():
    if settings.general.getboolean('multithreading'):
        return subliminal_patch.core.SZAsyncProviderPool
    return subliminal_patch.core.SZProviderPool


def get_providers():
    providers_list = []
    existing_providers = provider_registry.names()
    providers = [x for x in get_array_from(settings.general.enabled_providers) if x in existing_providers]
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
    try:
        return ast.literal_eval(settings.general.enabled_providers)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
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
            'is_vip': settings.addic7ed.getboolean('vip'),
        },
        'opensubtitles': {
            'username': settings.opensubtitles.username,
            'password': settings.opensubtitles.password,
            'use_tag_search': settings.opensubtitles.getboolean(
                    'use_tag_search'
            ),
            'only_foreign': False,  # fixme
            'also_foreign': False,  # fixme
            'is_vip': settings.opensubtitles.getboolean('vip'),
            'use_ssl': settings.opensubtitles.getboolean('ssl'),
            'timeout': int(settings.opensubtitles.timeout) or 15,
            'skip_wrong_fps': settings.opensubtitles.getboolean(
                    'skip_wrong_fps'
            ),
        },
        'opensubtitlescom': {'username': settings.opensubtitlescom.username,
                             'password': settings.opensubtitlescom.password,
                             'use_hash': settings.opensubtitlescom.getboolean('use_hash'),
                             'api_key': 's38zmzVlW7IlYruWi7mHwDYl2SfMQoC1'
                             },
        'podnapisi': {
            'only_foreign': False,  # fixme
            'also_foreign': False,  # fixme
            'verify_ssl': settings.podnapisi.getboolean('verify_ssl')
        },
        'subscene': {
            'username': settings.subscene.username,
            'password': settings.subscene.password,
            'only_foreign': False,  # fixme
        },
        'legendasdivx': {
            'username': settings.legendasdivx.username,
            'password': settings.legendasdivx.password,
            'skip_wrong_fps': settings.legendasdivx.getboolean(
                    'skip_wrong_fps'
            ),
        },
        'legendastv': {
            'username': settings.legendastv.username,
            'password': settings.legendastv.password,
            'featured_only': settings.legendastv.getboolean(
                    'featured_only'
            ),
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
            'approved_only': settings.titulky.getboolean('approved_only'),
        },
        'titlovi': {
            'username': settings.titlovi.username,
            'password': settings.titlovi.password,
        },
        'ktuvit': {
            'email': settings.ktuvit.email,
            'hashed_password': settings.ktuvit.hashed_password,
        },
        'embeddedsubtitles': {
            'included_codecs': get_array_from(settings.embeddedsubtitles.included_codecs),
            'hi_fallback': settings.embeddedsubtitles.getboolean('hi_fallback'),
            'cache_dir': os.path.join(args.config_dir, "cache"),
            'ffprobe_path': _FFPROBE_BINARY,
            'ffmpeg_path': _FFMPEG_BINARY,
            'timeout': settings.embeddedsubtitles.timeout,
            'unknown_as_english': settings.embeddedsubtitles.getboolean('unknown_as_english'),
        },
        'karagarga': {
            'username': settings.karagarga.username,
            'password': settings.karagarga.password,
            'f_username': settings.karagarga.f_username,
            'f_password': settings.karagarga.f_password,
        },
        'subf2m': {
            'verify_ssl': settings.subf2m.getboolean('verify_ssl')
        },
        'whisperai': {
            'endpoint': settings.whisperai.endpoint,
            'timeout': settings.whisperai.timeout
        }
    }


def _handle_mgb(name, exception):
    # There's no way to get Radarr/Sonarr IDs from subliminal_patch. Blacklisted subtitles
    # will not appear on fronted but they will work with get_blacklist
    if exception.media_type == "series":
        blacklist_log("", "", name, exception.id, "")
    else:
        blacklist_log_movie("", name, exception.id, "")


def provider_throttle(name, exception):
    if isinstance(exception, MustGetBlacklisted):
        return _handle_mgb(name, exception)

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
        if cls_name == 'ValueError' and exception.args[0].startswith('unsupported pickle protocol'):
            for fn in subliminal_cache_region.backend.all_filenames:
                try:
                    os.remove(fn)
                except (IOError, OSError):
                    logging.debug("Couldn't remove cache file: %s", os.path.basename(fn))
        else:
            tp[name] = (cls_name, throttle_until, throttle_description)
            set_throttled_providers(str(tp))

            logging.info("Throttling %s for %s, until %s, because of: %s. Exception info: %r", name,
                         throttle_description, throttle_until.strftime("%y/%m/%d %H:%M"), cls_name, exception.args[0]
                         if exception.args else None)

    update_throttled_provider()


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
    providers_list = [x for x in get_array_from(settings.general.enabled_providers) if x in existing_providers]

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
    providers = [x for x in get_array_from(settings.general.enabled_providers) if x in existing_providers]
    for provider in providers:
        reason, until, throttle_desc = tp.get(provider, (None, None, None))
        throttled_providers.append([provider, reason, pretty.date(until)])
    return throttled_providers


def reset_throttled_providers():
    for provider in list(tp):
        del tp[provider]
    set_throttled_providers(str(tp))
    update_throttled_provider()
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
        set_throttled_providers(providers)
    finally:
        return providers


def set_throttled_providers(data):
    with open(os.path.normpath(os.path.join(args.config_dir, 'config', 'throttled_providers.dat')), 'w+') as handle:
        handle.write(data)


tp = get_throttled_providers()
if not isinstance(tp, dict):
    raise ValueError('tp should be a dict')

# coding=utf-8
import os
import datetime
import logging
import subliminal_patch
import pretty
import time
import socket
import requests
import ast

from get_args import args
from config import settings, get_array_from
from event_handler import event_stream
from subliminal_patch.exceptions import TooManyRequests, APIThrottled, ParseResponseError, IPAddressBlocked
from subliminal.providers.opensubtitles import DownloadLimitReached
from subliminal.exceptions import DownloadLimitExceeded, ServiceUnavailable
from subliminal import region as subliminal_cache_region


def time_until_end_of_day(dt=None):
    # type: (datetime.datetime) -> datetime.timedelta
    """
    Get timedelta until end of day on the datetime passed, or current time.
    """
    if dt is None:
        dt = datetime.datetime.now()
    tomorrow = dt + datetime.timedelta(days=1)
    return datetime.datetime.combine(tomorrow, datetime.time.min) - dt


hours_until_end_of_day = time_until_end_of_day().seconds // 3600 + 1

VALID_THROTTLE_EXCEPTIONS = (TooManyRequests, DownloadLimitExceeded, ServiceUnavailable, APIThrottled,
                             ParseResponseError, IPAddressBlocked)
VALID_COUNT_EXCEPTIONS = ('TooManyRequests', 'ServiceUnavailable', 'APIThrottled', requests.exceptions.Timeout,
                          requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, socket.timeout)

PROVIDER_THROTTLE_MAP = {
    "default"         : {
        TooManyRequests                   : (datetime.timedelta(hours=1), "1 hour"),
        DownloadLimitExceeded             : (datetime.timedelta(hours=3), "3 hours"),
        ServiceUnavailable                : (datetime.timedelta(minutes=20), "20 minutes"),
        APIThrottled                      : (datetime.timedelta(minutes=10), "10 minutes"),
        ParseResponseError                : (datetime.timedelta(hours=6), "6 hours"),
        requests.exceptions.Timeout       : (datetime.timedelta(hours=1), "1 hour"),
        socket.timeout                    : (datetime.timedelta(hours=1), "1 hour"),
        requests.exceptions.ConnectTimeout: (datetime.timedelta(hours=1), "1 hour"),
        requests.exceptions.ReadTimeout   : (datetime.timedelta(hours=1), "1 hour"),
    },
    "opensubtitles"   : {
        TooManyRequests      : (datetime.timedelta(hours=3), "3 hours"),
        DownloadLimitExceeded: (datetime.timedelta(hours=6), "6 hours"),
        DownloadLimitReached : (datetime.timedelta(hours=6), "6 hours"),
        APIThrottled         : (datetime.timedelta(seconds=15), "15 seconds"),
    },
    "opensubtitlescom": {
        TooManyRequests      : (datetime.timedelta(minutes=1), "1 minute"),
        DownloadLimitExceeded: (
        datetime.timedelta(hours=hours_until_end_of_day), "{} hours".format(str(hours_until_end_of_day))),
    },
    "addic7ed"        : {
        DownloadLimitExceeded: (datetime.timedelta(hours=3), "3 hours"),
        TooManyRequests      : (datetime.timedelta(minutes=5), "5 minutes"),
        IPAddressBlocked     : (datetime.timedelta(hours=1), "1 hours"),
    },
    "titulky"         : {
        DownloadLimitExceeded: (
        datetime.timedelta(hours=hours_until_end_of_day), "{} hours".format(str(hours_until_end_of_day)))
    },
    "legendasdivx"    : {
        TooManyRequests      : (datetime.timedelta(hours=3), "3 hours"),
        DownloadLimitExceeded: (
        datetime.timedelta(hours=hours_until_end_of_day), "{} hours".format(str(hours_until_end_of_day))),
        IPAddressBlocked     : (
        datetime.timedelta(hours=hours_until_end_of_day), "{} hours".format(str(hours_until_end_of_day))),
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
    providers = get_array_from(settings.general.enabled_providers)
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


def get_providers_auth():
    return {
        'addic7ed'        : {
            'username': settings.addic7ed.username,
            'password': settings.addic7ed.password,
        },
        'opensubtitles'   : {
            'username'      : settings.opensubtitles.username,
            'password'      : settings.opensubtitles.password,
            'use_tag_search': settings.opensubtitles.getboolean(
                    'use_tag_search'
            ),
            'only_foreign'  : False,  # fixme
            'also_foreign'  : False,  # fixme
            'is_vip'        : settings.opensubtitles.getboolean('vip'),
            'use_ssl'       : settings.opensubtitles.getboolean('ssl'),
            'timeout'       : int(settings.opensubtitles.timeout) or 15,
            'skip_wrong_fps': settings.opensubtitles.getboolean(
                    'skip_wrong_fps'
            ),
        },
        'opensubtitlescom': {'username': settings.opensubtitlescom.username,
                             'password': settings.opensubtitlescom.password,
                             'use_hash': settings.opensubtitlescom.getboolean('use_hash'),
                             'api_key' : 's38zmzVlW7IlYruWi7mHwDYl2SfMQoC1'
                             },
        'podnapisi'       : {
            'only_foreign': False,  # fixme
            'also_foreign': False,  # fixme
        },
        'subscene'        : {
            'username'    : settings.subscene.username,
            'password'    : settings.subscene.password,
            'only_foreign': False,  # fixme
        },
        'legendasdivx'    : {
            'username'      : settings.legendasdivx.username,
            'password'      : settings.legendasdivx.password,
            'skip_wrong_fps': settings.legendasdivx.getboolean(
                    'skip_wrong_fps'
            ),
        },
        'legendastv'      : {
            'username': settings.legendastv.username,
            'password': settings.legendastv.password,
        },
        'xsubs'           : {
            'username': settings.xsubs.username,
            'password': settings.xsubs.password,
        },
        'assrt'           : {
            'token': settings.assrt.token,
        },
        'napisy24'        : {
            'username': settings.napisy24.username,
            'password': settings.napisy24.password,
        },
        'betaseries'      : {'token': settings.betaseries.token},
        'titulky'         : {
            'username': settings.titulky.username,
            'password': settings.titulky.password,
        },
        'titlovi'         : {
            'username': settings.titlovi.username,
            'password': settings.titlovi.password,
        },
    }


def provider_throttle(name, exception):
    cls = getattr(exception, "__class__")
    cls_name = getattr(cls, "__name__")
    if cls not in VALID_THROTTLE_EXCEPTIONS:
        for valid_cls in VALID_THROTTLE_EXCEPTIONS:
            if isinstance(cls, valid_cls):
                cls = valid_cls

    throttle_data = PROVIDER_THROTTLE_MAP.get(name, PROVIDER_THROTTLE_MAP["default"]).get(cls, None) or \
                    PROVIDER_THROTTLE_MAP["default"].get(cls, None)

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
    changed = False
    providers_list = get_array_from(settings.general.enabled_providers)

    for provider in list(tp):
        if provider not in providers_list:
            del tp[provider]
            settings.general.throtteled_providers = str(tp)
            changed = True

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

        event_stream(type='badges_providers')


def list_throttled_providers():
    update_throttled_provider()
    throttled_providers = []
    providers = get_array_from(settings.general.enabled_providers)
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
    if os.path.exists(os.path.join(args.config_dir, 'config', 'throttled_providers.dat')):
        with open(os.path.normpath(os.path.join(args.config_dir, 'config', 'throttled_providers.dat')), 'r') as handle:
            providers = handle.read()
    if not providers:
        providers = {}
    return providers


def set_throttled_providers(data):
    with open(os.path.normpath(os.path.join(args.config_dir, 'config', 'throttled_providers.dat')), 'w+') as handle:
        handle.write(data)


try:
    tp = eval(str(get_throttled_providers()))
    if not isinstance(tp, dict):
        raise ValueError('tp should be a dict')
except Exception:
    logging.error("Invalid content in throttled_providers.dat. Resetting")
    # set empty content in throttled_providers.dat
    set_throttled_providers('')
    tp = eval(str(get_throttled_providers()))

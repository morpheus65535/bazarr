# coding=utf-8
# fmt: off

import logging
import time

from inspect import getfullargspec

from radarr.blacklist import get_blacklist_movie
from sonarr.blacklist import get_blacklist
from app.get_providers import get_providers, get_providers_auth, provider_throttle, provider_pool

from .utils import get_ban_list


# fmt: on
def _init_pool(media_type, profile_id=None, providers=None):
    pool = provider_pool()
    return pool(
        providers=providers or get_providers(),
        provider_configs=get_providers_auth(),
        blacklist=get_blacklist() if media_type == 'series' else get_blacklist_movie(),
        throttle_callback=provider_throttle,
        ban_list=get_ban_list(profile_id),
        language_hook=None,
    )


_pools = {}


def _get_pool(media_type, profile_id=None):
    try:
        return _pools[f'{media_type}_{profile_id or ""}']
    except KeyError:
        _update_pool(media_type, profile_id)

        return _pools[f'{media_type}_{profile_id or ""}']


def _update_pool(media_type, profile_id=None):
    pool_key = f'{media_type}_{profile_id or ""}'
    logging.debug(f"BAZARR updating pool: {pool_key}")

    # Init a new pool if not present
    if pool_key not in _pools:
        logging.debug(f"BAZARR pool not initialized: {pool_key}. Initializing")
        _pools[pool_key] = _init_pool(media_type, profile_id)

    pool = _pools[pool_key]
    if pool is None:
        return False

    return pool.update(
        get_providers(),
        get_providers_auth(),
        get_blacklist() if media_type == 'series' else get_blacklist_movie(),
        get_ban_list(profile_id),
    )


def update_pools(f):
    """Decorator that ensures all pools are updated on each function run.
    It will detect any config changes in Bazarr"""

    def decorated(*args, **kwargs):
        logging.debug(f"BAZARR updating pools: {_pools}", )

        start = time.time()
        args_spec = getfullargspec(f).args

        try:
            profile_id = args[args_spec.index("profile_id")]
        except (IndexError, ValueError):
            profile_id = None

        updated = _update_pool(args[args_spec.index("media_type")], profile_id)

        if updated:
            logging.debug(f"BAZARR pools update elapsed time: {round((time.time() - start) * 1000, 2)}ms")
        return f(*args, **kwargs)

    return decorated

# -*- coding: utf-8 -*-

import datetime
import time
import pickle
import tmdbsimple as tmdb

from database import TableTmdbCache

# the cache is marked to expire after 1 day. This could be fine tuned in the future.
CACHE_EXPIRATION_TIME = datetime.timedelta(days=1).total_seconds()

# TMDB v3 API key for Bazarr
tmdb.API_KEY = "e5577e69d409c601acb98d5bfcee31c7"


def tmdb_func_cache(func, *args, **kwargs):
    try:
        # try to pickle both func and kwargs
        pickled_func = pickle.dumps(func, pickle.HIGHEST_PROTOCOL)
        pickled_kwargs = pickle.dumps(kwargs, pickle.HIGHEST_PROTOCOL)
    except Exception:
        # if we can't pickle them, we run the function and return the result directly without caching it
        return func(**kwargs)
    else:
        try:
            # If we were able to pickle func and kwargs, we try to find a matching result in db that isn't expired
            cached_result = TableTmdbCache.select(TableTmdbCache.result) \
                .where((TableTmdbCache.function == pickled_func) &
                       (TableTmdbCache.arguments == pickled_kwargs) &
                       (TableTmdbCache.timestamp > (time.time() - CACHE_EXPIRATION_TIME))) \
                .dicts() \
                .get()
        except TableTmdbCache.DoesNotExist:
            # ok we didn't find one...
            cached_result = None
        if cached_result:
            try:
                # we try to unpickle the matching cache result
                pickled_result = pickle.loads(cached_result['result'])
            except Exception:
                # if we fail we renew the cache
                return renew_cache(func, pickled_func, pickled_kwargs, **kwargs)
            else:
                # else we return the cached value
                return pickled_result
        else:
            # as we haven't found a non expired cache item, we'll have to renew the cache
            return renew_cache(func, pickled_func, pickled_kwargs, **kwargs)


def renew_cache(func, pickled_func, pickled_kwargs, **kwargs):
    # function to run a function with it's kwargs, store the pickled result in db and return it
    result = func(**kwargs)
    TableTmdbCache.insert({
        TableTmdbCache.timestamp: time.time(),
        TableTmdbCache.function: pickled_func,
        TableTmdbCache.arguments: pickled_kwargs,
        TableTmdbCache.result: pickle.dumps(result, pickle.HIGHEST_PROTOCOL)
    }).execute()
    return result


def clean_cache():
    # delete expired entries from the tmdb cache
    TableTmdbCache.delete().where(TableTmdbCache.timestamp < (time.time() - CACHE_EXPIRATION_TIME)).execute()

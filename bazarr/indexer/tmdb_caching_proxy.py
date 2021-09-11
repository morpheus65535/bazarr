# -*- coding: utf-8 -*-

import datetime
import time
import pickle
import tmdbsimple as tmdb

from subliminal.cache import region
from database import TableTmdbCache

CACHE_EXPIRATION_TIME = datetime.timedelta(days=1).total_seconds()

tmdb.API_KEY = "e5577e69d409c601acb98d5bfcee31c7"


def tmdb_func_cache(func, *args, **kwargs):
    try:
        pickled_func = pickle.dumps(func, pickle.HIGHEST_PROTOCOL)
        pickled_kwargs = pickle.dumps(kwargs, pickle.HIGHEST_PROTOCOL)
    except:
        return func(**kwargs)
    else:
        try:
            cached_result = TableTmdbCache.select(TableTmdbCache.result) \
                .where((TableTmdbCache.function == pickled_func) &
                       (TableTmdbCache.arguments == pickled_kwargs) &
                       (TableTmdbCache.timestamp > (time.time() - CACHE_EXPIRATION_TIME))) \
                .dicts() \
                .get()
        except TableTmdbCache.DoesNotExist:
            cached_result = None
        if cached_result:
            try:
                pickled_result = pickle.loads(cached_result['result'])
            except:
                return renew_cache(func, pickled_func, pickled_kwargs, **kwargs)
            else:
                return pickled_result
        else:
            return renew_cache(func, pickled_func, pickled_kwargs, **kwargs)


def renew_cache(func, pickled_func, pickled_kwargs, **kwargs):
    result = func(**kwargs)
    TableTmdbCache.insert({
        TableTmdbCache.timestamp: time.time(),
        TableTmdbCache.function: pickled_func,
        TableTmdbCache.arguments: pickled_kwargs,
        TableTmdbCache.result: pickle.dumps(result, pickle.HIGHEST_PROTOCOL)
    }).execute()
    return result

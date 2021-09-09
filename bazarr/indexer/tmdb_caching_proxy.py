# -*- coding: utf-8 -*-

import json
import datetime
import requests
import tmdbsimple as tmdb
import tmdbsimple.base

from subliminal.cache import region

CACHE_EXPIRATION_TIME = datetime.timedelta(days=1).total_seconds()


# Monkey patch to cache everything from TMDB
@region.cache_on_arguments(expiration_time=CACHE_EXPIRATION_TIME)
def _cached_request(self, method, path, params=None, payload=None):
    url = self._get_complete_url(path)
    params = self._get_params(params)

    if self.session is None:
        response = requests.request(
            method,
            url,
            params=params,
            data=json.dumps(payload) if payload else payload,
            headers=self.headers,
        )

    else:
        response = self.session.request(
            method,
            url,
            params=params,
            data=json.dumps(payload) if payload else payload,
            headers=self.headers,
        )

    response.raise_for_status()
    response.encoding = "utf-8"
    return response.json()


tmdbsimple.base.TMDB._request = _cached_request
tmdb.API_KEY = "e5577e69d409c601acb98d5bfcee31c7"

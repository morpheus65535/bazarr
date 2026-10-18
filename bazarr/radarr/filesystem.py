# coding=utf-8

import requests
import logging

from urllib.parse import urlencode

from app.config import settings
from radarr.info import url_api_radarr
from constants import HEADERS


def browse_radarr_filesystem(path='#'):
    if path == '#':
        path = ''

    query = urlencode({
        'path': path,
        'allowFoldersWithoutTrailingSlashes': 'true',
        'includeFiles': 'false',
        'apikey': settings.radarr.apikey,
    })
    url_radarr_api_filesystem = f"{url_api_radarr()}filesystem?{query}"
    try:
        r = requests.get(url_radarr_api_filesystem, timeout=int(settings.radarr.http_timeout), verify=False,
                         headers=HEADERS)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        logging.exception("BAZARR Error trying to get series from Radarr. Http error.")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get series from Radarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get series from Radarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get series from Radarr.")
        return

    return r.json()

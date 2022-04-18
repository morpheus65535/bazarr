# coding=utf-8

import requests
import logging

from config import settings
from radarr.info import get_radarr_info, url_radarr
from constants import headers


def browse_radarr_filesystem(path='#'):
    if path == '#':
        path = ''

    if get_radarr_info.is_legacy():
        url_radarr_api_filesystem = url_radarr() + "/api/filesystem?path=" + path + \
                                    "&allowFoldersWithoutTrailingSlashes=true&includeFiles=false&apikey=" + \
                                    settings.radarr.apikey
    else:
        url_radarr_api_filesystem = url_radarr() + "/api/v3/filesystem?path=" + path + \
                                    "&allowFoldersWithoutTrailingSlashes=true&includeFiles=false&apikey=" + \
                                    settings.radarr.apikey
    try:
        r = requests.get(url_radarr_api_filesystem, timeout=60, verify=False, headers=headers)
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

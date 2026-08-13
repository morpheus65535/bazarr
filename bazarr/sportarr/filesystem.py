# coding=utf-8

import requests
import logging

from app.config import settings
from sportarr.info import url_api_sportarr
from constants import HEADERS


def browse_sportarr_filesystem(path='#'):
    if path == '#':
        path = ''
    url_sportarr_api_filesystem = (f"{url_api_sportarr()}filesystem?path={path}&includeFiles=false&"
                                   f"apikey={settings.sportarr.apikey}")
    try:
        r = requests.get(url_sportarr_api_filesystem, timeout=int(settings.sportarr.http_timeout), verify=False,
                         headers=HEADERS)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        logging.exception("BAZARR Error trying to browse the file system from Sportarr. Http error.")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to browse the file system from Sportarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to browse the file system from Sportarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to browse the file system from Sportarr.")
        return

    return r.json()

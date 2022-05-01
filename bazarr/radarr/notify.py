# coding=utf-8

import logging
import requests

from app.config import settings
from radarr.info import get_radarr_info, url_radarr
from constants import headers


def notify_radarr(radarr_id):
    try:
        if get_radarr_info.is_legacy():
            url = url_radarr() + "/api/command?apikey=" + settings.radarr.apikey
        else:
            url = url_radarr() + "/api/v3/command?apikey=" + settings.radarr.apikey
        data = {
            'name': 'RescanMovie',
            'movieId': int(radarr_id)
        }
        requests.post(url, json=data, timeout=60, verify=False, headers=headers)
    except Exception:
        logging.exception('BAZARR cannot notify Radarr')

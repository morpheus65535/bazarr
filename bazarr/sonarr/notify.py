# coding=utf-8

import logging
import requests

from app.config import settings
from sonarr.info import get_sonarr_info, url_sonarr
from constants import headers


def notify_sonarr(sonarr_series_id):
    try:
        if get_sonarr_info.is_legacy():
            url = url_sonarr() + "/api/command?apikey=" + settings.sonarr.apikey
        else:
            url = url_sonarr() + "/api/v3/command?apikey=" + settings.sonarr.apikey
        data = {
            'name': 'RescanSeries',
            'seriesId': int(sonarr_series_id)
        }
        requests.post(url, json=data, timeout=sonarr_http_timeout, verify=False, headers=headers)
    except Exception:
        logging.exception('BAZARR cannot notify Sonarr')

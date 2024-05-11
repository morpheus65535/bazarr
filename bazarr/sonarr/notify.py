# coding=utf-8

import logging
import requests

from app.config import settings
from sonarr.info import url_api_sonarr
from constants import HEADERS


def notify_sonarr(sonarr_series_id):
    try:
        url = f"{url_api_sonarr()}command?apikey={settings.sonarr.apikey}"
        data = {
            'name': 'RescanSeries',
            'seriesId': int(sonarr_series_id)
        }
        requests.post(url, json=data, timeout=int(settings.sonarr.http_timeout), verify=False, headers=HEADERS)
    except Exception:
        logging.exception('BAZARR cannot notify Sonarr')

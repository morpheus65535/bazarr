# coding=utf-8

import logging
import requests

from bazarr.config import settings
from bazarr.sonarr.info import get_sonarr_info, url_sonarr
from bazarr.constants import headers


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
        requests.post(url, json=data, timeout=60, verify=False, headers=headers)
    except Exception:
        logging.exception('BAZARR cannot notify Sonarr')

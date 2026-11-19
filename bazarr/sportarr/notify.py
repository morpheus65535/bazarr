# coding=utf-8

import logging
import requests

from app.config import settings
from sportarr.info import url_api_sportarr
from constants import HEADERS


def notify_sportarr(sportarr_league_id):
    # Sportarr rescans the league folder to find a file that changed outside of
    # it, a subtitle for example. There is no per-event equivalent.
    try:
        url = f"{url_api_sportarr()}leagues/{int(sportarr_league_id)}/scan?apikey={settings.sportarr.apikey}"
        requests.post(url, timeout=int(settings.sportarr.http_timeout), verify=False, headers=HEADERS)
    except Exception:
        logging.exception('BAZARR cannot notify Sportarr')

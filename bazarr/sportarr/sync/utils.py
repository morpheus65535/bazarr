# coding=utf-8

import requests
import logging

from app.config import settings
from constants import HEADERS
from sportarr.info import url_api_sportarr


def get_tags():
    apikey_sportarr = settings.sportarr.apikey
    tagsDict = []

    # Get tags data from Sportarr
    url_sportarr_api_tags = f"{url_api_sportarr()}tag?apikey={apikey_sportarr}"

    try:
        tagsDict = requests.get(url_sportarr_api_tags, timeout=int(settings.sportarr.http_timeout), verify=False,
                                headers=HEADERS)
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get tags from Sportarr. Connection Error.")
        return []
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get tags from Sportarr. Timeout Error.")
        return []
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get tags from Sportarr.")
        return []
    else:
        return tagsDict.json()


def get_leagues_from_sportarr_api(apikey_sportarr, sportarr_league_id=None):
    url_sportarr_api_leagues = (f"{url_api_sportarr()}leagues/{sportarr_league_id if sportarr_league_id else ''}?"
                                f"apikey={apikey_sportarr}")

    try:
        r = requests.get(url_sportarr_api_leagues, timeout=int(settings.sportarr.http_timeout), verify=False,
                         headers=HEADERS)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code:
            logging.exception(f"BAZARR Error trying to get leagues from Sportarr. HTTP error {e.response.status_code}")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get leagues from Sportarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get leagues from Sportarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get leagues from Sportarr.")
        return
    except Exception as e:
        logging.exception(f"Exception raised while getting leagues from Sportarr API: {e}")
        return
    else:
        result = r.json()
        if isinstance(result, dict):
            return [result]
        return result

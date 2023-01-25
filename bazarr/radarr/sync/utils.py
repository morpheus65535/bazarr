# coding=utf-8

import requests
import logging

from app.config import settings
from radarr.info import get_radarr_info, url_radarr
from constants import headers


def get_profile_list():
    apikey_radarr = settings.radarr.apikey
    profiles_list = []
    # Get profiles data from radarr
    if get_radarr_info.is_legacy():
        url_radarr_api_movies = url_radarr() + "/api/profile?apikey=" + apikey_radarr
    else:
        url_radarr_api_movies = url_radarr() + "/api/v3/qualityprofile?apikey=" + apikey_radarr

    try:
        profiles_json = requests.get(url_radarr_api_movies, timeout=settings.radarr.http_timeout, verify=False, headers=headers)
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get profiles from Radarr. Connection Error.")
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get profiles from Radarr. Timeout Error.")
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get profiles from Radarr.")
    else:
        # Parsing data returned from radarr
        if get_radarr_info.is_legacy():
            for profile in profiles_json.json():
                profiles_list.append([profile['id'], profile['language'].capitalize()])
        else:
            for profile in profiles_json.json():
                profiles_list.append([profile['id'], profile['language']['name'].capitalize()])

        return profiles_list

    return None


def get_tags():
    apikey_radarr = settings.radarr.apikey
    tagsDict = []

    # Get tags data from Radarr
    if get_radarr_info.is_legacy():
        url_radarr_api_series = url_radarr() + "/api/tag?apikey=" + apikey_radarr
    else:
        url_radarr_api_series = url_radarr() + "/api/v3/tag?apikey=" + apikey_radarr

    try:
        tagsDict = requests.get(url_radarr_api_series, timeout=settings.radarr.http_timeout, verify=False, headers=headers)
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get tags from Radarr. Connection Error.")
        return []
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get tags from Radarr. Timeout Error.")
        return []
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get tags from Radarr.")
        return []
    except requests.exceptions.HTTPError:
        logging.exception("BAZARR Exception while trying to get tags from Radarr.")
        return []
    else:
        try:
            return tagsDict.json()
        except Exception:
            return []


def get_movies_from_radarr_api(url, apikey_radarr, radarr_id=None):
    if get_radarr_info.is_legacy():
        url_radarr_api_movies = url + "/api/movie" + ("/{}".format(radarr_id) if radarr_id else "") + "?apikey=" + \
                                apikey_radarr
    else:
        url_radarr_api_movies = url + "/api/v3/movie" + ("/{}".format(radarr_id) if radarr_id else "") + "?apikey=" + \
                                apikey_radarr

    try:
        r = requests.get(url_radarr_api_movies, timeout=settings.radarr.http_timeout, verify=False, headers=headers)
        if r.status_code == 404:
            return
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        logging.exception("BAZARR Error trying to get movies from Radarr. Http error.")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get movies from Radarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get movies from Radarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get movies from Radarr.")
        return
    else:
        return r.json()

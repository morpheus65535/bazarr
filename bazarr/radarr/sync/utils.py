# coding=utf-8

import requests
import logging

from app.config import settings
from radarr.info import get_radarr_info, url_api_radarr
from constants import HEADERS


def get_profile_list():
    apikey_radarr = settings.radarr.apikey
    profiles_list = []
    # Get profiles data from radarr
    url_radarr_api_movies = (f"{url_api_radarr()}{'quality' if url_api_radarr().endswith('v3/') else ''}profile?"
                             f"apikey={apikey_radarr}")

    try:
        profiles_json = requests.get(url_radarr_api_movies, timeout=int(settings.radarr.http_timeout), verify=False,
                                     headers=HEADERS)
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
                if 'language' in profile:
                    profiles_list.append([profile['id'], profile['language'].capitalize()])
        else:
            for profile in profiles_json.json():
                if 'language' in profile and 'name' in profile['language']:
                    profiles_list.append([profile['id'], profile['language']['name'].capitalize()])

    return profiles_list


def get_tags():
    apikey_radarr = settings.radarr.apikey
    tagsDict = []

    # Get tags data from Radarr
    url_radarr_api_series = f"{url_api_radarr()}tag?apikey={apikey_radarr}"

    try:
        tagsDict = requests.get(url_radarr_api_series, timeout=int(settings.radarr.http_timeout), verify=False, headers=HEADERS)
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


def get_movies_from_radarr_api(apikey_radarr, radarr_id=None):
    url_radarr_api_movies = f'{url_api_radarr()}movie{f"/{radarr_id}" if radarr_id else ""}?apikey={apikey_radarr}'

    try:
        r = requests.get(url_radarr_api_movies, timeout=int(settings.radarr.http_timeout), verify=False, headers=HEADERS)
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
    except Exception as e:
        logging.exception(f"Exception raised while getting movies from Radarr API: {e}")
        return
    else:
        if r.status_code == 200:
            return r.json()
        else:
            return


def get_history_from_radarr_api(apikey_radarr, movie_id):
    url_radarr_api_history = f"{url_api_radarr()}history?eventType=1&movieIds={movie_id}&apikey={apikey_radarr}"

    try:
        r = requests.get(url_radarr_api_history, timeout=int(settings.sonarr.http_timeout), verify=False,
                         headers=HEADERS)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        logging.exception("BAZARR Error trying to get history from Radarr. Http error.")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get history from Radarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get history from Radarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get history from Radarr.")
        return
    except Exception as e:
        logging.exception(f"Exception raised while getting history from Radarr API: {e}")
        return
    else:
        if r.status_code == 200:
            return r.json()
        else:
            return

# coding=utf-8

import requests
import logging

from app.config import settings
from sonarr.info import get_sonarr_info, url_sonarr
from constants import headers


def get_profile_list():
    apikey_sonarr = settings.sonarr.apikey
    profiles_list = []

    # Get profiles data from Sonarr
    if get_sonarr_info.is_legacy():
        url_sonarr_api_series = f"{url_sonarr()}/api/profile?apikey={apikey_sonarr}"
    else:
        url_sonarr_api_series = f"{url_sonarr()}/api/v3/languageprofile?apikey={apikey_sonarr}"

    try:
        profiles_json = requests.get(url_sonarr_api_series, timeout=60, verify=False, headers=headers)
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get profiles from Sonarr. Connection Error.")
        return None
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get profiles from Sonarr. Timeout Error.")
        return None
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get profiles from Sonarr.")
        return None

    # Parsing data returned from Sonarr
    if get_sonarr_info.is_legacy():
        profiles_list.extend([profile['id'], profile['language'].capitalize()] for profile in profiles_json.json())
    else:
        profiles_list.extend([profile['id'], profile['name'].capitalize()] for profile in profiles_json.json())

    return profiles_list


def get_tags():
    apikey_sonarr = settings.sonarr.apikey
    tagsDict = []

    # Get tags data from Sonarr
    if get_sonarr_info.is_legacy():
        url_sonarr_api_series = f"{url_sonarr()}/api/tag?apikey={apikey_sonarr}"
    else:
        url_sonarr_api_series = f"{url_sonarr()}/api/v3/tag?apikey={apikey_sonarr}"

    try:
        tagsDict = requests.get(url_sonarr_api_series, timeout=60, verify=False, headers=headers)
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get tags from Sonarr. Connection Error.")
        return []
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get tags from Sonarr. Timeout Error.")
        return []
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get tags from Sonarr.")
        return []
    else:
        return tagsDict.json()


def get_series_from_sonarr_api(url, apikey_sonarr, sonarr_series_id=None):
    url_sonarr_api_series = url + "/api/{0}series/{1}?apikey={2}".format('' if get_sonarr_info.is_legacy() else 'v3/', sonarr_series_id or "", apikey_sonarr)

    try:
        r = requests.get(url_sonarr_api_series, timeout=60, verify=False, headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code:
            raise requests.exceptions.HTTPError from e
        logging.exception("BAZARR Error trying to get series from Sonarr. Http error.")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get series from Sonarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get series from Sonarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get series from Sonarr.")
        return
    else:
        return r.json()


def get_episodes_from_sonarr_api(url, apikey_sonarr, series_id=None, episode_id=None):
    if series_id:
        url_sonarr_api_episode = f"{url}/api/{'' if get_sonarr_info.is_legacy() else 'v3/'}episode?seriesId={series_id}&apikey={apikey_sonarr}"
    elif episode_id:
        url_sonarr_api_episode = f"{url}/api/{'' if get_sonarr_info.is_legacy() else 'v3/'}episode/{episode_id}?apikey={apikey_sonarr}"
    else:
        return

    try:
        r = requests.get(url_sonarr_api_episode, timeout=60, verify=False, headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        logging.exception("BAZARR Error trying to get episodes from Sonarr. Http error.")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get episodes from Sonarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get episodes from Sonarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get episodes from Sonarr.")
        return
    else:
        return r.json()


def get_episodesFiles_from_sonarr_api(url, apikey_sonarr, series_id=None, episode_file_id=None):
    if series_id:
        url_sonarr_api_episodeFiles = f"{url}/api/v3/episodeFile?seriesId={series_id}&apikey={apikey_sonarr}"
    elif episode_file_id:
        url_sonarr_api_episodeFiles = f"{url}/api/v3/episodeFile/{episode_file_id}?apikey={apikey_sonarr}"
    else:
        return

    try:
        r = requests.get(url_sonarr_api_episodeFiles, timeout=60, verify=False, headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        logging.exception("BAZARR Error trying to get episodeFiles from Sonarr. Http error.")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get episodeFiles from Sonarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get episodeFiles from Sonarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get episodeFiles from Sonarr.")
        return
    else:
        return r.json()

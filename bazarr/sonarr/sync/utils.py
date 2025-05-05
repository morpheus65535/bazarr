# coding=utf-8

import requests
import logging

from app.config import settings
from sonarr.info import get_sonarr_info, url_api_sonarr
from constants import HEADERS


def get_profile_list():
    apikey_sonarr = settings.sonarr.apikey
    profiles_list = []

    # Get profiles data from Sonarr
    if get_sonarr_info.is_legacy():
        url_sonarr_api_series = f"{url_api_sonarr()}profile?apikey={apikey_sonarr}"
    else:
        if not get_sonarr_info.version().startswith('3.'):
            # return an empty list when using Sonarr >= v4 that does not support series languages profiles anymore
            return profiles_list
        url_sonarr_api_series = f"{url_api_sonarr()}languageprofile?apikey={apikey_sonarr}"

    try:
        profiles_json = requests.get(url_sonarr_api_series, timeout=int(settings.sonarr.http_timeout), verify=False,
                                     headers=HEADERS)
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get profiles from Sonarr. Connection Error.")
        return None
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get profiles from Sonarr. Timeout Error.")
        return None
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get profiles from Sonarr.")
        return None
    else:
        # Parsing data returned from Sonarr
        if get_sonarr_info.is_legacy():
            for profile in profiles_json.json():
                if 'language' in profile:
                    profiles_list.append([profile['id'], profile['language'].capitalize()])
        else:
            for profile in profiles_json.json():
                if 'name' in profile:
                    profiles_list.append([profile['id'], profile['name'].capitalize()])

    return profiles_list


def get_tags():
    apikey_sonarr = settings.sonarr.apikey
    tagsDict = []

    # Get tags data from Sonarr
    url_sonarr_api_series = f"{url_api_sonarr()}tag?apikey={apikey_sonarr}"

    try:
        tagsDict = requests.get(url_sonarr_api_series, timeout=int(settings.sonarr.http_timeout), verify=False, headers=HEADERS)
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


def get_series_from_sonarr_api(apikey_sonarr, sonarr_series_id=None):
    url_sonarr_api_series = (f"{url_api_sonarr()}series/{sonarr_series_id if sonarr_series_id else ''}?"
                             f"apikey={apikey_sonarr}")
    try:
        r = requests.get(url_sonarr_api_series, timeout=int(settings.sonarr.http_timeout), verify=False, headers=HEADERS)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code:
            raise requests.exceptions.HTTPError
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
    except Exception as e:
        logging.exception(f"Exception raised while getting series from Sonarr API: {e}")
        return
    else:
        if r.status_code == 200:
            result = r.json()
            if isinstance(result, dict):
                return [result]
            else:
                return r.json()
        else:
            return


def get_episodes_from_sonarr_api(apikey_sonarr, series_id=None, episode_id=None):
    if series_id:
        url_sonarr_api_episode = f"{url_api_sonarr()}episode?seriesId={series_id}&apikey={apikey_sonarr}"
    elif episode_id:
        url_sonarr_api_episode = f"{url_api_sonarr()}episode/{episode_id}?apikey={apikey_sonarr}"
    else:
        return

    try:
        r = requests.get(url_sonarr_api_episode, timeout=int(settings.sonarr.http_timeout), verify=False, headers=HEADERS)
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
    except Exception as e:
        logging.exception(f"Exception raised while getting episodes from Sonarr API: {e}")
        return
    else:
        if r.status_code == 200:
            return r.json()
        else:
            return


def get_episodesFiles_from_sonarr_api(apikey_sonarr, series_id=None, episode_file_id=None):
    if series_id:
        url_sonarr_api_episodeFiles = f"{url_api_sonarr()}episodeFile?seriesId={series_id}&apikey={apikey_sonarr}"
    elif episode_file_id:
        url_sonarr_api_episodeFiles = f"{url_api_sonarr()}episodeFile/{episode_file_id}?apikey={apikey_sonarr}"
    else:
        return

    try:
        r = requests.get(url_sonarr_api_episodeFiles, timeout=int(settings.sonarr.http_timeout), verify=False,
                         headers=HEADERS)
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
    except Exception as e:
        logging.exception(f"Exception raised while getting episodes from Sonarr API: {e}")
        return
    else:
        if r.status_code == 200:
            return r.json()
        else:
            return


def get_history_from_sonarr_api(apikey_sonarr, episode_id):
    url_sonarr_api_history = f"{url_api_sonarr()}history?eventType=1&episodeId={episode_id}&apikey={apikey_sonarr}"

    try:
        r = requests.get(url_sonarr_api_history, timeout=int(settings.sonarr.http_timeout), verify=False,
                         headers=HEADERS)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        logging.exception("BAZARR Error trying to get history from Sonarr. Http error.")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get history from Sonarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get history from Sonarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get history from Sonarr.")
        return
    except Exception as e:
        logging.exception(f"Exception raised while getting history from Sonarr API: {e}")
        return
    else:
        if r.status_code == 200:
            return r.json()
        else:
            return

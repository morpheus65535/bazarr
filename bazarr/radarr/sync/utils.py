# coding=utf-8

import requests
import logging

from app.config import settings
from radarr.info import (get_radarr_info, url_api_radarr,
                         url_api_radarr_from_instance, is_radarr_instance_legacy)
from constants import HEADERS


def get_profile_list(instance=None):
    """Fetch quality profiles from Radarr.

    Args:
        instance: dict from TableRadarrInstances.to_dict(). If None, uses primary instance from settings.
    """
    if instance is not None:
        apikey = instance.get('apikey', '')
        timeout = int(instance.get('http_timeout', 60))
        legacy = is_radarr_instance_legacy(instance)
        api_url = url_api_radarr_from_instance(instance, is_legacy=legacy)
    else:
        apikey = settings.radarr.apikey
        timeout = int(settings.radarr.http_timeout)
        api_url = url_api_radarr()
        legacy = get_radarr_info.is_legacy()

    profiles_list = []
    url = f"{api_url}{'quality' if api_url.endswith('v3/') else ''}profile?apikey={apikey}"

    try:
        profiles_json = requests.get(url, timeout=timeout, verify=False, headers=HEADERS)
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get profiles from Radarr. Connection Error.")
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get profiles from Radarr. Timeout Error.")
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get profiles from Radarr.")
    else:
        if legacy:
            for profile in profiles_json.json():
                if 'language' in profile:
                    profiles_list.append([profile['id'], profile['language'].capitalize()])
        else:
            for profile in profiles_json.json():
                if 'language' in profile and 'name' in profile['language']:
                    profiles_list.append([profile['id'], profile['language']['name'].capitalize()])

    return profiles_list


def get_tags(instance=None):
    """Fetch tags from Radarr.

    Args:
        instance: dict from TableRadarrInstances.to_dict(). If None, uses primary instance from settings.
    """
    if instance is not None:
        apikey = instance.get('apikey', '')
        timeout = int(instance.get('http_timeout', 60))
        legacy = is_radarr_instance_legacy(instance)
        api_url = url_api_radarr_from_instance(instance, is_legacy=legacy)
    else:
        apikey = settings.radarr.apikey
        timeout = int(settings.radarr.http_timeout)
        api_url = url_api_radarr()

    url = f"{api_url}tag?apikey={apikey}"

    try:
        tagsDict = requests.get(url, timeout=timeout, verify=False, headers=HEADERS)
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


def get_movies_from_radarr_api(apikey_radarr, radarr_id=None, instance=None):
    """Fetch movie(s) from Radarr API.

    Args:
        apikey_radarr: Radarr API key (used when instance is None).
        radarr_id: Optional specific movie ID to fetch.
        instance: dict from TableRadarrInstances.to_dict(). If None, uses primary instance from settings.
    """
    if instance is not None:
        legacy = is_radarr_instance_legacy(instance)
        api_url = url_api_radarr_from_instance(instance, is_legacy=legacy)
        timeout = int(instance.get('http_timeout', 60))
        apikey = instance.get('apikey', apikey_radarr)
    else:
        api_url = url_api_radarr()
        timeout = int(settings.radarr.http_timeout)
        apikey = apikey_radarr

    url = f'{api_url}movie{f"/{radarr_id}" if radarr_id else ""}?apikey={apikey}'

    try:
        r = requests.get(url, timeout=timeout, verify=False, headers=HEADERS)
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


def get_history_from_radarr_api(apikey_radarr, movie_id, instance=None):
    """Fetch download history for a movie from Radarr API.

    Args:
        apikey_radarr: Radarr API key (used when instance is None).
        movie_id: Radarr movie ID.
        instance: dict from TableRadarrInstances.to_dict(). If None, uses primary instance from settings.
    """
    if instance is not None:
        legacy = is_radarr_instance_legacy(instance)
        api_url = url_api_radarr_from_instance(instance, is_legacy=legacy)
        timeout = int(instance.get('http_timeout', 60))
        apikey = instance.get('apikey', apikey_radarr)
    else:
        api_url = url_api_radarr()
        timeout = int(settings.sonarr.http_timeout)
        apikey = apikey_radarr

    url = f"{api_url}history?eventType=1&movieIds={movie_id}&apikey={apikey}"

    try:
        r = requests.get(url, timeout=timeout, verify=False, headers=HEADERS)
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

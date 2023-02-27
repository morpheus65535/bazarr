import logging
from typing import List, Dict, Optional, Union

import requests

from app.config import settings
from constants import headers
from sonarr.info import get_sonarr_info, url_sonarr


def get_profile_list() -> List[Union[int, str]]:
    apikey_sonarr = settings.sonarr.apikey
    profiles_list = []

    # Get profiles data from Sonarr
    if get_sonarr_info.is_legacy():
        url_sonarr_api_series = f"{url_sonarr()}/api/profile?apikey={apikey_sonarr}"
    elif get_sonarr_info.version().startswith('3.'):
        url_sonarr_api_series = (
            f"{url_sonarr()}/api/v3/languageprofile?apikey={apikey_sonarr}"
        )
    else:
        # return an empty list when using Sonarr >= v4 that does not support series languages profiles anymore
        return profiles_list

    profiles_json = call_sonarr_api(url_sonarr_api_series)

    # Parsing data returned from Sonarr
    if get_sonarr_info.is_legacy():
        profiles_list.extend(
            [profile['id'], profile['language'].capitalize()]
            for profile in profiles_json
        )
    else:
        profiles_list.extend(
            [profile['id'], profile['name'].capitalize()]
            for profile in profiles_json
        )
    return profiles_list


def get_tags() -> List[Dict]:
    # Get tags data from Sonarr
    if get_sonarr_info.is_legacy():
        url_sonarr_api_series = f"{url_sonarr()}/api/tag?apikey={settings.sonarr.apikey}"
    else:
        url_sonarr_api_series = f"{url_sonarr()}/api/v3/tag?apikey={settings.sonarr.apikey}"

    return call_sonarr_api(url_sonarr_api_series)


def get_series_from_sonarr_api(sonarr_series_id: int = None) -> List[Dict]:
    url_sonarr_api_series = f"{url_sonarr()}/api/{'' if get_sonarr_info.is_legacy() else 'v3/'}series/{sonarr_series_id or ''}?apikey={settings.sonarr.apikey}"
    return call_sonarr_api(url_sonarr_api_series)


def get_episodes_from_sonarr_api(series_id: int = None, episode_id: int = None) -> Optional[List[Dict]]:
    if series_id:
        url_sonarr_api_episode = f"{url_sonarr()}/api/{'' if get_sonarr_info.is_legacy() else 'v3/'}episode?seriesId={series_id}&apikey={settings.sonarr.apikey}"
    elif episode_id:
        url_sonarr_api_episode = f"{url_sonarr()}/api/{'' if get_sonarr_info.is_legacy() else 'v3/'}episode/{episode_id}?apikey={settings.sonarr.apikey}"
    else:
        return

    return call_sonarr_api(url_sonarr_api_episode)


def get_episodes_files_from_sonarr_api(series_id=None, episode_file_id=None) -> Optional[List[Dict]]:

    if series_id:
        url_sonarr_api_episodeFiles = f"{url_sonarr()}/api/v3/episodeFile?seriesId={series_id}&apikey={settings.sonarr.apikey}"
    elif episode_file_id:
        url_sonarr_api_episodeFiles = f"{url_sonarr()}/api/v3/episodeFile/{episode_file_id}?apikey={settings.sonarr.apikey}"
    else:
        return

    return call_sonarr_api(url_sonarr_api_episodeFiles)


def call_sonarr_api(url: str) -> List[Dict]:
    try:
        r = requests.get(url, timeout=int(settings.sonarr.http_timeout), verify=False, headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        logging.exception("BAZARR Error trying to call Sonarr API. Http error.")
        raise
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to call Sonarr API. Connection Error.")
        raise
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to call Sonarr API. Timeout Error.")
        raise
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to call Sonarr API.")
        raise

    result = r.json()
    return [result] if isinstance(result, dict) else r.json()

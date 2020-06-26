import os
import requests
import logging
import string

from config import settings, url_sonarr, url_radarr


def browse_bazarr_filesystem(path='#'):
    if path == '#' or path == '/' or path == '':
        if os.name == 'nt':
            dir_list = []
            for drive in string.ascii_uppercase:
                drive_letter = drive + ':\\'
                if os.path.exists(drive_letter):
                    dir_list.append(drive_letter)
        else:
            path = "/"
            dir_list = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    else:
        dir_list = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]

    data = []
    for item in dir_list:
        full_path = os.path.join(path, item, '')
        item = {
            "name": item,
            "path": full_path
        }
        data.append(item)

    parent = os.path.dirname(path)

    result = {'directories': sorted(data, key=lambda i: i['name'])}
    if path == '#':
        result.update({'parent': '#'})
    else:
        result.update({'parent': parent})

    return result


def browse_sonarr_filesystem(path='#'):
    if path == '#':
        path = ''
    url_sonarr_api_filesystem = url_sonarr() + "/api/filesystem?path=" + path + \
                                "&allowFoldersWithoutTrailingSlashes=true&includeFiles=false&apikey=" + \
                                settings.sonarr.apikey
    try:
        r = requests.get(url_sonarr_api_filesystem, timeout=60, verify=False)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
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

    return r.json()


def browse_radarr_filesystem(path='#'):
    if path == '#':
        path = ''

    url_radarr_api_filesystem = url_radarr() + "/api/filesystem?path=" + path + \
                                "&allowFoldersWithoutTrailingSlashes=true&includeFiles=false&apikey=" + \
                                settings.radarr.apikey
    try:
        r = requests.get(url_radarr_api_filesystem, timeout=60, verify=False)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        logging.exception("BAZARR Error trying to get series from Radarr. Http error.")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get series from Radarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get series from Radarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get series from Radarr.")
        return

    return r.json()

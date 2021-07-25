# coding=utf-8

import os
import requests
import logging

from config import settings, url_sonarr, url_radarr
from helper import path_mappings
from database import TableShowsRootfolder, TableMoviesRootfolder, TableShows, TableMovies
from utils import get_sonarr_version, get_radarr_version

headers = {"User-Agent": os.environ["SZ_USER_AGENT"]}


def get_sonarr_rootfolder():
    apikey_sonarr = settings.sonarr.apikey
    sonarr_rootfolder = []
    sonarr_version = get_sonarr_version()

    # Get root folder data from Sonarr
    if sonarr_version.startswith(('0.', '2.')):
        url_sonarr_api_rootfolder = url_sonarr() + "/api/rootfolder?apikey=" + apikey_sonarr
    else:
        url_sonarr_api_rootfolder = url_sonarr() + "/api/v3/rootfolder?apikey=" + apikey_sonarr

    try:
        rootfolder = requests.get(url_sonarr_api_rootfolder, timeout=60, verify=False, headers=headers)
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get rootfolder from Sonarr. Connection Error.")
        return []
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get rootfolder from Sonarr. Timeout Error.")
        return []
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get rootfolder from Sonarr.")
        return []
    else:
        sonarr_movies_paths = list(TableShows.select(TableShows.path).dicts())
        for folder in rootfolder.json():
            if any(item['path'].startswith(folder['path']) for item in sonarr_movies_paths):
                sonarr_rootfolder.append({'id': folder['id'], 'path': folder['path']})
        db_rootfolder = TableShowsRootfolder.select(TableShowsRootfolder.id, TableShowsRootfolder.path).dicts()
        rootfolder_to_remove = [x for x in db_rootfolder if not
                                next((item for item in sonarr_rootfolder if item['id'] == x['id']), False)]
        rootfolder_to_update = [x for x in sonarr_rootfolder if
                                next((item for item in db_rootfolder if item['id'] == x['id']), False)]
        rootfolder_to_insert = [x for x in sonarr_rootfolder if not
                                next((item for item in db_rootfolder if item['id'] == x['id']), False)]

        for item in rootfolder_to_remove:
            TableShowsRootfolder.delete().where(TableShowsRootfolder.id == item['id']).execute()
        for item in rootfolder_to_update:
            TableShowsRootfolder.update({TableShowsRootfolder.path: item['path']})\
                .where(TableShowsRootfolder.id == item['id'])\
                .execute()
        for item in rootfolder_to_insert:
            TableShowsRootfolder.insert({TableShowsRootfolder.id: item['id'], TableShowsRootfolder.path: item['path']})\
                .execute()


def check_sonarr_rootfolder():
    get_sonarr_rootfolder()
    rootfolder = TableShowsRootfolder.select(TableShowsRootfolder.id, TableShowsRootfolder.path).dicts()
    for item in rootfolder:
        root_path = item['path']
        if not root_path.endswith(os.path.sep):
            root_path += os.path.sep
        if not os.path.isdir(path_mappings.path_replace(root_path)):
            TableShowsRootfolder.update({TableShowsRootfolder.accessible: 0,
                                         TableShowsRootfolder.error: 'This Sonarr root directory does not seems to '
                                                                     'be accessible by Bazarr. Please check path '
                                                                     'mapping.'})\
                .where(TableShowsRootfolder.id == item['id'])\
                .execute()
        elif not os.access(path_mappings.path_replace(root_path), os.W_OK):
            TableShowsRootfolder.update({TableShowsRootfolder.accessible: 0,
                                         TableShowsRootfolder.error: 'Bazarr cannot write to this directory.'}) \
                .where(TableShowsRootfolder.id == item['id']) \
                .execute()
        else:
            TableShowsRootfolder.update({TableShowsRootfolder.accessible: 1,
                                         TableShowsRootfolder.error: ''}) \
                .where(TableShowsRootfolder.id == item['id']) \
                .execute()


def get_radarr_rootfolder():
    apikey_radarr = settings.radarr.apikey
    radarr_rootfolder = []
    radarr_version = get_radarr_version()

    # Get root folder data from Radarr
    if radarr_version.startswith('0'):
        url_radarr_api_rootfolder = url_radarr() + "/api/rootfolder?apikey=" + apikey_radarr
    else:
        url_radarr_api_rootfolder = url_radarr() + "/api/v3/rootfolder?apikey=" + apikey_radarr

    try:
        rootfolder = requests.get(url_radarr_api_rootfolder, timeout=60, verify=False, headers=headers)
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get rootfolder from Radarr. Connection Error.")
        return []
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get rootfolder from Radarr. Timeout Error.")
        return []
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get rootfolder from Radarr.")
        return []
    else:
        radarr_movies_paths = list(TableMovies.select(TableMovies.path).dicts())
        for folder in rootfolder.json():
            if any(item['path'].startswith(folder['path']) for item in radarr_movies_paths):
                radarr_rootfolder.append({'id': folder['id'], 'path': folder['path']})
        db_rootfolder = TableMoviesRootfolder.select(TableMoviesRootfolder.id, TableMoviesRootfolder.path).dicts()
        rootfolder_to_remove = [x for x in db_rootfolder if not
                                next((item for item in radarr_rootfolder if item['id'] == x['id']), False)]
        rootfolder_to_update = [x for x in radarr_rootfolder if
                                next((item for item in db_rootfolder if item['id'] == x['id']), False)]
        rootfolder_to_insert = [x for x in radarr_rootfolder if not
                                next((item for item in db_rootfolder if item['id'] == x['id']), False)]

        for item in rootfolder_to_remove:
            TableMoviesRootfolder.delete().where(TableMoviesRootfolder.id == item['id']).execute()
        for item in rootfolder_to_update:
            TableMoviesRootfolder.update({TableMoviesRootfolder.path: item['path']})\
                .where(TableMoviesRootfolder.id == item['id']).execute()
        for item in rootfolder_to_insert:
            TableMoviesRootfolder.insert({TableMoviesRootfolder.id: item['id'],
                                          TableMoviesRootfolder.path: item['path']}).execute()


def check_radarr_rootfolder():
    get_radarr_rootfolder()
    rootfolder = TableMoviesRootfolder.select(TableMoviesRootfolder.id, TableMoviesRootfolder.path).dicts()
    for item in rootfolder:
        root_path = item['path']
        if not root_path.endswith(os.path.sep):
            root_path += os.path.sep
        if not os.path.isdir(path_mappings.path_replace_movie(root_path)):
            TableMoviesRootfolder.update({TableMoviesRootfolder.accessible: 0,
                                         TableMoviesRootfolder.error: 'This Radarr root directory does not seems to '
                                                                      'be accessible by Bazarr. Please check path '
                                                                      'mapping.'}) \
                .where(TableMoviesRootfolder.id == item['id']) \
                .execute()
        elif not os.access(path_mappings.path_replace_movie(root_path), os.W_OK):
            TableMoviesRootfolder.update({TableMoviesRootfolder.accessible: 0,
                                          TableMoviesRootfolder.error: 'Bazarr cannot write to this directory'}) \
                .where(TableMoviesRootfolder.id == item['id']) \
                .execute()
        else:
            TableMoviesRootfolder.update({TableMoviesRootfolder.accessible: 1,
                                          TableMoviesRootfolder.error: ''}) \
                .where(TableMoviesRootfolder.id == item['id']) \
                .execute()

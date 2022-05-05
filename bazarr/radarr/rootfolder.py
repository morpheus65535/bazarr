# coding=utf-8

import os
import requests
import logging

from app.config import settings
from utilities.path_mappings import path_mappings
from app.database import TableMoviesRootfolder, TableMovies
from radarr.info import get_radarr_info, url_radarr
from constants import headers


def get_radarr_rootfolder():
    apikey_radarr = settings.radarr.apikey
    radarr_rootfolder = []

    # Get root folder data from Radarr
    if get_radarr_info.is_legacy():
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
        if not root_path.endswith(('/', '\\')):
            if root_path.startswith('/'):
                root_path += '/'
            else:
                root_path += '\\'
        if not os.path.isdir(path_mappings.path_replace_movie(root_path)):
            TableMoviesRootfolder.update({TableMoviesRootfolder.accessible: 0,
                                         TableMoviesRootfolder.error: 'This Radarr root directory does not seems to '
                                                                      'be accessible by  Please check path '
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

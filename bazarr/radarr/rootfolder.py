# coding=utf-8

import os
import requests
import logging

from app.config import settings
from utilities.path_mappings import path_mappings
from app.database import TableMoviesRootfolder, TableMovies, database, delete, update, insert, select
from radarr.info import url_api_radarr
from constants import headers


def get_radarr_rootfolder():
    apikey_radarr = settings.radarr.apikey
    radarr_rootfolder = []

    # Get root folder data from Radarr
    url_radarr_api_rootfolder = f"{url_api_radarr()}rootfolder?apikey={apikey_radarr}"

    try:
        rootfolder = requests.get(url_radarr_api_rootfolder, timeout=int(settings.radarr.http_timeout), verify=False, headers=headers)
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
        for folder in rootfolder.json():
            if any(item.path.startswith(folder['path']) for item in database.execute(
                    select(TableMovies.path))
                    .all()):
                radarr_rootfolder.append({'id': folder['id'], 'path': folder['path']})
        db_rootfolder = database.execute(
            select(TableMoviesRootfolder.id, TableMoviesRootfolder.path))\
            .all()
        rootfolder_to_remove = [x for x in db_rootfolder if not
                                next((item for item in radarr_rootfolder if item['id'] == x.id), False)]
        rootfolder_to_update = [x for x in radarr_rootfolder if
                                next((item for item in db_rootfolder if item.id == x['id']), False)]
        rootfolder_to_insert = [x for x in radarr_rootfolder if not
                                next((item for item in db_rootfolder if item.id == x['id']), False)]

        for item in rootfolder_to_remove:
            database.execute(
                delete(TableMoviesRootfolder)
                .where(TableMoviesRootfolder.id == item.id))
        for item in rootfolder_to_update:
            database.execute(
                update(TableMoviesRootfolder)
                .values(path=item['path'])
                .where(TableMoviesRootfolder.id == item['id']))
        for item in rootfolder_to_insert:
            database.execute(
                insert(TableMoviesRootfolder)
                .values(id=item['id'], path=item['path']))


def check_radarr_rootfolder():
    get_radarr_rootfolder()
    rootfolder = database.execute(
        select(TableMoviesRootfolder.id, TableMoviesRootfolder.path))\
        .all()
    for item in rootfolder:
        root_path = item.path
        if not root_path.endswith(('/', '\\')):
            if root_path.startswith('/'):
                root_path += '/'
            else:
                root_path += '\\'
        if not os.path.isdir(path_mappings.path_replace_movie(root_path)):
            database.execute(
                update(TableMoviesRootfolder)
                .values(accessible=0, error='This Radarr root directory does not seems to be accessible by  Please '
                                            'check path mapping.')
                .where(TableMoviesRootfolder.id == item.id))
        elif not os.access(path_mappings.path_replace_movie(root_path), os.W_OK):
            database.execute(
                update(TableMoviesRootfolder)
                .values(accessible=0, error='Bazarr cannot write to this directory')
                .where(TableMoviesRootfolder.id == item.id))
        else:
            database.execute(
                update(TableMoviesRootfolder)
                .values(accessible=1, error='')
                .where(TableMoviesRootfolder.id == item.id))

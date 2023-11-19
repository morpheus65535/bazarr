# coding=utf-8

import os
import requests
import logging

from app.config import settings
from app.database import TableShowsRootfolder, TableShows, database, insert, update, delete, select
from utilities.path_mappings import path_mappings
from sonarr.info import url_api_sonarr
from constants import headers


def get_sonarr_rootfolder():
    apikey_sonarr = settings.sonarr.apikey
    sonarr_rootfolder = []

    # Get root folder data from Sonarr
    url_sonarr_api_rootfolder = f"{url_api_sonarr()}rootfolder?apikey={apikey_sonarr}"

    try:
        rootfolder = requests.get(url_sonarr_api_rootfolder, timeout=int(settings.sonarr.http_timeout), verify=False, headers=headers)
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
        for folder in rootfolder.json():
            if any(item.path.startswith(folder['path']) for item in database.execute(
                    select(TableShows.path))
                    .all()):
                sonarr_rootfolder.append({'id': folder['id'], 'path': folder['path']})
        db_rootfolder = database.execute(
            select(TableShowsRootfolder.id, TableShowsRootfolder.path))\
            .all()
        rootfolder_to_remove = [x for x in db_rootfolder if not
                                next((item for item in sonarr_rootfolder if item['id'] == x.id), False)]
        rootfolder_to_update = [x for x in sonarr_rootfolder if
                                next((item for item in db_rootfolder if item.id == x['id']), False)]
        rootfolder_to_insert = [x for x in sonarr_rootfolder if not
                                next((item for item in db_rootfolder if item.id == x['id']), False)]

        for item in rootfolder_to_remove:
            database.execute(
                delete(TableShowsRootfolder)
                .where(TableShowsRootfolder.id == item.id))
        for item in rootfolder_to_update:
            database.execute(
                update(TableShowsRootfolder)
                .values(path=item['path'])
                .where(TableShowsRootfolder.id == item['id']))
        for item in rootfolder_to_insert:
            database.execute(
                insert(TableShowsRootfolder)
                .values(id=item['id'], path=item['path']))


def check_sonarr_rootfolder():
    get_sonarr_rootfolder()
    rootfolder = database.execute(
        select(TableShowsRootfolder.id, TableShowsRootfolder.path))\
        .all()
    for item in rootfolder:
        root_path = item.path
        if not root_path.endswith(('/', '\\')):
            if root_path.startswith('/'):
                root_path += '/'
            else:
                root_path += '\\'
        if not os.path.isdir(path_mappings.path_replace(root_path)):
            database.execute(
                update(TableShowsRootfolder)
                .values(accessible=0, error='This Sonarr root directory does not seems to be accessible by Bazarr. '
                                            'Please check path mapping.')
                .where(TableShowsRootfolder.id == item.id))
        elif not os.access(path_mappings.path_replace(root_path), os.W_OK):
            database.execute(
                update(TableShowsRootfolder)
                .values(accessible=0, error='Bazarr cannot write to this directory.')
                .where(TableShowsRootfolder.id == item.id))
        else:
            database.execute(
                update(TableShowsRootfolder)
                .values(accessible=1, error='')
                .where(TableShowsRootfolder.id == item.id))

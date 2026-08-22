# coding=utf-8

import os
import requests
import logging

from app.config import settings
from app.database import TableSportsLeaguesRootfolder, TableSportsLeagues, database, insert, update, delete, select
from utilities.path_mappings import path_mappings
from sportarr.info import url_api_sportarr
from constants import HEADERS


def get_sportarr_rootfolder():
    apikey_sportarr = settings.sportarr.apikey
    sportarr_rootfolder = []

    # Get root folder data from Sportarr
    url_sportarr_api_rootfolder = f"{url_api_sportarr()}rootfolder?apikey={apikey_sportarr}"

    try:
        rootfolder = requests.get(url_sportarr_api_rootfolder, timeout=int(settings.sportarr.http_timeout),
                                  verify=False, headers=HEADERS)
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get rootfolder from Sportarr. Connection Error.")
        return []
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get rootfolder from Sportarr. Timeout Error.")
        return []
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get rootfolder from Sportarr.")
        return []
    else:
        for folder in rootfolder.json():
            if any(item.path.startswith(folder['path']) for item in database.execute(
                    select(TableSportsLeagues.path))
                    .all()):
                sportarr_rootfolder.append({'id': folder['id'], 'path': folder['path']})
        db_rootfolder = database.execute(
            select(TableSportsLeaguesRootfolder.id, TableSportsLeaguesRootfolder.path))\
            .all()
        rootfolder_to_remove = [x for x in db_rootfolder if not
                                next((item for item in sportarr_rootfolder if item['id'] == x.id), False)]
        rootfolder_to_update = [x for x in sportarr_rootfolder if
                                next((item for item in db_rootfolder if item.id == x['id']), False)]
        rootfolder_to_insert = [x for x in sportarr_rootfolder if not
                                next((item for item in db_rootfolder if item.id == x['id']), False)]

        for item in rootfolder_to_remove:
            database.execute(
                delete(TableSportsLeaguesRootfolder)
                .where(TableSportsLeaguesRootfolder.id == item.id))
        for item in rootfolder_to_update:
            database.execute(
                update(TableSportsLeaguesRootfolder)
                .values(path=item['path'])
                .where(TableSportsLeaguesRootfolder.id == item['id']))
        for item in rootfolder_to_insert:
            database.execute(
                insert(TableSportsLeaguesRootfolder)
                .values(id=item['id'], path=item['path']))


def check_sportarr_rootfolder():
    get_sportarr_rootfolder()
    rootfolder = database.execute(
        select(TableSportsLeaguesRootfolder.id, TableSportsLeaguesRootfolder.path))\
        .all()
    for item in rootfolder:
        root_path = item.path
        if not root_path.endswith(('/', '\\')):
            if root_path.startswith('/'):
                root_path += '/'
            else:
                root_path += '\\'
        if not os.path.isdir(path_mappings.path_replace_sports(root_path)):
            database.execute(
                update(TableSportsLeaguesRootfolder)
                .values(accessible=0, error='This Sportarr root directory does not seem to be accessible by Bazarr. '
                                            'Please check path mapping or if directory is empty.')
                .where(TableSportsLeaguesRootfolder.id == item.id))
        elif not os.access(path_mappings.path_replace_sports(root_path), os.W_OK):
            database.execute(
                update(TableSportsLeaguesRootfolder)
                .values(accessible=0, error='Bazarr cannot write to this directory.')
                .where(TableSportsLeaguesRootfolder.id == item.id))
        else:
            database.execute(
                update(TableSportsLeaguesRootfolder)
                .values(accessible=1, error='')
                .where(TableSportsLeaguesRootfolder.id == item.id))

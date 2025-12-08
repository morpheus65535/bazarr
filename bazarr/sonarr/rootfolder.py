# coding=utf-8

import os
import requests
import logging

from app.config import settings
from app.database import TableShowsRootfolder, TableShows, database, insert, update, delete, select
from utilities.path_mappings import path_mappings
from sonarr.info import url_api_sonarr
from constants import HEADERS


def get_sonarr_rootfolder():
    apikey_sonarr = settings.sonarr.apikey
    sonarr_rootfolder = []

    # Get root folder data from Sonarr
    url_sonarr_api_rootfolder = f"{url_api_sonarr()}rootfolder?apikey={apikey_sonarr}"

    try:
        rootfolder = requests.get(url_sonarr_api_rootfolder, timeout=int(settings.sonarr.http_timeout), verify=False, headers=HEADERS)
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
                .values(accessible=0, error='This Sonarr root directory does not seem to be accessible by Bazarr. '
                                            'Please check path mapping or if directory/drive is online.')
                .where(TableShowsRootfolder.id == item.id))
        else:
            # Test actual write instead of os.access (which fails on NFS)
            try:
                test_file = os.path.join(path_mappings.path_replace(root_path), '.bazarr_write_test')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception as e:
                database.execute(
                    update(TableShowsRootfolder)
                    .values(accessible=0, error=f"There's an issue with this Sonarr root directory: {repr(e)}")
                    .where(TableShowsRootfolder.id == item.id))
            else:
                database.execute(
                    update(TableShowsRootfolder)
                    .values(accessible=1, error='')
                    .where(TableShowsRootfolder.id == item.id))

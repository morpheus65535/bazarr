import os
from typing import Optional, List

import requests
import logging

from app.config import settings
from app.database import TableShowsRootfolder, TableShows
from utilities.path_mappings import path_mappings
from sonarr.info import get_sonarr_info, url_sonarr
from constants import headers


def get_sonarr_rootfolder() -> Optional[List]:
    apikey_sonarr = settings.sonarr.apikey
    sonarr_rootfolder = []

    # Get root folder data from Sonarr
    if get_sonarr_info.is_legacy():
        url_sonarr_api_rootfolder = (
            f"{url_sonarr()}/api/rootfolder?apikey={apikey_sonarr}"
        )
    else:
        url_sonarr_api_rootfolder = (
            f"{url_sonarr()}/api/v3/rootfolder?apikey={apikey_sonarr}"
        )

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


def check_sonarr_rootfolder() -> None:
    get_sonarr_rootfolder()
    rootfolder = TableShowsRootfolder.select(TableShowsRootfolder.id, TableShowsRootfolder.path).dicts()
    for item in rootfolder:
        root_path = item['path']
        if not root_path.endswith(('/', '\\')):
            root_path += '/' if root_path.startswith('/') else '\\'
        if not os.path.isdir(path_mappings.path_replace(root_path)):
            TableShowsRootfolder.update({TableShowsRootfolder.accessible: 0,
                                         TableShowsRootfolder.error: 'This Sonarr root directory does not seems to '
                                                                     'be accessible by Please check path '
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

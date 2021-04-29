# coding=utf-8

import os
import requests
import logging

from config import settings, url_sonarr, url_radarr
from helper import path_mappings
from database import database

headers = {"User-Agent": os.environ["SZ_USER_AGENT"]}


def get_sonarr_rootfolder():
    apikey_sonarr = settings.sonarr.apikey
    sonarr_rootfolder = []

    # Get root folder data from Sonarr
    url_sonarr_api_rootfolder = url_sonarr() + "/api/rootfolder?apikey=" + apikey_sonarr

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
        for folder in rootfolder.json():
            sonarr_rootfolder.append({'id': folder['id'], 'path': folder['path']})
        db_rootfolder = database.execute('SELECT id, path FROM table_shows_rootfolder')
        rootfolder_to_remove = [x for x in db_rootfolder if not
                                next((item for item in sonarr_rootfolder if item['id'] == x['id']), False)]
        rootfolder_to_update = [x for x in sonarr_rootfolder if
                                next((item for item in db_rootfolder if item['id'] == x['id']), False)]
        rootfolder_to_insert = [x for x in sonarr_rootfolder if not
                                next((item for item in db_rootfolder if item['id'] == x['id']), False)]

        for item in rootfolder_to_remove:
            database.execute('DELETE FROM table_shows_rootfolder WHERE id = ?', (item['id'],))
        for item in rootfolder_to_update:
            database.execute('UPDATE table_shows_rootfolder SET path=? WHERE id = ?', (item['path'], item['id']))
        for item in rootfolder_to_insert:
            database.execute('INSERT INTO table_shows_rootfolder (id, path) VALUES (?, ?)', (item['id'], item['path']))


def check_sonarr_rootfolder():
    get_sonarr_rootfolder()
    rootfolder = database.execute('SELECT id, path FROM table_shows_rootfolder')
    for item in rootfolder:
        if not os.path.isdir(path_mappings.path_replace(item['path'])):
            database.execute("UPDATE table_shows_rootfolder SET accessible = 0, error = 'This Sonarr root directory "
                             "does not seems to be accessible by Bazarr. Please check path mapping.' WHERE id = ?",
                             (item['id'],))
        elif not os.access(path_mappings.path_replace(item['path']), os.W_OK):
            database.execute("UPDATE table_shows_rootfolder SET accessible = 0, error = 'Bazarr cannot write to "
                             "this directory' WHERE id = ?", (item['id'],))
        else:
            database.execute("UPDATE table_shows_rootfolder SET accessible = 1, error = '' WHERE id = ?", (item['id'],))


def get_radarr_rootfolder():
    apikey_radarr = settings.radarr.apikey
    radarr_rootfolder = []

    # Get root folder data from Radarr
    url_radarr_api_rootfolder = url_radarr() + "/api/rootfolder?apikey=" + apikey_radarr

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
        for folder in rootfolder.json():
            radarr_rootfolder.append({'id': folder['id'], 'path': folder['path']})
        db_rootfolder = database.execute('SELECT id, path FROM table_movies_rootfolder')
        rootfolder_to_remove = [x for x in db_rootfolder if not
                                next((item for item in radarr_rootfolder if item['id'] == x['id']), False)]
        rootfolder_to_update = [x for x in radarr_rootfolder if
                                next((item for item in db_rootfolder if item['id'] == x['id']), False)]
        rootfolder_to_insert = [x for x in radarr_rootfolder if not
                                next((item for item in db_rootfolder if item['id'] == x['id']), False)]

        for item in rootfolder_to_remove:
            database.execute('DELETE FROM table_movies_rootfolder WHERE id = ?', (item['id'],))
        for item in rootfolder_to_update:
            database.execute('UPDATE table_movies_rootfolder SET path=? WHERE id = ?', (item['path'], item['id']))
        for item in rootfolder_to_insert:
            database.execute('INSERT INTO table_movies_rootfolder (id, path) VALUES (?, ?)', (item['id'], item['path']))


def check_radarr_rootfolder():
    get_radarr_rootfolder()
    rootfolder = database.execute('SELECT id, path FROM table_movies_rootfolder')
    for item in rootfolder:
        if not os.path.isdir(path_mappings.path_replace_movie(item['path'])):
            database.execute("UPDATE table_movies_rootfolder SET accessible = 0, error = 'This Radarr root directory "
                             "does not seems to be accessible by Bazarr. Please check path mapping.' WHERE id = ?",
                             (item['id'],))
        elif not os.access(path_mappings.path_replace_movie(item['path']), os.W_OK):
            database.execute("UPDATE table_movies_rootfolder SET accessible = 0, error = 'Bazarr cannot write to "
                             "this directory' WHERE id = ?", (item['id'],))
        else:
            database.execute("UPDATE table_movies_rootfolder SET accessible = 1, error = '' WHERE id = ?",
                             (item['id'],))

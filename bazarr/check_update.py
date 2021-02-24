# coding=utf-8

import os
import logging
import json
import requests
import semver
from zipfile import ZipFile

from get_args import args
from config import settings
from database import database


def check_releases():
    releases = []
    url_releases = 'https://api.github.com/repos/morpheus65535/Bazarr/releases'
    try:
        r = requests.get(url_releases, timeout=15)
        r.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        logging.exception("Error trying to get releases from Github. Http error.")
    except requests.exceptions.ConnectionError as errc:
        logging.exception("Error trying to get releases from Github. Connection Error.")
    except requests.exceptions.Timeout as errt:
        logging.exception("Error trying to get releases from Github. Timeout Error.")
    except requests.exceptions.RequestException as err:
        logging.exception("Error trying to get releases from Github.")
    else:
        for release in r.json():
            releases.append({'name': release['name'],
                             'body': release['body'],
                             'date': release['published_at'],
                             'prerelease': release['prerelease'],
                             'download_link': release['zipball_url']})
        with open(os.path.join(args.config_dir, 'config', 'releases.txt'), 'w') as f:
            json.dump(releases, f)


def check_if_new_update():
    if settings.general.branch == 'master':
        use_prerelease = False
    elif settings.general.branch == 'development':
        use_prerelease = True
    else:
        logging.error('BAZARR unknown branch provided to updater: {}'.format(settings.general.branch))
        return
    logging.debug('BAZARR updater is using {} branch'.format(settings.general.branch))

    check_releases()

    with open(os.path.join(args.config_dir, 'config', 'releases.txt'), 'r') as f:
        data = json.load(f)
    if not args.no_update:
        release = next((item for item in data if item["prerelease"] == use_prerelease), None)
        if release:
            if semver.compare(release['name'].lstrip('v'), os.environ["BAZARR_VERSION"]) > 0:
                download_release(url=release['download_link'])


def download_release(url):
    update_dir = os.path.join(args.config_dir, 'update')
    os.makedirs(update_dir, exist_ok=True)
    r = requests.get(url, allow_redirects=True)
    try:
        with open(os.path.join(update_dir, 'bazarr.zip'), 'wb') as f:
            f.write(r.content)
    except Exception as e:
        logging.exception('BAZARR unable to download new release')
    else:
        from server import webserver
        webserver.restart()


def apply_update():
    is_updated = False
    update_dir = os.path.join(args.config_dir, 'update')
    bazarr_zip = os.path.join(update_dir, 'bazarr.zip')
    bazarr_dir = os.path.dirname(os.path.dirname(__file__))
    if os.path.isdir(update_dir):
        if os.path.isfile(bazarr_zip):
            try:
                with ZipFile(bazarr_zip, 'r') as archive:
                    zip_root_directory = archive.namelist()[0]
                    for file in archive.namelist():
                        if file.startswith(zip_root_directory) and file != zip_root_directory:
                            file_path = os.path.join(bazarr_dir, file[len(zip_root_directory):])
                            parent_dir = os.path.dirname(file_path)
                            os.makedirs(parent_dir, exist_ok=True)
                            if not os.path.isdir(file_path):
                                with open(file_path, 'wb+') as f:
                                    f.write(archive.read(file))
            except Exception as e:
                logging.exception('BAZARR unable to unzip release')
            else:
                is_updated = True
            finally:
                os.remove(bazarr_zip)
    else:
        return

    if is_updated:
        updated()


def updated():
    if settings.general.getboolean('update_restart'):
        from server import webserver
        webserver.restart()
    else:
        database.execute("UPDATE system SET updated='1'")

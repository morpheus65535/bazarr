# coding=utf-8

import os
import logging
import json
import requests
import semver
from zipfile import ZipFile

from get_args import args
from config import settings


def check_releases():
    releases = []
    url_releases = 'https://api.github.com/repos/morpheus65535/Bazarr/releases'
    try:
        logging.debug('BAZARR getting releases from Github: {}'.format(url_releases))
        r = requests.get(url_releases, allow_redirects=True)
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
        logging.debug('BAZARR saved {} releases to releases.txt'.format(len(r.json())))


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
        if use_prerelease:
            release = next((item for item in data), None)
        else:
            release = next((item for item in data if not item["prerelease"]), None)
        if release:
            logging.debug('BAZARR last release available is {}'.format(release['name']))

            try:
                semver.parse(os.environ["BAZARR_VERSION"])
                semver.parse(release['name'].lstrip('v'))
            except ValueError:
                new_version = True
            else:
                new_version = True if semver.compare(release['name'].lstrip('v'), os.environ["BAZARR_VERSION"]) > 0 \
                    else False

            # skip update process if latest release is v0.9.1.1 which is the latest pre-semver compatible release
            if new_version and release['name'] != 'v0.9.1.1':
                logging.debug('BAZARR newer release available and will be downloaded: {}'.format(release['name']))
                download_release(url=release['download_link'])
            else:
                logging.debug('BAZARR no newer release have been found')
        else:
            logging.debug('BAZARR no release found')
    else:
        logging.debug('BAZARR --no_update have been used as an argument')


def download_release(url):
    r = None
    update_dir = os.path.join(args.config_dir, 'update')
    try:
        os.makedirs(update_dir, exist_ok=True)
    except Exception as e:
        logging.debug('BAZARR unable to create update directory {}'.format(update_dir))
    else:
        logging.debug('BAZARR downloading release from Github: {}'.format(url))
        r = requests.get(url, allow_redirects=True)
    if r:
        try:
            with open(os.path.join(update_dir, 'bazarr.zip'), 'wb') as f:
                f.write(r.content)
        except Exception as e:
            logging.exception('BAZARR unable to download new release and save it to disk')
        else:
            apply_update()


def apply_update():
    is_updated = False
    update_dir = os.path.join(args.config_dir, 'update')
    bazarr_zip = os.path.join(update_dir, 'bazarr.zip')
    bazarr_dir = os.path.dirname(os.path.dirname(__file__))
    if os.path.isdir(update_dir):
        if os.path.isfile(bazarr_zip):
            logging.debug('BAZARR is trying to unzip this release to {0}: {1}'.format(bazarr_dir, bazarr_zip))
            try:
                with ZipFile(bazarr_zip, 'r') as archive:
                    zip_root_directory = archive.namelist()[0]
                    for file in archive.namelist():
                        if file.startswith(zip_root_directory) and file != zip_root_directory and not \
                                file.endswith('bazarr.py'):
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
                logging.debug('BAZARR now deleting release archive')
                os.remove(bazarr_zip)
    else:
        return

    if is_updated:
        logging.debug('BAZARR new release have been installed, now we restart')
        from server import webserver
        webserver.restart()

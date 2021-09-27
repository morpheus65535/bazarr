# coding=utf-8
# pylama:ignore=W0611
# TODO unignore and fix W0611

import os
import shutil
import re
import logging
import json
import requests
import semver
from shutil import rmtree
from zipfile import ZipFile

from get_args import args
from config import settings


def check_releases():
    releases = []
    url_releases = 'https://api.github.com/repos/Bazarr/Bazarr2/releases?per_page=100'
    try:
        logging.debug('BAZARR getting releases from Github: {}'.format(url_releases))
        r = requests.get(url_releases, allow_redirects=True)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        logging.exception("Error trying to get releases from Github. Http error.")
    except requests.exceptions.ConnectionError:
        logging.exception("Error trying to get releases from Github. Connection Error.")
    except requests.exceptions.Timeout:
        logging.exception("Error trying to get releases from Github. Timeout Error.")
    except requests.exceptions.RequestException:
        logging.exception("Error trying to get releases from Github.")
    else:
        for release in r.json():
            download_link = None
            for asset in release['assets']:
                if asset['name'] == 'bazarr.zip':
                    download_link = asset['browser_download_url']
            if not download_link:
                continue
            releases.append({'name': release['name'],
                             'body': release['body'],
                             'date': release['published_at'],
                             'prerelease': release['prerelease'],
                             'download_link': download_link})
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

            current_version = None
            try:
                current_version = semver.VersionInfo.parse(os.environ["BAZARR_VERSION"])
                semver.VersionInfo.parse(release['name'].lstrip('v'))
            except ValueError:
                new_version = True
            else:
                new_version = True if semver.compare(release['name'].lstrip('v'), os.environ["BAZARR_VERSION"]) > 0 \
                    else False

            # skip update process if latest release is v0.9.1.1 which is the latest pre-semver compatible release
            if new_version and release['name'] != 'v0.9.1.1':
                logging.debug('BAZARR newer release available and will be downloaded: {}'.format(release['name']))
                download_release(url=release['download_link'])
            # rolling back from nightly to stable release
            elif current_version:
                if current_version.prerelease and not use_prerelease:
                    logging.debug('BAZARR previous stable version will be downloaded: {}'.format(release['name']))
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
    except Exception:
        logging.debug('BAZARR unable to create update directory {}'.format(update_dir))
    else:
        logging.debug('BAZARR downloading release from Github: {}'.format(url))
        r = requests.get(url, allow_redirects=True)
    if r:
        try:
            with open(os.path.join(update_dir, 'bazarr.zip'), 'wb') as f:
                f.write(r.content)
        except Exception:
            logging.exception('BAZARR unable to download new release and save it to disk')
        else:
            apply_update()


def apply_update():
    is_updated = False
    update_dir = os.path.join(args.config_dir, 'update')
    bazarr_zip = os.path.join(update_dir, 'bazarr.zip')
    bazarr_dir = os.path.dirname(os.path.dirname(__file__))
    build_dir = os.path.join(os.path.dirname(__file__), 'frontend', 'build')

    if os.path.isdir(update_dir):
        if os.path.isfile(bazarr_zip):
            logging.debug('BAZARR is trying to unzip this release to {0}: {1}'.format(bazarr_dir, bazarr_zip))
            try:
                with ZipFile(bazarr_zip, 'r') as archive:
                    zip_root_directory = ''
                    if len({item.split('/')[0] for item in archive.namelist()}) == 1:
                        zip_root_directory = archive.namelist()[0]

                    if os.path.isdir(build_dir):
                        try:
                            rmtree(build_dir, ignore_errors=True)
                        except Exception:
                            logging.exception(
                                'BAZARR was unable to delete the previous build directory during upgrade process.')

                    for file in archive.namelist():
                        if file.startswith(zip_root_directory) and file != zip_root_directory and not \
                                file.endswith('bazarr.py'):
                            file_path = os.path.join(bazarr_dir, file[len(zip_root_directory):])
                            parent_dir = os.path.dirname(file_path)
                            os.makedirs(parent_dir, exist_ok=True)
                            if not os.path.isdir(file_path):
                                with open(file_path, 'wb+') as f:
                                    f.write(archive.read(file))
            except Exception:
                logging.exception('BAZARR unable to unzip release')
            else:
                is_updated = True
                try:
                    logging.debug('BAZARR successfully unzipped new release and will now try to delete the leftover '
                                  'files.')
                    update_cleaner(zipfile=bazarr_zip, bazarr_dir=bazarr_dir, config_dir=args.config_dir)
                except Exception:
                    logging.exception('BAZARR unable to cleanup leftover files after upgrade.')
                else:
                    logging.debug('BAZARR successfully deleted leftover files.')
            finally:
                logging.debug('BAZARR now deleting release archive')
                os.remove(bazarr_zip)
    else:
        return

    if is_updated:
        logging.debug('BAZARR new release have been installed, now we restart')
        from server import webserver
        webserver.restart()


def update_cleaner(zipfile, bazarr_dir, config_dir):
    with ZipFile(zipfile, 'r') as archive:
        file_in_zip = archive.namelist()
    logging.debug('BAZARR zip file contain {} directories and files'.format(len(file_in_zip)))
    separator = os.path.sep
    if os.path.sep == '\\':
        logging.debug('BAZARR upgrade leftover cleaner is running on Windows. We\'ll fix the zip file separator '
                      'accordingly.')
        for i, item in enumerate(file_in_zip):
            file_in_zip[i] = item.replace('/', '\\')
        separator += os.path.sep
    else:
        logging.debug('BAZARR upgrade leftover cleaner is running on something else than Windows. The zip file '
                      'separator are fine.')

    dir_to_ignore = ['^.' + separator,
                     '^bin' + separator,
                     '^venv' + separator,
                     '^WinPython' + separator,
                     separator + '__pycache__' + separator + '$']
    if os.path.abspath(bazarr_dir) in os.path.abspath(config_dir):
        dir_to_ignore.append('^' + os.path.relpath(config_dir, bazarr_dir) + os.path.sep)
    dir_to_ignore_regex = re.compile('(?:% s)' % '|'.join(dir_to_ignore))
    logging.debug('BAZARR upgrade leftover cleaner will ignore directories matching this regex: '
                  '{}'.format(dir_to_ignore_regex))

    file_to_ignore = ['nssm.exe', '7za.exe']
    logging.debug('BAZARR upgrade leftover cleaner will ignore those files: {}'.format(', '.join(file_to_ignore)))
    extension_to_ignore = ['.pyc']
    logging.debug('BAZARR upgrade leftover cleaner will ignore files with those extensions: '
                  '{}'.format(', '.join(extension_to_ignore)))

    file_on_disk = []
    folder_list = []
    for foldername, subfolders, filenames in os.walk(bazarr_dir):
        relative_foldername = os.path.relpath(foldername, bazarr_dir) + os.path.sep

        if not dir_to_ignore_regex.findall(relative_foldername):
            if relative_foldername not in folder_list:
                folder_list.append(relative_foldername)

        for file in filenames:
            if file in file_to_ignore:
                continue
            elif os.path.splitext(file)[1] in extension_to_ignore:
                continue
            elif foldername == bazarr_dir:
                file_on_disk.append(file)
            else:
                current_dir = relative_foldername
                filepath = os.path.join(current_dir, file)
                if not dir_to_ignore_regex.findall(filepath):
                    file_on_disk.append(filepath)
    logging.debug('BAZARR directory contain {} files'.format(len(file_on_disk)))
    logging.debug('BAZARR directory contain {} directories'.format(len(folder_list)))
    file_on_disk += folder_list
    logging.debug('BAZARR directory contain {} directories and files'.format(len(file_on_disk)))

    file_to_remove = list(set(file_on_disk) - set(file_in_zip))
    logging.debug('BAZARR will delete {} directories and files'.format(len(file_to_remove)))
    logging.debug('BAZARR will delete this: {}'.format(', '.join(file_to_remove)))

    for file in file_to_remove:
        filepath = os.path.join(bazarr_dir, file)
        try:
            if os.path.isdir(filepath):
                rmtree(filepath, ignore_errors=True)
            else:
                os.remove(filepath)
        except Exception:
            logging.debug('BAZARR upgrade leftover cleaner cannot delete {}'.format(filepath))

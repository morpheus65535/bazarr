# coding=utf-8

import os
import re
import logging
import json
import requests
import semver
import sys

from shutil import rmtree
from zipfile import ZipFile

from .get_args import args
from .config import settings
from .jobs_queue import jobs_queue


def deprecated_python_version():
    # return True if Python version is deprecated
    return sys.version_info.major == 2 or (sys.version_info.major == 3 and sys.version_info.minor < 8)


def check_releases(job_id=None, startup=False):
    # startup is used to prevent trying to create a job before the jobs queue is initialized
    if not startup and not job_id:
        jobs_queue.add_job_from_function("Update Release Info", is_progress=False)
        return

    releases = []
    url_releases = 'https://api.github.com/repos/morpheus65535/Bazarr/releases?per_page=100'
    try:
        logging.debug(f'BAZARR getting releases from Github: {url_releases}')
        r = requests.get(url_releases, allow_redirects=True, timeout=15)
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
        logging.debug(f'BAZARR saved {len(r.json())} releases to releases.txt')


def check_if_new_update():
    if settings.general.branch == 'master':
        use_prerelease = False
    elif settings.general.branch == 'development':
        use_prerelease = True
    else:
        logging.error(f'BAZARR unknown branch provided to updater: {settings.general.branch}')
        return
    logging.debug(f'BAZARR updater is using {settings.general.branch} branch')

    check_releases(startup=True)

    with open(os.path.join(args.config_dir, 'config', 'releases.txt'), 'r') as f:
        data = json.load(f)
    if not args.no_update:
        release = None
        if use_prerelease:
            if deprecated_python_version():
                release = next((item['name'].lstrip('v') for item in data if
                                semver.VersionInfo.parse('1.3.1') > semver.VersionInfo.parse(item['name'].lstrip('v'))))
            else:
                release = next((item for item in data), None)
        else:
            if deprecated_python_version():
                next((item['name'].lstrip('v') for item in data if
                      not item['prerelease'] and semver.VersionInfo.parse('1.3.1') > semver.VersionInfo.parse(
                          item['name'].lstrip('v'))))
            else:
                release = next((item for item in data if not item["prerelease"]), None)

        if release and 'name' in release:
            logging.debug(f'BAZARR last release available is {release["name"]}')
            if deprecated_python_version():
                logging.warning('BAZARR is using a deprecated Python version, you must update Python to get latest '
                                'version available.')

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
                logging.debug(f'BAZARR newer release available and will be downloaded: {release["name"]}')
                download_release(url=release['download_link'])
            # rolling back from nightly to stable release
            elif current_version:
                if current_version.prerelease and not use_prerelease:
                    logging.debug(f'BAZARR previous stable version will be downloaded: {release["name"]}')
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
        logging.debug(f'BAZARR unable to create update directory {update_dir}')
    else:
        logging.debug(f'BAZARR downloading release from Github: {url}')
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
    bazarr_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    build_dir = os.path.join(bazarr_dir, 'frontend', 'build')

    if os.path.isdir(update_dir):
        if os.path.isfile(bazarr_zip):
            logging.debug(f'BAZARR is trying to unzip this release to {bazarr_dir}: {bazarr_zip}')
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
                        if file.startswith(zip_root_directory) and file != zip_root_directory:
                            file_path = os.path.join(bazarr_dir, file[len(zip_root_directory):])
                            parent_dir = os.path.dirname(file_path)
                            os.makedirs(parent_dir, exist_ok=True)
                            if not os.path.isdir(file_path):
                                if os.path.exists(file_path):
                                    # remove the file first to handle case-insensitive file systems
                                    os.remove(file_path)
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
        from .server import webserver
        webserver.restart()


def update_cleaner(zipfile, bazarr_dir, config_dir):
    with ZipFile(zipfile, 'r') as archive:
        file_in_zip = archive.namelist()
    logging.debug(f'BAZARR zip file contain {len(file_in_zip)} directories and files')
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

    dir_to_ignore = [f'^.{separator}',
                     f'^bin{separator}',
                     f'^venv{separator}',
                     f'^WinPython{separator}',
                     f'{separator}__pycache__{separator}$']
    if os.path.abspath(bazarr_dir).lower() == os.path.abspath(config_dir).lower():
        # for users who installed Bazarr inside the config directory (ie: `%programdata%\Bazarr` on windows)
        dir_to_ignore.append(f'^backup{separator}')
        dir_to_ignore.append(f'^cache{separator}')
        dir_to_ignore.append(f'^config{separator}')
        dir_to_ignore.append(f'^db{separator}')
        dir_to_ignore.append(f'^log{separator}')
        dir_to_ignore.append(f'^restore{separator}')
        dir_to_ignore.append(f'^update{separator}')
    elif os.path.abspath(bazarr_dir).lower() in os.path.abspath(config_dir).lower():
        # when config directory is a child of Bazarr installation directory
        dir_to_ignore.append(f'^{os.path.relpath(config_dir, bazarr_dir)}{separator}')
    dir_to_ignore_regex_string = '(?:% s)' % '|'.join(dir_to_ignore)
    logging.debug(f'BAZARR upgrade leftover cleaner will ignore directories matching this '
                  f'regex: {dir_to_ignore_regex_string}')
    dir_to_ignore_regex = re.compile(dir_to_ignore_regex_string)

    file_to_ignore = ['nssm.exe', '7za.exe', 'unins000.exe', 'unins000.dat']
    # prevent deletion of leftover Apprise.py/pyi files after 1.8.0 version that caused issue on case-insensitive
    # filesystem. This could be removed in a couple of major versions.
    file_to_ignore += ['Apprise.py', 'Apprise.pyi', 'apprise.py', 'apprise.pyi']
    logging.debug(f'BAZARR upgrade leftover cleaner will ignore those files: {", ".join(file_to_ignore)}')
    extension_to_ignore = ['.pyc']
    logging.debug(
        f'BAZARR upgrade leftover cleaner will ignore files with those extensions: {", ".join(extension_to_ignore)}')

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
    logging.debug(f'BAZARR directory contain {len(file_on_disk)} files')
    logging.debug(f'BAZARR directory contain {len(folder_list)} directories')
    file_on_disk += folder_list
    logging.debug(f'BAZARR directory contain {len(file_on_disk)} directories and files')

    file_to_remove = list(set(file_on_disk) - set(file_in_zip))
    logging.debug(f'BAZARR will delete {len(file_to_remove)} directories and files')
    logging.debug(f'BAZARR will delete this: {", ".join(file_to_remove)}')

    for file in file_to_remove:
        filepath = os.path.join(bazarr_dir, file)
        try:
            if os.path.isdir(filepath):
                rmtree(filepath, ignore_errors=True)
            else:
                os.remove(filepath)
        except Exception:
            logging.debug(f'BAZARR upgrade leftover cleaner cannot delete {filepath}')

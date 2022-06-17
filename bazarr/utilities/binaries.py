# coding=utf-8

import os
import platform
import logging
import requests
import json
import hashlib
import stat

from whichcraft import which
from dogpile.cache import make_region

region = make_region().configure('dogpile.cache.memory')


class BinaryNotFound(Exception):
    pass


@region.cache_on_arguments()
def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


@region.cache_on_arguments()
def get_binaries_from_json():
    try:
        binaries_json_file = os.path.realpath(os.path.join(os.path.dirname(__file__), 'binaries.json'))
        with open(binaries_json_file) as json_file:
            binaries_json = json.load(json_file)
    except OSError:
        logging.exception('BAZARR cannot access binaries.json')
        return []
    else:
        return binaries_json


def get_binary(name):
    installed_exe = which(name)

    if installed_exe and os.path.isfile(installed_exe):
        logging.debug(f'BAZARR returning this binary: {installed_exe}')
        return installed_exe
    else:
        logging.debug('BAZARR binary not found in path, searching for it...')
        binaries_dir = os.path.realpath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'bin'))
        system = platform.system()
        machine = platform.machine()
        dir_name = name

        # deals with exceptions
        if platform.system() == "Windows":  # Windows
            machine = "i386"
            name = f"{name}.exe"
        elif platform.system() == "Darwin":  # MacOSX
            system = 'MacOSX'
        if name in ['ffprobe', 'ffprobe.exe']:
            dir_name = 'ffmpeg'

        exe_dir = os.path.abspath(os.path.join(binaries_dir, system, machine, dir_name))
        exe = os.path.abspath(os.path.join(exe_dir, name))

        binaries_json = get_binaries_from_json()
        binary = next((item for item in binaries_json if item['system'] == system and item['machine'] == machine and
                       item['directory'] == dir_name and item['name'] == name), None)
        if not binary:
            logging.debug('BAZARR binary not found in binaries.json')
            raise BinaryNotFound
        else:
            logging.debug(f'BAZARR found this in binaries.json: {binary}')

        if os.path.isfile(exe) and md5(exe) == binary['checksum']:
            logging.debug(f'BAZARR returning this existing and up-to-date binary: {exe}')
            return exe
        else:
            try:
                logging.debug(f'BAZARR creating directory tree for {exe_dir}')
                os.makedirs(exe_dir, exist_ok=True)
                logging.debug('BAZARR downloading {0} from {1}'.format(name, binary['url']))
                r = requests.get(binary['url'])
                logging.debug('BAZARR saving {0} to {1}'.format(name, exe_dir))
                with open(exe, 'wb') as f:
                    f.write(r.content)
                if system != 'Windows':
                    logging.debug(f'BAZARR adding execute permission on {exe}')
                    st = os.stat(exe)
                    os.chmod(exe, st.st_mode | stat.S_IEXEC)
            except Exception as e:
                logging.exception('BAZARR unable to download {0} to {1}'.format(name, exe_dir))
                raise BinaryNotFound from e
            else:
                logging.debug(f'BAZARR returning this new binary: {exe}')
                return exe

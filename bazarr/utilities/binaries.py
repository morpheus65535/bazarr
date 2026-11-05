# coding=utf-8

import os
import platform
import logging
import requests
import json
import hashlib
import stat
from typing import TypedDict

from whichcraft import which
from dogpile.cache import make_region

region = make_region().configure('dogpile.cache.memory')


class BinaryNotFound(Exception):
    pass


class BinaryDescriptor(TypedDict):
    system: str
    machine: str
    directory: str
    name: str
    checksum: str
    url: str


@region.cache_on_arguments()
def _md5(fname: str) -> str:
    """
    Compute the MD5 hexadecimal digest of a file identified by its path.
    The file is opened in binary mode and read in chunks of 4096 bytes so
    that large files can be hashed without loading them entirely into
    memory. The result is cached on the given arguments via the region
    cache decorator, so repeated calls with the same path return the
    previously computed digest.

    :param fname: Path to the file whose MD5 digest should be computed.
    :return: Hexadecimal string representation of the MD5 digest of the
        file contents.
    :raises FileNotFoundError: If the file at the given path does not
        exist.
    :raises PermissionError: If the file cannot be opened for reading due
        to insufficient permissions.
    :raises OSError: If any other I/O error occurs while opening or
        reading the file.
    """
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


@region.cache_on_arguments()
def _get_binaries_from_json() -> list[BinaryDescriptor]:
    """
    Load and return the list of binary descriptors stored in the bundled
    ``binaries.json`` file located next to this module.

    The file path is resolved relative to the directory of the current module,
    opened, and its JSON content is parsed into a list of binary descriptors.
    The result is cached on its arguments by the configured cache region, so
    subsequent calls return the cached value without re-reading the file. If
    the file cannot be accessed, the error is logged and an empty list is
    returned instead of propagating the exception.

    :return: The parsed list of binary descriptors read from ``binaries.json``,
        or an empty list if the file could not be accessed.

    """
    try:
        binaries_json_file = os.path.realpath(os.path.join(os.path.dirname(__file__), 'binaries.json'))
        with open(binaries_json_file) as json_file:
            binaries_json = json.load(json_file)
    except OSError:
        logging.exception('BAZARR cannot access binaries.json')
        return []
    else:
        return binaries_json


def get_binary(name: str) -> str:
    """
    Locate an executable binary by name, downloading it if necessary.

    The function first checks whether the requested binary is available on
    the system ``PATH``. If it is found there, its path is returned
    immediately. Otherwise, the function searches the bundled ``bin``
    directory of the application, resolving the proper subdirectory based
    on the current operating system and machine architecture. Platform
    specific adjustments are applied: on Windows the architecture is forced
    to ``i386`` and the ``.exe`` suffix is appended, while on macOS the
    system name is mapped to ``MacOSX``. The ``ffprobe`` binary is looked up
    inside the ``ffmpeg`` directory.

    The expected binary is then matched against the entries described in
    the ``binaries.json`` manifest. If a matching entry exists and the local
    file is present with a matching MD5 checksum, its path is returned.
    Otherwise the binary is downloaded from the URL declared in the
    manifest, saved to the expected location and, on non-Windows systems,
    given execute permission before its path is returned.

    :param name: Name of the binary to locate, without any platform
        specific extension.
    :return: Absolute path to the located, verified or freshly downloaded
        binary.
    :raises BinaryNotFound: If no matching entry exists in the
        ``binaries.json`` manifest, or if the binary could not be
        downloaded or written to its destination.
    """
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
            name = "%s.exe" % name
        elif platform.system() == "Darwin":  # MacOSX
            system = 'MacOSX'
        if name in ['ffprobe', 'ffprobe.exe']:
            dir_name = 'ffmpeg'

        exe_dir = os.path.abspath(os.path.join(binaries_dir, system, machine, dir_name))
        exe = os.path.abspath(os.path.join(exe_dir, name))

        binaries_json = _get_binaries_from_json()
        binary = next((item for item in binaries_json if item['system'] == system and item['machine'] == machine and
                       item['directory'] == dir_name and item['name'] == name), None)
        if not binary:
            logging.debug('BAZARR binary not found in binaries.json')
            raise BinaryNotFound
        else:
            logging.debug(f'BAZARR found this in binaries.json: {binary}')

        if os.path.isfile(exe) and _md5(exe) == binary['checksum']:
            logging.debug(f'BAZARR returning this existing and up-to-date binary: {exe}')
            return exe
        else:
            try:
                logging.debug(f'BAZARR creating directory tree for {exe_dir}')
                os.makedirs(exe_dir, exist_ok=True)
                logging.debug(f'BAZARR downloading {name} from {binary["url"]}')
                r = requests.get(binary['url'])
                logging.debug(f'BAZARR saving {name} to {exe_dir}')
                with open(exe, 'wb') as f:
                    f.write(r.content)
                if system != 'Windows':
                    logging.debug(f'BAZARR adding execute permission on {exe}')
                    st = os.stat(exe)
                    os.chmod(exe, st.st_mode | stat.S_IEXEC)
            except Exception:
                logging.exception(f'BAZARR unable to download {name} to {exe_dir}')
                raise BinaryNotFound
            else:
                logging.debug(f'BAZARR returning this new binary: {exe}')
                return exe

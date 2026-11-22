# coding=utf-8

import os
import string
from typing import TypedDict


class DirectoryEntry(TypedDict):
    name: str
    path: str


class BrowseFilesystemResult(TypedDict):
    directories: list[DirectoryEntry]
    parent: str


def browse_bazarr_filesystem(path: str = '#') -> BrowseFilesystemResult:
    """
    Browse the local filesystem and list the subdirectories of a given path.

    When the requested path is the root marker (``'#'``), the root (``'/'``) or
    an empty string, the function enumerates the top-level entries of the
    filesystem. On Windows this means every existing drive letter (for example
    ``C:\\``), while on other operating systems the directories located directly
    under ``/`` are listed. For any other path, only the immediate
    subdirectories of that path are returned. Each directory entry contains
    its name and its full path with a trailing separator. The entries are
    sorted alphabetically by name and the parent directory of the browsed
    path is included in the result, with ``'#'`` used as the parent of the
    root marker.

    :param path: Filesystem path to browse. Defaults to ``'#'``, which denotes
        the root of the filesystem.
    :return: A mapping containing the sorted list of subdirectory entries under
        the ``'directories'`` key and the parent directory under the
        ``'parent'`` key.
    :raises FileNotFoundError: If the given path does not exist.
    :raises NotADirectoryError: If the given path exists but is not a
        directory.
    :raises PermissionError: If the given path cannot be read due to
        insufficient permissions.
    """
    if path == '#' or path == '/' or path == '':
        if os.name == 'nt':
            dir_list = []
            for drive in string.ascii_uppercase:
                drive_letter = f'{drive}:\\'
                if os.path.exists(drive_letter):
                    dir_list.append(drive_letter)
        else:
            path = "/"
            dir_list = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    else:
        dir_list = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]

    data: list[DirectoryEntry] = []
    for item in dir_list:
        full_path = os.path.join(path, item, '')
        entry: DirectoryEntry = {
            "name": item,
            "path": full_path
        }
        data.append(entry)

    parent = os.path.dirname(path)

    result: BrowseFilesystemResult = {
        'directories': sorted(data, key=lambda i: i['name']),
        'parent': '#' if path == '#' else parent,
    }
    return result

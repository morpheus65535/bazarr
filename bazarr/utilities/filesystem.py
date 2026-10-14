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

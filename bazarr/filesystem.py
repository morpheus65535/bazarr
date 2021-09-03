# coding=utf-8

import os
import requests
import logging
import string

from config import settings

headers = {"User-Agent": os.environ["SZ_USER_AGENT"]}


def browse_bazarr_filesystem(path='#'):
    if path == '#' or path == '/' or path == '':
        if os.name == 'nt':
            dir_list = []
            for drive in string.ascii_uppercase:
                drive_letter = drive + ':\\'
                if os.path.exists(drive_letter):
                    dir_list.append(drive_letter)
        else:
            path = "/"
            dir_list = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    else:
        dir_list = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]

    data = []
    for item in dir_list:
        full_path = os.path.join(path, item, '')
        item = {
            "name": item,
            "path": full_path
        }
        data.append(item)

    parent = os.path.dirname(path)

    result = {'directories': sorted(data, key=lambda i: i['name'])}
    if path == '#':
        result.update({'parent': '#'})
    else:
        result.update({'parent': parent})

    return result

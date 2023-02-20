# coding=utf-8

import os
import hashlib
import requests
import logging
import json
import pretty

from datetime import datetime
from operator import itemgetter

from app.get_providers import get_providers
from app.database import TableAnnouncements
from .get_args import args


# Announcements as receive by browser must be in the form of a list of dicts converted to JSON
# [
#     {
#         'text': 'some text',
#         'link': 'http://to.somewhere.net',
#         'hash': '',
#         'dismissible': True,
#         'timestamp': 1676236978,
#         'enabled': True,
#     },
# ]


def parse_announcement_dict(announcement_dict):
    announcement_dict['timestamp'] = pretty.date(announcement_dict['timestamp'])
    announcement_dict['link'] = announcement_dict.get('link', '')
    announcement_dict['dismissible'] = announcement_dict.get('dismissible', True)
    announcement_dict['enabled'] = announcement_dict.get('enabled', True)
    announcement_dict['hash'] = hashlib.sha256(announcement_dict['text'].encode('UTF8')).hexdigest()

    return announcement_dict


def get_announcements_to_file():
    try:
        r = requests.get("https://raw.githubusercontent.com/morpheus65535/bazarr-binaries/master/announcements.json")
    except requests.exceptions.HTTPError:
        logging.exception("Error trying to get announcements from Github. Http error.")
    except requests.exceptions.ConnectionError:
        logging.exception("Error trying to get announcements from Github. Connection Error.")
    except requests.exceptions.Timeout:
        logging.exception("Error trying to get announcements from Github. Timeout Error.")
    except requests.exceptions.RequestException:
        logging.exception("Error trying to get announcements from Github.")
    else:
        with open(os.path.join(args.config_dir, 'config', 'announcements.json'), 'wb') as f:
            f.write(r.content)


def get_online_announcements():
    try:
        with open(os.path.join(args.config_dir, 'config', 'announcements.json'), 'r') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    else:
        for announcement in data['data']:
            if 'enabled' not in announcement:
                data['data'][announcement]['enabled'] = True
            if 'dismissible' not in announcement:
                data['data'][announcement]['dismissible'] = True

        return data['data']


def get_local_announcements():
    announcements = []

    # opensubtitles.org end-of-life
    enabled_providers = get_providers()
    if enabled_providers and 'opensubtitles' in enabled_providers:
        announcements.append({
            'text': 'Opensubtitles.org will be deprecated soon, migrate to Opensubtitles.com ASAP and disable this '
                    'provider to remove this announcement.',
            'link': 'https://wiki.bazarr.media/Troubleshooting/OpenSubtitles-migration/',
            'dismissible': False,
            'timestamp': 1676236978,
        })

    for announcement in announcements:
        if 'enabled' not in announcement:
            announcement['enabled'] = True
        if 'dismissible' not in announcement:
            announcement['dismissible'] = True

    return announcements


def get_all_announcements():
    # get announcements that haven't been dismissed yet
    announcements = [parse_announcement_dict(x) for x in get_online_announcements() + get_local_announcements() if
                     x['enabled'] and (not x['dismissible'] or not TableAnnouncements.select()
                                       .where(TableAnnouncements.hash ==
                                              hashlib.sha256(x['text'].encode('UTF8')).hexdigest()).get_or_none())]

    return sorted(announcements, key=itemgetter('timestamp'), reverse=True)


def mark_announcement_as_dismissed(hashed_announcement):
    text = [x['text'] for x in get_all_announcements() if x['hash'] == hashed_announcement]
    if text:
        TableAnnouncements.insert({TableAnnouncements.hash: hashed_announcement,
                                   TableAnnouncements.timestamp: datetime.now(),
                                   TableAnnouncements.text: text[0]})\
            .on_conflict_ignore(ignore=True)\
            .execute()

# coding=utf-8

import os
import sys
import hashlib
import requests
import logging
import json
import pretty

from datetime import datetime
from operator import itemgetter

from app.get_providers import get_enabled_providers
from app.database import TableAnnouncements, database, insert, select

from app.config import settings
from app.get_args import args
from sonarr.info import get_sonarr_info
from radarr.info import get_radarr_info


def upcoming_deprecated_python_version():
    # return True if Python version is deprecated
    return sys.version_info.major == 2 or (sys.version_info.major == 3 and sys.version_info.minor < 10)


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
        r = requests.get(
            url="https://cdn.statically.io/gh/morpheus65535/bazarr-binaries/refs/heads/master/announcements.json",
            timeout=30
        )
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
    enabled_providers = get_enabled_providers()
    if enabled_providers and 'opensubtitles' in enabled_providers and not settings.opensubtitles.vip:
        announcements.append({
            'text': 'Opensubtitles.org is deprecated for non-VIP users, migrate to Opensubtitles.com ASAP and disable '
                    'this provider to remove this announcement.',
            'link': 'https://wiki.bazarr.media/Troubleshooting/OpenSubtitles-migration/',
            'dismissible': False,
            'timestamp': 1676236978,
        })

    # deprecated Sonarr and Radarr versions
    if get_sonarr_info.is_deprecated():
        announcements.append({
            'text': f'Sonarr {get_sonarr_info.version()} is deprecated and unsupported. You should consider upgrading '
                    f'as Bazarr will eventually drop support for deprecated Sonarr version.',
            'link': 'https://forums.sonarr.tv/t/v3-is-now-officially-stable-v2-is-eol/27858',
            'dismissible': False,
            'timestamp': 1679606061,
        })
    if get_radarr_info.is_deprecated():
        announcements.append({
            'text': f'Radarr {get_radarr_info.version()} is deprecated and unsupported. You should consider upgrading '
                    f'as Bazarr will eventually drop support for deprecated Radarr version.',
            'link': 'https://discord.com/channels/264387956343570434/264388019585286144/1051567458697363547',
            'dismissible': False,
            'timestamp': 1679606309,
        })

    # upcoming deprecated Python versions
    if upcoming_deprecated_python_version():
        announcements.append({
            'text': 'Starting with Bazarr 1.6, support for Python 3.8 and 3.9 will get dropped. Upgrade your current '
                    'version of Python ASAP to get further updates.',
            'link': 'https://wiki.bazarr.media/Troubleshooting/Windows_installer_reinstall/',
            'dismissible': False,
            'timestamp': 1744469706,
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
                     x['enabled'] and (not x['dismissible'] or not
                     database.execute(
                         select(TableAnnouncements)
                         .where(TableAnnouncements.hash ==
                                hashlib.sha256(x['text'].encode('UTF8')).hexdigest()))
                                       .first())]

    return sorted(announcements, key=itemgetter('timestamp'), reverse=True)


def mark_announcement_as_dismissed(hashed_announcement):
    text = [x['text'] for x in get_all_announcements() if x['hash'] == hashed_announcement]
    if text:
        database.execute(
            insert(TableAnnouncements)
            .values(hash=hashed_announcement,
                    timestamp=datetime.now(),
                    text=text[0])
            .on_conflict_do_nothing())

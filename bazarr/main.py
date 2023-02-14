# coding=utf-8

import os

from threading import Thread

bazarr_version = 'unknown'

version_file = os.path.join(os.path.dirname(__file__), '..', 'VERSION')
if os.path.isfile(version_file):
    with open(version_file, 'r') as f:
        bazarr_version = f.readline()
        bazarr_version = bazarr_version.rstrip('\n')

os.environ["BAZARR_VERSION"] = bazarr_version.lstrip('v')

import app.libs  # noqa W0611

from app.get_args import args  # noqa E402
from app.check_update import apply_update, check_releases, check_if_new_update  # noqa E402
from app.config import settings, configure_proxy_func, base_url  # noqa E402
from init import *  # noqa E402

# Install downloaded update
if bazarr_version != '':
    apply_update()

# Check for new update and install latest
if args.no_update or not settings.general.getboolean('auto_update'):
    # user have explicitly requested that we do not update or is using some kind of package/docker that prevent it
    check_releases()
else:
    # we want to update to the latest version before loading too much stuff. This should prevent deadlock when
    # there's missing embedded packages after a commit
    check_if_new_update()

from app.database import System  # noqa E402
from app.notifier import update_notifier  # noqa E402
from languages.get_languages import load_language_in_db  # noqa E402
from app.signalr_client import sonarr_signalr_client, radarr_signalr_client  # noqa E402
from app.server import webserver  # noqa E402
from app.announcements import get_announcements_to_file  # noqa E402

configure_proxy_func()

get_announcements_to_file()

# Reset the updated once Bazarr have been restarted after an update
System.update({System.updated: '0'}).execute()

# Load languages in database
load_language_in_db()

login_auth = settings.auth.type

update_notifier()

if not args.no_signalr:
    if settings.general.getboolean('use_sonarr'):
        Thread(target=sonarr_signalr_client.start).start()
    if settings.general.getboolean('use_radarr'):
        Thread(target=radarr_signalr_client.start).start()


if __name__ == "__main__":
    webserver.start()

# coding=utf-8

import os

from threading import Thread

bazarr_version = 'unknown'

# Try to read version from VERSION file (authoritative for releases)
version_file = os.path.join(os.path.dirname(__file__), '..', 'VERSION')
if os.path.isfile(version_file):
    with open(version_file, 'r') as f:
        bazarr_version = f.readline()
        bazarr_version = bazarr_version.rstrip('\n')

# Fall back to environment variable if VERSION file not found (dev/Docker setups)
if bazarr_version == 'unknown' and "BAZARR_VERSION" in os.environ:
    bazarr_version = os.environ["BAZARR_VERSION"]

os.environ["BAZARR_VERSION"] = bazarr_version.lstrip('v')

import app.libs  # noqa W0611

from app.get_args import args  # noqa E402
from app.check_update import apply_update, check_releases, check_if_new_update  # noqa E402
from app.config import settings, configure_proxy_func, base_url  # noqa E402
from init import *  # noqa E402
import logging  # noqa E402

# Install downloaded update
if bazarr_version != '':
    apply_update()

# Check for new update and install latest
if args.no_update or not settings.general.auto_update:
    # user have explicitly requested that we do not update or is using some kind of package/docker that prevent it
    check_releases(startup=True)
else:
    # we want to update to the latest version before loading too much stuff. This should prevent deadlock when
    # there's missing embedded packages after a commit
    check_if_new_update()

from app.database import (System, database, update, migrate_db, create_db_revision, upgrade_languages_profile_values,
                          fix_languages_profiles_with_duplicate_ids)  # noqa E402
from app.notifier import update_notifier  # noqa E402
from languages.get_languages import load_language_in_db  # noqa E402
from app.jobs_queue import jobs_queue  # noqa E402
from app.signalr_client import sonarr_signalr_client, radarr_signalr_client  # noqa E402
from app.server import webserver, app  # noqa E402
from app.announcements import get_announcements_to_file  # noqa E402
from utilities.central import stop_bazarr  # noqa E402
from literals import EXIT_NORMAL  # noqa E402

if args.create_db_revision:
    create_db_revision(app)
    stop_bazarr(EXIT_NORMAL)
else:
    migrate_db(app)
    upgrade_languages_profile_values()
    fix_languages_profiles_with_duplicate_ids()

configure_proxy_func()

get_announcements_to_file(startup=True)

# Reset the updated once Bazarr have been restarted after an update
database.execute(
    update(System)
    .values(updated='0'))

# Load languages in database
load_language_in_db()

update_notifier()

jobs_queue_thread = Thread(target=jobs_queue.consume_jobs_pending_queue)
jobs_queue_thread.daemon = True
jobs_queue_thread.start()
logging.info("Interactive jobs queue started and waiting for tasks")

if not args.no_signalr:
    if settings.general.use_sonarr:
        sonarr_signalr_thread = Thread(target=sonarr_signalr_client.start)
        sonarr_signalr_thread.daemon = True
        sonarr_signalr_thread.start()
    if settings.general.use_radarr:
        radarr_signalr_thread = Thread(target=radarr_signalr_client.start)
        radarr_signalr_thread.daemon = True
        radarr_signalr_thread.start()


if __name__ == "__main__":
    webserver.start()

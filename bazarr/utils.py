# coding=utf-8

import os
import sqlite3
import time
import platform

from whichcraft import which
from get_args import args


def history_log(action, sonarrSeriesId, sonarrEpisodeId, description, video_path=None, language=None, provider=None,
                score=None, forced=False):
    # Open database connection
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()

    history = c.execute(
        '''INSERT INTO table_history(action, sonarrSeriesId, sonarrEpisodeId, timestamp, description, video_path, language, provider, score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (action, sonarrSeriesId, sonarrEpisodeId, time.time(), description, video_path, language, provider, score))

    # Commit changes to DB
    db.commit()

    # Close database connection
    db.close()


def history_log_movie(action, radarrId, description, video_path=None, language=None, provider=None, score=None,
                      forced=False):
    # Open database connection
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()

    history = c.execute(
        '''INSERT INTO table_history_movie(action, radarrId, timestamp, description, video_path, language, provider, score) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (action, radarrId, time.time(), description, video_path, language, provider, score))

    # Commit changes to DB
    db.commit()

    # Close database connection
    db.close()


def get_binary(name):
    binaries_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'bin'))

    exe = None
    installed_exe = which(name)

    if installed_exe and os.path.isfile(installed_exe):
        return installed_exe
    else:
        if platform.system() == "Windows":  # Windows
            exe = os.path.abspath(os.path.join(binaries_dir, "Windows", "i386", name, "%s.exe" % name))

        elif platform.system() == "Darwin":  # MacOSX
            exe = os.path.abspath(os.path.join(binaries_dir, "MacOSX", "i386", name, name))

        elif platform.system() == "Linux":  # Linux
            exe = os.path.abspath(os.path.join(binaries_dir, "Linux", platform.machine(), name, name))

    if exe and os.path.isfile(exe):
        return exe

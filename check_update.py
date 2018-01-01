from get_general_settings import *

import os
import logging
import sqlite3

import git

current_working_directory = os.path.dirname(__file__)

def check_and_apply_update():
    g = git.cmd.Git(current_working_directory)
    result = g.pull('origin', branch)
    if result.startswith('Already'):
        logging.info('No new version of Bazarr available.')
    elif result.startswith('Updating'):
        logging.info('Bazarr updated to latest version and need to be restarted.')
    else:
        logging.info(result)
        updated()

def updated():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = conn.cursor()
    c.execute("UPDATE table_settings_general SET updated = 1")
    conn.commit()
    c.close()
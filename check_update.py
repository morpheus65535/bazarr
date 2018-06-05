from get_general_settings import *

import os
import logging
import sqlite3

import git

current_working_directory = os.path.dirname(__file__)

def gitconfig():
    g = git.Repo.init(current_working_directory)
    config_read = g.config_reader()
    config_write = g.config_writer()
    
    try:
        username = config_read.get_value("user", "name")
    except:
        config_write.set_value("user", "name", "Bazarr")
    
    try:
        email = config_read.get_value("user", "email")
    except:
        config_write.set_value("user", "email", "bazarr@fake.email")

def check_and_apply_update():
    gitconfig()
    g = git.cmd.Git(current_working_directory)
    result = g.diff('--shortstat', 'origin/' + branch)
    if len(result) == 0:
        logging.info('No new version of Bazarr available.')
    else:
        g.reset('--hard', 'HEAD')
        g.checkout(branch)
        g.reset('--hard','origin/' + branch)
        g.pull('origin/' + branch)
        logging.info('Bazarr updated to latest version and need to be restarted. ' + result)
        updated()

def updated():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = conn.cursor()
    c.execute("UPDATE table_settings_general SET updated = 1")
    conn.commit()
    c.close()
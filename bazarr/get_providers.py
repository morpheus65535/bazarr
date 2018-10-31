# coding=utf-8

import sqlite3
import os
import collections

from subliminal_patch.extensions import provider_registry as provider_manager
from get_args import args


def load_providers():
    # Get providers list from subliminal
    providers_list = sorted(provider_manager.names())

    # Open database connection
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()

    # Remove unsupported providers
    providers_in_db = c.execute('SELECT name FROM table_settings_providers').fetchall()
    for provider_in_db in providers_in_db:
        if provider_in_db[0] not in providers_list:
            c.execute('DELETE FROM table_settings_providers WHERE name = ?', (provider_in_db[0],))

    # Commit changes to database table
    db.commit()

    # Insert providers in database table
    for provider_name in providers_list:
        c.execute('''INSERT OR IGNORE INTO table_settings_providers(name) VALUES(?)''', (provider_name,))

    # Commit changes to database table
    db.commit()

    # Close database connection
    db.close()


def get_providers():
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    enabled_providers = c.execute("SELECT * FROM table_settings_providers WHERE enabled = 1").fetchall()
    c.close()

    providers_list = []
    if len(enabled_providers) > 0:
        for provider in enabled_providers:
            providers_list.append(provider[0])
    else:
        providers_list = None

    return providers_list


def get_providers_auth():
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    enabled_providers = c.execute(
        "SELECT * FROM table_settings_providers WHERE enabled = 1 AND username is not NULL AND password is not NULL").fetchall()
    c.close()

    providers_auth = collections.defaultdict(dict)
    if len(enabled_providers) > 0:
        for provider in enabled_providers:
            providers_auth[provider[0]] = {}
            providers_auth[provider[0]]['username'] = provider[2]
            providers_auth[provider[0]]['password'] = provider[3]
    else:
        providers_auth = None

    return providers_auth

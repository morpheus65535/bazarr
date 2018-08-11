import sqlite3
import os

def get_auth_settings():
    # Open database connection
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()

    c.execute('''SELECT * FROM table_settings_auth''')
    config_auth = c.fetchone()

    # Close database connection
    db.close()

    auth_enabled = config_auth[0]
    auth_username = config_auth[1]
    auth_password = config_auth[2]

    return [auth_enabled, auth_username, auth_password]
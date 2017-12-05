import sqlite3
import os
import ast

# Open database connection
db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
c = db.cursor()

# Get general settings from database table
c.execute("SELECT * FROM table_settings_general")
general_settings = c.fetchone()

# Close database connection
db.close()

ip = general_settings[0]
port = general_settings[1]
base_url = general_settings[2]
if base_url == (''):
    base_url = '/'
if general_settings[3] is None:
   path_mappings = []
else:
   path_mappings = ast.literal_eval(general_settings[3])
log_level = general_settings[4]
branch = general_settings[5]
automatic = general_settings[6]

def path_replace(path):
    for path_mapping in path_mappings:
        if path_mapping[0] in path:
            path = path.replace(path_mapping[0], path_mapping[1])
            if path.startswith('\\\\'):
                path = path.replace('/', '\\')
            elif path.startswith('/'):
                path = path.replace('\\', '/')
            break
    return path

def path_replace_reverse(path):
    for path_mapping in path_mappings:
        if path_mapping[1] in path:
            path = path.replace(path_mapping[1], path_mapping[0])
            if path.startswith('\\\\'):
                path = path.replace('/', '\\')
            elif path.startswith('/'):
                path = path.replace('\\', '/')
            break
    return path

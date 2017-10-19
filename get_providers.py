import sqlite3
from subliminal import *

# Get providers list from subliminal
providers_list = sorted(provider_manager.names())

# Open database connection
db = sqlite3.connect('data/db/bazarr.db')
c = db.cursor()

# Insert providers in database table
for provider_name in providers_list:
    c.execute('''INSERT OR IGNORE INTO table_settings_providers(name) VALUES(?)''', (provider_name, ))

# Commit changes to database table
db.commit()

# Close database connection
db.close()

import sqlite3
import os
from subliminal import provider_manager

# Get providers list from subliminal
providers_list = sorted(provider_manager.names())

# Open database connection
db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
c = db.cursor()

# Remove unsupported providers
providers_in_db = c.execute('SELECT name FROM table_settings_providers').fetchall()
for provider_in_db in providers_in_db:
    if provider_in_db[0] not in providers_list:
        c.execute('DELETE FROM table_settings_providers WHERE name = ?', (provider_in_db[0], ))

# Commit changes to database table
db.commit()

# Insert providers in database table
for provider_name in providers_list:
    c.execute('''INSERT OR IGNORE INTO table_settings_providers(name) VALUES(?)''', (provider_name, ))

# Commit changes to database table
db.commit()

# Close database connection
db.close()

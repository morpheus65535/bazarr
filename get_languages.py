import sqlite3
import pycountry
import os

# Get languages list in langs tuple
langs = [[lang.alpha_3,lang.alpha_2,lang.name]
    for lang in pycountry.languages
    if hasattr(lang, 'alpha_2')]

# Open database connection
db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'))
c = db.cursor()

# Insert languages in database table
c.executemany('''INSERT OR IGNORE INTO table_settings_languages(code3, code2, name) VALUES(?, ?, ?)''', langs)

# Commit changes to database table
db.commit()

# Close database connection
db.close()

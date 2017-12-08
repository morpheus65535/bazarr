import os
import sqlite3

# Check if database exist
if os.path.exists(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db')) == True:
    # Open database connection
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()
    
    # Execute table modification
    try:
        c.execute('alter table table_settings_providers add column "username" "text"')
        c.execute('UPDATE table_settings_providers SET username=""')
    except:
        pass

    try:
        c.execute('alter table table_settings_providers add column "password" "text"')
        c.execute('UPDATE table_settings_providers SET password=""')
    except:
        pass
    
    # Commit change to db
    db.commit()

    # Close database connection
    db.close()

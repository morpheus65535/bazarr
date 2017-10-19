import os.path
import sqlite3

# Check if database exist
if os.path.exists('data/db/bazarr.db') == True:
    pass
else:
    # Get SQL script from file
    fd = open('create_db.sql', 'r')
    script = fd.read()
    
    # Open database connection
    db = sqlite3.connect('data/db/bazarr.db')
    c = db.cursor()
	
    # Execute script and commit change to database
    c.executescript(script)
	
    # Close database connection
    db.close()
	
    # Close SQL script file
    fd.close()

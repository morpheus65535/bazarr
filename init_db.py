# coding: utf-8 
from __future__ import unicode_literals

import os
import sqlite3

# Check if database exist
if os.path.exists(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db')) == True:
    pass
else:
    # Create data directory tree
    try:
        os.mkdir(os.path.join(os.path.dirname(__file__), 'data'))
    except OSError:
        pass

    try:
        os.mkdir(os.path.join(os.path.dirname(__file__), 'data/cache'))
    except OSError:
        pass

    try:
        os.mkdir(os.path.join(os.path.dirname(__file__), 'data/db'))
    except OSError:
        pass

    try:
        os.mkdir(os.path.join(os.path.dirname(__file__), 'data/log'))
    except OSError:
        pass

    # Get SQL script from file
    fd = open(os.path.join(os.path.dirname(__file__), 'create_db.sql'), 'r')
    script = fd.read()
    
    # Open database connection
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'))
    c = db.cursor()
	
    # Execute script and commit change to database
    c.executescript(script)
	
    # Close database connection
    db.close()
	
    # Close SQL script file
    fd.close()

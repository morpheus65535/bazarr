from get_argv import config_dir

import os
import sqlite3
import logging

# Check if config_dir exist
if os.path.exists(config_dir) == True:
    pass
else:
    # Create config_dir directory tree
    try:
        os.mkdir(os.path.join(config_dir))
    except OSError:
        logging.exception("The configuration directory doesn't exist and Bazarr cannot create it (permission issue?).")
        exit(2)

# Check if database exist
if os.path.exists(os.path.join(config_dir, 'db/bazarr.db')) == True:
    pass
else:
    # Create data directory tree
    try:
        os.mkdir(os.path.join(config_dir, 'db'))
    except OSError:
        pass

    try:
        os.mkdir(os.path.join(config_dir, 'log'))
    except OSError:
        pass

    # Get SQL script from file
    fd = open(os.path.join(os.path.dirname(__file__), 'create_db.sql'), 'r')
    script = fd.read()
    
    # Close SQL script file
    fd.close()
    
    # Open database connection
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()
	
    # Execute script and commit change to database
    c.executescript(script)
	
    # Close database connection
    db.close()

    logging.info('Database created successfully')
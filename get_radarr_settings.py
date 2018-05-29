import sqlite3
import os
import ast

def get_radarr_settings():
    # Open database connection
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()

    # Get Radarr API URL from database config table
    c.execute('''SELECT * FROM table_settings_radarr''')
    config_radarr = c.fetchone()

    # Close database connection
    db.close()

    # Build radarr URL
    ip_radarr = config_radarr[0]
    port_radarr = str(config_radarr[1])
    baseurl_radarr = config_radarr[2]
    ssl_radarr = config_radarr[3]
    apikey_radarr = config_radarr[4]
    full_update = config_radarr[5]

    if ssl_radarr == 1:
        protocol_radarr = "https"
    else:
        protocol_radarr = "http"

    if baseurl_radarr == None:
        baseurl_radarr = "/"
    if baseurl_radarr.startswith("/") == False:
        baseurl_radarr = "/" + baseurl_radarr
    if baseurl_radarr.endswith("/"):
        baseurl_radarr = baseurl_radarr[:-1]

    url_radarr = protocol_radarr + "://" + ip_radarr + ":" + port_radarr + baseurl_radarr
    url_radarr_short = protocol_radarr + "://" + ip_radarr + ":" + port_radarr

    return [url_radarr, url_radarr_short, apikey_radarr, full_update]
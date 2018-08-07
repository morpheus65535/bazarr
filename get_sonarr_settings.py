import sqlite3
import os
import ast

def get_sonarr_settings():
    # Open database connection
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()

    # Get Sonarr API URL from database config table
    c.execute('''SELECT * FROM table_settings_sonarr''')
    config_sonarr = c.fetchone()

    # Close database connection
    db.close()

    # Build Sonarr URL
    ip_sonarr = config_sonarr[0]
    port_sonarr = str(config_sonarr[1])
    baseurl_sonarr = config_sonarr[2]
    ssl_sonarr = config_sonarr[3]
    apikey_sonarr = config_sonarr[4]
    full_update = config_sonarr[5]
    monitored_sonarr = config_sonarr[6]

    if ssl_sonarr == 1:
        protocol_sonarr = "https"
    else:
        protocol_sonarr = "http"

    if baseurl_sonarr == None:
        baseurl_sonarr = "/"
    if baseurl_sonarr.startswith("/") == False:
        baseurl_sonarr = "/" + baseurl_sonarr
    if baseurl_sonarr.endswith("/"):
        baseurl_sonarr = baseurl_sonarr[:-1]

    url_sonarr = protocol_sonarr + "://" + ip_sonarr + ":" + port_sonarr + baseurl_sonarr
    url_sonarr_short = protocol_sonarr + "://" + ip_sonarr + ":" + port_sonarr

    return [url_sonarr, url_sonarr_short, apikey_sonarr, full_update, monitored_sonarr]
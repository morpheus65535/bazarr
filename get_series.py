import os
import sqlite3
import requests

from get_general_settings import *
from get_sonarr_settings import *

def update_series():
    # Open database connection
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()

    if apikey_sonarr == None:
        pass
    else:
        # Get shows data from Sonarr
        url_sonarr_api_series = url_sonarr + "/api/series?apikey=" + apikey_sonarr
        r = requests.get(url_sonarr_api_series)
        shows_list = []

        # Get current shows in DB
        current_shows_db = c.execute('SELECT tvdbId FROM table_shows').fetchall()
        current_shows_db_list = [x[0] for x in current_shows_db]
        current_shows_sonarr = []

        # Parsing data returned from Sonarr
        for show in r.json():
            try:
                overview = unicode(show['overview'])
            except:
                overview = ""
            try:
                poster_big = show['images'][2]['url'].split('?')[0]
                poster = os.path.splitext(poster_big)[0] + '-250' + os.path.splitext(poster_big)[1]
            except:
                poster = ""
            try:
                fanart = show['images'][0]['url'].split('?')[0]
            except:
                fanart = ""
            
            # Add shows in Sonarr to current shows list
            current_shows_sonarr.append(show['tvdbId'])

            # Update or insert shows list in database table
            result = c.execute('''UPDATE table_shows SET title = ?, path = ?, tvdbId = ?, sonarrSeriesId = ?, overview = ?, poster = ?, fanart = ? WHERE tvdbid = ?''', (show["title"],show["path"],show["tvdbId"],show["id"],overview,poster,fanart,show["tvdbId"]))
            if result.rowcount == 0:
                c.execute('''INSERT INTO table_shows(title, path, tvdbId, languages,`hearing_impaired`, sonarrSeriesId, overview, poster, fanart) VALUES (?,?,?,(SELECT languages FROM table_shows WHERE tvdbId = ?),(SELECT `hearing_impaired` FROM table_shows WHERE tvdbId = ?), ?, ?, ?, ?)''', (show["title"],show["path"],show["tvdbId"],show["tvdbId"],show["tvdbId"],show["id"],overview,poster,fanart))

        # Delete shows not in Sonarr anymore
        deleted_items = []
        for item in current_shows_db_list:
            if item not in current_shows_sonarr:
                deleted_items.append(tuple([item]))
        c.executemany('DELETE FROM table_shows WHERE tvdbId = ?',deleted_items)

        # Commit changes to database table
        db.commit()

    # Close database connection
    db.close()

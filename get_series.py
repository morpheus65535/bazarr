import os
import sqlite3
import requests

from get_sonarr_settings import *

# Open database connection
db = sqlite3.connect('bazarr.db')
c = db.cursor()

# Get shows data from Sonarr
url_sonarr_api_series = url_sonarr + "/api/series?apikey=" + apikey_sonarr

r = requests.get(url_sonarr_api_series)
shows_list = []
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
    # Update or insert shows list in database table
    try:
        c.execute('''UPDATE table_shows SET title = ?, path = ?, tvdbId = ?, sonarrSeriesId = ?, overview = ?, poster = ?, fanart = ? WHERE tvdbid = ?''', (show["title"],show["path"],show["tvdbId"],show["id"],overview,poster,fanart,show["tvdbId"]))
    except:
        print show["title"]
        c.execute('''INSERT INTO table_shows(title, path, tvdbId, languages,`hearing_impaired`, sonarrSeriesId, overview, poster, fanart) VALUES (?,?,?,(SELECT languages FROM table_shows WHERE tvdbId = ?),(SELECT `hearing_impaired` FROM table_shows WHERE tvdbId = ?), ?, ?, ?, ?)''', (show["title"],show["path"],show["tvdbId"],show["tvdbId"],show["tvdbId"],show["id"],overview,poster,fanart))

# Commit changes to database table
db.commit()

# Close database connection
db.close()

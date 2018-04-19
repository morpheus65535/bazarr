import os
import sqlite3
import requests

from get_general_settings import *

def update_movies():
    from get_radarr_settings import get_radarr_settings
    url_radarr = get_radarr_settings()[0]
    url_radarr_short = get_radarr_settings()[1]
    apikey_radarr = get_radarr_settings()[2]

    # Open database connection
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()

    if apikey_radarr == None:
        pass
    else:
        get_profile_list()

        # Get movies data from radarr
        url_radarr_api_movies = url_radarr + "/api/movie?apikey=" + apikey_radarr
        r = requests.get(url_radarr_api_movies)

        # Get current movies in DB
        current_movies_db = c.execute('SELECT tmdbId FROM table_movies').fetchall()
        current_movies_db_list = [x[0] for x in current_movies_db]
        current_movies_radarr = []

        for movie in r.json():
            if movie['hasFile'] is True:
                try:
                    overview = unicode(movie['overview'])
                except:
                    overview = ""
                try:
                    poster_big = movie['images'][0]['url']
                    poster = os.path.splitext(poster_big)[0] + '-250' + os.path.splitext(poster_big)[1]
                except:
                    poster = ""
                try:
                    fanart = movie['images'][1]['url']
                except:
                    fanart = ""

                # Add movies in radarr to current movies list
                current_movies_radarr.append(unicode(movie['tmdbId']))

                # Update or insert movies list in database table
                try:
                    c.execute('''INSERT INTO table_movies(title, path, tmdbId, languages,`hearing_impaired`, radarrId, overview, poster, fanart, `audio_language`) VALUES (?,?,?,(SELECT languages FROM table_movies WHERE tmdbId = ?),(SELECT `hearing_impaired` FROM table_movies WHERE tmdbId = ?), ?, ?, ?, ?, ?)''', (movie["title"], os.path.join(movie["path"], movie['movieFile']['relativePath']), movie["tmdbId"], movie["tmdbId"], movie["tmdbId"], movie["id"], overview, poster, fanart, profile_id_to_language(movie['qualityProfileId'])))
                except:
                    c.execute('''UPDATE table_movies SET title = ?, path = ?, tmdbId = ?, radarrId = ?, overview = ?, poster = ?, fanart = ?, `audio_language` = ? WHERE tmdbid = ?''', (movie["title"],os.path.join(movie["path"], movie['movieFile']['relativePath']),movie["tmdbId"],movie["id"],overview,poster,fanart,profile_id_to_language(movie['qualityProfileId']),movie["tmdbId"]))

        # Delete movies not in radarr anymore
        deleted_items = []
        for item in current_movies_db_list:
            if item not in current_movies_radarr:
                deleted_items.append(tuple([item]))
        c.executemany('DELETE FROM table_movies WHERE tmdbId = ?',deleted_items)

        # Commit changes to database table
        db.commit()

    # Close database connection
    db.close()

def get_profile_list():
    from get_radarr_settings import get_radarr_settings
    url_radarr = get_radarr_settings()[0]
    url_radarr_short = get_radarr_settings()[1]
    apikey_radarr = get_radarr_settings()[2]

    # Get profiles data from radarr
    url_radarr_api_movies = url_radarr + "/api/profile?apikey=" + apikey_radarr
    profiles_json = requests.get(url_radarr_api_movies)
    global profiles_list
    profiles_list = []

    # Parsing data returned from radarr
    for profile in profiles_json.json():
        profiles_list.append([profile['id'], profile['language'].capitalize()])

def profile_id_to_language(id):
    for profile in profiles_list:
        if id == profile[0]:
            return profile[1]

if __name__ == '__main__':
    update_movies()
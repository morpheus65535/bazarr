from get_argv import config_dir

import os
import sqlite3
import requests
import logging

from get_settings import get_general_settings, path_replace_movie
from list_subtitles import store_subtitles_movie, list_missing_subtitles_movies

def update_movies():
    logging.debug('BAZARR Starting movie sync from Radarr.')
    from get_settings import get_radarr_settings
    url_radarr = get_radarr_settings()[6]
    apikey_radarr = get_radarr_settings()[4]
    movie_default_enabled = get_general_settings()[18]
    movie_default_language = get_general_settings()[19]
    movie_default_hi = get_general_settings()[20]

    if apikey_radarr == None:
        pass
    else:
        get_profile_list()

        # Get movies data from radarr
        url_radarr_api_movies = url_radarr + "/api/movie?apikey=" + apikey_radarr
        try:
            r = requests.get(url_radarr_api_movies, timeout=15, verify=False)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logging.exception("BAZARR Error trying to get movies from Radarr. Http error.")
        except requests.exceptions.ConnectionError as errc:
            logging.exception("BAZARR Error trying to get movies from Radarr. Connection Error.")
        except requests.exceptions.Timeout as errt:
            logging.exception("BAZARR Error trying to get movies from Radarr. Timeout Error.")
        except requests.exceptions.RequestException as err:
            logging.exception("BAZARR Error trying to get movies from Radarr.")
        else:
            # Get current movies in DB
            db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
            c = db.cursor()
            current_movies_db = c.execute('SELECT tmdbId FROM table_movies').fetchall()
            db.close()

            current_movies_db_list = [x[0] for x in current_movies_db]
            current_movies_radarr = []
            movies_to_update = []
            movies_to_add = []

            for movie in r.json():
                if movie['hasFile'] is True:
                    if 'movieFile' in movie:
                        try:
                            overview = unicode(movie['overview'])
                        except:
                            overview = ""
                        try:
                            poster_big = movie['images'][0]['url']
                            poster = os.path.splitext(poster_big)[0] + '-500' + os.path.splitext(poster_big)[1]
                        except:
                            poster = ""
                        try:
                            fanart = movie['images'][1]['url']
                        except:
                            fanart = ""

                        if 'sceneName' in movie['movieFile']:
                            sceneName = movie['movieFile']['sceneName']
                        else:
                            sceneName = None

                        # Add movies in radarr to current movies list
                        current_movies_radarr.append(unicode(movie['tmdbId']))

                        # Detect file separator
                        if movie['path'][0] == "/":
                            separator = "/"
                        else:
                            separator = "\\"

                        if unicode(movie['tmdbId']) in current_movies_db_list:
                            movies_to_update.append((movie["title"],movie["path"] + separator + movie['movieFile']['relativePath'],movie["tmdbId"],movie["id"],overview,poster,fanart,profile_id_to_language(movie['qualityProfileId']),sceneName,unicode(bool(movie['monitored'])),movie["tmdbId"]))
                        else:
                            if movie_default_enabled is True:
                                movies_to_add.append((movie["title"], movie["path"] + separator + movie['movieFile']['relativePath'], movie["tmdbId"], movie_default_language, '[]', movie_default_hi, movie["id"], overview, poster, fanart, profile_id_to_language(movie['qualityProfileId']), sceneName, unicode(bool(movie['monitored']))))
                            else:
                                movies_to_add.append((movie["title"], movie["path"] + separator + movie['movieFile']['relativePath'], movie["tmdbId"], movie["tmdbId"], movie["tmdbId"], movie["id"], overview, poster, fanart, profile_id_to_language(movie['qualityProfileId']), sceneName, unicode(bool(movie['monitored']))))

            # Update or insert movies in DB
            db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
            c = db.cursor()

            updated_result = c.executemany('''UPDATE table_movies SET title = ?, path = ?, tmdbId = ?, radarrId = ?, overview = ?, poster = ?, fanart = ?, `audio_language` = ?, sceneName = ?, monitored = ? WHERE tmdbid = ?''', movies_to_update)
            db.commit()

            if movie_default_enabled is True:
                added_result = c.executemany('''INSERT OR IGNORE INTO table_movies(title, path, tmdbId, languages, subtitles,`hearing_impaired`, radarrId, overview, poster, fanart, `audio_language`, sceneName, monitored) VALUES (?,?,?,?,?, ?, ?, ?, ?, ?, ?, ?, ?)''', movies_to_add)
                db.commit()
            else:
                added_result = c.executemany('''INSERT OR IGNORE INTO table_movies(title, path, tmdbId, languages, subtitles,`hearing_impaired`, radarrId, overview, poster, fanart, `audio_language`, sceneName, monitored) VALUES (?,?,?,(SELECT languages FROM table_movies WHERE tmdbId = ?), '[]',(SELECT `hearing_impaired` FROM table_movies WHERE tmdbId = ?), ?, ?, ?, ?, ?, ?, ?)''', movies_to_add)
                db.commit()
            db.close()

            added_movies = list(set(current_movies_radarr) - set(current_movies_db_list))
            removed_movies = list(set(current_movies_db_list) - set(current_movies_radarr))

            db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
            c = db.cursor()
            for removed_movie in removed_movies:
                c.execute('DELETE FROM table_movies WHERE tmdbId = ?', (removed_movie,))
            db.commit()
            db.close()

            db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
            c = db.cursor()
            for added_movie in added_movies:
                added_path = c.execute('SELECT path FROM table_movies WHERE tmdbId = ?', (added_movie,)).fetchone()
                store_subtitles_movie(path_replace_movie(added_path[0]))
            db.close()

    logging.debug('BAZARR All movies synced from Radarr into database.')

    list_missing_subtitles_movies()
    logging.debug('BAZARR All movie missing subtitles updated in database.')

def get_profile_list():
    from get_settings import get_radarr_settings
    url_radarr = get_radarr_settings()[6]
    # url_radarr_short = get_radarr_settings()[7]
    apikey_radarr = get_radarr_settings()[4]

    # Get profiles data from radarr
    global profiles_list
    profiles_list = []

    url_radarr_api_movies = url_radarr + "/api/profile?apikey=" + apikey_radarr
    try:
        profiles_json = requests.get(url_radarr_api_movies, timeout=15, verify=False)
    except requests.exceptions.ConnectionError as errc:
        logging.exception("BAZARR Error trying to get profiles from Radarr. Connection Error.")
    except requests.exceptions.Timeout as errt:
        logging.exception("BAZARR Error trying to get profiles from Radarr. Timeout Error.")
    except requests.exceptions.RequestException as err:
        logging.exception("BAZARR Error trying to get profiles from Radarr.")
    else:
        # Parsing data returned from radarr
        for profile in profiles_json.json():
            profiles_list.append([profile['id'], profile['language'].capitalize()])

def profile_id_to_language(id):
    for profile in profiles_list:
        if id == profile[0]:
            return profile[1]

if __name__ == '__main__':
    update_movies()

import os
import sqlite3
import requests
import logging

from get_general_settings import *
from list_subtitles import *

def update_series():
    from get_sonarr_settings import get_sonarr_settings
    url_sonarr = get_sonarr_settings()[0]
    url_sonarr_short = get_sonarr_settings()[1]
    apikey_sonarr = get_sonarr_settings()[2]
    monitored_sonarr = get_sonarr_settings()[4]
    serie_default_enabled = get_general_settings()[15]
    serie_default_language = get_general_settings()[16]
    serie_default_hi = get_general_settings()[17]

    # Open database connection
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()

    if apikey_sonarr == None:
        pass
    else:
        get_profile_list()
    
        # Get shows data from Sonarr
        url_sonarr_api_series = url_sonarr + "/api/series?apikey=" + apikey_sonarr
        try:
            r = requests.get(url_sonarr_api_series, timeout=15)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logging.exception("Error trying to get series from Sonarr. Http error.")
        except requests.exceptions.ConnectionError as errc:
            logging.exception("Error trying to get series from Sonarr. Connection Error.")
        except requests.exceptions.Timeout as errt:
            logging.exception("Error trying to get series from Sonarr. Timeout Error.")
        except requests.exceptions.RequestException as err:
            logging.exception("Error trying to get series from Sonarr.")
        else:
            # Get current shows in DB
            current_shows_db = c.execute('SELECT tvdbId FROM table_shows').fetchall()
            current_shows_db_list = [x[0] for x in current_shows_db]
            current_shows_sonarr = []

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
                try:
                    if serie_default_enabled == 'True':
                        c.execute('''INSERT INTO table_shows(title, path, tvdbId, languages,`hearing_impaired`, sonarrSeriesId, overview, poster, fanart, `audio_language`, sortTitle) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (show["title"], show["path"], show["tvdbId"], serie_default_language, serie_default_hi, show["id"], overview, poster, fanart, profile_id_to_language(show['qualityProfileId']), show['sortTitle']))
                        list_missing_subtitles(show["id"])
                    else:
                        c.execute('''INSERT INTO table_shows(title, path, tvdbId, languages,`hearing_impaired`, sonarrSeriesId, overview, poster, fanart, `audio_language`, sortTitle) VALUES (?,?,?,(SELECT languages FROM table_shows WHERE tvdbId = ?),(SELECT `hearing_impaired` FROM table_shows WHERE tvdbId = ?), ?, ?, ?, ?, ?, ?)''', (show["title"], show["path"], show["tvdbId"], show["tvdbId"], show["tvdbId"], show["id"], overview, poster, fanart, profile_id_to_language(show['qualityProfileId']), show['sortTitle']))
                except:
                    c.execute('''UPDATE table_shows SET title = ?, path = ?, tvdbId = ?, sonarrSeriesId = ?, overview = ?, poster = ?, fanart = ?, `audio_language` = ? , sortTitle = ? WHERE tvdbid = ?''', (show["title"],show["path"],show["tvdbId"],show["id"],overview,poster,fanart,profile_id_to_language((show['qualityProfileId'] if sonarr_version == 2 else show['languageProfileId'])),show['sortTitle'],show["tvdbId"]))

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

def get_profile_list():
    from get_sonarr_settings import get_sonarr_settings
    url_sonarr = get_sonarr_settings()[0]
    url_sonarr_short = get_sonarr_settings()[1]
    apikey_sonarr = get_sonarr_settings()[2]

    # Get profiles data from Sonarr
    error = False

    url_sonarr_api_series = url_sonarr + "/api/profile?apikey=" + apikey_sonarr
    try:
        profiles_json = requests.get(url_sonarr_api_series, timeout=15)
    except requests.exceptions.ConnectionError as errc:
        error = True
        logging.exception("Error trying to get profiles from Sonarr. Connection Error.")
    except requests.exceptions.Timeout as errt:
        error = True
        logging.exception("Error trying to get profiles from Sonarr. Timeout Error.")
    except requests.exceptions.RequestException as err:
        error = True
        logging.exception("Error trying to get profiles from Sonarr.")

    url_sonarr_api_series_v3 = url_sonarr + "/api/v3/languageprofile?apikey=" + apikey_sonarr
    try:
        profiles_json_v3 = requests.get(url_sonarr_api_series_v3, timeout=15)
    except requests.exceptions.ConnectionError as errc:
        error = True
        logging.exception("Error trying to get profiles from Sonarr. Connection Error.")
    except requests.exceptions.Timeout as errt:
        error = True
        logging.exception("Error trying to get profiles from Sonarr. Timeout Error.")
    except requests.exceptions.RequestException as err:
        error = True
        logging.exception("Error trying to get profiles from Sonarr.")

    global profiles_list
    profiles_list = []

    if error is False:
        # Parsing data returned from Sonarr
        global sonarr_version
        if type(profiles_json_v3.json()) != list:
            sonarr_version = 2
            for profile in profiles_json.json():
                profiles_list.append([profile['id'], profile['language'].capitalize()])
        else:
            sonarr_version = 3
            for profile in profiles_json_v3.json():
                profiles_list.append([profile['id'], profile['name'].capitalize()])

def profile_id_to_language(id):
    for profile in profiles_list:
        if id == profile[0]:
            return profile[1]

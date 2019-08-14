# coding=utf-8

import os
import sqlite3
import requests
import logging
from queueconfig import notifications
import datetime

from get_args import args
from config import settings, url_sonarr
from list_subtitles import list_missing_subtitles
from database import TableShows


def update_series():
    notifications.write(msg="Update series list from Sonarr is running...", queue='get_series')
    apikey_sonarr = settings.sonarr.apikey
    serie_default_enabled = settings.general.getboolean('serie_default_enabled')
    serie_default_language = settings.general.serie_default_language
    serie_default_hi = settings.general.serie_default_hi
    serie_default_forced = settings.general.serie_default_forced
    
    if apikey_sonarr is None:
        pass
    else:
        get_profile_list()
        
        # Get shows data from Sonarr
        url_sonarr_api_series = url_sonarr + "/api/series?apikey=" + apikey_sonarr
        try:
            r = requests.get(url_sonarr_api_series, timeout=60, verify=False)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logging.exception("BAZARR Error trying to get series from Sonarr. Http error.")
        except requests.exceptions.ConnectionError as errc:
            logging.exception("BAZARR Error trying to get series from Sonarr. Connection Error.")
        except requests.exceptions.Timeout as errt:
            logging.exception("BAZARR Error trying to get series from Sonarr. Timeout Error.")
        except requests.exceptions.RequestException as err:
            logging.exception("BAZARR Error trying to get series from Sonarr.")
        else:
            # Get current shows in DB
            current_shows_db = TableShows.select(
                TableShows.tvdb_id
            )
            
            current_shows_db_list = [x.tvdb_id for x in current_shows_db]
            current_shows_sonarr = []
            series_to_update = []
            series_to_add = []

            seriesListLength = len(r.json())
            for i, show in enumerate(r.json(), 1):
                notifications.write(msg="Getting series data from Sonarr...", queue='get_series', item=i, length=seriesListLength)
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

                if show['alternateTitles'] != None:
                    alternateTitles = str([item['title'] for item in show['alternateTitles']])
                else:
                    alternateTitles = None

                # Add shows in Sonarr to current shows list
                current_shows_sonarr.append(show['tvdbId'])
                
                if show['tvdbId'] in current_shows_db_list:
                    series_to_update.append({'title': show["title"],
                                             'path': show["path"],
                                             'tvdb_id': show["tvdbId"],
                                             'sonarr_series_id': show["id"],
                                             'overview': overview,
                                             'poster': poster,
                                             'fanart': fanart,
                                             'audio_language': profile_id_to_language((show['qualityProfileId'] if sonarr_version == 2 else show['languageProfileId'])),
                                             'sort_title': show['sortTitle'],
                                             'year': show['year'],
                                             'alternate_titles': alternateTitles})
                else:
                    if serie_default_enabled is True:
                        series_to_add.append({'title': show["title"],
                                              'path': show["path"],
                                              'tvdb_id': show["tvdbId"],
                                              'languages': serie_default_language,
                                              'hearing_impaired': serie_default_hi,
                                              'sonarr_series_id': show["id"],
                                              'overview': overview,
                                              'poster': poster,
                                              'fanart': fanart,
                                              'audio_language': profile_id_to_language(show['qualityProfileId']),
                                              'sort_title': show['sortTitle'],
                                              'year': show['year'],
                                              'alternate_titles': alternateTitles,
                                              'forced': serie_default_forced})
                    else:
                        series_to_add.append({'title': show["title"],
                                              'path': show["path"],
                                              'tvdb_id': show["tvdbId"],
                                              'sonarr_series_id': show["id"],
                                              'overview': overview,
                                              'poster': poster,
                                              'fanart': fanart,
                                              'audio_language': profile_id_to_language(show['qualityProfileId']),
                                              'sort_title': show['sortTitle'],
                                              'year': show['year'],
                                              'alternate_title': alternateTitles})
            
            # Update or insert series in DB
            db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
            c = db.cursor()
            
            updated_result = c.executemany(
                '''UPDATE table_shows SET title = ?, path = ?, tvdbId = ?, sonarrSeriesId = ?, overview = ?, poster = ?, fanart = ?, `audio_language` = ? , sortTitle = ?, year = ?, alternateTitles = ? WHERE tvdbid = ?''',
                series_to_update)
            db.commit()
            
            if serie_default_enabled is True:
                added_result = c.executemany(
                    '''INSERT OR IGNORE INTO table_shows(title, path, tvdbId, languages,`hearing_impaired`, sonarrSeriesId, overview, poster, fanart, `audio_language`, sortTitle, year, alternateTitles, forced) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    series_to_add)
                db.commit()
            else:
                added_result = c.executemany(
                    '''INSERT OR IGNORE INTO table_shows(title, path, tvdbId, languages,`hearing_impaired`, sonarrSeriesId, overview, poster, fanart, `audio_language`, sortTitle, year, alternateTitles, forced) VALUES (?,?,?,(SELECT languages FROM table_shows WHERE tvdbId = ?),(SELECT `hearing_impaired` FROM table_shows WHERE tvdbId = ?), ?, ?, ?, ?, ?, ?, ?, ?, (SELECT `forced` FROM table_shows WHERE tvdbId = ?))''',
                    series_to_add)
                db.commit()
            db.close()
            
            for show in series_to_add:
                list_missing_subtitles(show[5])
            
            # Delete shows not in Sonarr anymore
            deleted_items = []
            for item in current_shows_db_list:
                if item not in current_shows_sonarr:
                    deleted_items.append(tuple([item]))
            db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
            c = db.cursor()
            c.executemany('DELETE FROM table_shows WHERE tvdbId = ?', deleted_items)
            db.commit()
            db.close()


def get_profile_list():
    apikey_sonarr = settings.sonarr.apikey
    
    # Get profiles data from Sonarr
    error = False
    
    url_sonarr_api_series = url_sonarr + "/api/profile?apikey=" + apikey_sonarr
    try:
        profiles_json = requests.get(url_sonarr_api_series, timeout=60, verify=False)
    except requests.exceptions.ConnectionError as errc:
        error = True
        logging.exception("BAZARR Error trying to get profiles from Sonarr. Connection Error.")
    except requests.exceptions.Timeout as errt:
        error = True
        logging.exception("BAZARR Error trying to get profiles from Sonarr. Timeout Error.")
    except requests.exceptions.RequestException as err:
        error = True
        logging.exception("BAZARR Error trying to get profiles from Sonarr.")
    
    url_sonarr_api_series_v3 = url_sonarr + "/api/v3/languageprofile?apikey=" + apikey_sonarr
    try:
        profiles_json_v3 = requests.get(url_sonarr_api_series_v3, timeout=60, verify=False)
    except requests.exceptions.ConnectionError as errc:
        error = True
        logging.exception("BAZARR Error trying to get profiles from Sonarr. Connection Error.")
    except requests.exceptions.Timeout as errt:
        error = True
        logging.exception("BAZARR Error trying to get profiles from Sonarr. Timeout Error.")
    except requests.exceptions.RequestException as err:
        error = True
        logging.exception("BAZARR Error trying to get profiles from Sonarr.")
    
    global profiles_list
    profiles_list = []
    
    if not error:
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

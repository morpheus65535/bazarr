# coding=utf-8

from __future__ import absolute_import
from __future__ import print_function
import os
import requests
import logging
from queueconfig import notifications

from config import settings, url_sonarr
from list_subtitles import list_missing_subtitles
from database import database, dict_converter
from utils import get_sonarr_version
from helper import path_replace


def update_series():
    notifications.write(msg="Update series list from Sonarr is running...", queue='get_series')
    apikey_sonarr = settings.sonarr.apikey
    if apikey_sonarr is None:
        return

    sonarr_version = get_sonarr_version()
    serie_default_enabled = settings.general.getboolean('serie_default_enabled')
    serie_default_language = settings.general.serie_default_language
    serie_default_hi = settings.general.serie_default_hi
    serie_default_forced = settings.general.serie_default_forced
    audio_profiles = get_profile_list()

    # Get shows data from Sonarr
    url_sonarr_api_series = url_sonarr() + "/api/series?apikey=" + apikey_sonarr
    try:
        r = requests.get(url_sonarr_api_series, timeout=60, verify=False)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        logging.exception("BAZARR Error trying to get series from Sonarr. Http error.")
        return
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get series from Sonarr. Connection Error.")
        return
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get series from Sonarr. Timeout Error.")
        return
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get series from Sonarr.")
        return

    # Get current shows in DB
    current_shows_db = database.execute("SELECT sonarrSeriesId FROM table_shows")

    current_shows_db_list = [x['sonarrSeriesId'] for x in current_shows_db]
    current_shows_sonarr = []
    series_to_update = []
    series_to_add = []

    series_list_length = len(r.json())
    for i, show in enumerate(r.json(), 1):
        notifications.write(msg="Getting series data from Sonarr...", queue='get_series', item=i,
                            length=series_list_length)

        overview = show['overview'] if 'overview' in show else ''
        poster = ''
        fanart = ''
        for image in show['images']:
            if image['coverType'] == 'poster':
                poster_big = image['url'].split('?')[0]
                poster = os.path.splitext(poster_big)[0] + '-250' + os.path.splitext(poster_big)[1]

            if image['coverType'] == 'fanart':
                fanart = image['url'].split('?')[0]

        alternate_titles = None
        if show['alternateTitles'] is not None:
            alternate_titles = str([item['title'] for item in show['alternateTitles']])

        if sonarr_version.startswith('2'):
            audio_language = profile_id_to_language(show['qualityProfileId'], audio_profiles)
        else:
            audio_language = profile_id_to_language(show['languageProfileId'], audio_profiles)

        # Add shows in Sonarr to current shows list
        current_shows_sonarr.append(show['id'])

        if show['id'] in current_shows_db_list:
            series_to_update.append({'title': show["title"],
                                     'path': show["path"],
                                     'tvdbId': int(show["tvdbId"]),
                                     'sonarrSeriesId': int(show["id"]),
                                     'overview': overview,
                                     'poster': poster,
                                     'fanart': fanart,
                                     'audio_language': audio_language,
                                     'sortTitle': show['sortTitle'],
                                     'year': show['year'],
                                     'alternateTitles': alternate_titles})
        else:
            if serie_default_enabled is True:
                series_to_add.append({'title': show["title"],
                                      'path': show["path"],
                                      'tvdbId': show["tvdbId"],
                                      'languages': serie_default_language,
                                      'hearing_impaired': serie_default_hi,
                                      'sonarrSeriesId': show["id"],
                                      'overview': overview,
                                      'poster': poster,
                                      'fanart': fanart,
                                      'audio_language': audio_language,
                                      'sortTitle': show['sortTitle'],
                                      'year': show['year'],
                                      'alternateTitles': alternate_titles,
                                      'forced': serie_default_forced})
            else:
                series_to_add.append({'title': show["title"],
                                      'path': show["path"],
                                      'tvdbId': show["tvdbId"],
                                      'sonarrSeriesId': show["id"],
                                      'overview': overview,
                                      'poster': poster,
                                      'fanart': fanart,
                                      'audio_language': audio_language,
                                      'sortTitle': show['sortTitle'],
                                      'year': show['year'],
                                      'alternateTitles': alternate_titles})

    # Remove old series from DB
    removed_series = list(set(current_shows_db_list) - set(current_shows_sonarr))

    for series in removed_series:
        database.execute("DELETE FROM table_shows WHERE sonarrSEriesId=?", (series,))

    # Update existing series in DB
    series_in_db_list = []
    series_in_db = database.execute("SELECT title, path, tvdbId, sonarrSeriesId, overview, poster, fanart, "
                                    "audio_language, sortTitle, year, alternateTitles FROM table_shows")

    for item in series_in_db:
        series_in_db_list.append(item)

    series_to_update_list = [i for i in series_to_update if i not in series_in_db_list]

    for updated_series in series_to_update_list:
        query = dict_converter.convert(updated_series)
        database.execute('''UPDATE table_shows SET ''' + query.keys_update + ''' WHERE sonarrSeriesId = ?''',
                         query.values + (updated_series['sonarrSeriesId'],))

    # Insert new series in DB
    for added_series in series_to_add:
        query = dict_converter.convert(added_series)
        result = database.execute(
            '''INSERT OR IGNORE INTO table_shows(''' + query.keys_insert + ''') VALUES(''' +
            query.question_marks + ''')''', query.values)
        if result:
            list_missing_subtitles(no=added_series['sonarrSeriesId'])
        else:
            logging.debug('BAZARR unable to insert this series into the database:',
                          path_replace(added_series['path']))

    logging.debug('BAZARR All series synced from Sonarr into database.')


def get_profile_list():
    apikey_sonarr = settings.sonarr.apikey
    sonarr_version = get_sonarr_version()
    profiles_list = []

    # Get profiles data from Sonarr
    if sonarr_version.startswith('2'):
        url_sonarr_api_series = url_sonarr() + "/api/profile?apikey=" + apikey_sonarr
    else:
        url_sonarr_api_series = url_sonarr() + "/api/v3/languageprofile?apikey=" + apikey_sonarr

    try:
        profiles_json = requests.get(url_sonarr_api_series, timeout=60, verify=False)
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get profiles from Sonarr. Connection Error.")
        return None
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get profiles from Sonarr. Timeout Error.")
        return None
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get profiles from Sonarr.")
        return None

    # Parsing data returned from Sonarr
    if sonarr_version.startswith('2'):
        for profile in profiles_json.json():
            profiles_list.append([profile['id'], profile['language'].capitalize()])
    else:
        for profile in profiles_json.json():
            profiles_list.append([profile['id'], profile['name'].capitalize()])

    return profiles_list


def profile_id_to_language(id_, profiles):
    for profile in profiles:
        if id_ == profile[0]:
            return profile[1]

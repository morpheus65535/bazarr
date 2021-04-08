# coding=utf-8

import os
import requests
import logging

from config import settings, url_sonarr
from list_subtitles import list_missing_subtitles
from database import database, dict_converter
from utils import get_sonarr_version
from helper import path_mappings
from event_handler import event_stream

headers = {"User-Agent": os.environ["SZ_USER_AGENT"]}


def update_series():
    apikey_sonarr = settings.sonarr.apikey
    if apikey_sonarr is None:
        return

    sonarr_version = get_sonarr_version()
    serie_default_enabled = settings.general.getboolean('serie_default_enabled')

    if serie_default_enabled is True:
        serie_default_profile = settings.general.serie_default_profile
        if serie_default_profile == '':
            serie_default_profile = None
    else:
        serie_default_profile = None

    audio_profiles = get_profile_list()
    tagsDict = get_tags()

    # Get shows data from Sonarr
    url_sonarr_api_series = url_sonarr() + "/api/series?apikey=" + apikey_sonarr
    try:
        r = requests.get(url_sonarr_api_series, timeout=60, verify=False, headers=headers)
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
        # Add shows in Sonarr to current shows list
        current_shows_sonarr.append(show['id'])

        if show['id'] in current_shows_db_list:
            series_to_update.append(seriesParser(show, action='update', sonarr_version=sonarr_version,
                                                 tags_dict=tagsDict, serie_default_profile=serie_default_profile,
                                                 audio_profiles=audio_profiles))
        else:
            series_to_add.append(seriesParser(show, action='insert', sonarr_version=sonarr_version,
                                              tags_dict=tagsDict, serie_default_profile=serie_default_profile,
                                              audio_profiles=audio_profiles))

    # Remove old series from DB
    removed_series = list(set(current_shows_db_list) - set(current_shows_sonarr))

    for series in removed_series:
        database.execute("DELETE FROM table_shows WHERE sonarrSeriesId=?",(series,))
        event_stream(type='series', action='delete', id=series)

    # Update existing series in DB
    series_in_db_list = []
    series_in_db = database.execute("SELECT title, path, tvdbId, sonarrSeriesId, overview, poster, fanart, "
                                    "audio_language, sortTitle, year, alternateTitles, tags, seriesType, imdbId FROM "
                                    "table_shows")

    for item in series_in_db:
        series_in_db_list.append(item)

    series_to_update_list = [i for i in series_to_update if i not in series_in_db_list]

    for updated_series in series_to_update_list:
        query = dict_converter.convert(updated_series)
        database.execute('''UPDATE table_shows SET ''' + query.keys_update + ''' WHERE sonarrSeriesId = ?''',
                         query.values + (updated_series['sonarrSeriesId'],))
        event_stream(type='series', id=updated_series['sonarrSeriesId'])

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
                          path_mappings.path_replace(added_series['path']))

            event_stream(type='series', action='insert', id=added_series['sonarrSeriesId'])

            logging.debug('BAZARR All series synced from Sonarr into database.')


def update_one_series(series):
    # Get some values before altering the series dict
    if 'body' not in series:
        return
    if 'resource' not in series['body']:
        return
    if 'id' not in series['body']['resource']:
        return

    action = series['body']['action']
    seriesId = series['body']['resource']['id']
    logging.debug('BAZARR syncing this specific series from Sonarr: {}'.format(seriesId))

    # Check if there's a row in database for this series ID
    existing_series = database.execute('SELECT path FROM table_shows WHERE sonarrSeriesId = ?', (seriesId,),
                                       only_one=True)

    # Validate the provided series
    sonarr_version = get_sonarr_version()
    serie_default_enabled = settings.general.getboolean('serie_default_enabled')

    if serie_default_enabled is True:
        serie_default_profile = settings.general.serie_default_profile
        if serie_default_profile == '':
            serie_default_profile = None
    else:
        serie_default_profile = None

    audio_profiles = get_profile_list()
    tagsDict = get_tags()

    try:
        if action == 'updated' and existing_series:
            series = seriesParser(series['body']['resource'], action='update', sonarr_version=sonarr_version,
                                  tags_dict=tagsDict, serie_default_profile=serie_default_profile,
                                  audio_profiles=audio_profiles)
        elif action == 'updated' and not existing_series:
            series = seriesParser(series['body']['resource'], action='insert', sonarr_version=sonarr_version,
                                  tags_dict=tagsDict, serie_default_profile=serie_default_profile,
                                  audio_profiles=audio_profiles)
        else:
            series = None
    except Exception:
        logging.debug('BAZARR cannot parse series returned by SignalR feed.')
        return

    # Remove series from DB
    if action == 'deleted':
        database.execute("DELETE FROM table_shows WHERE sonarrSeriesId=?", (seriesId,))
        event_stream(type='series', action='delete', id=seriesId)
        logging.debug('BAZARR deleted this series from the database:{}'.format(path_mappings.path_replace(
            existing_series['path'])))
        return

    # Update existing series in DB
    elif action == 'updated' and existing_series:
        query = dict_converter.convert(series)
        database.execute('''UPDATE table_shows SET ''' + query.keys_update + ''' WHERE sonarrSeriesId = ?''',
                         query.values + (series['sonarrSeriesId'],))
        event_stream(type='series', action='update', id=seriesId)
        logging.debug('BAZARR updated this series into the database:{}'.format(path_mappings.path_replace(
            series['path'])))

    # Insert new series in DB
    elif action == 'updated' and not existing_series:
        query = dict_converter.convert(series)
        database.execute('''INSERT OR IGNORE INTO table_shows(''' + query.keys_insert + ''') VALUES(''' +
                         query.question_marks + ''')''', query.values)
        event_stream(type='series', action='insert', id=seriesId)
        logging.debug('BAZARR inserted this series into the database:{}'.format(path_mappings.path_replace(
            series['path'])))


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
        profiles_json = requests.get(url_sonarr_api_series, timeout=60, verify=False, headers=headers)
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
    profiles_to_return = []
    for profile in profiles:
        if id_ == profile[0]:
            profiles_to_return.append(profile[1])
    return profiles_to_return


def get_tags():
    apikey_sonarr = settings.sonarr.apikey
    tagsDict = []

    # Get tags data from Sonarr
    url_sonarr_api_series = url_sonarr() + "/api/tag?apikey=" + apikey_sonarr

    try:
        tagsDict = requests.get(url_sonarr_api_series, timeout=60, verify=False, headers=headers)
    except requests.exceptions.ConnectionError:
        logging.exception("BAZARR Error trying to get tags from Sonarr. Connection Error.")
        return []
    except requests.exceptions.Timeout:
        logging.exception("BAZARR Error trying to get tags from Sonarr. Timeout Error.")
        return []
    except requests.exceptions.RequestException:
        logging.exception("BAZARR Error trying to get tags from Sonarr.")
        return []
    else:
        return tagsDict.json()


def seriesParser(show, action, sonarr_version, tags_dict, serie_default_profile, audio_profiles):
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

    audio_language = []
    if sonarr_version.startswith('2'):
        audio_language = profile_id_to_language(show['qualityProfileId'], audio_profiles)
    else:
        audio_language = profile_id_to_language(show['languageProfileId'], audio_profiles)

    tags = [d['label'] for d in tags_dict if d['id'] in show['tags']]

    imdbId = show['imdbId'] if 'imdbId' in show else None

    if action == 'update':
        return {'title': show["title"],
                'path': show["path"],
                'tvdbId': int(show["tvdbId"]),
                'sonarrSeriesId': int(show["id"]),
                'overview': overview,
                'poster': poster,
                'fanart': fanart,
                'audio_language': str(audio_language),
                'sortTitle': show['sortTitle'],
                'year': str(show['year']),
                'alternateTitles': alternate_titles,
                'tags': str(tags),
                'seriesType': show['seriesType'],
                'imdbId': imdbId}
    else:
        return {'title': show["title"],
                'path': show["path"],
                'tvdbId': show["tvdbId"],
                'sonarrSeriesId': show["id"],
                'overview': overview,
                'poster': poster,
                'fanart': fanart,
                'audio_language': str(audio_language),
                'sortTitle': show['sortTitle'],
                'year': str(show['year']),
                'alternateTitles': alternate_titles,
                'tags': str(tags),
                'seriesType': show['seriesType'],
                'imdbId': imdbId,
                'profileId': serie_default_profile}

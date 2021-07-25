# coding=utf-8

import os
import requests
import logging
from gevent import sleep
from peewee import DoesNotExist

from config import settings, url_sonarr
from list_subtitles import list_missing_subtitles
from get_rootfolder import check_sonarr_rootfolder
from database import TableShows, TableEpisodes
from get_episodes import sync_episodes
from utils import get_sonarr_version
from helper import path_mappings
from event_handler import event_stream, show_progress, hide_progress

headers = {"User-Agent": os.environ["SZ_USER_AGENT"]}


def update_series(send_event=True):
    check_sonarr_rootfolder()
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
    series = get_series_from_sonarr_api(url=url_sonarr(), apikey_sonarr=apikey_sonarr, 
                                        sonarr_version=sonarr_version)
    if not series:
        return
    else:
        # Get current shows in DB
        current_shows_db = TableShows.select(TableShows.sonarrSeriesId).dicts()

        current_shows_db_list = [x['sonarrSeriesId'] for x in current_shows_db]
        current_shows_sonarr = []
        series_to_update = []
        series_to_add = []

        series_count = len(series)
        for i, show in enumerate(series, 1):
            sleep()
            if send_event:
                show_progress(id='series_progress',
                              header='Syncing series...',
                              name=show['title'],
                              value=i,
                              count=series_count)

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

        if send_event:
            show_progress(id='series_progress',
                          header='Syncing series...',
                          name='Completed successfully',
                          value=series_count,
                          count=series_count)

            hide_progress(id='series_progress')

        # Remove old series from DB
        removed_series = list(set(current_shows_db_list) - set(current_shows_sonarr))

        for series in removed_series:
            sleep()
            TableShows.delete().where(TableShows.sonarrSeriesId == series).execute()
            if send_event:
                event_stream(type='series', action='delete', payload=series)

        # Update existing series in DB
        series_in_db_list = []
        series_in_db = TableShows.select(TableShows.title,
                                         TableShows.path,
                                         TableShows.tvdbId,
                                         TableShows.sonarrSeriesId,
                                         TableShows.overview,
                                         TableShows.poster,
                                         TableShows.fanart,
                                         TableShows.audio_language,
                                         TableShows.sortTitle,
                                         TableShows.year,
                                         TableShows.alternateTitles,
                                         TableShows.tags,
                                         TableShows.seriesType,
                                         TableShows.imdbId).dicts()

        for item in series_in_db:
            series_in_db_list.append(item)

        series_to_update_list = [i for i in series_to_update if i not in series_in_db_list]

        for updated_series in series_to_update_list:
            sleep()
            TableShows.update(updated_series).where(TableShows.sonarrSeriesId ==
                                                    updated_series['sonarrSeriesId']).execute()
            if send_event:
                event_stream(type='series', payload=updated_series['sonarrSeriesId'])

        # Insert new series in DB
        for added_series in series_to_add:
            sleep()
            result = TableShows.insert(added_series).on_conflict(action='IGNORE').execute()
            if result:
                list_missing_subtitles(no=added_series['sonarrSeriesId'])
            else:
                logging.debug('BAZARR unable to insert this series into the database:',
                              path_mappings.path_replace(added_series['path']))

                if send_event:
                    event_stream(type='series', action='update', payload=added_series['sonarrSeriesId'])

                logging.debug('BAZARR All series synced from Sonarr into database.')


def update_one_series(series_id, action):
    logging.debug('BAZARR syncing this specific series from Sonarr: {}'.format(series_id))

    # Check if there's a row in database for this series ID
    try:
        existing_series = TableShows.select(TableShows.path)\
            .where(TableShows.sonarrSeriesId == series_id)\
            .dicts()\
            .get()
    except DoesNotExist:
        existing_series = None

    # Delete series from DB
    if action == 'deleted' and existing_series:
        TableShows.delete().where(TableShows.sonarrSeriesId == int(series_id)).execute()
        TableEpisodes.delete().where(TableEpisodes.sonarrSeriesId == int(series_id)).execute()
        event_stream(type='series', action='delete', payload=int(series_id))
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

    try:
        # Get series data from sonarr api
        series = None

        series_data = get_series_from_sonarr_api(url=url_sonarr(), apikey_sonarr=settings.sonarr.apikey,
                                                 sonarr_series_id=int(series_id), sonarr_version=get_sonarr_version())

        if not series_data:
            return
        else:
            if action == 'updated' and existing_series:
                series = seriesParser(series_data, action='update', sonarr_version=sonarr_version,
                                      tags_dict=tagsDict, serie_default_profile=serie_default_profile,
                                      audio_profiles=audio_profiles)
            elif action == 'updated' and not existing_series:
                series = seriesParser(series_data, action='insert', sonarr_version=sonarr_version,
                                      tags_dict=tagsDict, serie_default_profile=serie_default_profile,
                                      audio_profiles=audio_profiles)
    except Exception:
        logging.debug('BAZARR cannot parse series returned by SignalR feed.')
        return

    # Update existing series in DB
    if action == 'updated' and existing_series:
        TableShows.update(series).where(TableShows.sonarrSeriesId == series['sonarrSeriesId']).execute()
        sync_episodes(series_id=int(series_id), send_event=True)
        event_stream(type='series', action='update', payload=int(series_id))
        logging.debug('BAZARR updated this series into the database:{}'.format(path_mappings.path_replace(
            series['path'])))

    # Insert new series in DB
    elif action == 'updated' and not existing_series:
        TableShows.insert(series).on_conflict(action='IGNORE').execute()
        event_stream(type='series', action='update', payload=int(series_id))
        logging.debug('BAZARR inserted this series into the database:{}'.format(path_mappings.path_replace(
            series['path'])))


def get_profile_list():
    apikey_sonarr = settings.sonarr.apikey
    sonarr_version = get_sonarr_version()
    profiles_list = []

    # Get profiles data from Sonarr
    if sonarr_version.startswith(('0.', '2.')):
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
    if sonarr_version.startswith(('0.', '2.')):
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
    sonarr_version = get_sonarr_version()
    tagsDict = []

    # Get tags data from Sonarr
    if sonarr_version.startswith(('0.', '2.')):
        url_sonarr_api_series = url_sonarr() + "/api/tag?apikey=" + apikey_sonarr
    else:
        url_sonarr_api_series = url_sonarr() + "/api/v3/tag?apikey=" + apikey_sonarr

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
    if sonarr_version.startswith(('0.', '2.')):
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


def get_series_from_sonarr_api(url, apikey_sonarr, sonarr_version, sonarr_series_id=None):
    url_sonarr_api_series = url + "/api/{0}series/{1}?apikey={2}".format(
        '' if sonarr_version.startswith(('0.', '2.')) else 'v3/', sonarr_series_id if sonarr_series_id else "", apikey_sonarr)
    try:
        r = requests.get(url_sonarr_api_series, timeout=60, verify=False, headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code:
            raise requests.exceptions.HTTPError
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
    else:
        return r.json()

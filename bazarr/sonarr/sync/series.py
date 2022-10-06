# coding=utf-8

import logging

from peewee import IntegrityError

from app.config import settings
from sonarr.info import url_sonarr
from subtitles.indexer.series import list_missing_subtitles
from sonarr.rootfolder import check_sonarr_rootfolder
from app.database import TableShows, TableEpisodes
from utilities.path_mappings import path_mappings
from app.event_handler import event_stream, show_progress, hide_progress

from .episodes import sync_episodes
from .parser import seriesParser
from .utils import get_profile_list, get_tags, get_series_from_sonarr_api


def update_series(send_event=True):
    check_sonarr_rootfolder()
    apikey_sonarr = settings.sonarr.apikey
    if apikey_sonarr is None:
        return

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
    series = get_series_from_sonarr_api(url=url_sonarr(), apikey_sonarr=apikey_sonarr)
    if not isinstance(series, list):
        return
    else:
        # Get current shows in DB
        current_shows_db = TableShows.select(TableShows.sonarrSeriesId).dicts()

        current_shows_db_list = [x['sonarrSeriesId'] for x in current_shows_db]
        current_shows_sonarr = []
        series_to_update = []
        series_to_add = []

        series_count = len(series)
        for i, show in enumerate(series):
            if send_event:
                show_progress(id='series_progress',
                              header='Syncing series...',
                              name=show['title'],
                              value=i,
                              count=series_count)

            # Add shows in Sonarr to current shows list
            current_shows_sonarr.append(show['id'])

            if show['id'] in current_shows_db_list:
                series_to_update.append(seriesParser(show, action='update', tags_dict=tagsDict,
                                                     serie_default_profile=serie_default_profile,
                                                     audio_profiles=audio_profiles))
            else:
                series_to_add.append(seriesParser(show, action='insert', tags_dict=tagsDict,
                                                  serie_default_profile=serie_default_profile,
                                                  audio_profiles=audio_profiles))

        if send_event:
            hide_progress(id='series_progress')

        # Remove old series from DB
        removed_series = list(set(current_shows_db_list) - set(current_shows_sonarr))

        for series in removed_series:
            try:
                TableShows.delete().where(TableShows.sonarrSeriesId == series).execute()
            except Exception as e:
                logging.error(f"BAZARR cannot delete series with sonarrSeriesId {series} because of {e}")
                continue
            else:
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
                                         TableShows.imdbId,
                                         TableShows.monitored).dicts()

        for item in series_in_db:
            series_in_db_list.append(item)

        series_to_update_list = [i for i in series_to_update if i not in series_in_db_list]

        for updated_series in series_to_update_list:
            try:
                TableShows.update(updated_series).where(TableShows.sonarrSeriesId ==
                                                        updated_series['sonarrSeriesId']).execute()
            except IntegrityError as e:
                logging.error(f"BAZARR cannot update series {updated_series['path']} because of {e}")
                continue
            else:
                if send_event:
                    event_stream(type='series', payload=updated_series['sonarrSeriesId'])

        # Insert new series in DB
        for added_series in series_to_add:
            try:
                result = TableShows.insert(added_series).on_conflict(action='IGNORE').execute()
            except IntegrityError as e:
                logging.error(f"BAZARR cannot insert series {added_series['path']} because of {e}")
                continue
            else:
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
    existing_series = TableShows.select(TableShows.path)\
        .where(TableShows.sonarrSeriesId == series_id)\
        .dicts()\
        .get_or_none()

    # Delete series from DB
    if action == 'deleted' and existing_series:
        try:
            TableShows.delete().where(TableShows.sonarrSeriesId == int(series_id)).execute()
        except Exception as e:
            logging.error(f"BAZARR cannot delete series with sonarrSeriesId {series_id} because of {e}")
        else:
            TableEpisodes.delete().where(TableEpisodes.sonarrSeriesId == int(series_id)).execute()
            event_stream(type='series', action='delete', payload=int(series_id))
            return

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
                                                 sonarr_series_id=int(series_id))

        if not series_data:
            return
        else:
            if action == 'updated' and existing_series:
                series = seriesParser(series_data[0], action='update', tags_dict=tagsDict,
                                      serie_default_profile=serie_default_profile,
                                      audio_profiles=audio_profiles)
            elif action == 'updated' and not existing_series:
                series = seriesParser(series_data[0], action='insert', tags_dict=tagsDict,
                                      serie_default_profile=serie_default_profile,
                                      audio_profiles=audio_profiles)
    except Exception:
        logging.exception('BAZARR cannot get series returned by SignalR feed from Sonarr API.')
        return

    # Update existing series in DB
    if action == 'updated' and existing_series:
        try:
            TableShows.update(series).where(TableShows.sonarrSeriesId == series['sonarrSeriesId']).execute()
        except IntegrityError as e:
            logging.error(f"BAZARR cannot update series {series['path']} because of {e}")
        else:
            sync_episodes(series_id=int(series_id), send_event=True)
            event_stream(type='series', action='update', payload=int(series_id))
            logging.debug('BAZARR updated this series into the database:{}'.format(path_mappings.path_replace(
                series['path'])))

    # Insert new series in DB
    elif action == 'updated' and not existing_series:
        try:
            TableShows.insert(series).on_conflict(action='IGNORE').execute()
        except IntegrityError as e:
            logging.error(f"BAZARR cannot insert series {series['path']} because of {e}")
        else:
            event_stream(type='series', action='update', payload=int(series_id))
            logging.debug('BAZARR inserted this series into the database:{}'.format(path_mappings.path_replace(
                series['path'])))

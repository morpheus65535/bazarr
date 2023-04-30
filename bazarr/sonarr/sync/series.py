# coding=utf-8

import logging

from app.config import settings
from sonarr.info import url_sonarr
from subtitles.indexer.series import list_missing_subtitles
from sonarr.rootfolder import check_sonarr_rootfolder
from app.database import TableShows, database, insert, update, delete, select
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
        current_shows_db = [x.sonarrSeriesId for x in
                            database.execute(
                                select(TableShows.sonarrSeriesId))
                            .all()]
        current_shows_sonarr = []

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

            if show['id'] in current_shows_db:
                updated_series = seriesParser(show, action='update', tags_dict=tagsDict,
                                              serie_default_profile=serie_default_profile,
                                              audio_profiles=audio_profiles)

                if not database.execute(
                        select(TableShows)
                        .filter_by(**updated_series))\
                        .first():
                    database.execute(
                        update(TableShows)
                        .values(updated_series)
                        .where(TableShows.sonarrSeriesId == show['id']))

                if send_event:
                    event_stream(type='series', payload=show['id'])
            else:
                added_series = seriesParser(show, action='insert', tags_dict=tagsDict,
                                            serie_default_profile=serie_default_profile,
                                            audio_profiles=audio_profiles)

                database.execute(
                    insert(TableShows)
                    .values(added_series))

                list_missing_subtitles(no=show['id'])

                if send_event:
                    event_stream(type='series', action='update', payload=show['id'])

            sync_episodes(series_id=show['id'], send_event=send_event)

        # Remove old series from DB
        removed_series = list(set(current_shows_db) - set(current_shows_sonarr))

        for series in removed_series:
            database.execute(
                delete(TableShows)
                .where(TableShows.sonarrSeriesId == series))

            if send_event:
                event_stream(type='series', action='delete', payload=series)

        if send_event:
            hide_progress(id='series_progress')

        logging.debug('BAZARR All series synced from Sonarr into database.')


def update_one_series(series_id, action):
    logging.debug('BAZARR syncing this specific series from Sonarr: {}'.format(series_id))

    # Check if there's a row in database for this series ID
    existing_series = database.execute(
        select(TableShows)
        .where(TableShows.sonarrSeriesId == series_id))\
        .first()

    # Delete series from DB
    if action == 'deleted' and existing_series:
        database.execute(
            delete(TableShows)
            .where(TableShows.sonarrSeriesId == int(series_id)))

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
        database.execute(
            update(TableShows)
            .values(series)
            .where(TableShows.sonarrSeriesId == series['sonarrSeriesId']))
        sync_episodes(series_id=int(series_id), send_event=False)
        event_stream(type='series', action='update', payload=int(series_id))
        logging.debug('BAZARR updated this series into the database:{}'.format(path_mappings.path_replace(
            series['path'])))

    # Insert new series in DB
    elif action == 'updated' and not existing_series:
        database.execute(
            insert(TableShows)
            .values(series))
        event_stream(type='series', action='update', payload=int(series_id))
        logging.debug('BAZARR inserted this series into the database:{}'.format(path_mappings.path_replace(
            series['path'])))

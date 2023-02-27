import logging
from typing import List, Dict

from peewee import IntegrityError

from app.config import settings
from subtitles.indexer.series import list_missing_subtitles
from sonarr.rootfolder import check_sonarr_rootfolder
from app.database import TableShows, TableEpisodes
from utilities.path_mappings import path_mappings
from app.event_handler import event_stream, show_progress, hide_progress

from .episodes import sync_episodes
from .parser import seriesParser
from .utils import get_profile_list, get_tags, get_series_from_sonarr_api


def sync_sonarr(send_event: bool = True) -> None:
    """Sync Sonarr series and episodes with Bazarr."""
    check_sonarr_rootfolder()

    current_series_db = TableShows.select(TableShows.sonarrSeriesId).dicts()

    current_series_db_list = [x['sonarrSeriesId'] for x in current_series_db]
    current_series_sonarr = []

    # Get shows data from Sonarr
    series = get_series_from_sonarr_api()
    if not isinstance(series, list):
        return
    series_count = len(series)
    show_progress(id='sonarr_progress',
                  header='Syncing sonarr...',
                  name='',
                  value=0,
                  count=series_count)
    for i, show in enumerate(series, 1):
        parsed_show = seriesParser(show)
        show_progress(id='sonarr_progress',
                      header='Syncing sonarr...',
                      name=show['title'],
                      value=i,
                      count=series_count)

        # Get current shows in DB
        current_series_sonarr.append(show['id'])
        need_upgrade = TableShows.need_update(parsed_show)
        if need_upgrade is None:
            add_show(parsed_show)
        elif need_upgrade:
            update_show(parsed_show)
        sync_episodes(show['id'])

    # Remove old episodes from DB
    removed_episodes = list(set(current_series_db_list) - set(current_series_sonarr))
    delete_series(removed_episodes)

    if send_event:
        hide_progress(id='series_progress')

    logging.debug('BAZARR All series synced from Sonarr into database.')
    return


# sync_sonarr()


def add_show(show: dict, send_event: bool = True) -> None:
    serie_default_enabled = settings.general.getboolean('serie_default_enabled')

    if serie_default_enabled:
        serie_default_profile = settings.general.serie_default_profile
        if serie_default_profile == '':
            serie_default_profile = None
    else:
        serie_default_profile = None
    show["profileId"] = serie_default_profile
    try:
        result = TableShows.insert(show).on_conflict(action='IGNORE').execute()
    except IntegrityError as e:
        logging.error(f"BAZARR cannot insert series {show['path']} because of {e}")
        return
    if result:
        list_missing_subtitles(no=show['sonarrSeriesId'])
    else:
        logging.debug('BAZARR unable to insert this series into the database:',
                      path_mappings.path_replace(show['path']))

    if send_event:
        event_stream(type='series', action='update', payload=show['sonarrSeriesId'])
    return


def update_show(show: dict, send_event: bool = True) -> None:
    try:
        TableShows.update(show).where(TableShows.sonarrSeriesId == show['sonarrSeriesId']).execute()
    except IntegrityError as e:
        logging.error(f"BAZARR cannot update series {show['path']} because of {e}")
        return

    if send_event:
        event_stream(type='series', payload=show['sonarrSeriesId'])
    return


def delete_series(series: List[int], send_event: bool = True) -> None:
    for show in series:
        try:
            TableShows.delete().where(TableShows.sonarrSeriesId == show).execute()
        except Exception as e:
            logging.error(f"BAZARR cannot delete series_id {show} because of {e}")
            return

        if send_event:
            event_stream(type='series', action='delete', payload=show)
    return


def update_one_series(series_id, action):
    logging.debug(f'BAZARR syncing this specific series from Sonarr: {series_id}')

    # Check if there's a row in database for this series ID
    existing_series = TableShows.select(TableShows.path)\
        .where(TableShows.sonarrSeriesId == series_id)\
        .dicts()\
        .get_or_none()

    # Delete series from DB
    if action == 'deleted' and existing_series:
        delete_series([series_id])

    try:
        # Get series data from sonarr api
        series = None

        series_data = get_series_from_sonarr_api(sonarr_series_id=int(series_id))

        if not series_data:
            return
        parsed_show = seriesParser(series_data)
        if action == 'updated':
            series = (
                seriesParser(
                    series_data[0],
                    action='update',
                    tags_dict=tagsDict,
                    serie_default_profile=serie_default_profile,
                    audio_profiles=audio_profiles,
                )
                if existing_series
                else seriesParser(
                    series_data[0],
                    action='insert',
                    tags_dict=tagsDict,
                    serie_default_profile=serie_default_profile,
                    audio_profiles=audio_profiles,
                )
            )
    except Exception:
        logging.exception('BAZARR cannot get series returned by SignalR feed from Sonarr API.')
        return

    # Update existing series in DB
    if action == 'updated':
        if existing_series:
            try:
                TableShows.update(series).where(TableShows.sonarrSeriesId == series['sonarrSeriesId']).execute()
            except IntegrityError as e:
                logging.error(f"BAZARR cannot update series {series['path']} because of {e}")
            else:
                sync_episodes(serie_id=int(series_id), send_event=False)
                event_stream(type='series', action='update', payload=int(series_id))
                logging.debug('BAZARR updated this series into the database:{}'.format(path_mappings.path_replace(
                    series['path'])))

        else:
            try:
                TableShows.insert(series).on_conflict(action='IGNORE').execute()
            except IntegrityError as e:
                logging.error(f"BAZARR cannot insert series {series['path']} because of {e}")
            else:
                event_stream(type='series', action='update', payload=int(series_id))
                logging.debug('BAZARR inserted this series into the database:{}'.format(path_mappings.path_replace(
                    series['path'])))

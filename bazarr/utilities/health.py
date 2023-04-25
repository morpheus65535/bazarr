# coding=utf-8

from app.config import settings
from app.database import TableShowsRootfolder, TableMoviesRootfolder, database, select
from app.event_handler import event_stream
from .path_mappings import path_mappings
from sonarr.rootfolder import check_sonarr_rootfolder
from radarr.rootfolder import check_radarr_rootfolder


def check_health():
    if settings.general.getboolean('use_sonarr'):
        check_sonarr_rootfolder()
    if settings.general.getboolean('use_radarr'):
        check_radarr_rootfolder()
    event_stream(type='badges')

    from .backup import backup_rotation
    backup_rotation()


def get_health_issues():
    # this function must return a list of dictionaries consisting of to keys: object and issue
    health_issues = []

    # get Sonarr rootfolder issues
    if settings.general.getboolean('use_sonarr'):
        rootfolder = database.execute(
            select(TableShowsRootfolder.path,
                   TableShowsRootfolder.accessible,
                   TableShowsRootfolder.error)
            .where(TableShowsRootfolder.accessible == 0)) \
            .all()
        for item in rootfolder:
            health_issues.append({'object': path_mappings.path_replace(item.path),
                                  'issue': item.error})

    # get Radarr rootfolder issues
    if settings.general.getboolean('use_radarr'):
        rootfolder = database.execute(
            select(TableMoviesRootfolder.path,
                   TableMoviesRootfolder.accessible,
                   TableMoviesRootfolder.error)
            .where(TableMoviesRootfolder.accessible == 0)) \
            .all()
        for item in rootfolder:
            health_issues.append({'object': path_mappings.path_replace_movie(item.path),
                                  'issue': item.error})

    return health_issues

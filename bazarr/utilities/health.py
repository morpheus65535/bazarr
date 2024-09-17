# coding=utf-8

import json

from app.config import settings
from app.database import TableShowsRootfolder, TableMoviesRootfolder, TableLanguagesProfiles, database, select
from app.event_handler import event_stream
from .path_mappings import path_mappings
from sonarr.rootfolder import check_sonarr_rootfolder
from radarr.rootfolder import check_radarr_rootfolder


def check_health():
    if settings.general.use_sonarr:
        check_sonarr_rootfolder()
    if settings.general.use_radarr:
        check_radarr_rootfolder()
    event_stream(type='badges')

    from .backup import backup_rotation
    backup_rotation()


def get_health_issues():
    # this function must return a list of dictionaries consisting of to keys: object and issue
    health_issues = []

    # get Sonarr rootfolder issues
    if settings.general.use_sonarr:
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
    if settings.general.use_radarr:
        rootfolder = database.execute(
            select(TableMoviesRootfolder.path,
                   TableMoviesRootfolder.accessible,
                   TableMoviesRootfolder.error)
            .where(TableMoviesRootfolder.accessible == 0)) \
            .all()
        for item in rootfolder:
            health_issues.append({'object': path_mappings.path_replace_movie(item.path),
                                  'issue': item.error})

    # get languages profiles duplicate ids issues when there's a cutoff set
    languages_profiles = database.execute(
        select(TableLanguagesProfiles.items, TableLanguagesProfiles.name, TableLanguagesProfiles.cutoff)).all()
    for languages_profile in languages_profiles:
        if not languages_profile.cutoff:
            # ignore profiles that don't have a cutoff set
            continue
        languages_profile_ids = []
        for items in json.loads(languages_profile.items):
            if items['id'] in languages_profile_ids:
                health_issues.append({'object': languages_profile.name,
                                      'issue': 'This languages profile has duplicate IDs. You need to edit this profile'
                                               ' and make sure to select the proper cutoff if required.'})
                break
            else:
                languages_profile_ids.append(items['id'])

    return health_issues

# coding=utf-8

import json

from sqlalchemy import func

from app.config import settings
from app.database import (TableShowsRootfolder, TableMoviesRootfolder, TableLanguagesProfiles, database, select,
                          TableShows, TableMovies)
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue
from .path_mappings import path_mappings
from sonarr.rootfolder import check_sonarr_rootfolder
from radarr.rootfolder import check_radarr_rootfolder


def check_health(job_id=None):
    if not job_id:
        jobs_queue.add_job_from_function("Check Health", is_progress=False)
        return

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

    # check if there's at least one languages profile created
    languages_profiles_count = database.execute(select(func.count(TableLanguagesProfiles.profileId))).scalar()
    series_with_profile = database.execute(select(func.count(TableShows.sonarrSeriesId))
                                           .where(TableShows.profileId.is_not(None))).scalar()
    movies_with_profile = database.execute(select(func.count(TableMovies.radarrId))
                                           .where(TableMovies.profileId.is_not(None))).scalar()
    default_series_profile_empty = settings.general.serie_default_enabled and settings.general.serie_default_profile == ''
    default_movies_profile_empty = settings.general.movie_default_enabled and settings.general.movie_default_profile == ''
    if languages_profiles_count == 0:
        health_issues.append({'object': 'Missing languages profile',
                              'issue': 'You must create at least one languages profile and assign it to your content.'})
    elif languages_profiles_count > 0 and ((settings.general.use_sonarr and series_with_profile == 0 and default_series_profile_empty) or
                                           (settings.general.use_radarr and movies_with_profile == 0 and default_movies_profile_empty)):
        health_issues.append({'object': 'No assigned languages profile',
                              'issue': 'Although you have created at least one languages profile, you must assign it '
                                       'to your content.'})

    return health_issues

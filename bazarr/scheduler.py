# coding=utf-8

from get_episodes import sync_episodes, update_all_episodes, update_all_movies
from get_movies import update_movies
from get_series import update_series
from config import settings
from get_subtitle import wanted_search_missing_subtitles
from get_args import args

if not args.no_update:
    from check_update import check_and_apply_update, check_releases
else:
    from check_update import check_releases
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
from tzlocal import get_localzone


def sonarr_full_update():
    if settings.general.getboolean('use_sonarr'):
        full_update = settings.sonarr.full_update
        if full_update == "Daily":
            scheduler.add_job(update_all_episodes, CronTrigger(hour=4), max_instances=1, coalesce=True,
                              misfire_grace_time=15, id='update_all_episodes',
                              name='Update all episodes subtitles from disk', replace_existing=True)
        elif full_update == "Weekly":
            scheduler.add_job(update_all_episodes, CronTrigger(day_of_week='sun'), hour=4, max_instances=1,
                              coalesce=True,
                              misfire_grace_time=15, id='update_all_episodes',
                              name='Update all episodes subtitles from disk', replace_existing=True)
        elif full_update == "Manually":
            scheduler.add_job(update_all_episodes, CronTrigger(year='2100'), hour=4, max_instances=1, coalesce=True,
                              misfire_grace_time=15, id='update_all_episodes',
                              name='Update all episodes subtitles from disk', replace_existing=True)


def radarr_full_update():
    if settings.general.getboolean('use_radarr'):
        full_update = settings.radarr.full_update
        if full_update == "Daily":
            scheduler.add_job(update_all_movies, CronTrigger(hour=5), max_instances=1, coalesce=True,
                              misfire_grace_time=15,
                              id='update_all_movies', name='Update all movies subtitles from disk',
                              replace_existing=True)
        elif full_update == "Weekly":
            scheduler.add_job(update_all_movies, CronTrigger(day_of_week='sun'), hour=5, max_instances=1, coalesce=True,
                              misfire_grace_time=15, id='update_all_movies',
                              name='Update all movies subtitles from disk',
                              replace_existing=True)
        elif full_update == "Manually":
            scheduler.add_job(update_all_movies, CronTrigger(year='2100'), hour=5, max_instances=1, coalesce=True,
                              misfire_grace_time=15, id='update_all_movies',
                              name='Update all movies subtitles from disk',
                              replace_existing=True)


def execute_now(taskid):
    scheduler.modify_job(taskid, next_run_time=datetime.now())


if str(get_localzone()) == "local":
    scheduler = BackgroundScheduler(timezone=pytz.timezone('UTC'))
else:
    scheduler = BackgroundScheduler()

if not args.no_update:
    if settings.general.getboolean('auto-update'):
        scheduler.add_job(check_and_apply_update, IntervalTrigger(hours=6), max_instances=1, coalesce=True,
        misfire_grace_time=15, id='update_bazarr', name='Update bazarr from source on Github')
    else:
        scheduler.add_job(check_and_apply_update, CronTrigger(year='2100'), hour=4, id='update_bazarr',
                          name='Update bazarr from source on Github')
        scheduler.add_job(check_releases, IntervalTrigger(hours=6), max_instances=1, coalesce=True,
                          misfire_grace_time=15, id='update_release', name='Update release info')
else:
    scheduler.add_job(check_releases, IntervalTrigger(hours=6), max_instances=1, coalesce=True, misfire_grace_time=15,
                      id='update_release', name='Update release info')

if settings.general.getboolean('use_sonarr'):
    scheduler.add_job(update_series, IntervalTrigger(minutes=1), max_instances=1, coalesce=True, misfire_grace_time=15,
                      id='update_series', name='Update series list from Sonarr')
    scheduler.add_job(sync_episodes, IntervalTrigger(minutes=5), max_instances=1, coalesce=True, misfire_grace_time=15,
                      id='sync_episodes', name='Sync episodes with Sonarr')

if settings.general.getboolean('use_radarr'):
    scheduler.add_job(update_movies, IntervalTrigger(minutes=5), max_instances=1, coalesce=True, misfire_grace_time=15,
                      id='update_movies', name='Update movies list from Radarr')

if settings.general.getboolean('use_sonarr') or settings.general.getboolean('use_radarr'):
    scheduler.add_job(wanted_search_missing_subtitles, IntervalTrigger(hours=3), max_instances=1, coalesce=True,
                      misfire_grace_time=15, id='wanted_search_missing_subtitles', name='Search for wanted subtitles')

sonarr_full_update()
radarr_full_update()
scheduler.start()


def shutdown_scheduler():
    scheduler.shutdown(wait=True)

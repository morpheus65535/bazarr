# coding=utf-8

from get_episodes import sync_episodes, update_all_episodes
from get_movies import update_movies, update_all_movies
from get_series import update_series
from config import settings
from get_subtitle import wanted_search_missing_subtitles, upgrade_subtitles
from utils import cache_maintenance
from get_args import args
if not args.no_update:
    from check_update import check_and_apply_update, check_releases
else:
    from check_update import check_releases
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.events import EVENT_JOB_SUBMITTED, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime
import pytz
from tzlocal import get_localzone


def sonarr_full_update():
    if settings.general.getboolean('use_sonarr'):
        full_update = settings.sonarr.full_update
        if full_update == "Daily":
            scheduler.add_job(update_all_episodes, CronTrigger(hour=settings.sonarr.full_update_hour), max_instances=1, coalesce=True,
                              misfire_grace_time=15, id='update_all_episodes',
                              name='Update all Episode Subtitles from disk', replace_existing=True)
        elif full_update == "Weekly":
            scheduler.add_job(update_all_episodes, CronTrigger(day_of_week=settings.sonarr.full_update_day, hour=settings.sonarr.full_update_hour), max_instances=1,
                              coalesce=True,
                              misfire_grace_time=15, id='update_all_episodes',
                              name='Update all Episode Subtitles from disk', replace_existing=True)
        elif full_update == "Manually":
            scheduler.add_job(update_all_episodes, CronTrigger(year='2100'), max_instances=1, coalesce=True,
                              misfire_grace_time=15, id='update_all_episodes',
                              name='Update all Episode Subtitles from disk', replace_existing=True)


def radarr_full_update():
    if settings.general.getboolean('use_radarr'):
        full_update = settings.radarr.full_update
        if full_update == "Daily":
            scheduler.add_job(update_all_movies, CronTrigger(hour=settings.radarr.full_update_hour), max_instances=1, coalesce=True,
                              misfire_grace_time=15,
                              id='update_all_movies', name='Update all Movie Subtitles from disk',
                              replace_existing=True)
        elif full_update == "Weekly":
            scheduler.add_job(update_all_movies, CronTrigger(day_of_week=settings.radarr.full_update_day, hour=settings.radarr.full_update_hour), max_instances=1, coalesce=True,
                              misfire_grace_time=15, id='update_all_movies',
                              name='Update all Movie Subtitles from disk',
                              replace_existing=True)
        elif full_update == "Manually":
            scheduler.add_job(update_all_movies, CronTrigger(year='2100'), max_instances=1, coalesce=True,
                              misfire_grace_time=15, id='update_all_movies',
                              name='Update all Movie Subtitles from disk',
                              replace_existing=True)


def execute_now(taskid):
    scheduler.modify_job(taskid, next_run_time=datetime.now())


if str(get_localzone()) == "local":
    scheduler = BackgroundScheduler(timezone=pytz.timezone('UTC'))
else:
    scheduler = BackgroundScheduler()

global running_tasks
running_tasks = []


def task_listener_add(event):
    if event.job_id not in running_tasks:
        running_tasks.append(event.job_id)


def task_listener_remove(event):
    if event.job_id in running_tasks:
        running_tasks.remove(event.job_id)


scheduler.add_listener(task_listener_add, EVENT_JOB_SUBMITTED)
scheduler.add_listener(task_listener_remove, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)


def schedule_update_job():
    if not args.no_update:
        if settings.general.getboolean('auto_update'):
            scheduler.add_job(check_and_apply_update, IntervalTrigger(hours=6), max_instances=1, coalesce=True,
                              misfire_grace_time=15, id='update_bazarr',
                              name='Update Bazarr from source on Github' if not args.release_update else 'Update Bazarr from release on Github',
                              replace_existing=True)
        else:
            scheduler.add_job(check_and_apply_update, CronTrigger(year='2100'), hour=4, id='update_bazarr',
                              name='Update Bazarr from source on Github' if not args.release_update else 'Update Bazarr from release on Github',
                              replace_existing=True)
            scheduler.add_job(check_releases, IntervalTrigger(hours=6), max_instances=1, coalesce=True,
                              misfire_grace_time=15, id='update_release', name='Update Release Info',
                              replace_existing=True)
    
    else:
        scheduler.add_job(check_releases, IntervalTrigger(hours=6), max_instances=1, coalesce=True,
                          misfire_grace_time=15,
                          id='update_release', name='Update Release Info', replace_existing=True)


if settings.general.getboolean('use_sonarr'):
    scheduler.add_job(update_series, IntervalTrigger(minutes=1), max_instances=1, coalesce=True, misfire_grace_time=15,
                      id='update_series', name='Update Series list from Sonarr')
    scheduler.add_job(sync_episodes, IntervalTrigger(minutes=5), max_instances=1, coalesce=True, misfire_grace_time=15,
                      id='sync_episodes', name='Sync episodes with Sonarr')

if settings.general.getboolean('use_radarr'):
    scheduler.add_job(update_movies, IntervalTrigger(minutes=5), max_instances=1, coalesce=True, misfire_grace_time=15,
                      id='update_movies', name='Update Movie list from Radarr')

def schedule_wanted_search():
    if settings.general.getboolean('use_sonarr') or settings.general.getboolean('use_radarr'):
        scheduler.add_job(wanted_search_missing_subtitles,
                          IntervalTrigger(hours=int(settings.general.wanted_search_frequency)), max_instances=1,
                          coalesce=True, misfire_grace_time=15, id='wanted_search_missing_subtitles',
                          name='Search for wanted Subtitles', replace_existing=True)


def schedule_upgrade_subs():
    if settings.general.getboolean('upgrade_subs') and (settings.general.getboolean('use_sonarr') or
                                                        settings.general.getboolean('use_radarr')):
        scheduler.add_job(upgrade_subtitles, IntervalTrigger(hours=int(settings.general.upgrade_frequency)),
                          max_instances=1, coalesce=True, misfire_grace_time=15, id='upgrade_subtitles',
                          name='Upgrade previously downloaded Subtitles', replace_existing=True)

scheduler.add_job(cache_maintenance, IntervalTrigger(hours=24), max_instances=1, coalesce=True,
                  misfire_grace_time=15, id='cache_cleanup', name='Cache maintenance')

schedule_update_job()
sonarr_full_update()
radarr_full_update()
schedule_wanted_search()
schedule_upgrade_subs()
scheduler.start()


def add_job(job, name=None, max_instances=1, coalesce=True, args=None):
    scheduler.add_job(job, DateTrigger(run_date=datetime.now()), name=name, id=name, max_instances=max_instances,
                      coalesce=coalesce, args=args)


def shutdown_scheduler():
    scheduler.shutdown(wait=True)

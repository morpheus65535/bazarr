# coding=utf-8

import os
import pretty

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_SUBMITTED, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime, timedelta
from calendar import day_name
from random import randrange
from tzlocal import get_localzone
try:
    import zoneinfo  # pragma: no cover
except ImportError:
    from backports import zoneinfo  # pragma: no cover
from dateutil import tz
import logging

from app.announcements import get_announcements_to_file
from sonarr.sync.series import update_series
from radarr.sync.movies import update_movies
from subtitles.indexer.movies import movies_full_scan_subtitles
from subtitles.indexer.series import series_full_scan_subtitles
from subtitles.wanted import wanted_search_missing_subtitles_series, wanted_search_missing_subtitles_movies
from subtitles.upgrade import upgrade_subtitles
from utilities.cache import cache_maintenance
from utilities.health import check_health
from utilities.backup import backup_to_zip

from .config import settings
from .get_args import args
from .event_handler import event_stream

if not args.no_update:
    from .check_update import check_if_new_update, check_releases
else:
    from .check_update import check_releases

from dateutil.relativedelta import relativedelta

NO_INTERVAL = "None"
NEVER_DATE = "Never"
ONE_YEAR_IN_SECONDS = 60 * 60 * 24 * 365


def a_long_time_from_now(job):
    # job isn't scheduled at all
    if job.next_run_time is None:
        return True

    # currently defined as more than a year from now
    delta = job.next_run_time - datetime.now(job.next_run_time.tzinfo)
    return delta.total_seconds() > ONE_YEAR_IN_SECONDS


def in_a_century():
    century = datetime.now() + relativedelta(years=100)
    return century.year


class Scheduler:

    def __init__(self):
        self.__running_tasks = []

        # delete empty TZ environment variable to prevent UserWarning
        if os.environ.get("TZ") == "":
            del os.environ["TZ"]

        try:
            self.timezone = get_localzone()
        except zoneinfo.ZoneInfoNotFoundError:
            logging.error("BAZARR cannot use the specified timezone and will use UTC instead.")
            self.timezone = tz.gettz("UTC")
        else:
            logging.info(f"Scheduler will use this timezone: {self.timezone}")

        self.aps_scheduler = BackgroundScheduler({'apscheduler.timezone': self.timezone})

        # task listener
        def task_listener_add(event):
            if event.job_id not in self.__running_tasks:
                self.__running_tasks.append(event.job_id)
                event_stream(type='task')

        def task_listener_remove(event):
            if event.job_id in self.__running_tasks:
                self.__running_tasks.remove(event.job_id)
                event_stream(type='task')

        self.aps_scheduler.add_listener(task_listener_add, EVENT_JOB_SUBMITTED)
        self.aps_scheduler.add_listener(task_listener_remove, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

        # configure all tasks
        self.__cache_cleanup_task()
        self.__check_health_task()
        self.update_configurable_tasks()

        self.aps_scheduler.start()

    def update_configurable_tasks(self):
        self.__sonarr_update_task()
        self.__radarr_update_task()
        self.__sonarr_full_update_task()
        self.__radarr_full_update_task()
        self.__update_bazarr_task()
        self.__search_wanted_subtitles_task()
        self.__upgrade_subtitles_task()
        self.__randomize_interval_task()
        self.__automatic_backup()
        if args.no_tasks:
            self.__no_task()

    def execute_job_now(self, taskid):
        self.aps_scheduler.modify_job(taskid, next_run_time=datetime.now())

    def get_running_tasks(self):
        return self.__running_tasks

    def get_task_list(self):
        def get_time_from_interval(td_object):
            seconds = int(td_object.total_seconds())
            periods = [
                ('year', 60 * 60 * 24 * 365),
                ('month', 60 * 60 * 24 * 30),
                ('day', 60 * 60 * 24),
                ('hour', 60 * 60),
                ('minute', 60),
                ('second', 1)
            ]
            if seconds > ONE_YEAR_IN_SECONDS:
                # more than a year is None
                return NO_INTERVAL
            strings = []
            for period_name, period_seconds in periods:
                if seconds > period_seconds:
                    period_value, seconds = divmod(seconds, period_seconds)
                    has_s = 's' if period_value > 1 else ''
                    strings.append("%s %s%s" % (period_value, period_name, has_s))

            return ", ".join(strings)

        def get_time_from_cron(cron):
            day = str(cron[4])
            hour = str(cron[5])

            if day == "*":
                text = "every day"
            else:
                text = f"every {day_name[int(day)]}"

            if hour != "*":
                text += f" at {hour}:00"

            return text

        task_list = []
        for job in self.aps_scheduler.get_jobs():
            next_run = NEVER_DATE
            if job.next_run_time:
                if a_long_time_from_now(job):
                    # Never for IntervalTrigger jobs
                    next_run = NEVER_DATE
                else:
                    next_run = pretty.date(job.next_run_time.replace(tzinfo=None))
            if isinstance(job.trigger, CronTrigger):
                if a_long_time_from_now(job):
                    # Never for CronTrigger jobs
                    next_run = NEVER_DATE
                else:
                    if job.next_run_time:
                        next_run = pretty.date(job.next_run_time.replace(tzinfo=None))

            if job.id in self.__running_tasks:
                running = True
            else:
                running = False

            if isinstance(job.trigger, IntervalTrigger):
                interval = get_time_from_interval(job.trigger.__getstate__()['interval'])
                if interval != NO_INTERVAL:
                    interval = f"every {interval}"
                # else:
                #     interval = "100 Year Interval"
                task_list.append({'name': job.name, 'interval': interval, 'next_run_in': next_run,
                                  'next_run_time': next_run, 'job_id': job.id, 'job_running': running})
            elif isinstance(job.trigger, CronTrigger):
                if a_long_time_from_now(job):
                    interval = NO_INTERVAL
                else:
                    interval = get_time_from_cron(job.trigger.fields)
                task_list.append({'name': job.name, 'interval': interval,
                                  'next_run_in': next_run, 'next_run_time': next_run, 'job_id': job.id,
                                  'job_running': running})

        return task_list

    def __sonarr_update_task(self):
        if settings.general.use_sonarr:
            self.aps_scheduler.add_job(
                update_series, 'interval', minutes=int(settings.sonarr.series_sync), max_instances=1,
                coalesce=True, misfire_grace_time=15, id='update_series', name='Sync with Sonarr',
                replace_existing=True)

    def __radarr_update_task(self):
        if settings.general.use_radarr:
            self.aps_scheduler.add_job(
                update_movies, 'interval', minutes=int(settings.radarr.movies_sync), max_instances=1,
                coalesce=True, misfire_grace_time=15, id='update_movies', name='Sync with Radarr',
                replace_existing=True)

    def __cache_cleanup_task(self):
        self.aps_scheduler.add_job(cache_maintenance, 'interval', hours=24, max_instances=1, coalesce=True,
                                   misfire_grace_time=15, id='cache_cleanup', name='Cache Maintenance')

    def __check_health_task(self):
        self.aps_scheduler.add_job(check_health, 'interval', hours=6, max_instances=1, coalesce=True,
                                   misfire_grace_time=15, id='check_health', name='Check Health')

    def __automatic_backup(self):
        backup = settings.backup.frequency
        if backup == "Daily":
            trigger = {'hour': settings.backup.hour}
        elif backup == "Weekly":
            trigger = {'day_of_week': settings.backup.day, 'hour': settings.backup.hour}
        else:
            trigger = {'year': in_a_century()}
        self.aps_scheduler.add_job(backup_to_zip, 'cron', **trigger,
                                   max_instances=1, coalesce=True, misfire_grace_time=15, id='backup',
                                   name='Backup Database and Configuration File', replace_existing=True)

    def __sonarr_full_update_task(self):
        if settings.general.use_sonarr:
            full_update = settings.sonarr.full_update
            if full_update == "Daily":
                self.aps_scheduler.add_job(
                    series_full_scan_subtitles, 'cron', hour=settings.sonarr.full_update_hour, max_instances=1,
                    coalesce=True, misfire_grace_time=15, id='series_full_scan_subtitles',
                    name='Index All Episode Subtitles from Disk', replace_existing=True)
            elif full_update == "Weekly":
                self.aps_scheduler.add_job(
                    series_full_scan_subtitles, 'cron', day_of_week=settings.sonarr.full_update_day,
                    hour=settings.sonarr.full_update_hour, max_instances=1, coalesce=True, misfire_grace_time=15,
                    id='series_full_scan_subtitles', name='Index All Episode Subtitles from Disk',
                    replace_existing=True)
            elif full_update == "Manually":
                self.aps_scheduler.add_job(
                    series_full_scan_subtitles, 'cron', year=in_a_century(), max_instances=1, coalesce=True,
                    misfire_grace_time=15, id='series_full_scan_subtitles',
                    name='Index All Episode Subtitles from Disk', replace_existing=True)

    def __radarr_full_update_task(self):
        if settings.general.use_radarr:
            full_update = settings.radarr.full_update
            if full_update == "Daily":
                self.aps_scheduler.add_job(
                    movies_full_scan_subtitles, 'cron', hour=settings.radarr.full_update_hour, max_instances=1,
                    coalesce=True, misfire_grace_time=15,
                    id='movies_full_scan_subtitles', name='Index All Movie Subtitles from Disk', replace_existing=True)
            elif full_update == "Weekly":
                self.aps_scheduler.add_job(
                    movies_full_scan_subtitles,
                    'cron', day_of_week=settings.radarr.full_update_day, hour=settings.radarr.full_update_hour,
                    max_instances=1, coalesce=True, misfire_grace_time=15, id='movies_full_scan_subtitles',
                    name='Index All Movie Subtitles from Disk', replace_existing=True)
            elif full_update == "Manually":
                self.aps_scheduler.add_job(
                    movies_full_scan_subtitles, 'cron', year=in_a_century(), max_instances=1, coalesce=True,
                    misfire_grace_time=15, id='movies_full_scan_subtitles', name='Index All Movie Subtitles from Disk',
                    replace_existing=True)

    def __update_bazarr_task(self):
        if not args.no_update and os.environ["BAZARR_VERSION"] != '':
            task_name = 'Update Bazarr'

            if settings.general.auto_update:
                self.aps_scheduler.add_job(
                    check_if_new_update, 'interval', hours=6, max_instances=1, coalesce=True,
                    misfire_grace_time=15, id='update_bazarr', name=task_name, replace_existing=True)
            else:
                self.aps_scheduler.add_job(
                    check_if_new_update, 'cron', year=in_a_century(), hour=4, id='update_bazarr', name=task_name,
                    replace_existing=True)
                self.aps_scheduler.add_job(
                    check_releases, 'interval', hours=3, max_instances=1, coalesce=True, misfire_grace_time=15,
                    id='update_release', name='Update Release Info', replace_existing=True)

        else:
            self.aps_scheduler.add_job(
                check_releases, 'interval', hours=3, max_instances=1, coalesce=True, misfire_grace_time=15,
                id='update_release', name='Update Release Info', replace_existing=True)

        self.aps_scheduler.add_job(
            get_announcements_to_file, 'interval', hours=6, max_instances=1, coalesce=True, misfire_grace_time=15,
            id='update_announcements', name='Update Announcements File', replace_existing=True)

    def __search_wanted_subtitles_task(self):
        if settings.general.use_sonarr:
            self.aps_scheduler.add_job(
                wanted_search_missing_subtitles_series, 'interval', hours=int(settings.general.wanted_search_frequency),
                max_instances=1, coalesce=True, misfire_grace_time=15, id='wanted_search_missing_subtitles_series',
                replace_existing=True, name='Search for Missing Series Subtitles')
        if settings.general.use_radarr:
            self.aps_scheduler.add_job(
                wanted_search_missing_subtitles_movies, 'interval',
                hours=int(settings.general.wanted_search_frequency_movie), max_instances=1, coalesce=True,
                misfire_grace_time=15, id='wanted_search_missing_subtitles_movies',
                name='Search for Missing Movies Subtitles', replace_existing=True)

    def __upgrade_subtitles_task(self):
        if settings.general.use_sonarr or settings.general.use_radarr:
            self.aps_scheduler.add_job(
                upgrade_subtitles, 'interval', hours=int(settings.general.upgrade_frequency), max_instances=1,
                coalesce=True, misfire_grace_time=15, id='upgrade_subtitles',
                name='Upgrade Previously Downloaded Subtitles', replace_existing=True)

    def __randomize_interval_task(self):
        for job in self.aps_scheduler.get_jobs():
            if isinstance(job.trigger, IntervalTrigger):
                # do not randomize the Never jobs
                if job.trigger.interval.total_seconds() > ONE_YEAR_IN_SECONDS:
                    continue
                self.aps_scheduler.modify_job(job.id,
                                              next_run_time=datetime.now(tz=self.timezone) +
                                              timedelta(seconds=randrange(
                                                  int(job.trigger.interval.total_seconds() * 0.75),
                                                  int(job.trigger.interval.total_seconds()))))

    def __no_task(self):
        for job in self.aps_scheduler.get_jobs():
            self.aps_scheduler.modify_job(job.id, next_run_time=None)


scheduler = Scheduler()

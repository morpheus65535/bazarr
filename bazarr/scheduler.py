# coding=utf-8
# pylama:ignore=E402

from get_episodes import sync_episodes, update_all_episodes
from get_movies import update_movies, update_all_movies
from get_series import update_series
from config import settings
from get_subtitle import wanted_search_missing_subtitles_series, wanted_search_missing_subtitles_movies, \
    upgrade_subtitles
from utils import cache_maintenance, check_health
from get_args import args
if not args.no_update:
    from check_update import check_if_new_update, check_releases
else:
    from check_update import check_releases
from apscheduler.schedulers.gevent import GeventScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.events import EVENT_JOB_SUBMITTED, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime, timedelta
from calendar import day_name
import pretty
from random import randrange
from event_handler import event_stream
import os


class Scheduler:

    def __init__(self):
        self.__running_tasks = []

        self.aps_scheduler = GeventScheduler()

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
        if args.no_tasks:
            self.__no_task()

    def add_job(self, job, name=None, max_instances=1, coalesce=True, args=None, kwargs=None):
        self.aps_scheduler.add_job(
            job, DateTrigger(run_date=datetime.now()), name=name, id=name, max_instances=max_instances,
            coalesce=coalesce, args=args, kwargs=kwargs)

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

            strings = []
            for period_name, period_seconds in periods:
                if seconds > period_seconds:
                    period_value, seconds = divmod(seconds, period_seconds)
                    has_s = 's' if period_value > 1 else ''
                    strings.append("%s %s%s" % (period_value, period_name, has_s))

            return ", ".join(strings)

        def get_time_from_cron(cron):
            year = str(cron[0])
            if year == "2100":
                return "Never"

            day = str(cron[4])
            hour = str(cron[5])

            if day == "*":
                text = "everyday"
            else:
                text = "every " + day_name[int(day)]

            if hour != "*":
                text += " at " + hour + ":00"

            return text

        task_list = []
        for job in self.aps_scheduler.get_jobs():
            next_run = 'Never'
            if job.next_run_time:
                next_run = pretty.date(job.next_run_time.replace(tzinfo=None))
            if isinstance(job.trigger, CronTrigger):
                if job.next_run_time and str(job.trigger.__getstate__()['fields'][0]) != "2100":
                    next_run = pretty.date(job.next_run_time.replace(tzinfo=None))

            if job.id in self.__running_tasks:
                running = True
            else:
                running = False

            if isinstance(job.trigger, IntervalTrigger):
                interval = "every " + get_time_from_interval(job.trigger.__getstate__()['interval'])
                task_list.append({'name': job.name, 'interval': interval, 'next_run_in': next_run,
                                  'next_run_time': next_run, 'job_id': job.id, 'job_running': running})
            elif isinstance(job.trigger, CronTrigger):
                task_list.append({'name': job.name, 'interval': get_time_from_cron(job.trigger.fields),
                                  'next_run_in': next_run, 'next_run_time': next_run, 'job_id': job.id,
                                  'job_running': running})

        return task_list

    def __sonarr_update_task(self):
        if settings.general.getboolean('use_sonarr'):
            self.aps_scheduler.add_job(
                update_series, IntervalTrigger(minutes=int(settings.sonarr.series_sync)), max_instances=1,
                coalesce=True, misfire_grace_time=15, id='update_series', name='Update Series list from Sonarr',
                replace_existing=True)
            self.aps_scheduler.add_job(
                sync_episodes, IntervalTrigger(minutes=int(settings.sonarr.episodes_sync)), max_instances=1,
                coalesce=True, misfire_grace_time=15, id='sync_episodes', name='Sync episodes with Sonarr',
                replace_existing=True)

    def __radarr_update_task(self):
        if settings.general.getboolean('use_radarr'):
            self.aps_scheduler.add_job(
                update_movies, IntervalTrigger(minutes=int(settings.radarr.movies_sync)), max_instances=1,
                coalesce=True, misfire_grace_time=15, id='update_movies', name='Update Movie list from Radarr',
                replace_existing=True)

    def __cache_cleanup_task(self):
        self.aps_scheduler.add_job(cache_maintenance, IntervalTrigger(hours=24), max_instances=1, coalesce=True,
                                   misfire_grace_time=15, id='cache_cleanup', name='Cache maintenance')

    def __check_health_task(self):
        self.aps_scheduler.add_job(check_health, IntervalTrigger(hours=6), max_instances=1, coalesce=True,
                                   misfire_grace_time=15, id='check_health', name='Check health')

    def __sonarr_full_update_task(self):
        if settings.general.getboolean('use_sonarr'):
            full_update = settings.sonarr.full_update
            if full_update == "Daily":
                self.aps_scheduler.add_job(
                    update_all_episodes, CronTrigger(hour=settings.sonarr.full_update_hour), max_instances=1,
                    coalesce=True, misfire_grace_time=15, id='update_all_episodes',
                    name='Update all Episode Subtitles from disk', replace_existing=True)
            elif full_update == "Weekly":
                self.aps_scheduler.add_job(
                    update_all_episodes,
                    CronTrigger(day_of_week=settings.sonarr.full_update_day, hour=settings.sonarr.full_update_hour),
                    max_instances=1, coalesce=True, misfire_grace_time=15, id='update_all_episodes',
                    name='Update all Episode Subtitles from disk', replace_existing=True)
            elif full_update == "Manually":
                self.aps_scheduler.add_job(
                    update_all_episodes, CronTrigger(year='2100'), max_instances=1, coalesce=True,
                    misfire_grace_time=15, id='update_all_episodes',
                    name='Update all Episode Subtitles from disk', replace_existing=True)

    def __radarr_full_update_task(self):
        if settings.general.getboolean('use_radarr'):
            full_update = settings.radarr.full_update
            if full_update == "Daily":
                self.aps_scheduler.add_job(
                    update_all_movies, CronTrigger(hour=settings.radarr.full_update_hour), max_instances=1,
                    coalesce=True, misfire_grace_time=15,
                    id='update_all_movies', name='Update all Movie Subtitles from disk', replace_existing=True)
            elif full_update == "Weekly":
                self.aps_scheduler.add_job(
                    update_all_movies,
                    CronTrigger(day_of_week=settings.radarr.full_update_day, hour=settings.radarr.full_update_hour),
                    max_instances=1, coalesce=True, misfire_grace_time=15, id='update_all_movies',
                    name='Update all Movie Subtitles from disk', replace_existing=True)
            elif full_update == "Manually":
                self.aps_scheduler.add_job(
                    update_all_movies, CronTrigger(year='2100'), max_instances=1, coalesce=True, misfire_grace_time=15,
                    id='update_all_movies', name='Update all Movie Subtitles from disk', replace_existing=True)

    def __update_bazarr_task(self):
        if not args.no_update and os.environ["BAZARR_VERSION"] != '':
            task_name = 'Update Bazarr'

            if settings.general.getboolean('auto_update'):
                self.aps_scheduler.add_job(
                    check_if_new_update, IntervalTrigger(hours=6), max_instances=1, coalesce=True,
                    misfire_grace_time=15, id='update_bazarr', name=task_name, replace_existing=True)
            else:
                self.aps_scheduler.add_job(
                    check_if_new_update, CronTrigger(year='2100'), hour=4, id='update_bazarr', name=task_name,
                    replace_existing=True)
                self.aps_scheduler.add_job(
                    check_releases, IntervalTrigger(hours=3), max_instances=1, coalesce=True, misfire_grace_time=15,
                    id='update_release', name='Update Release Info', replace_existing=True)

        else:
            self.aps_scheduler.add_job(
                check_releases, IntervalTrigger(hours=3), max_instances=1, coalesce=True, misfire_grace_time=15,
                id='update_release', name='Update Release Info', replace_existing=True)

    def __search_wanted_subtitles_task(self):
        if settings.general.getboolean('use_sonarr'):
            self.aps_scheduler.add_job(
                wanted_search_missing_subtitles_series, IntervalTrigger(hours=int(settings.general.wanted_search_frequency)),
                max_instances=1, coalesce=True, misfire_grace_time=15, id='wanted_search_missing_subtitles_series',
                name='Search for wanted Series Subtitles', replace_existing=True)
        if settings.general.getboolean('use_radarr'):
            self.aps_scheduler.add_job(
                wanted_search_missing_subtitles_movies, IntervalTrigger(hours=int(settings.general.wanted_search_frequency_movie)),
                max_instances=1, coalesce=True, misfire_grace_time=15, id='wanted_search_missing_subtitles_movies',
                name='Search for wanted Movies Subtitles', replace_existing=True)

    def __upgrade_subtitles_task(self):
        if settings.general.getboolean('upgrade_subs') and \
                (settings.general.getboolean('use_sonarr') or settings.general.getboolean('use_radarr')):
            self.aps_scheduler.add_job(
                upgrade_subtitles, IntervalTrigger(hours=int(settings.general.upgrade_frequency)), max_instances=1,
                coalesce=True, misfire_grace_time=15, id='upgrade_subtitles',
                name='Upgrade previously downloaded Subtitles', replace_existing=True)

    def __randomize_interval_task(self):
        for job in self.aps_scheduler.get_jobs():
            if isinstance(job.trigger, IntervalTrigger):
                self.aps_scheduler.modify_job(job.id, next_run_time=datetime.now() + timedelta(seconds=randrange(job.trigger.interval.total_seconds()*0.75, job.trigger.interval.total_seconds())))

    def __no_task(self):
        for job in self.aps_scheduler.get_jobs():
            self.aps_scheduler.modify_job(job.id, next_run_time=None)


scheduler = Scheduler()

# Force the execution of the sync process with Sonarr and Radarr after migration to v0.9.1
if 'BAZARR_AUDIO_PROFILES_MIGRATION' in os.environ:
    if settings.general.getboolean('use_sonarr'):
        scheduler.aps_scheduler.modify_job('update_series', next_run_time=datetime.now())
        scheduler.aps_scheduler.modify_job('sync_episodes', next_run_time=datetime.now())
    if settings.general.getboolean('use_radarr'):
        scheduler.aps_scheduler.modify_job('update_movies', next_run_time=datetime.now())
    del os.environ['BAZARR_AUDIO_PROFILES_MIGRATION']

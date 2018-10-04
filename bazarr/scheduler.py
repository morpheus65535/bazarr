from get_argv import no_update

from get_settings import get_general_settings, automatic, get_radarr_settings, get_sonarr_settings
from get_series import update_series
from get_episodes import update_all_episodes, update_all_movies, sync_episodes
from get_movies import update_movies
from list_subtitles import store_subtitles
from get_subtitle import wanted_search_missing_subtitles
if no_update is False:
    from check_update import check_and_apply_update

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
from tzlocal import get_localzone

integration = get_general_settings()


def sonarr_full_update():
    if integration[12] is True:
        full_update = get_sonarr_settings()[5]
        if full_update == "Daily":
            scheduler.add_job(update_all_episodes, CronTrigger(hour=4), max_instances=1, coalesce=True,
                          misfire_grace_time=15, id='update_all_episodes',
                          name='Update all episodes subtitles from disk', replace_existing=True)
        elif full_update == "Weekly":
            scheduler.add_job(update_all_episodes, CronTrigger(day_of_week='sun'), hour=4, max_instances=1, coalesce=True,
                          misfire_grace_time=15, id='update_all_episodes',
                          name='Update all episodes subtitles from disk', replace_existing=True)
        elif full_update == "Manually":
            scheduler.add_job(update_all_episodes, CronTrigger(year='2100'), hour=4, max_instances=1, coalesce=True,
                          misfire_grace_time=15, id='update_all_episodes',
                          name='Update all episodes subtitles from disk', replace_existing=True)


def radarr_full_update():
    if integration[13] is True:
        full_update = get_radarr_settings()[5]
        if full_update == "Daily":
            scheduler.add_job(update_all_movies, CronTrigger(hour=5), max_instances=1, coalesce=True, misfire_grace_time=15,
                          id='update_all_movies', name='Update all movies subtitles from disk', replace_existing=True)
        elif full_update == "Weekly":
            scheduler.add_job(update_all_movies, CronTrigger(day_of_week='sun'), hour=5, max_instances=1, coalesce=True,
                          misfire_grace_time=15, id='update_all_movies', name='Update all movies subtitles from disk',
                          replace_existing=True)
        elif full_update == "Manually":
            scheduler.add_job(update_all_movies, CronTrigger(year='2100'), hour=5, max_instances=1, coalesce=True,
                          misfire_grace_time=15, id='update_all_movies', name='Update all movies subtitles from disk',
                          replace_existing=True)


def execute_now(taskid):
    scheduler.modify_job(taskid, next_run_time=datetime.now())


if str(get_localzone()) == "local":
    scheduler = BackgroundScheduler(timezone=pytz.timezone('UTC'))
else:
    scheduler = BackgroundScheduler()

if no_update is False:
    if automatic is True:
        scheduler.add_job(check_and_apply_update, IntervalTrigger(hours=6), max_instances=1, coalesce=True, misfire_grace_time=15, id='update_bazarr', name='Update bazarr from source on Github')
    else:
        scheduler.add_job(check_and_apply_update, CronTrigger(year='2100'), hour=4, id='update_bazarr', name='Update bazarr from source on Github')

if integration[12] is True:
    scheduler.add_job(update_series, IntervalTrigger(minutes=1), max_instances=1, coalesce=True, misfire_grace_time=15, id='update_series', name='Update series list from Sonarr')
    scheduler.add_job(sync_episodes, IntervalTrigger(minutes=5), max_instances=1, coalesce=True, misfire_grace_time=15, id='sync_episodes', name='Sync episodes with Sonarr')

if integration[13] is True:
    scheduler.add_job(update_movies, IntervalTrigger(minutes=5), max_instances=1, coalesce=True, misfire_grace_time=15, id='update_movies', name='Update movies list from Radarr')

if integration[12] is True or integration[13] is True:
    scheduler.add_job(wanted_search_missing_subtitles, IntervalTrigger(hours=3), max_instances=1, coalesce=True, misfire_grace_time=15, id='wanted_search_missing_subtitles', name='Search for wanted subtitles')

sonarr_full_update()
radarr_full_update()
scheduler.start()

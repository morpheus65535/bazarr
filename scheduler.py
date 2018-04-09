from get_general_settings import *
from get_sonarr_settings import get_sonarr_settings
from get_series import *
from get_episodes import *
from list_subtitles import *
from get_subtitle import *
from check_update import *

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz
from tzlocal import get_localzone


def sonarr_full_update():
    full_update = get_sonarr_settings()[3]
    if full_update == "Daily":
        scheduler.add_job(update_all_episodes, 'cron', hour=4, max_instances=1, coalesce=True, misfire_grace_time=15, id='update_all_episodes', name='Update all episodes from Sonarr', replace_existing=True)
    elif full_update == "Weekly":
        scheduler.add_job(update_all_episodes, 'cron', day_of_week='sun', hour=4, max_instances=1, coalesce=True, misfire_grace_time=15, id='update_all_episodes', name='Update all episodes from Sonarr', replace_existing=True)
    elif full_update == "Manually":
        scheduler.add_job(update_all_episodes, 'cron', year='2100', hour=4, max_instances=1, coalesce=True, misfire_grace_time=15, id='update_all_episodes', name='Update all episodes from Sonarr', replace_existing=True)

def execute_now(taskid):
    scheduler.modify_job(taskid, jobstore=None, next_run_time=datetime.now())


if str(get_localzone()) == "local":
    scheduler = BackgroundScheduler(timezone=pytz.timezone('UTC'))
else:
    scheduler = BackgroundScheduler()

if automatic == 'True':
    scheduler.add_job(check_and_apply_update, 'interval', hours=6, max_instances=1, coalesce=True, misfire_grace_time=15, id='update_bazarr', name='Update bazarr from source on Github')
else:
    scheduler.add_job(check_and_apply_update, 'cron', year='2100', hour=4, id='update_bazarr', name='Update bazarr from source on Github')
scheduler.add_job(update_series, 'interval', minutes=1, max_instances=1, coalesce=True, misfire_grace_time=15, id='update_series', name='Update series list from Sonarr')
scheduler.add_job(sync_episodes, 'interval', minutes=5, max_instances=1, coalesce=True, misfire_grace_time=15, id='sync_episodes', name='Sync episodes with Sonarr')
scheduler.add_job(wanted_search_missing_subtitles, 'interval', hours=3, max_instances=1, coalesce=True, misfire_grace_time=15, id='wanted_search_missing_subtitles', name='Search for wanted subtitles')
sonarr_full_update()
scheduler.start()
from get_general_settings import *
from get_series import *
from get_episodes import *
from list_subtitles import *
from get_subtitle import *
from check_update import *

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

scheduler = BackgroundScheduler()
if automatic == 'True':
    scheduler.add_job(check_and_apply_update, 'interval', hours=6, max_instances=1, coalesce=True, id='update_bazarr', name='Update bazarr from source on Github')
scheduler.add_job(update_series, 'interval', minutes=1, max_instances=1, coalesce=True, id='update_series', name='Update series list from Sonarr')
scheduler.add_job(add_new_episodes, 'interval', minutes=1, max_instances=1, coalesce=True, id='add_new_episodes', name='Add new episodes from Sonarr')
scheduler.add_job(update_all_episodes, 'cron', hour=4, max_instances=1, coalesce=True, id='update_all_episodes', name='Update all episodes from Sonarr')
scheduler.add_job(list_missing_subtitles, 'interval', minutes=5, max_instances=1, coalesce=True, id='list_missing_subtitles', name='Process missing subtitles for all series')
scheduler.add_job(wanted_search_missing_subtitles, 'interval', hours=3, max_instances=1, coalesce=True, id='wanted_search_missing_subtitles', name='Search for wanted subtitles')
scheduler.start()

def execute_now(taskid):
    scheduler.modify_job(taskid, jobstore=None, next_run_time=datetime.now())

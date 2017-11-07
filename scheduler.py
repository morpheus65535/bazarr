from get_series import *
from get_episodes import *
from get_subtitle import *

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(update_bazarr, 'interval', hours=6, max_instances=1, coalesce=True, id='update_bazarr', name='Update bazarr from source on Github')
scheduler.add_job(update_series, 'interval', minutes=1, max_instances=1, coalesce=True, id='update_series', name='Update series list from Sonarr')
scheduler.add_job(add_new_episodes, 'interval', minutes=1, max_instances=1, coalesce=True, id='add_new_episodes', name='Add new episodes from Sonarr')
scheduler.add_job(wanted_search_missing_subtitles, 'interval', minutes=15, max_instances=1, coalesce=True, id='wanted_search_missing_subtitles', name='Search for wanted subtitles')
scheduler.start()

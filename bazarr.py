# coding: utf-8 
from __future__ import unicode_literals

bazarr_version = '0.1.4'

from bottle import route, run, template, static_file, request, redirect
import bottle
bottle.debug(True)
bottle.TEMPLATES.clear()

import os
bottle.TEMPLATE_PATH.insert(0,os.path.join(os.path.dirname(__file__), 'views/'))

import sqlite3
import itertools
import operator
import requests
import pycountry
import pretty
import datetime
from PIL import Image
from io import BytesIO
from fdsend import send_file
import urllib

from init_db import *
from get_languages import *
from get_providers import *

from get_series import *
from get_episodes import *
from get_general_settings import *
from get_sonarr_settings import *
from check_update import *
from list_subtitles import *
from get_subtitle import *
from utils import *
from scheduler import *

import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger('waitress')
db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'))
c = db.cursor()
c.execute("SELECT log_level FROM table_settings_general")
log_level = c.fetchone()
log_level = log_level[0]
if log_level is None:
    log_level = "INFO"
log_level = getattr(logging, log_level)
c.close()

class OneLineExceptionFormatter(logging.Formatter):
    def formatException(self, exc_info):
        """
        Format an exception so that it prints on a single line.
        """
        result = super(OneLineExceptionFormatter, self).formatException(exc_info)
        return repr(result) # or format into one line however you want to

    def format(self, record):
        s = super(OneLineExceptionFormatter, self).format(record)
        if record.exc_text:
            s = s.replace('\n', '') + '|'
        return s

def configure_logging():
    fh = TimedRotatingFileHandler(os.path.join(os.path.dirname(__file__), 'data/log/bazarr.log'), when="midnight", interval=1, backupCount=7)
    f = OneLineExceptionFormatter('%(asctime)s|%(levelname)s|%(message)s|',
                                  '%d/%m/%Y %H:%M:%S')
    fh.setFormatter(f)
    logging.getLogger("enzyme").setLevel(logging.ERROR)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("subliminal").setLevel(logging.ERROR)
    root = logging.getLogger()
    root.setLevel(log_level)
    root.addHandler(fh)

configure_logging()

@route('/')
def redirect_root():
    redirect (base_url)

@route(base_url + 'static/:path#.+#', name='static')
def static(path):
    return static_file(path, root=os.path.join(os.path.dirname(__file__), 'static'))

@route(base_url + 'image_proxy/<url:path>', method='GET')
def image_proxy(url):
    img_pil = Image.open(BytesIO(requests.get(url_sonarr_short + '/' + url).content))
    img_buffer = BytesIO()
    img_pil.tobytes()
    img_pil.save(img_buffer, img_pil.format)
    img_buffer.seek(0)
    return send_file(img_buffer, ctype=img_pil.format)

@route(base_url)
def series():
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'))
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()
    c.execute("SELECT tvdbId, title, path_substitution(path), languages, hearing_impaired, sonarrSeriesId, poster FROM table_shows ORDER BY title")
    data = c.fetchall()
    c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1")
    languages = c.fetchall()
    c.close()
    output = template('series', rows=data, languages=languages, base_url=base_url)
    return output

@route(base_url + 'edit_series/<no:int>', method='POST')
def edit_series(no):
    ref = request.environ['HTTP_REFERER']

    lang = request.forms.getall('languages')
    if len(lang) > 0:
        if lang[0] == '':
            lang = None
        else:
            pass
    else:
        lang = None
    hi = request.forms.get('hearing_impaired')

    if hi == "on":
        hi = "True"
    else:
        hi = "False"

    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'))
    c = conn.cursor()
    c.execute("UPDATE table_shows SET languages = ?, hearing_impaired = ? WHERE tvdbId LIKE ?", (str(lang), hi, no))
    conn.commit()
    c.close()

    list_missing_subtitles(no)

    redirect(ref)

@route(base_url + 'episodes/<no:int>', method='GET')
def episodes(no):
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'))
    conn.create_function("path_substitution", 1, path_replace)
    c = conn.cursor()

    series_details = []
    series_details = c.execute("SELECT title, overview, poster, fanart, hearing_impaired, tvdbid FROM table_shows WHERE sonarrSeriesId LIKE ?", (str(no),)).fetchone()
    tvdbid = series_details[5]

    episodes = c.execute("SELECT title, path_substitution(path), season, episode, subtitles, sonarrSeriesId, missing_subtitles, sonarrEpisodeId FROM table_episodes WHERE sonarrSeriesId LIKE ? ORDER BY episode ASC", (str(no),)).fetchall()
    episodes = reversed(sorted(episodes, key=operator.itemgetter(2)))
    seasons_list = []
    for key,season in itertools.groupby(episodes,operator.itemgetter(2)):
        seasons_list.append(list(season))
    c.close()
    
    return template('episodes', no=no, details=series_details, seasons=seasons_list, url_sonarr_short=url_sonarr_short, base_url=base_url, tvdbid=tvdbid)

@route(base_url + 'scan_disk/<no:int>', method='GET')
def scan_disk(no):
    ref = request.environ['HTTP_REFERER']

    series_scan_subtitles(no)

    redirect(ref)

@route(base_url + 'search_missing_subtitles/<no:int>', method='GET')
def search_missing_subtitles(no):
    ref = request.environ['HTTP_REFERER']

    series_download_subtitles(no)

    redirect(ref)

@route(base_url + 'history')
def history():
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'))
    c = db.cursor()
    
    c.execute("SELECT COUNT(*) FROM table_history")
    row_count = c.fetchone()
    row_count = row_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    offset = (int(page) - 1) * 15
    max_page = (row_count / 15) + 1

    c.execute("SELECT table_history.action, table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, table_history.timestamp, table_history.description, table_history.sonarrSeriesId FROM table_history INNER JOIN table_shows on table_shows.sonarrSeriesId = table_history.sonarrSeriesId INNER JOIN table_episodes on table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId ORDER BY id DESC LIMIT 15 OFFSET ?", (offset,))
    data = c.fetchall()
    data = reversed(sorted(data, key=operator.itemgetter(4)))
    c.close()
    return template('history', rows=data, row_count=row_count, page=page, max_page=max_page, base_url=base_url)

@route(base_url + 'wanted')
def wanted():
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'))
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM table_episodes WHERE missing_subtitles != '[]'")
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    offset = (int(page) - 1) * 15
    max_page = (missing_count / 15) + 1

    c.execute("SELECT table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, table_episodes.missing_subtitles, table_episodes.sonarrSeriesId, path_substitution(table_episodes.path), table_shows.hearing_impaired, table_episodes.sonarrEpisodeId FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE table_episodes.missing_subtitles != '[]' ORDER BY table_episodes._rowid_ DESC LIMIT 15 OFFSET ?", (offset,))
    data = c.fetchall()
    c.close()
    return template('wanted', rows=data, missing_count=missing_count, page=page, max_page=max_page, base_url=base_url)

@route(base_url + 'wanted_search_missing_subtitles')
def wanted_search_missing_subtitles_list():
    ref = request.environ['HTTP_REFERER']

    wanted_search_missing_subtitles()
    
    redirect(ref)

@route(base_url + 'settings')
def settings():
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'))
    c = db.cursor()
    c.execute("SELECT * FROM table_settings_general")
    settings_general = c.fetchone()
    c.execute("SELECT * FROM table_settings_languages ORDER BY name")
    settings_languages = c.fetchall()
    c.execute("SELECT * FROM table_settings_providers ORDER BY name")
    settings_providers = c.fetchall()
    c.execute("SELECT * FROM table_settings_sonarr")
    settings_sonarr = c.fetchone()
    c.close()
    return template('settings', settings_general=settings_general, settings_languages=settings_languages, settings_providers=settings_providers, settings_sonarr=settings_sonarr, base_url=base_url)

@route(base_url + 'save_settings', method='POST')
def save_settings():
    ref = request.environ['HTTP_REFERER']

    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'))
    c = conn.cursor()    

    settings_general_ip = request.forms.get('settings_general_ip')
    settings_general_port = request.forms.get('settings_general_port')
    settings_general_baseurl = request.forms.get('settings_general_baseurl')
    settings_general_loglevel = request.forms.get('settings_general_loglevel')
    settings_general_sourcepath = request.forms.getall('settings_general_sourcepath')
    settings_general_destpath = request.forms.getall('settings_general_destpath')
    settings_general_pathmapping = []
    settings_general_pathmapping.extend([list(a) for a in zip(settings_general_sourcepath, settings_general_destpath)])
    settings_general_branch = request.forms.get('settings_general_branch')
    settings_general_automatic = request.forms.get('settings_general_automatic')
    if settings_general_automatic is None:
        settings_general_automatic = 'False'
    else:
        settings_general_automatic = 'True'
    c.execute("UPDATE table_settings_general SET ip = ?, port = ?, base_url = ?, path_mapping = ?, log_level = ?, branch=?, auto_update=?", (settings_general_ip, settings_general_port, settings_general_baseurl, str(settings_general_pathmapping), settings_general_loglevel, settings_general_branch, settings_general_automatic))
    
    settings_sonarr_ip = request.forms.get('settings_sonarr_ip')
    settings_sonarr_port = request.forms.get('settings_sonarr_port')
    settings_sonarr_baseurl = request.forms.get('settings_sonarr_baseurl')
    settings_sonarr_ssl = request.forms.get('settings_sonarr_ssl')
    if settings_sonarr_ssl is None:
        settings_sonarr_ssl = 'False'
    else:
        settings_sonarr_ssl = 'True'
    settings_sonarr_apikey = request.forms.get('settings_sonarr_apikey')
    c.execute("UPDATE table_settings_sonarr SET ip = ?, port = ?, base_url = ?, ssl = ?, apikey = ?", (settings_sonarr_ip, settings_sonarr_port, settings_sonarr_baseurl, settings_sonarr_ssl, settings_sonarr_apikey))
    
    settings_subliminal_providers = request.forms.getall('settings_subliminal_providers')
    c.execute("UPDATE table_settings_providers SET enabled = 0")
    for item in settings_subliminal_providers:
        c.execute("UPDATE table_settings_providers SET enabled = '1' WHERE name = ?", (item,))
    settings_subliminal_languages = request.forms.getall('settings_subliminal_languages')
    c.execute("UPDATE table_settings_languages SET enabled = 0")
    for item in settings_subliminal_languages:
        c.execute("UPDATE table_settings_languages SET enabled = '1' WHERE code2 = ?", (item,))
    
    conn.commit()
    c.close()
    
    redirect(ref)

@route(base_url + 'check_update')
def check_update():
    ref = request.environ['HTTP_REFERER']

    result = check_and_apply_update()
    logging.info(result)
    
    redirect(ref)

@route(base_url + 'system')
def system():
    def get_time_from_interval(interval):
        interval_clean = interval.split('[')
        interval_clean = interval_clean[1][:-1]
        interval_split = interval_clean.split(':')

        hour = interval_split[0]
        minute = interval_split[1].lstrip("0")
        second = interval_split[2].lstrip("0")

        text = "every "
        if hour != "0":
            text = text + hour
            if hour == "1":
                text = text + " hour"
            else:
                text = text + " hours"
                
            if minute != "" and second != "":
                text = text + ", "
            elif minute == "" and second != "":
                text = text + " and "
            elif minute != "" and second == "":
                text = text + " and "
        if minute != "":
            text = text + minute
            if minute == "1":
                text = text + " minute"
            else:
                text = text + " minutes"
                
            if second != "":
                text = text + " and "
        if second != "":
            text = text + second
            if second == "1":
                text = text + " second"
            else:
                text = text + " seconds"

        return text

    def get_time_from_cron(cron):
        text = "at "
        hour = str(cron[5])
        minute = str(cron[6])
        second = str(cron[7])
        
        if hour != "0" and hour != "*":
            text = text + hour
            if hour == "0" or hour == "1":
                text = text + " hour"
            else:
                text = text + " hours"
                
            if minute != "*" and second != "0":
                text = text + ", "
            elif minute == "*" and second != "0":
                text = text + " and "
            elif minute != "0" and minute != "*" and second == "0":
                text = text + " and "
        if minute != "0" and minute != "*":
            text = text + minute
            if minute == "0" or minute == "1":
                text = text + " minute"
            else:
                text = text + " minutes"
                
            if second != "0" and second != "*":
                text = text + " and "
        if second != "0" and second != "*":
            text = text + second
            if second == "0" or second == "1":
                text = text + " second"
            else:
                text = text + " seconds"

        return text
    

    task_list = []
    for job in scheduler.get_jobs():
        if job.trigger.__str__().startswith('interval'):
            task_list.append([job.name, get_time_from_interval(str(job.trigger)), pretty.date(job.next_run_time.replace(tzinfo=None)), job.id])
        elif job.trigger.__str__().startswith('cron'):
            task_list.append([job.name, get_time_from_cron(job.trigger.fields), pretty.date(job.next_run_time.replace(tzinfo=None)), job.id])

    with open(os.path.join(os.path.dirname(__file__), 'data/log/bazarr.log')) as f:
        for i, l in enumerate(f, 1):
            pass
        row_count = i
        max_page = (row_count / 50) + 1
    
    return template('system', base_url=base_url, task_list=task_list, row_count=row_count, max_page=max_page, bazarr_version=bazarr_version)

@route(base_url + 'logs/<page:int>')
def get_logs(page):
    page_size = 50
    begin = (page * page_size) - page_size
    end = (page * page_size) - 1
    logs_complete = []
    for line in reversed(open(os.path.join(os.path.dirname(__file__), 'data/log/bazarr.log')).readlines()):
        logs_complete.append(line.rstrip())
    logs = logs_complete[begin:end]

    return template('logs', logs=logs, base_url=base_url)

@route(base_url + 'execute/<taskid>')
def execute_task(taskid):
    ref = request.environ['HTTP_REFERER']

    execute_now(taskid)
    
    redirect(ref)

@route(base_url + 'remove_subtitles', method='POST')
def remove_subtitles():
        episodePath = request.forms.get('episodePath')
        language = request.forms.get('language')
        subtitlesPath = request.forms.get('subtitlesPath')
        sonarrSeriesId = request.forms.get('sonarrSeriesId')
        sonarrEpisodeId = request.forms.get('sonarrEpisodeId')
        tvdbid = request.forms.get('tvdbid')

        try:
            os.remove(subtitlesPath)
            result = pycountry.languages.lookup(language).name + " subtitles deleted from disk."
            history_log(0, sonarrSeriesId, sonarrEpisodeId, result)
        except OSError:
            pass
        store_subtitles(episodePath)
        list_missing_subtitles(sonarrSeriesId)
        
@route(base_url + 'get_subtitle', method='POST')
def get_subtitle():
        ref = request.environ['HTTP_REFERER']

        episodePath = request.forms.get('episodePath')
        language = request.forms.get('language')
        hi = request.forms.get('hi')
        sonarrSeriesId = request.forms.get('sonarrSeriesId')
        sonarrEpisodeId = request.forms.get('sonarrEpisodeId')
        tvdbid = request.forms.get('tvdbid')

        db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'))
        c = db.cursor()
        c.execute("SELECT name FROM table_settings_providers WHERE enabled = 1")
        providers = c.fetchall()
        c.close()

        providers_list = []
        for provider in providers:
            providers_list.append(provider[0])
        
        try:
            result = download_subtitle(episodePath, language, hi, providers_list)
            if result is not None:
                history_log(1, sonarrSeriesId, sonarrEpisodeId, result)
                store_subtitles(episodePath)
                list_missing_subtitles(sonarrSeriesId)
            redirect(ref)
        except OSError:
            pass

run(host=ip, port=port, server='waitress')

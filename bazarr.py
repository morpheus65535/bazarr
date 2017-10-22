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
from list_subtitles import *
from get_subtitle import *
from utils import *

import logging
from logging.handlers import TimedRotatingFileHandler
logger = logging.getLogger('waitress')
db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'))
c = db.cursor()
c.execute("SELECT log_level FROM table_settings_general")
log_level = c.fetchone()
log_level = log_level[0]
if log_level is None:
    log_level = "WARNING"
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
    root = logging.getLogger()
    root.setLevel(log_level)
    root.addHandler(fh)

configure_logging()

@route(base_url + '/static/:path#.+#', name='static')
def static(path):
    return static_file(path, root='static')

@route(base_url + '/image_proxy/<url:path>', method='GET')
def image_proxy(url):
    img_pil = Image.open(BytesIO(requests.get(url_sonarr_short + '/' + url).content))
    img_buffer = BytesIO()
    img_pil.tobytes()
    img_pil.save(img_buffer, img_pil.format)
    img_buffer.seek(0)
    return send_file(img_buffer, ctype=img_pil.format)

@route(base_url + '/')
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

@route(base_url + '/edit_series/<no:int>', method='POST')
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

@route(base_url + '/update_series')
def update_series_list():
    ref = request.environ['HTTP_REFERER']

    update_series()

    redirect(ref)

@route(base_url + '/update_all_episodes')
def update_all_episodes_list():
    ref = request.environ['HTTP_REFERER']

    update_all_episodes()

    redirect(ref)

@route(base_url + '/add_new_episodes')
def add_new_episodes_list():
    ref = request.environ['HTTP_REFERER']

    add_new_episodes()

    redirect(ref)

@route(base_url + '/episodes/<no:int>', method='GET')
def episodes(no):
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'))
    conn.create_function("path_substitution", 1, path_replace)
    c = conn.cursor()

    series_details = []
    series_details = c.execute("SELECT title, overview, poster, fanart, hearing_impaired FROM table_shows WHERE sonarrSeriesId LIKE ?", (str(no),)).fetchone()

    episodes = c.execute("SELECT title, path_substitution(path), season, episode, subtitles, sonarrSeriesId, missing_subtitles, sonarrEpisodeId FROM table_episodes WHERE sonarrSeriesId LIKE ? ORDER BY episode ASC", (str(no),)).fetchall()
    episodes = reversed(sorted(episodes, key=operator.itemgetter(2)))
    seasons_list = []
    for key,season in itertools.groupby(episodes,operator.itemgetter(2)):
        seasons_list.append(list(season))
    c.close()
    
    return template('episodes', no=no, details=series_details, seasons=seasons_list, url_sonarr_short=url_sonarr_short, base_url=base_url)

@route(base_url + '/scan_disk/<no:int>', method='GET')
def scan_disk(no):
    ref = request.environ['HTTP_REFERER']

    series_scan_subtitles(no)

    redirect(ref)

@route(base_url + '/search_missing_subtitles/<no:int>', method='GET')
def search_missing_subtitles(no):
    ref = request.environ['HTTP_REFERER']

    series_download_subtitles(no)

    redirect(ref)

@route(base_url + '/history')
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

@route(base_url + '/wanted')
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

@route(base_url + '/wanted_search_missing_subtitles')
def wanted_search_missing_subtitles():
    ref = request.environ['HTTP_REFERER']

    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'))
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()

    c.execute("SELECT path_substitution(path) FROM table_episodes WHERE table_episodes.missing_subtitles != '[]'")
    data = c.fetchall()
    c.close()

    for episode in data:
        wanted_download_subtitles(episode[0])
    
    redirect(ref)

@route(base_url + '/settings')
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

@route(base_url + '/save_settings', method='POST')
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
    c.execute("UPDATE table_settings_general SET ip = ?, port = ?, base_url = ?, path_mapping = ?, log_level = ?", (settings_general_ip, settings_general_port, settings_general_baseurl, str(settings_general_pathmapping), settings_general_loglevel))
    
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

@route(base_url + '/system')
def system():
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'))
    c = db.cursor()
    c.execute("SELECT * FROM table_scheduler")
    tasks = c.fetchall()
    c.close()

    logs = []
    for line in reversed(open(os.path.join(os.path.dirname(__file__), 'data/log/bazarr.log')).readlines()):
        logs.append(line.rstrip())
    
    return template('system', tasks=tasks, logs=logs, base_url=base_url)

@route(base_url + '/remove_subtitles', method='POST')
def remove_subtitles():
        episodePath = request.forms.get('episodePath')
        language = request.forms.get('language')
        subtitlesPath = request.forms.get('subtitlesPath')
        sonarrSeriesId = request.forms.get('sonarrSeriesId')
        sonarrEpisodeId = request.forms.get('sonarrEpisodeId')

        try:
            os.remove(subtitlesPath)
            result = pycountry.languages.lookup(language).name + " subtitles deleted from disk."
            history_log(0, sonarrSeriesId, sonarrEpisodeId, result)
        except OSError:
            pass
        store_subtitles(episodePath)
        list_missing_subtitles(sonarrSeriesId)
        
@route(base_url + '/get_subtitle', method='POST')
def get_subtitle():
        ref = request.environ['HTTP_REFERER']

        episodePath = request.forms.get('episodePath')
        language = request.forms.get('language')
        hi = request.forms.get('hi')
        sonarrSeriesId = request.forms.get('sonarrSeriesId')
        sonarrEpisodeId = request.forms.get('sonarrEpisodeId')

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
            redirect(ref + '?error=2')

run(host=ip, port=port, server='waitress')

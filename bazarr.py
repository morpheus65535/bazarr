bazarr_version = '0.6.0'

import gc
gc.enable()

from get_argv import config_dir

import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs/'))

import sqlite3
from update_modules import *
from init import *
from update_db import *


from get_settings import get_general_settings
import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger('waitress')
log_level = get_general_settings()[4]
if log_level is None:
    log_level = "INFO"

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
    global fh
    fh = TimedRotatingFileHandler(os.path.join(config_dir, 'log/bazarr.log'), when="midnight", interval=1, backupCount=7)
    f = OneLineExceptionFormatter('%(asctime)s|%(levelname)s|%(message)s|',
                                  '%d/%m/%Y %H:%M:%S')
    fh.setFormatter(f)
    logging.getLogger("enzyme").setLevel(logging.CRITICAL)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("subliminal").setLevel(logging.CRITICAL)
    logging.getLogger("stevedore.extension").setLevel(logging.CRITICAL)
    root = logging.getLogger()
    root.setLevel(log_level)
    root.addHandler(fh)

configure_logging()

from bottle import route, run, template, static_file, request, redirect, response, HTTPError, app
import bottle
bottle.TEMPLATE_PATH.insert(0, os.path.join(os.path.dirname(__file__), 'views/'))
bottle.debug(True)
bottle.TEMPLATES.clear()

from beaker.middleware import SessionMiddleware
from cork import Cork
from json import dumps
import itertools
import operator
import requests
import pretty
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO
from fdsend import send_file
import urllib
import math
import ast
import hashlib

from get_languages import load_language_in_db, language_from_alpha3
from get_providers import *

from get_series import *
from get_episodes import *
from get_settings import base_url, ip, port, path_replace, path_replace_movie
from check_update import check_and_apply_update
from list_subtitles import store_subtitles, store_subtitles_movie, series_scan_subtitles, movies_scan_subtitles, list_missing_subtitles, list_missing_subtitles_movies
from get_subtitle import download_subtitle, series_download_subtitles, movies_download_subtitles, wanted_download_subtitles, wanted_search_missing_subtitles
from utils import history_log, history_log_movie
from scheduler import *
from notifier import send_notifications, send_notifications_movie

# Reset restart required warning on start
conn = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
c = conn.cursor()
c.execute("UPDATE system SET configured = 0, updated = 0")
conn.commit()
c.close()

# Load languages in database
load_language_in_db()

from get_settings import get_auth_settings

aaa = Cork('data')
        
app = app()
session_opts = {
    'session.cookie_expires': True,
    'session.key': 'Bazarr',
    'session.encrypt_key': 'Bazarr',
    'session.httponly': True,
    'session.timeout': 3600 * 24,  # 1 day TODO: Decide how long keep cookies
    'session.type': 'cookie',
    'session.validate_key': True,
}
app = SessionMiddleware(app, session_opts)


def authorize():
    # TODO: Make some configuration
    if get_auth_settings()[0] is True:
        aaa.require(fail_redirect=(base_url + 'login'))


def post_get(name, default=''):
    return request.POST.get(name, default).strip()


@route(base_url + 'login')
def login_form():
    """Serve login form"""
    return template('login', base_url=base_url)


@route(base_url + 'login', method='POST')
def login():
    # TODO: Make Lgoin error message
    """Authenticate users"""
    username = post_get('username')
    password = post_get('password')
    aaa.login(username, password, success_redirect=base_url, fail_redirect=(base_url + 'login'))


@route('/logout')
def logout():
    aaa.logout(success_redirect=(base_url + 'login'))
    

@route('/')
def redirect_root():
    authorize()
    redirect (base_url)

@route(base_url + 'static/:path#.+#', name='static')
def static(path):
    authorize()
    return static_file(path, root=os.path.join(os.path.dirname(__file__), 'static'))

@route(base_url + 'emptylog')
def emptylog():
    authorize()
    ref = request.environ['HTTP_REFERER']

    fh.doRollover()
    logging.info('Log file emptied')

    redirect(ref)

@route(base_url + 'bazarr.log')
def download_log():
    authorize()
    return static_file('bazarr.log', root=os.path.join(config_dir, 'log/'), download='bazarr.log')

@route(base_url + 'image_proxy/<url:path>', method='GET')
def image_proxy(url):
    authorize()
    url_sonarr = get_sonarr_settings()[6]
    url_sonarr_short = get_sonarr_settings()[7]
    apikey = get_sonarr_settings()[4]
    url_image = url_sonarr_short + '/' + url + '?apikey=' + apikey
    try:
        img_pil = Image.open(BytesIO(requests.get(url_sonarr_short + '/api' + url_image.split(url_sonarr)[1], timeout=15).content))
    except:
        return None
    else:
        img_buffer = BytesIO()
        img_pil.tobytes()
        img_pil.save(img_buffer, img_pil.format)
        img_buffer.seek(0)
        return send_file(img_buffer, ctype=img_pil.format)

@route(base_url + 'image_proxy_movies/<url:path>', method='GET')
def image_proxy_movies(url):
    authorize()
    url_radarr = get_radarr_settings()[6]
    url_radarr_short = get_radarr_settings()[7]
    apikey = get_radarr_settings()[4]
    try:
        url_image = (url_radarr_short + '/' + url + '?apikey=' + apikey).replace('/fanart.jpg', '/banner.jpg')
        img_pil = Image.open(BytesIO(requests.get(url_radarr_short + '/api' + url_image.split(url_radarr)[1], timeout=15).content))
    except:
        url_image = url_radarr_short + '/' + url + '?apikey=' + apikey
        img_pil = Image.open(BytesIO(requests.get(url_radarr_short + '/api' + url_image.split(url_radarr)[1], timeout=15).content))

    img_buffer = BytesIO()
    img_pil.tobytes()
    img_pil.save(img_buffer, img_pil.format)
    img_buffer.seek(0)
    return send_file(img_buffer, ctype=img_pil.format)


@route(base_url)
def redirect_root():
    authorize()
    if get_general_settings()[12] is True:
        redirect(base_url + 'series')
    elif get_general_settings()[13] is True:
        redirect(base_url + 'movies')
    else:
        redirect(base_url + 'settings')


@route(base_url + 'series')
def series():
    authorize()
    single_language = get_general_settings()[7]

    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM table_shows")
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    page_size = int(get_general_settings()[21])
    offset = (int(page) - 1) * page_size
    max_page = int(math.ceil(missing_count / (page_size + 0.0)))

    c.execute("SELECT tvdbId, title, path_substitution(path), languages, hearing_impaired, sonarrSeriesId, poster, audio_language FROM table_shows ORDER BY sortTitle ASC LIMIT ? OFFSET ?", (page_size, offset,))
    data = c.fetchall()
    c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1")
    languages = c.fetchall()
    c.execute("SELECT table_shows.sonarrSeriesId, COUNT(table_episodes.missing_subtitles) FROM table_shows LEFT JOIN table_episodes ON table_shows.sonarrSeriesId=table_episodes.sonarrSeriesId WHERE table_shows.languages IS NOT 'None' AND table_episodes.missing_subtitles IS NOT '[]' GROUP BY table_shows.sonarrSeriesId")
    missing_subtitles_list = c.fetchall()
    c.execute("SELECT table_shows.sonarrSeriesId, COUNT(table_episodes.missing_subtitles) FROM table_shows LEFT JOIN table_episodes ON table_shows.sonarrSeriesId=table_episodes.sonarrSeriesId WHERE table_shows.languages IS NOT 'None' GROUP BY table_shows.sonarrSeriesId")
    total_subtitles_list = c.fetchall()
    c.close()
    output = template('series', __file__=__file__, bazarr_version=bazarr_version, rows=data, missing_subtitles_list=missing_subtitles_list, total_subtitles_list=total_subtitles_list, languages=languages, missing_count=missing_count, page=page, max_page=max_page, base_url=base_url, single_language=single_language, page_size=page_size)
    return output

@route(base_url + 'serieseditor')
def serieseditor():
    authorize()
    single_language = get_general_settings()[7]

    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM table_shows")
    missing_count = c.fetchone()
    missing_count = missing_count[0]

    c.execute("SELECT tvdbId, title, path_substitution(path), languages, hearing_impaired, sonarrSeriesId, poster, audio_language FROM table_shows ORDER BY title ASC")
    data = c.fetchall()
    c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1")
    languages = c.fetchall()
    c.close()
    output = template('serieseditor', __file__=__file__, bazarr_version=bazarr_version, rows=data, languages=languages, missing_count=missing_count, base_url=base_url, single_language=single_language)
    return output

@route(base_url + 'search_json/<query>', method='GET')
def search_json(query):
    authorize()
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()

    c.execute("SELECT title, sonarrSeriesId FROM table_shows WHERE title LIKE ? ORDER BY title", ('%'+query+'%',))
    series = c.fetchall()

    c.execute("SELECT title, radarrId FROM table_movies WHERE title LIKE ? ORDER BY title", ('%' + query + '%',))
    movies = c.fetchall()

    search_list = []
    for serie in series:
        search_list.append(dict([('name', serie[0]), ('url', base_url + 'episodes/' + str(serie[1]))]))

    for movie in movies:
        search_list.append(dict([('name', movie[0]), ('url', base_url + 'movie/' + str(movie[1]))]))

    response.content_type = 'application/json'
    return dict(items=search_list)


@route(base_url + 'edit_series/<no:int>', method='POST')
def edit_series(no):
    authorize()
    ref = request.environ['HTTP_REFERER']

    lang = request.forms.getall('languages')
    if len(lang) > 0:
        pass
    else:
        lang = 'None'

    single_language = get_general_settings()[7]
    if single_language is True:
        if str(lang) == "['None']":
            lang = 'None'
        else:
            lang = str(lang)
    else:
        if str(lang) == "['']":
            lang = '[]'

    hi = request.forms.get('hearing_impaired')

    if hi == "on":
        hi = "True"
    else:
        hi = "False"

    conn = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = conn.cursor()
    c.execute("UPDATE table_shows SET languages = ?, hearing_impaired = ? WHERE sonarrSeriesId LIKE ?", (str(lang), hi, no))
    conn.commit()
    c.close()

    list_missing_subtitles(no)

    redirect(ref)

@route(base_url + 'edit_serieseditor', method='POST')
def edit_serieseditor():
    authorize()
    ref = request.environ['HTTP_REFERER']

    series = request.forms.get('series')
    series = ast.literal_eval(str('[' + series + ']'))
    lang = request.forms.getall('languages')
    hi = request.forms.get('hearing_impaired')

    conn = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = conn.cursor()

    for serie in series:
        if str(lang) != "[]" and str(lang) != "['']":
            if str(lang) == "['None']":
                lang = 'None'
            else:
                lang = str(lang)
            c.execute("UPDATE table_shows SET languages = ? WHERE sonarrSeriesId LIKE ?", (lang, serie))
        if hi != '':
            c.execute("UPDATE table_shows SET hearing_impaired = ? WHERE sonarrSeriesId LIKE ?", (hi, serie))

    conn.commit()
    c.close()

    for serie in series:
        list_missing_subtitles(serie)

    redirect(ref)

@route(base_url + 'episodes/<no:int>', method='GET')
def episodes(no):
    authorize()
    # single_language = get_general_settings()[7]
    url_sonarr_short = get_sonarr_settings()[7]

    conn = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    conn.create_function("path_substitution", 1, path_replace)
    c = conn.cursor()

    series_details = []
    series_details = c.execute("SELECT title, overview, poster, fanart, hearing_impaired, tvdbid, audio_language, languages, path_substitution(path) FROM table_shows WHERE sonarrSeriesId LIKE ?", (str(no),)).fetchone()
    tvdbid = series_details[5]

    episodes = c.execute("SELECT title, path_substitution(path), season, episode, subtitles, sonarrSeriesId, missing_subtitles, sonarrEpisodeId, scene_name, monitored FROM table_episodes WHERE sonarrSeriesId LIKE ? ORDER BY episode ASC", (str(no),)).fetchall()
    number = len(episodes)
    languages = c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1").fetchall()
    c.close()
    episodes = reversed(sorted(episodes, key=operator.itemgetter(2)))
    seasons_list = []
    for key, season in itertools.groupby(episodes,operator.itemgetter(2)):
        seasons_list.append(list(season))

    return template('episodes', __file__=__file__, bazarr_version=bazarr_version, no=no, details=series_details, languages=languages, seasons=seasons_list, url_sonarr_short=url_sonarr_short, base_url=base_url, tvdbid=tvdbid, number=number)

@route(base_url + 'movies')
def movies():
    authorize()
    single_language = get_general_settings()[7]

    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace_movie)
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM table_movies")
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    page_size = int(get_general_settings()[21])
    offset = (int(page) - 1) * page_size
    max_page = int(math.ceil(missing_count / (page_size + 0.0)))

    c.execute("SELECT tmdbId, title, path_substitution(path), languages, hearing_impaired, radarrId, poster, audio_language, monitored FROM table_movies ORDER BY title ASC LIMIT ? OFFSET ?", (page_size, offset,))
    data = c.fetchall()
    c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1")
    languages = c.fetchall()
    c.close()
    output = template('movies', __file__=__file__, bazarr_version=bazarr_version, rows=data, languages=languages, missing_count=missing_count, page=page, max_page=max_page, base_url=base_url, single_language=single_language, page_size=page_size)
    return output

@route(base_url + 'movieseditor')
def movieseditor():
    authorize()
    single_language = get_general_settings()[7]

    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace_movie)
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM table_movies")
    missing_count = c.fetchone()
    missing_count = missing_count[0]

    c.execute("SELECT tmdbId, title, path_substitution(path), languages, hearing_impaired, radarrId, poster, audio_language FROM table_movies ORDER BY title ASC")
    data = c.fetchall()
    c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1")
    languages = c.fetchall()
    c.close()
    output = template('movieseditor', __file__=__file__, bazarr_version=bazarr_version, rows=data, languages=languages, missing_count=missing_count, base_url=base_url, single_language=single_language)
    return output

@route(base_url + 'edit_movieseditor', method='POST')
def edit_movieseditor():
    authorize()
    ref = request.environ['HTTP_REFERER']

    movies = request.forms.get('movies')
    movies = ast.literal_eval(str('[' + movies + ']'))
    lang = request.forms.getall('languages')
    hi = request.forms.get('hearing_impaired')

    conn = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = conn.cursor()

    for movie in movies:
        if str(lang) != "[]" and str(lang) != "['']":
            if str(lang) == "['None']":
                lang = 'None'
            else:
                lang = str(lang)
            c.execute("UPDATE table_movies SET languages = ? WHERE radarrId LIKE ?", (lang, movie))
        if hi != '':
            c.execute("UPDATE table_movies SET hearing_impaired = ? WHERE radarrId LIKE ?", (hi, movie))

    conn.commit()
    c.close()

    for movie in movies:
        list_missing_subtitles_movies(movie)

    redirect(ref)

@route(base_url + 'edit_movie/<no:int>', method='POST')
def edit_movie(no):
    authorize()
    ref = request.environ['HTTP_REFERER']

    lang = request.forms.getall('languages')
    if len(lang) > 0:
        pass
    else:
        lang = 'None'

    if str(lang) == "['']":
        lang = '[]'

    hi = request.forms.get('hearing_impaired')

    if hi == "on":
        hi = "True"
    else:
        hi = "False"

    conn = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = conn.cursor()
    c.execute("UPDATE table_movies SET languages = ?, hearing_impaired = ? WHERE radarrId LIKE ?", (str(lang), hi, no))
    conn.commit()
    c.close()

    list_missing_subtitles_movies(no)

    redirect(ref)

@route(base_url + 'movie/<no:int>', method='GET')
def movie(no):
    authorize()
    # single_language = get_general_settings()[7]
    url_radarr_short = get_radarr_settings()[7]

    conn = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    conn.create_function("path_substitution", 1, path_replace_movie)
    c = conn.cursor()

    movies_details = []
    movies_details = c.execute("SELECT title, overview, poster, fanart, hearing_impaired, tmdbid, audio_language, languages, path_substitution(path), subtitles, radarrId, missing_subtitles, sceneName, monitored FROM table_movies WHERE radarrId LIKE ?", (str(no),)).fetchone()
    tmdbid = movies_details[5]

    languages = c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1").fetchall()
    c.close()

    return template('movie', __file__=__file__, bazarr_version=bazarr_version, no=no, details=movies_details, languages=languages, url_radarr_short=url_radarr_short, base_url=base_url, tmdbid=tmdbid)

@route(base_url + 'scan_disk/<no:int>', method='GET')
def scan_disk(no):
    authorize()
    ref = request.environ['HTTP_REFERER']

    series_scan_subtitles(no)

    redirect(ref)

@route(base_url + 'scan_disk_movie/<no:int>', method='GET')
def scan_disk_movie(no):
    authorize()
    ref = request.environ['HTTP_REFERER']

    movies_scan_subtitles(no)

    redirect(ref)

@route(base_url + 'search_missing_subtitles/<no:int>', method='GET')
def search_missing_subtitles(no):
    authorize()
    ref = request.environ['HTTP_REFERER']

    series_download_subtitles(no)

    redirect(ref)

@route(base_url + 'search_missing_subtitles_movie/<no:int>', method='GET')
def search_missing_subtitles_movie(no):
    authorize()
    ref = request.environ['HTTP_REFERER']

    movies_download_subtitles(no)

    redirect(ref)

@route(base_url + 'history')
def history():
    authorize()
    return template('history', __file__=__file__, bazarr_version=bazarr_version, base_url=base_url)

@route(base_url + 'historyseries')
def historyseries():
    authorize()
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM table_history")
    row_count = c.fetchone()
    row_count = row_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    page_size = int(get_general_settings()[21])
    offset = (int(page) - 1) * page_size
    max_page = int(math.ceil(row_count / (page_size + 0.0)))

    now = datetime.now()
    today = []
    thisweek = []
    thisyear = []
    stats = c.execute("SELECT timestamp FROM table_history WHERE action LIKE '1'").fetchall()
    total = len(stats)
    for stat in stats:
        if now - timedelta(hours=24) <= datetime.fromtimestamp(stat[0]) <= now:
            today.append(datetime.fromtimestamp(stat[0]).date())
        if now - timedelta(weeks=1) <= datetime.fromtimestamp(stat[0]) <= now:
            thisweek.append(datetime.fromtimestamp(stat[0]).date())
        if now - timedelta(weeks=52) <= datetime.fromtimestamp(stat[0]) <= now:
            thisyear.append(datetime.fromtimestamp(stat[0]).date())
    stats = [len(today), len(thisweek), len(thisyear), total]

    c.execute("SELECT table_history.action, table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, table_history.timestamp, table_history.description, table_history.sonarrSeriesId FROM table_history LEFT JOIN table_shows on table_shows.sonarrSeriesId = table_history.sonarrSeriesId LEFT JOIN table_episodes on table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId ORDER BY id DESC LIMIT ? OFFSET ?", (page_size, offset,))
    data = c.fetchall()
    c.close()
    data = reversed(sorted(data, key=operator.itemgetter(4)))
    return template('historyseries', __file__=__file__, bazarr_version=bazarr_version, rows=data, row_count=row_count, page=page, max_page=max_page, stats=stats, base_url=base_url, page_size=page_size)

@route(base_url + 'historymovies')
def historymovies():
    authorize()
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM table_history_movie")
    row_count = c.fetchone()
    row_count = row_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    page_size = int(get_general_settings()[21])
    offset = (int(page) - 1) * page_size
    max_page = int(math.ceil(row_count / (page_size + 0.0)))

    now = datetime.now()
    today = []
    thisweek = []
    thisyear = []
    stats = c.execute("SELECT timestamp FROM table_history_movie WHERE action LIKE '1'").fetchall()
    total = len(stats)
    for stat in stats:
        if now - timedelta(hours=24) <= datetime.fromtimestamp(stat[0]) <= now:
            today.append(datetime.fromtimestamp(stat[0]).date())
        if now - timedelta(weeks=1) <= datetime.fromtimestamp(stat[0]) <= now:
            thisweek.append(datetime.fromtimestamp(stat[0]).date())
        if now - timedelta(weeks=52) <= datetime.fromtimestamp(stat[0]) <= now:
            thisyear.append(datetime.fromtimestamp(stat[0]).date())
    stats = [len(today), len(thisweek), len(thisyear), total]

    c.execute("SELECT table_history_movie.action, table_movies.title, table_history_movie.timestamp, table_history_movie.description, table_history_movie.radarrId FROM table_history_movie LEFT JOIN table_movies on table_movies.radarrId = table_history_movie.radarrId ORDER BY id DESC LIMIT ? OFFSET ?", (page_size, offset,))
    data = c.fetchall()
    c.close()
    data = reversed(sorted(data, key=operator.itemgetter(2)))
    return template('historymovies', __file__=__file__, bazarr_version=bazarr_version, rows=data, row_count=row_count, page=page, max_page=max_page, stats=stats, base_url=base_url, page_size=page_size)

@route(base_url + 'wanted')
def wanted():
    authorize()
    return template('wanted', __file__=__file__, bazarr_version=bazarr_version, base_url=base_url)

@route(base_url + 'wantedseries')
def wantedseries():
    authorize()
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()

    if get_general_settings()[24] is True:
        monitored_only_query_string = ' AND monitored = "True"'
    else:
        monitored_only_query_string = ""

    c.execute("SELECT COUNT(*) FROM table_episodes WHERE missing_subtitles != '[]'" + monitored_only_query_string)
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    page_size = int(get_general_settings()[21])
    offset = (int(page) - 1) * page_size
    max_page = int(math.ceil(missing_count / (page_size + 0.0)))

    c.execute("SELECT table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, table_episodes.missing_subtitles, table_episodes.sonarrSeriesId, path_substitution(table_episodes.path), table_shows.hearing_impaired, table_episodes.sonarrEpisodeId, table_episodes.scene_name FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE table_episodes.missing_subtitles != '[]'" + monitored_only_query_string + " ORDER BY table_episodes._rowid_ DESC LIMIT ? OFFSET ?", (page_size, offset,))
    data = c.fetchall()
    c.close()
    return template('wantedseries', __file__=__file__, bazarr_version=bazarr_version, rows=data, missing_count=missing_count, page=page, max_page=max_page, base_url=base_url, page_size=page_size)

@route(base_url + 'wantedmovies')
def wantedmovies():
    authorize()
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace_movie)
    c = db.cursor()

    if get_general_settings()[24] is True:
        monitored_only_query_string = ' AND monitored = "True"'
    else:
        monitored_only_query_string = ""

    c.execute("SELECT COUNT(*) FROM table_movies WHERE missing_subtitles != '[]'" + monitored_only_query_string)
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    page_size = int(get_general_settings()[21])
    offset = (int(page) - 1) * page_size
    max_page = int(math.ceil(missing_count / (page_size + 0.0)))

    c.execute("SELECT title, missing_subtitles, radarrId, path_substitution(path), hearing_impaired, sceneName FROM table_movies WHERE missing_subtitles != '[]'" + monitored_only_query_string + " ORDER BY _rowid_ DESC LIMIT ? OFFSET ?", (page_size, offset,))
    data = c.fetchall()
    c.close()
    return template('wantedmovies', __file__=__file__, bazarr_version=bazarr_version, rows=data, missing_count=missing_count, page=page, max_page=max_page, base_url=base_url, page_size=page_size)

@route(base_url + 'wanted_search_missing_subtitles')
def wanted_search_missing_subtitles_list():
    authorize()
    ref = request.environ['HTTP_REFERER']

    wanted_search_missing_subtitles()

    redirect(ref)

@route(base_url + 'settings')
def settings():
    authorize()
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()
    c.execute("SELECT * FROM table_settings_languages ORDER BY name")
    settings_languages = c.fetchall()
    c.execute("SELECT * FROM table_settings_providers ORDER BY name")
    settings_providers = c.fetchall()
    c.execute("SELECT * FROM table_settings_notifier ORDER BY name")
    settings_notifier = c.fetchall()
    c.close()
    from get_settings import get_general_settings, get_auth_settings, get_radarr_settings, get_sonarr_settings
    settings_general = get_general_settings()
    settings_auth = get_auth_settings()
    settings_sonarr = get_sonarr_settings()
    settings_radarr = get_radarr_settings()

    return template('settings', __file__=__file__, bazarr_version=bazarr_version, settings_general=settings_general, settings_auth=settings_auth, settings_languages=settings_languages, settings_providers=settings_providers, settings_sonarr=settings_sonarr, settings_radarr=settings_radarr, settings_notifier=settings_notifier, base_url=base_url)

@route(base_url + 'save_settings', method='POST')
def save_settings():
    authorize()
    ref = request.environ['HTTP_REFERER']

    conn = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = conn.cursor()

    settings_general_ip = request.forms.get('settings_general_ip')
    settings_general_port = request.forms.get('settings_general_port')
    settings_general_baseurl = request.forms.get('settings_general_baseurl')
    settings_general_loglevel = request.forms.get('settings_general_loglevel')
    settings_general_auth_enabled = request.forms.get('settings_general_auth_enabled')
    if settings_general_auth_enabled is None:
        settings_general_auth_enabled = 'False'
    else:
        settings_general_auth_enabled = 'True'
    settings_general_auth_username = request.forms.get('settings_general_auth_username')
    settings_general_auth_password = request.forms.get('settings_general_auth_password')
    settings_general_sourcepath = request.forms.getall('settings_general_sourcepath')
    settings_general_destpath = request.forms.getall('settings_general_destpath')
    settings_general_pathmapping = []
    settings_general_pathmapping.extend([list(a) for a in zip(settings_general_sourcepath, settings_general_destpath)])
    settings_general_sourcepath_movie = request.forms.getall('settings_general_sourcepath_movie')
    settings_general_destpath_movie = request.forms.getall('settings_general_destpath_movie')
    settings_general_pathmapping_movie = []
    settings_general_pathmapping_movie.extend([list(a) for a in zip(settings_general_sourcepath_movie, settings_general_destpath_movie)])
    settings_general_branch = request.forms.get('settings_general_branch')
    settings_general_automatic = request.forms.get('settings_general_automatic')
    if settings_general_automatic is None:
        settings_general_automatic = 'False'
    else:
        settings_general_automatic = 'True'
    settings_general_single_language = request.forms.get('settings_general_single_language')
    if settings_general_single_language is None:
        settings_general_single_language = 'False'
    else:
        settings_general_single_language = 'True'
    settings_general_scenename = request.forms.get('settings_general_scenename')
    if settings_general_scenename is None:
        settings_general_scenename = 'False'
    else:
        settings_general_scenename = 'True'
    settings_general_embedded = request.forms.get('settings_general_embedded')
    if settings_general_embedded is None:
        settings_general_embedded = 'False'
    else:
        settings_general_embedded = 'True'
    settings_general_only_monitored = request.forms.get('settings_general_only_monitored')
    if settings_general_only_monitored is None:
        settings_general_only_monitored = 'False'
    else:
        settings_general_only_monitored = 'True'
    settings_general_adaptive_searching = request.forms.get('settings_general_adaptive_searching')
    if settings_general_adaptive_searching is None:
        settings_general_adaptive_searching = 'False'
    else:
        settings_general_adaptive_searching = 'True'
    settings_general_minimum_score = request.forms.get('settings_general_minimum_score')
    settings_general_minimum_score_movies = request.forms.get('settings_general_minimum_score_movies')
    settings_general_use_postprocessing = request.forms.get('settings_general_use_postprocessing')
    if settings_general_use_postprocessing is None:
        settings_general_use_postprocessing = 'False'
    else:
        settings_general_use_postprocessing = 'True'
    settings_general_postprocessing_cmd = request.forms.get('settings_general_postprocessing_cmd')
    settings_general_use_sonarr = request.forms.get('settings_general_use_sonarr')
    if settings_general_use_sonarr is None:
        settings_general_use_sonarr = 'False'
    else:
        settings_general_use_sonarr = 'True'
    settings_general_use_radarr = request.forms.get('settings_general_use_radarr')
    if settings_general_use_radarr is None:
        settings_general_use_radarr = 'False'
    else:
        settings_general_use_radarr = 'True'
    settings_page_size = request.forms.get('settings_page_size')

    settings_general = get_general_settings()

    before = (unicode(settings_general[0]), int(settings_general[1]), unicode(settings_general[2]), unicode(settings_general[4]), unicode(settings_general[3]), unicode(settings_general[12]), unicode(settings_general[13]), unicode(settings_general[14]))
    after = (unicode(settings_general_ip), int(settings_general_port), unicode(settings_general_baseurl), unicode(settings_general_loglevel), unicode(settings_general_pathmapping), unicode(settings_general_use_sonarr), unicode(settings_general_use_radarr), unicode(settings_general_pathmapping_movie))
    from six import text_type

    cfg = ConfigParser()

    with open(config_file, 'r') as f:
        cfg.read_file(f)

    cfg.set('general', 'ip', text_type(settings_general_ip))
    cfg.set('general', 'port', text_type(settings_general_port))
    cfg.set('general', 'base_url', text_type(settings_general_baseurl))
    cfg.set('general', 'path_mappings', text_type(settings_general_pathmapping))
    cfg.set('general', 'log_level', text_type(settings_general_loglevel))
    cfg.set('general', 'branch', text_type(settings_general_branch))
    cfg.set('general', 'auto_update', text_type(settings_general_automatic))
    cfg.set('general', 'single_language', text_type(settings_general_single_language))
    cfg.set('general', 'minimum_score', text_type(settings_general_minimum_score))
    cfg.set('general', 'use_scenename', text_type(settings_general_scenename))
    cfg.set('general', 'use_postprocessing', text_type(settings_general_use_postprocessing))
    cfg.set('general', 'postprocessing_cmd', text_type(settings_general_postprocessing_cmd))
    cfg.set('general', 'use_sonarr', text_type(settings_general_use_sonarr))
    cfg.set('general', 'use_radarr', text_type(settings_general_use_radarr))
    cfg.set('general', 'path_mappings_movie', text_type(settings_general_pathmapping_movie))
    cfg.set('general', 'page_size', text_type(settings_page_size))
    cfg.set('general', 'minimum_score_movie', text_type(settings_general_minimum_score_movies))
    cfg.set('general', 'use_embedded_subs', text_type(settings_general_embedded))
    cfg.set('general', 'only_monitored', text_type(settings_general_only_monitored))
    cfg.set('general', 'adaptive_searching', text_type(settings_general_adaptive_searching))


    if after != before:
        configured()
    get_general_settings()

    settings_auth = get_auth_settings()

    before_auth_password = (unicode(settings_auth[0]), unicode(settings_auth[2]))
    if before_auth_password[0] != settings_general_auth_enabled:
        configured()
    if before_auth_password[1] == settings_general_auth_password:
        cfg.set('auth', 'enabled', text_type(settings_general_auth_enabled))
        cfg.set('auth', 'username', text_type(settings_general_auth_username))
    else:
        cfg.set('auth', 'enabled', text_type(settings_general_auth_enabled))
        cfg.set('auth', 'username', text_type(settings_general_auth_username))
        cfg.set('auth', 'password', hashlib.md5(settings_general_auth_password).hexdigest())

    settings_sonarr_ip = request.forms.get('settings_sonarr_ip')
    settings_sonarr_port = request.forms.get('settings_sonarr_port')
    settings_sonarr_baseurl = request.forms.get('settings_sonarr_baseurl')
    settings_sonarr_ssl = request.forms.get('settings_sonarr_ssl')
    if settings_sonarr_ssl is None:
        settings_sonarr_ssl = 'False'
    else:
        settings_sonarr_ssl = 'True'
    settings_sonarr_apikey = request.forms.get('settings_sonarr_apikey')
    settings_sonarr_sync = request.forms.get('settings_sonarr_sync')

    cfg.set('sonarr', 'ip', text_type(settings_sonarr_ip))
    cfg.set('sonarr', 'port', text_type(settings_sonarr_port))
    cfg.set('sonarr', 'base_url', text_type(settings_sonarr_baseurl))
    cfg.set('sonarr', 'ssl', text_type(settings_sonarr_ssl))
    cfg.set('sonarr', 'apikey', text_type(settings_sonarr_apikey))
    cfg.set('sonarr', 'full_update', text_type(settings_sonarr_sync))

    settings_radarr_ip = request.forms.get('settings_radarr_ip')
    settings_radarr_port = request.forms.get('settings_radarr_port')
    settings_radarr_baseurl = request.forms.get('settings_radarr_baseurl')
    settings_radarr_ssl = request.forms.get('settings_radarr_ssl')
    if settings_radarr_ssl is None:
        settings_radarr_ssl = 'False'
    else:
        settings_radarr_ssl = 'True'
    settings_radarr_apikey = request.forms.get('settings_radarr_apikey')
    settings_radarr_sync = request.forms.get('settings_radarr_sync')

    cfg.set('radarr', 'ip', text_type(settings_radarr_ip))
    cfg.set('radarr', 'port', text_type(settings_radarr_port))
    cfg.set('radarr', 'base_url', text_type(settings_radarr_baseurl))
    cfg.set('radarr', 'ssl', text_type(settings_radarr_ssl))
    cfg.set('radarr', 'apikey', text_type(settings_radarr_apikey))
    cfg.set('radarr', 'full_update', text_type(settings_radarr_sync))

    settings_subliminal_providers = request.forms.getall('settings_subliminal_providers')
    c.execute("UPDATE table_settings_providers SET enabled = 0")
    for item in settings_subliminal_providers:
        c.execute("UPDATE table_settings_providers SET enabled = '1' WHERE name = ?", (item,))

    settings_addic7ed_username = request.forms.get('settings_addic7ed_username')
    settings_addic7ed_password = request.forms.get('settings_addic7ed_password')
    c.execute("UPDATE table_settings_providers SET username = ?, password = ? WHERE name = 'addic7ed'", (settings_addic7ed_username, settings_addic7ed_password))
    settings_legendastv_username = request.forms.get('settings_legendastv_username')
    settings_legendastv_password = request.forms.get('settings_legendastv_password')
    c.execute("UPDATE table_settings_providers SET username = ?, password = ? WHERE name = 'legendastv'", (settings_legendastv_username, settings_legendastv_password))
    settings_opensubtitles_username = request.forms.get('settings_opensubtitles_username')
    settings_opensubtitles_password = request.forms.get('settings_opensubtitles_password')
    c.execute("UPDATE table_settings_providers SET username = ?, password = ? WHERE name = 'opensubtitles'", (settings_opensubtitles_username, settings_opensubtitles_password))

    settings_subliminal_languages = request.forms.getall('settings_subliminal_languages')
    c.execute("UPDATE table_settings_languages SET enabled = 0")
    for item in settings_subliminal_languages:
        c.execute("UPDATE table_settings_languages SET enabled = '1' WHERE code2 = ?", (item,))

    settings_serie_default_enabled = request.forms.get('settings_serie_default_enabled')
    if settings_serie_default_enabled is None:
        settings_serie_default_enabled = 'False'
    else:
        settings_serie_default_enabled = 'True'
    cfg.set('general', 'serie_default_enabled', text_type(settings_serie_default_enabled))

    settings_serie_default_languages = str(request.forms.getall('settings_serie_default_languages'))
    if settings_serie_default_languages == "['None']":
        settings_serie_default_languages = 'None'
    cfg.set('general', 'serie_default_language', text_type(settings_serie_default_languages))

    settings_serie_default_hi = request.forms.get('settings_serie_default_hi')
    if settings_serie_default_hi is None:
        settings_serie_default_hi = 'False'
    else:
        settings_serie_default_hi = 'True'
    cfg.set('general', 'serie_default_hi', text_type(settings_serie_default_hi))

    settings_movie_default_enabled = request.forms.get('settings_movie_default_enabled')
    if settings_movie_default_enabled is None:
        settings_movie_default_enabled = 'False'
    else:
        settings_movie_default_enabled = 'True'
    cfg.set('general', 'movie_default_enabled', text_type(settings_movie_default_enabled))

    settings_movie_default_languages = str(request.forms.getall('settings_movie_default_languages'))
    if settings_movie_default_languages == "['None']":
        settings_movie_default_languages = 'None'
    cfg.set('general', 'movie_default_language', text_type(settings_movie_default_languages))

    settings_movie_default_hi = request.forms.get('settings_movie_default_hi')
    if settings_movie_default_hi is None:
        settings_movie_default_hi = 'False'
    else:
        settings_movie_default_hi = 'True'
    cfg.set('general', 'movie_default_hi', text_type(settings_movie_default_hi))

    with open(config_file, 'wb') as f:
        cfg.write(f)

    settings_notifier_Boxcar_enabled = request.forms.get('settings_notifier_Boxcar_enabled')
    if settings_notifier_Boxcar_enabled == 'on':
        settings_notifier_Boxcar_enabled = 1
    else:
        settings_notifier_Boxcar_enabled = 0
    settings_notifier_Boxcar_url = request.forms.get('settings_notifier_Boxcar_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Boxcar'", (settings_notifier_Boxcar_enabled, settings_notifier_Boxcar_url))

    settings_notifier_Faast_enabled = request.forms.get('settings_notifier_Faast_enabled')
    if settings_notifier_Faast_enabled == 'on':
        settings_notifier_Faast_enabled = 1
    else:
        settings_notifier_Faast_enabled = 0
    settings_notifier_Faast_url = request.forms.get('settings_notifier_Faast_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Faast'", (settings_notifier_Faast_enabled, settings_notifier_Faast_url))

    settings_notifier_Growl_enabled = request.forms.get('settings_notifier_Growl_enabled')
    if settings_notifier_Growl_enabled == 'on':
        settings_notifier_Growl_enabled = 1
    else:
        settings_notifier_Growl_enabled = 0
    settings_notifier_Growl_url = request.forms.get('settings_notifier_Growl_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Growl'", (settings_notifier_Growl_enabled, settings_notifier_Growl_url))

    settings_notifier_Join_enabled = request.forms.get('settings_notifier_Join_enabled')
    if settings_notifier_Join_enabled == 'on':
        settings_notifier_Join_enabled = 1
    else:
        settings_notifier_Join_enabled = 0
    settings_notifier_Join_url = request.forms.get('settings_notifier_Join_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Join'", (settings_notifier_Join_enabled, settings_notifier_Join_url))

    settings_notifier_KODI_enabled = request.forms.get('settings_notifier_KODI_enabled')
    if settings_notifier_KODI_enabled == 'on':
        settings_notifier_KODI_enabled = 1
    else:
        settings_notifier_KODI_enabled = 0
    settings_notifier_KODI_url = request.forms.get('settings_notifier_KODI_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'KODI'", (settings_notifier_KODI_enabled, settings_notifier_KODI_url))

    settings_notifier_Mattermost_enabled = request.forms.get('settings_notifier_Mattermost_enabled')
    if settings_notifier_Mattermost_enabled == 'on':
        settings_notifier_Mattermost_enabled = 1
    else:
        settings_notifier_Mattermost_enabled = 0
    settings_notifier_Mattermost_url = request.forms.get('settings_notifier_Mattermost_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Mattermost'", (settings_notifier_Mattermost_enabled, settings_notifier_Mattermost_url))

    settings_notifier_NMA_enabled = request.forms.get('settings_notifier_Notify My Android_enabled')
    if settings_notifier_NMA_enabled == 'on':
        settings_notifier_NMA_enabled = 1
    else:
        settings_notifier_NMA_enabled = 0
    settings_notifier_NMA_url = request.forms.get('settings_notifier_Notify My Android_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Notify My Android'", (settings_notifier_NMA_enabled, settings_notifier_NMA_url))

    settings_notifier_Prowl_enabled = request.forms.get('settings_notifier_Prowl_enabled')
    if settings_notifier_Prowl_enabled == 'on':
        settings_notifier_Prowl_enabled = 1
    else:
        settings_notifier_Prowl_enabled = 0
    settings_notifier_Prowl_url = request.forms.get('settings_notifier_Prowl_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Prowl'", (settings_notifier_Prowl_enabled, settings_notifier_Prowl_url))

    settings_notifier_Pushalot_enabled = request.forms.get('settings_notifier_Pushalot_enabled')
    if settings_notifier_Pushalot_enabled == 'on':
        settings_notifier_Pushalot_enabled = 1
    else:
        settings_notifier_Pushalot_enabled = 0
    settings_notifier_Pushalot_url = request.forms.get('settings_notifier_Pushalot_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Pushalot'", (settings_notifier_Pushalot_enabled, settings_notifier_Pushalot_url))

    settings_notifier_PushBullet_enabled = request.forms.get('settings_notifier_PushBullet_enabled')
    if settings_notifier_PushBullet_enabled == 'on':
        settings_notifier_PushBullet_enabled = 1
    else:
        settings_notifier_PushBullet_enabled = 0
    settings_notifier_PushBullet_url = request.forms.get('settings_notifier_PushBullet_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'PushBullet'", (settings_notifier_PushBullet_enabled, settings_notifier_PushBullet_url))

    settings_notifier_Pushjet_enabled = request.forms.get('settings_notifier_Pushjet_enabled')
    if settings_notifier_Pushjet_enabled == 'on':
        settings_notifier_Pushjet_enabled = 1
    else:
        settings_notifier_Pushjet_enabled = 0
    settings_notifier_Pushjet_url = request.forms.get('settings_notifier_Pushjet_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Pushjet'", (settings_notifier_Pushjet_enabled, settings_notifier_Pushjet_url))

    settings_notifier_Pushover_enabled = request.forms.get('settings_notifier_Pushover_enabled')
    if settings_notifier_Pushover_enabled == 'on':
        settings_notifier_Pushover_enabled = 1
    else:
        settings_notifier_Pushover_enabled = 0
    settings_notifier_Pushover_url = request.forms.get('settings_notifier_Pushover_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Pushover'", (settings_notifier_Pushover_enabled, settings_notifier_Pushover_url))

    settings_notifier_RocketChat_enabled = request.forms.get('settings_notifier_Rocket.Chat_enabled')
    if settings_notifier_RocketChat_enabled == 'on':
        settings_notifier_RocketChat_enabled = 1
    else:
        settings_notifier_RocketChat_enabled = 0
    settings_notifier_RocketChat_url = request.forms.get('settings_notifier_Rocket.Chat_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Rocket.Chat'", (settings_notifier_RocketChat_enabled, settings_notifier_RocketChat_url))

    settings_notifier_Slack_enabled = request.forms.get('settings_notifier_Slack_enabled')
    if settings_notifier_Slack_enabled == 'on':
        settings_notifier_Slack_enabled = 1
    else:
        settings_notifier_Slack_enabled = 0
    settings_notifier_Slack_url = request.forms.get('settings_notifier_Slack_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Slack'", (settings_notifier_Slack_enabled, settings_notifier_Slack_url))

    settings_notifier_SuperToasty_enabled = request.forms.get('settings_notifier_Super Toasty_enabled')
    if settings_notifier_SuperToasty_enabled == 'on':
        settings_notifier_SuperToasty_enabled = 1
    else:
        settings_notifier_SuperToasty_enabled = 0
    settings_notifier_SuperToasty_url = request.forms.get('settings_notifier_Super Toasty_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Super Toasty'", (settings_notifier_SuperToasty_enabled, settings_notifier_SuperToasty_url))

    settings_notifier_Telegram_enabled = request.forms.get('settings_notifier_Telegram_enabled')
    if settings_notifier_Telegram_enabled == 'on':
        settings_notifier_Telegram_enabled = 1
    else:
        settings_notifier_Telegram_enabled = 0
    settings_notifier_Telegram_url = request.forms.get('settings_notifier_Telegram_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Telegram'", (settings_notifier_Telegram_enabled, settings_notifier_Telegram_url))

    settings_notifier_Twitter_enabled = request.forms.get('settings_notifier_Twitter_enabled')
    if settings_notifier_Twitter_enabled == 'on':
        settings_notifier_Twitter_enabled = 1
    else:
        settings_notifier_Twitter_enabled = 0
    settings_notifier_Twitter_url = request.forms.get('settings_notifier_Twitter_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Twitter'", (settings_notifier_Twitter_enabled, settings_notifier_Twitter_url))

    settings_notifier_XBMC_enabled = request.forms.get('settings_notifier_XBMC_enabled')
    if settings_notifier_XBMC_enabled == 'on':
        settings_notifier_XBMC_enabled = 1
    else:
        settings_notifier_XBMC_enabled = 0
    settings_notifier_XBMC_url = request.forms.get('settings_notifier_XBMC_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'XBMC'", (settings_notifier_XBMC_enabled, settings_notifier_XBMC_url))

    settings_notifier_Discord_enabled = request.forms.get('settings_notifier_Discord_enabled')
    if settings_notifier_Discord_enabled == 'on':
        settings_notifier_Discord_enabled = 1
    else:
        settings_notifier_Discord_enabled = 0
    settings_notifier_Discord_url = request.forms.get('settings_notifier_Discord_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Discord'", (settings_notifier_Discord_enabled, settings_notifier_Discord_url))

    settings_notifier_E_Mail_enabled = request.forms.get('settings_notifier_E-Mail_enabled')
    if settings_notifier_E_Mail_enabled == 'on':
        settings_notifier_E_Mail_enabled = 1
    else:
        settings_notifier_E_Mail_enabled = 0
    settings_notifier_E_Mail_url = request.forms.get('settings_notifier_E-Mail_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'E-Mail'", (settings_notifier_E_Mail_enabled, settings_notifier_E_Mail_url))

    settings_notifier_Emby_enabled = request.forms.get('settings_notifier_Emby_enabled')
    if settings_notifier_Emby_enabled == 'on':
        settings_notifier_Emby_enabled = 1
    else:
        settings_notifier_Emby_enabled = 0
    settings_notifier_Emby_url = request.forms.get('settings_notifier_Emby_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Emby'", (settings_notifier_Emby_enabled, settings_notifier_Emby_url))

    settings_notifier_IFTTT_enabled = request.forms.get('settings_notifier_IFTTT_enabled')
    if settings_notifier_IFTTT_enabled == 'on':
        settings_notifier_IFTTT_enabled = 1
    else:
        settings_notifier_IFTTT_enabled = 0
    settings_notifier_IFTTT_url = request.forms.get('settings_notifier_IFTTT_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'IFTTT'", (settings_notifier_IFTTT_enabled, settings_notifier_IFTTT_url))

    settings_notifier_Stride_enabled = request.forms.get('settings_notifier_Stride_enabled')
    if settings_notifier_Stride_enabled == 'on':
        settings_notifier_Stride_enabled = 1
    else:
        settings_notifier_Stride_enabled = 0
    settings_notifier_Stride_url = request.forms.get('settings_notifier_Stride_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Stride'", (settings_notifier_Stride_enabled, settings_notifier_Stride_url))

    settings_notifier_Windows_enabled = request.forms.get('settings_notifier_Windows_enabled')
    if settings_notifier_Windows_enabled == 'on':
        settings_notifier_Windows_enabled = 1
    else:
        settings_notifier_Windows_enabled = 0
    settings_notifier_Windows_url = request.forms.get('settings_notifier_Windows_url')
    c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = 'Windows'", (settings_notifier_Windows_enabled, settings_notifier_Windows_url))

    conn.commit()
    c.close()

    sonarr_full_update()
    radarr_full_update()

    logging.info('Settings saved succesfully.')

    # reschedule full update task according to settings
    sonarr_full_update()

    redirect(ref)

@route(base_url + 'check_update')
def check_update():
    authorize()
    ref = request.environ['HTTP_REFERER']

    check_and_apply_update()

    redirect(ref)

@route(base_url + 'system')
def system():
    authorize()
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
        if job.next_run_time is not None:
            next_run = pretty.date(job.next_run_time.replace(tzinfo=None))
        else:
            next_run = "Never"

        if job.trigger.__str__().startswith('interval'):
            task_list.append([job.name, get_time_from_interval(str(job.trigger)), next_run, job.id])
        elif job.trigger.__str__().startswith('cron'):
            task_list.append([job.name, get_time_from_cron(job.trigger.fields), next_run, job.id])

    i = 0
    with open(os.path.join(config_dir, 'log/bazarr.log')) as f:
        for i, l in enumerate(f, 1):
            pass
        row_count = i
        page_size = int(get_general_settings()[21])
        max_page = int(math.ceil(row_count / (page_size + 0.0)))

    releases = []
    url_releases = 'https://api.github.com/repos/morpheus65535/Bazarr/releases'
    try:
        r = requests.get(url_releases, timeout=15)
        r.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        logging.exception("Error trying to get releases from Github. Http error.")
    except requests.exceptions.ConnectionError as errc:
        logging.exception("Error trying to get releases from Github. Connection Error.")
    except requests.exceptions.Timeout as errt:
        logging.exception("Error trying to get releases from Github. Timeout Error.")
    except requests.exceptions.RequestException as err:
        logging.exception("Error trying to get releases from Github.")
    else:
        for release in r.json():
            releases.append([release['name'],release['body']])

    return template('system', __file__=__file__, bazarr_version=bazarr_version, base_url=base_url, task_list=task_list, row_count=row_count, max_page=max_page, page_size=page_size, releases=releases)

@route(base_url + 'logs/<page:int>')
def get_logs(page):
    authorize()
    page_size = int(get_general_settings()[21])
    begin = (page * page_size) - page_size
    end = (page * page_size) - 1
    logs_complete = []
    for line in reversed(open(os.path.join(config_dir, 'log/bazarr.log')).readlines()):
        logs_complete.append(line.rstrip())
    logs = logs_complete[begin:end]

    return template('logs', logs=logs, base_url=base_url)

@route(base_url + 'execute/<taskid>')
def execute_task(taskid):
    authorize()
    ref = request.environ['HTTP_REFERER']

    execute_now(taskid)

    redirect(ref)


@route(base_url + 'remove_subtitles', method='POST')
def remove_subtitles():
    authorize()
    episodePath = request.forms.get('episodePath')
    language = request.forms.get('language')
    subtitlesPath = request.forms.get('subtitlesPath')
    sonarrSeriesId = request.forms.get('sonarrSeriesId')
    sonarrEpisodeId = request.forms.get('sonarrEpisodeId')

    try:
        os.remove(subtitlesPath)
        result = language_from_alpha3(language) + " subtitles deleted from disk."
        history_log(0, sonarrSeriesId, sonarrEpisodeId, result)
    except OSError:
        pass
    store_subtitles(unicode(episodePath))
    list_missing_subtitles(sonarrSeriesId)


@route(base_url + 'remove_subtitles_movie', method='POST')
def remove_subtitles_movie():
    authorize()
    moviePath = request.forms.get('moviePath')
    language = request.forms.get('language')
    subtitlesPath = request.forms.get('subtitlesPath')
    radarrId = request.forms.get('radarrId')

    try:
        os.remove(subtitlesPath)
        result = language_from_alpha3(language) + " subtitles deleted from disk."
        history_log_movie(0, radarrId, result)
    except OSError:
        pass
    store_subtitles_movie(unicode(moviePath))
    list_missing_subtitles_movies(radarrId)


@route(base_url + 'get_subtitle', method='POST')
def get_subtitle():
    authorize()
    ref = request.environ['HTTP_REFERER']

    episodePath = request.forms.get('episodePath')
    sceneName = request.forms.get('sceneName')
    language = request.forms.get('language')
    hi = request.forms.get('hi')
    sonarrSeriesId = request.forms.get('sonarrSeriesId')
    sonarrEpisodeId = request.forms.get('sonarrEpisodeId')
    # tvdbid = request.forms.get('tvdbid')

    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()
    c.execute("SELECT * FROM table_settings_providers WHERE enabled = 1")
    enabled_providers = c.fetchall()
    c.close()

    providers_list = []
    providers_auth = {}
    if len(enabled_providers) > 0:
        for provider in enabled_providers:
            providers_list.append(provider[0])
            try:
                if provider[2] is not '' and provider[3] is not '':
                    provider_auth = providers_auth.append(provider[0])
                    provider_auth.update({'username':providers[2], 'password':providers[3]})
                else:
                    providers_auth = None
            except:
                providers_auth = None
    else:
        providers_list = None
        providers_auth = None

    try:
        result = download_subtitle(episodePath, language, hi, providers_list, providers_auth, sceneName, 'series')
        if result is not None:
            history_log(1, sonarrSeriesId, sonarrEpisodeId, result)
            send_notifications(sonarrSeriesId, sonarrEpisodeId, result)
            store_subtitles(unicode(episodePath))
            list_missing_subtitles(sonarrSeriesId)
        redirect(ref)
    except OSError:
        pass

@route(base_url + 'get_subtitle_movie', method='POST')
def get_subtitle_movie():
    authorize()
    ref = request.environ['HTTP_REFERER']

    moviePath = request.forms.get('moviePath')
    sceneName = request.forms.get('sceneName')
    language = request.forms.get('language')
    hi = request.forms.get('hi')
    radarrId = request.forms.get('radarrId')
    # tmdbid = request.forms.get('tmdbid')

    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()
    c.execute("SELECT * FROM table_settings_providers WHERE enabled = 1")
    enabled_providers = c.fetchall()
    c.close()

    providers_list = []
    providers_auth = {}
    if len(enabled_providers) > 0:
        for provider in enabled_providers:
            providers_list.append(provider[0])
            try:
                if provider[2] is not '' and provider[3] is not '':
                    provider_auth = providers_auth.append(provider[0])
                    provider_auth.update({'username':providers[2], 'password':providers[3]})
                else:
                    providers_auth = None
            except:
                providers_auth = None
    else:
        providers_list = None
        providers_auth = None

    try:
        result = download_subtitle(moviePath, language, hi, providers_list, providers_auth, sceneName, 'movies')
        if result is not None:
            history_log_movie(1, radarrId, result)
            send_notifications_movie(radarrId, result)
            store_subtitles_movie(unicode(moviePath))
            list_missing_subtitles_movies(radarrId)
        redirect(ref)
    except OSError:
        pass

def configured():
    conn = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = conn.cursor()
    c.execute("UPDATE system SET configured = 1")
    conn.commit()
    c.close()

@route(base_url + 'api/wanted')
def api_wanted():
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()
    data = c.execute("SELECT table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, table_episodes.missing_subtitles FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE table_episodes.missing_subtitles != '[]' ORDER BY table_episodes._rowid_ DESC").fetchall()
    c.close()
    return dict(subtitles=data)

@route(base_url + 'api/history')
def api_history():
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()
    data = c.execute("SELECT table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, strftime('%Y-%m-%d', datetime(table_history.timestamp, 'unixepoch')), table_history.description FROM table_history INNER JOIN table_shows on table_shows.sonarrSeriesId = table_history.sonarrSeriesId INNER JOIN table_episodes on table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId WHERE table_history.action = '1' ORDER BY id DESC").fetchall()
    c.close()
    return dict(subtitles=data)

logging.info('Bazarr is started and waiting for request on http://' + str(ip) + ':' + str(port) + str(base_url))
run(host=ip, port=port, server='waitress', app=app)
logging.info('Bazarr has been stopped.')

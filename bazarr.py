bazarr_version = '0.5.0'

import gc
gc.enable()

import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.insert(0,os.path.join(os.path.dirname(__file__), 'libs/'))

import sqlite3
from init_db import *
from update_db import *

import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger('waitress')
db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
c = db.cursor()
c.execute("SELECT log_level FROM table_settings_general")
log_level = c.fetchone()
c.close()
log_level = log_level[0]
if log_level is None:
    log_level = "INFO"
log_level = getattr(logging, log_level)

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
    fh = TimedRotatingFileHandler(os.path.join(os.path.dirname(__file__), 'data/log/bazarr.log'), when="midnight", interval=1, backupCount=7)
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

from update_modules import *

from bottle import route, run, template, static_file, request, redirect, response
import bottle
bottle.TEMPLATE_PATH.insert(0,os.path.join(os.path.dirname(__file__), 'views/'))
bottle.debug(True)
bottle.TEMPLATES.clear()

from json import dumps
import itertools
import operator
import requests
import pycountry
import pretty
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO
from fdsend import send_file
import urllib
import math
import ast

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
from notifier import send_notifications

# Reset restart required warning on start
conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
c = conn.cursor()
c.execute("UPDATE table_settings_general SET configured = 0, updated = 0")
conn.commit()
c.close()


@route('/')
def redirect_root():
    redirect (base_url)

@route(base_url + 'static/:path#.+#', name='static')
def static(path):
    return static_file(path, root=os.path.join(os.path.dirname(__file__), 'static'))

@route(base_url + 'emptylog')
def emptylog():
    ref = request.environ['HTTP_REFERER']

    fh.doRollover()
    logging.info('Log file emptied')

    redirect(ref)

@route(base_url + 'bazarr.log')
def download_log():
    return static_file('bazarr.log', root=os.path.join(os.path.dirname(__file__), 'data/log/'), download='bazarr.log')

@route(base_url + 'image_proxy/<url:path>', method='GET')
def image_proxy(url):
    from get_sonarr_settings import get_sonarr_settings
    url_sonarr = get_sonarr_settings()[0]
    url_sonarr_short = get_sonarr_settings()[1]
    apikey = get_sonarr_settings()[2]
    url_image = url_sonarr_short + '/' + url + '?apikey=' + apikey
    try:
        img_pil = Image.open(BytesIO(requests.get(url_sonarr_short + '/api' + url_image.split(url_sonarr)[1]).content))
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
    from get_radarr_settings import get_radarr_settings
    url_radarr = get_radarr_settings()[0]
    url_radarr_short = get_radarr_settings()[1]
    apikey = get_radarr_settings()[2]
    try:
        url_image = (url_radarr_short + '/' + url + '?apikey=' + apikey).replace('/fanart.jpg', '/banner.jpg')
        img_pil = Image.open(BytesIO(requests.get(url_radarr_short + '/api' + url_image.split(url_radarr)[1]).content))
    except:
        url_image = url_radarr_short + '/' + url + '?apikey=' + apikey
        img_pil = Image.open(BytesIO(requests.get(url_radarr_short + '/api' + url_image.split(url_radarr)[1]).content))

    img_buffer = BytesIO()
    img_pil.tobytes()
    img_pil.save(img_buffer, img_pil.format)
    img_buffer.seek(0)
    return send_file(img_buffer, ctype=img_pil.format)


@route(base_url)
def redirect_root():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = conn.cursor()
    integration = c.execute("SELECT use_sonarr, use_radarr FROM table_settings_general").fetchone()
    c.close()

    if integration[0] == "True":
        redirect(base_url + 'series')
    elif integration[1] == "True":
        redirect(base_url + 'movies')
    else:
        redirect(base_url + 'settings')


@route(base_url + 'series')
def series():
    import update_db
    single_language = get_general_settings()[7]

    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM table_shows")
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    offset = (int(page) - 1) * 15
    max_page = int(math.ceil(missing_count / 15.0))

    c.execute("SELECT tvdbId, title, path_substitution(path), languages, hearing_impaired, sonarrSeriesId, poster, audio_language FROM table_shows ORDER BY sortTitle ASC LIMIT 15 OFFSET ?", (offset,))
    data = c.fetchall()
    c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1")
    languages = c.fetchall()
    c.execute("SELECT table_shows.sonarrSeriesId, COUNT(table_episodes.missing_subtitles) FROM table_shows LEFT JOIN table_episodes ON table_shows.sonarrSeriesId=table_episodes.sonarrSeriesId WHERE table_shows.languages IS NOT 'None' AND table_episodes.missing_subtitles IS NOT '[]' GROUP BY table_shows.sonarrSeriesId")
    missing_subtitles_list = c.fetchall()
    c.execute("SELECT table_shows.sonarrSeriesId, COUNT(table_episodes.missing_subtitles) FROM table_shows LEFT JOIN table_episodes ON table_shows.sonarrSeriesId=table_episodes.sonarrSeriesId WHERE table_shows.languages IS NOT 'None' GROUP BY table_shows.sonarrSeriesId")
    total_subtitles_list = c.fetchall()
    c.close()
    output = template('series', __file__=__file__, bazarr_version=bazarr_version, rows=data, missing_subtitles_list=missing_subtitles_list, total_subtitles_list=total_subtitles_list, languages=languages, missing_count=missing_count, page=page, max_page=max_page, base_url=base_url, single_language=single_language)
    return output

@route(base_url + 'serieseditor')
def serieseditor():
    single_language = get_general_settings()[7]

    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
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
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
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

    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = conn.cursor()
    c.execute("UPDATE table_shows SET languages = ?, hearing_impaired = ? WHERE sonarrSeriesId LIKE ?", (str(lang), hi, no))
    conn.commit()
    c.close()

    list_missing_subtitles(no)

    redirect(ref)

@route(base_url + 'edit_serieseditor', method='POST')
def edit_serieseditor():
    ref = request.environ['HTTP_REFERER']

    series = request.forms.get('series')
    series = ast.literal_eval(str('[' + series + ']'))
    lang = request.forms.getall('languages')
    hi = request.forms.get('hearing_impaired')

    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
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
    single_language = get_general_settings()[7]
    url_sonarr_short = get_sonarr_settings()[1]

    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    conn.create_function("path_substitution", 1, path_replace)
    c = conn.cursor()

    series_details = []
    series_details = c.execute("SELECT title, overview, poster, fanart, hearing_impaired, tvdbid, audio_language, languages, path_substitution(path) FROM table_shows WHERE sonarrSeriesId LIKE ?", (str(no),)).fetchone()
    tvdbid = series_details[5]

    episodes = c.execute("SELECT title, path_substitution(path), season, episode, subtitles, sonarrSeriesId, missing_subtitles, sonarrEpisodeId, scene_name FROM table_episodes WHERE sonarrSeriesId LIKE ? ORDER BY episode ASC", (str(no),)).fetchall()
    number = len(episodes)
    languages = c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1").fetchall()
    c.close()
    episodes = reversed(sorted(episodes, key=operator.itemgetter(2)))
    seasons_list = []
    for key,season in itertools.groupby(episodes,operator.itemgetter(2)):
        seasons_list.append(list(season))

    return template('episodes', __file__=__file__, bazarr_version=bazarr_version, no=no, details=series_details, languages=languages, seasons=seasons_list, url_sonarr_short=url_sonarr_short, base_url=base_url, tvdbid=tvdbid, number=number)

@route(base_url + 'movies')
def movies():
    import update_db
    single_language = get_general_settings()[7]

    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM table_movies")
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    offset = (int(page) - 1) * 15
    max_page = int(math.ceil(missing_count / 15.0))

    c.execute("SELECT tmdbId, title, path_substitution(path), languages, hearing_impaired, radarrId, poster, audio_language FROM table_movies ORDER BY title ASC LIMIT 15 OFFSET ?", (offset,))
    data = c.fetchall()
    c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1")
    languages = c.fetchall()
    c.close()
    output = template('movies', __file__=__file__, bazarr_version=bazarr_version, rows=data, languages=languages, missing_count=missing_count, page=page, max_page=max_page, base_url=base_url, single_language=single_language)
    return output

@route(base_url + 'movieseditor')
def movieseditor():
    single_language = get_general_settings()[7]

    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace)
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
    ref = request.environ['HTTP_REFERER']

    movies = request.forms.get('movies')
    movies = ast.literal_eval(str('[' + movies + ']'))
    lang = request.forms.getall('languages')
    hi = request.forms.get('hearing_impaired')

    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
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

    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = conn.cursor()
    c.execute("UPDATE table_movies SET languages = ?, hearing_impaired = ? WHERE radarrId LIKE ?", (str(lang), hi, no))
    conn.commit()
    c.close()

    list_missing_subtitles_movies(no)

    redirect(ref)

@route(base_url + 'movie/<no:int>', method='GET')
def movie(no):
    from get_radarr_settings import get_radarr_settings
    single_language = get_general_settings()[7]
    url_radarr_short = get_radarr_settings()[1]

    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    conn.create_function("path_substitution", 1, path_replace)
    c = conn.cursor()

    movies_details = []
    movies_details = c.execute("SELECT title, overview, poster, fanart, hearing_impaired, tmdbid, audio_language, languages, path_substitution(path), subtitles, radarrId, missing_subtitles, sceneName FROM table_movies WHERE radarrId LIKE ?", (str(no),)).fetchone()
    tmdbid = movies_details[5]

    languages = c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1").fetchall()
    c.close()

    return template('movie', __file__=__file__, bazarr_version=bazarr_version, no=no, details=movies_details, languages=languages, url_radarr_short=url_radarr_short, base_url=base_url, tmdbid=tmdbid)

@route(base_url + 'scan_disk/<no:int>', method='GET')
def scan_disk(no):
    ref = request.environ['HTTP_REFERER']

    series_scan_subtitles(no)

    redirect(ref)

@route(base_url + 'scan_disk_movie/<no:int>', method='GET')
def scan_disk_movie(no):
    ref = request.environ['HTTP_REFERER']

    movies_scan_subtitles(no)

    redirect(ref)

@route(base_url + 'search_missing_subtitles/<no:int>', method='GET')
def search_missing_subtitles(no):
    ref = request.environ['HTTP_REFERER']

    series_download_subtitles(no)

    redirect(ref)

@route(base_url + 'search_missing_subtitles_movie/<no:int>', method='GET')
def search_missing_subtitles_movie(no):
    ref = request.environ['HTTP_REFERER']

    movies_download_subtitles(no)

    redirect(ref)

@route(base_url + 'history')
def history():
    return template('history', __file__=__file__, bazarr_version=bazarr_version, base_url=base_url)

@route(base_url + 'historyseries')
def historyseries():
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM table_history")
    row_count = c.fetchone()
    row_count = row_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    offset = (int(page) - 1) * 15
    max_page = int(math.ceil(row_count / 15.0))

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

    c.execute("SELECT table_history.action, table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, table_history.timestamp, table_history.description, table_history.sonarrSeriesId FROM table_history LEFT JOIN table_shows on table_shows.sonarrSeriesId = table_history.sonarrSeriesId LEFT JOIN table_episodes on table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId ORDER BY id DESC LIMIT 15 OFFSET ?", (offset,))
    data = c.fetchall()
    c.close()
    data = reversed(sorted(data, key=operator.itemgetter(4)))
    return template('historyseries', __file__=__file__, bazarr_version=bazarr_version, rows=data, row_count=row_count, page=page, max_page=max_page, stats=stats, base_url=base_url)

@route(base_url + 'historymovies')
def historymovies():
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM table_history_movie")
    row_count = c.fetchone()
    row_count = row_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    offset = (int(page) - 1) * 15
    max_page = int(math.ceil(row_count / 15.0))

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

    c.execute("SELECT table_history_movie.action, table_movies.title, table_history_movie.timestamp, table_history_movie.description, table_history_movie.radarrId FROM table_history_movie LEFT JOIN table_movies on table_movies.radarrId = table_history_movie.radarrId ORDER BY id DESC LIMIT 15 OFFSET ?", (offset,))
    data = c.fetchall()
    c.close()
    data = reversed(sorted(data, key=operator.itemgetter(2)))
    return template('historymovies', __file__=__file__, bazarr_version=bazarr_version, rows=data, row_count=row_count, page=page, max_page=max_page, stats=stats, base_url=base_url)

@route(base_url + 'wanted')
def wanted():
    return template('wanted', __file__=__file__, bazarr_version=bazarr_version, base_url=base_url)

@route(base_url + 'wantedseries')
def wantedseries():
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM table_episodes WHERE missing_subtitles != '[]'")
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    offset = (int(page) - 1) * 15
    max_page = int(math.ceil(missing_count / 15.0))

    c.execute("SELECT table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, table_episodes.missing_subtitles, table_episodes.sonarrSeriesId, path_substitution(table_episodes.path), table_shows.hearing_impaired, table_episodes.sonarrEpisodeId, table_episodes.scene_name FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE table_episodes.missing_subtitles != '[]' ORDER BY table_episodes._rowid_ DESC LIMIT 15 OFFSET ?", (offset,))
    data = c.fetchall()
    c.close()
    return template('wantedseries', __file__=__file__, bazarr_version=bazarr_version, rows=data, missing_count=missing_count, page=page, max_page=max_page, base_url=base_url)

@route(base_url + 'wantedmovies')
def wantedmovies():
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM table_movies WHERE missing_subtitles != '[]'")
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    offset = (int(page) - 1) * 15
    max_page = int(math.ceil(missing_count / 15.0))

    c.execute("SELECT title, missing_subtitles, radarrId, path_substitution(path), hearing_impaired, sceneName FROM table_movies WHERE missing_subtitles != '[]' ORDER BY _rowid_ DESC LIMIT 15 OFFSET ?", (offset,))
    data = c.fetchall()
    c.close()
    return template('wantedmovies', __file__=__file__, bazarr_version=bazarr_version, rows=data, missing_count=missing_count, page=page, max_page=max_page, base_url=base_url)

@route(base_url + 'wanted_search_missing_subtitles')
def wanted_search_missing_subtitles_list():
    ref = request.environ['HTTP_REFERER']

    wanted_search_missing_subtitles()

    redirect(ref)

@route(base_url + 'settings')
def settings():
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()
    c.execute("SELECT * FROM table_settings_general")
    settings_general = c.fetchone()
    c.execute("SELECT * FROM table_settings_languages ORDER BY name")
    settings_languages = c.fetchall()
    c.execute("SELECT * FROM table_settings_providers ORDER BY name")
    settings_providers = c.fetchall()
    c.execute("SELECT * FROM table_settings_sonarr")
    settings_sonarr = c.fetchone()
    c.execute("SELECT * FROM table_settings_radarr")
    settings_radarr = c.fetchone()
    c.execute("SELECT * FROM table_settings_notifier")
    settings_notifier = c.fetchall()
    c.close()
    return template('settings', __file__=__file__, bazarr_version=bazarr_version, settings_general=settings_general, settings_languages=settings_languages, settings_providers=settings_providers, settings_sonarr=settings_sonarr, settings_radarr=settings_radarr, settings_notifier=settings_notifier, base_url=base_url)

@route(base_url + 'save_settings', method='POST')
def save_settings():
    ref = request.environ['HTTP_REFERER']

    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
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
    settings_general_minimum_score = request.forms.get('settings_general_minimum_score')
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

    before = c.execute("SELECT ip, port, base_url, log_level, path_mapping, use_sonarr, use_radarr FROM table_settings_general").fetchone()
    after = (unicode(settings_general_ip), int(settings_general_port), unicode(settings_general_baseurl), unicode(settings_general_loglevel), unicode(settings_general_pathmapping), unicode(settings_general_use_sonarr), unicode(settings_general_use_radarr))
    c.execute("UPDATE table_settings_general SET ip = ?, port = ?, base_url = ?, path_mapping = ?, log_level = ?, branch=?, auto_update=?, single_language=?, minimum_score=?, use_scenename=?, use_postprocessing=?, postprocessing_cmd=?, use_sonarr=?, use_radarr=?", (unicode(settings_general_ip), int(settings_general_port), unicode(settings_general_baseurl), unicode(settings_general_pathmapping), unicode(settings_general_loglevel), unicode(settings_general_branch), unicode(settings_general_automatic), unicode(settings_general_single_language), unicode(settings_general_minimum_score), unicode(settings_general_scenename), unicode(settings_general_use_postprocessing), unicode(settings_general_postprocessing_cmd), unicode(settings_general_use_sonarr), unicode(settings_general_use_radarr)))
    conn.commit()
    if after != before:
        configured()
    get_general_settings()

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
    c.execute("UPDATE table_settings_sonarr SET ip = ?, port = ?, base_url = ?, ssl = ?, apikey = ?, full_update = ?", (settings_sonarr_ip, settings_sonarr_port, settings_sonarr_baseurl, settings_sonarr_ssl, settings_sonarr_apikey, settings_sonarr_sync))
    sonarr_full_update()

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
    c.execute("UPDATE table_settings_radarr SET ip = ?, port = ?, base_url = ?, ssl = ?, apikey = ?, full_update = ?", (settings_radarr_ip, settings_radarr_port, settings_radarr_baseurl, settings_radarr_ssl, settings_radarr_apikey, settings_radarr_sync))
    radarr_full_update()

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


    conn.commit()
    c.close()

    logging.info('Settings saved succesfully.')

    # reschedule full update task according to settings
    sonarr_full_update()

    redirect(ref)

@route(base_url + 'check_update')
def check_update():
    ref = request.environ['HTTP_REFERER']

    check_and_apply_update()

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
        if job.next_run_time is not None:
            next_run = pretty.date(job.next_run_time.replace(tzinfo=None))
        else:
            next_run = "Never"

        if job.trigger.__str__().startswith('interval'):
            task_list.append([job.name, get_time_from_interval(str(job.trigger)), next_run, job.id])
        elif job.trigger.__str__().startswith('cron'):
            task_list.append([job.name, get_time_from_cron(job.trigger.fields), next_run, job.id])

    i = 0
    with open(os.path.join(os.path.dirname(__file__), 'data/log/bazarr.log')) as f:
        for i, l in enumerate(f, 1):
            pass
        row_count = i
        max_page = int(math.ceil(row_count / 50.0))

    return template('system', __file__=__file__, bazarr_version=bazarr_version, base_url=base_url, task_list=task_list, row_count=row_count, max_page=max_page)

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

        try:
            os.remove(subtitlesPath)
            result = pycountry.languages.lookup(language).name + " subtitles deleted from disk."
            history_log(0, sonarrSeriesId, sonarrEpisodeId, result)
        except OSError:
            pass
        store_subtitles(unicode(episodePath))
        list_missing_subtitles(sonarrSeriesId)


@route(base_url + 'remove_subtitles_movie', method='POST')
def remove_subtitles_movie():
        moviePath = request.forms.get('moviePath')
        language = request.forms.get('language')
        subtitlesPath = request.forms.get('subtitlesPath')
        radarrId = request.forms.get('radarrId')

        try:
            os.remove(subtitlesPath)
            result = pycountry.languages.lookup(language).name + " subtitles deleted from disk."
            history_log_movie(0, radarrId, result)
        except OSError:
            pass
        store_subtitles_movie(unicode(moviePath))
        list_missing_subtitles_movies(radarrId)


@route(base_url + 'get_subtitle', method='POST')
def get_subtitle():
        ref = request.environ['HTTP_REFERER']

        episodePath = request.forms.get('episodePath')
        sceneName = request.forms.get('sceneName')
        language = request.forms.get('language')
        hi = request.forms.get('hi')
        sonarrSeriesId = request.forms.get('sonarrSeriesId')
        sonarrEpisodeId = request.forms.get('sonarrEpisodeId')
        tvdbid = request.forms.get('tvdbid')

        db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
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
        ref = request.environ['HTTP_REFERER']

        moviePath = request.forms.get('moviePath')
        sceneName = request.forms.get('sceneName')
        language = request.forms.get('language')
        hi = request.forms.get('hi')
        radarrId = request.forms.get('radarrId')
        tmdbid = request.forms.get('tmdbid')

        db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
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
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = conn.cursor()
    c.execute("UPDATE table_settings_general SET configured = 1")
    conn.commit()
    c.close()

@route(base_url + 'api/wanted')
def api_wanted():
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()
    data = c.execute("SELECT table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, table_episodes.missing_subtitles FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE table_episodes.missing_subtitles != '[]' ORDER BY table_episodes._rowid_ DESC").fetchall()
    c.close()
    return dict(subtitles=data)

@route(base_url + 'api/history')
def api_history():
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()
    data = c.execute("SELECT table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, strftime('%Y-%m-%d', datetime(table_history.timestamp, 'unixepoch')), table_history.description FROM table_history INNER JOIN table_shows on table_shows.sonarrSeriesId = table_history.sonarrSeriesId INNER JOIN table_episodes on table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId WHERE table_history.action = '1' ORDER BY id DESC").fetchall()
    c.close()
    return dict(subtitles=data)

logging.info('Bazarr is started and waiting for request on http://' + str(ip) + ':' + str(port) + str(base_url))
run(host=ip, port=port, server='waitress')
logging.info('Bazarr has been stopped.')

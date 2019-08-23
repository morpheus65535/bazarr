# coding=utf-8

bazarr_version = '0.8.1'

import gc
import sys
import libs
import bottle
import itertools
import operator
import pretty
import math
import ast
import hashlib
import urllib
import warnings
import queueconfig
import platform
import apprise

from get_args import args
from init import *
from update_db import *
from notifier import update_notifier
from logger import configure_logging, empty_log


# Try to import gevent and exit if it's not available. This one is required to use websocket.
try:
    import gevent
except ImportError:
    import logging
    
    logging.exception('BAZARR require gevent Python module to be installed using pip.')
    try:
        import os
        from get_args import args
        
        stop_file = open(os.path.join(args.config_dir, "bazarr.stop"), "w")
    except Exception as e:
        logging.error('BAZARR Cannot create bazarr.stop file.')
    else:
        stop_file.write('')
        stop_file.close()
        os._exit(0)

from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler

from io import BytesIO
from six import text_type
from beaker.middleware import SessionMiddleware
from cork import Cork
from bottle import route, template, static_file, request, redirect, response, HTTPError, app, hook
from datetime import timedelta
from get_languages import load_language_in_db, language_from_alpha3
from get_providers import get_providers, get_providers_auth, list_throttled_providers
from get_series import *
from get_episodes import *

from list_subtitles import store_subtitles, store_subtitles_movie, series_scan_subtitles, movies_scan_subtitles, \
    list_missing_subtitles, list_missing_subtitles_movies
from get_subtitle import download_subtitle, series_download_subtitles, movies_download_subtitles, \
    manual_search, manual_download_subtitle, manual_upload_subtitle
from utils import history_log, history_log_movie
from scheduler import *
from notifier import send_notifications, send_notifications_movie
from config import settings, url_sonarr, url_radarr, url_radarr_short, url_sonarr_short, base_url
from helper import path_replace_movie
from subliminal_patch.core import SUBTITLE_EXTENSIONS
from subliminal_patch.extensions import provider_registry as provider_manager

reload(sys)
sys.setdefaultencoding('utf8')
gc.enable()
update_notifier()

os.environ["SZ_USER_AGENT"] = "Bazarr/1"
os.environ["BAZARR_VERSION"] = bazarr_version

configure_logging(settings.general.getboolean('debug') or args.debug)

# Check and install update on startup when running on Windows from installer
if args.release_update:
    check_and_apply_update()

if settings.proxy.type != 'None':
    if settings.proxy.username != '' and settings.proxy.password != '':
        proxy = settings.proxy.type + '://' + settings.proxy.username + ':' + settings.proxy.password + '@' + \
                settings.proxy.url + ':' + settings.proxy.port
    else:
        proxy = settings.proxy.type + '://' + settings.proxy.url + ':' + settings.proxy.port
    os.environ['HTTP_PROXY'] = str(proxy)
    os.environ['HTTPS_PROXY'] = str(proxy)
    os.environ['NO_PROXY'] = str(settings.proxy.exclude)

bottle.TEMPLATE_PATH.insert(0, os.path.join(os.path.dirname(__file__), '../views/'))
if "PYCHARM_HOSTED" in os.environ:
    bottle.debug(True)
    bottle.TEMPLATES.clear()
else:
    bottle.ERROR_PAGE_TEMPLATE = bottle.ERROR_PAGE_TEMPLATE.replace('if DEBUG and', 'if')

# Reset restart required warning on start
conn = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
c = conn.cursor()
c.execute("UPDATE system SET configured = 0, updated = 0")
conn.commit()
c.close()

# Load languages in database
load_language_in_db()

aaa = Cork(os.path.normpath(os.path.join(args.config_dir, 'config')))

app = app()
session_opts = {
    'session.cookie_expires': True,
    'session.key': 'Bazarr',
    'session.httponly': True,
    'session.timeout': 3600 * 24,  # 1 day
    'session.type': 'cookie',
    'session.validate_key': True
}
app = SessionMiddleware(app, session_opts)
login_auth = settings.auth.type


def custom_auth_basic(check):
    def decorator(func):
        def wrapper(*a, **ka):
            if settings.auth.type == 'basic':
                user, password = request.auth or (None, None)
                if user is None or not check(user, password):
                    err = HTTPError(401, "Access denied")
                    err.add_header('WWW-Authenticate', 'Basic realm="Bazarr"')
                    return err
                return func(*a, **ka)
            else:
                return func(*a, **ka)
        
        return wrapper
    
    return decorator


def check_credentials(user, pw):
    username = settings.auth.username
    password = settings.auth.password
    if hashlib.md5(pw).hexdigest() == password and user == username:
        return True
    return False


def authorize():
    if login_auth == 'form':
        aaa = Cork(os.path.normpath(os.path.join(args.config_dir, 'config')))
        aaa.require(fail_redirect=(base_url + 'login'))


def post_get(name, default=''):
    return request.POST.get(name, default).strip()


@hook('before_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'


@route(base_url + 'login')
def login_form():
    msg = bottle.request.query.get('msg', '')
    return template('login', base_url=base_url, msg=msg)


@route(base_url + 'login', method='POST')
def login():
    aaa = Cork(os.path.normpath(os.path.join(args.config_dir, 'config')))
    username = post_get('username')
    password = post_get('password')
    aaa.login(username, password, success_redirect=base_url, fail_redirect=(base_url + 'login?msg=fail'))


@route(base_url + 'logout')
def logout():
    aaa.logout(success_redirect=(base_url + 'login'))


@route('/')
@custom_auth_basic(check_credentials)
def redirect_root():
    authorize()
    redirect(base_url)


@route(base_url + 'shutdown')
def shutdown():
    try:
        stop_file = open(os.path.join(args.config_dir, "bazarr.stop"), "w")
    except Exception as e:
        logging.error('BAZARR Cannot create bazarr.stop file.')
    else:
        stop_file.write('')
        stop_file.close()
        server.stop()


@route(base_url + 'restart')
def restart():
    try:
        server.stop()
    except:
        logging.error('BAZARR Cannot stop CherryPy.')
    else:
        try:
            restart_file = open(os.path.join(args.config_dir, "bazarr.restart"), "w")
        except Exception as e:
            logging.error('BAZARR Cannot create bazarr.restart file.')
        else:
            # print 'Bazarr is being restarted...'
            logging.info('Bazarr is being restarted...')
            restart_file.write('')
            restart_file.close()


@route(base_url + 'wizard')
@custom_auth_basic(check_credentials)
def wizard():
    authorize()
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    settings_languages = c.execute("SELECT * FROM table_settings_languages ORDER BY name").fetchall()
    settings_providers = sorted(provider_manager.names())
    c.close()
    
    return template('wizard', bazarr_version=bazarr_version, settings=settings,
                    settings_languages=settings_languages, settings_providers=settings_providers,
                    base_url=base_url)


@route(base_url + 'save_wizard', method='POST')
@custom_auth_basic(check_credentials)
def save_wizard():
    authorize()
    
    conn = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = conn.cursor()
    
    settings_general_ip = request.forms.get('settings_general_ip')
    settings_general_port = request.forms.get('settings_general_port')
    settings_general_baseurl = request.forms.get('settings_general_baseurl')
    if not settings_general_baseurl.endswith('/'):
        settings_general_baseurl += '/'
    settings_general_sourcepath = request.forms.getall('settings_general_sourcepath')
    settings_general_destpath = request.forms.getall('settings_general_destpath')
    settings_general_pathmapping = []
    settings_general_pathmapping.extend([list(a) for a in zip(settings_general_sourcepath, settings_general_destpath)])
    settings_general_sourcepath_movie = request.forms.getall('settings_general_sourcepath_movie')
    settings_general_destpath_movie = request.forms.getall('settings_general_destpath_movie')
    settings_general_pathmapping_movie = []
    settings_general_pathmapping_movie.extend(
        [list(a) for a in zip(settings_general_sourcepath_movie, settings_general_destpath_movie)])
    settings_general_single_language = request.forms.get('settings_general_single_language')
    if settings_general_single_language is None:
        settings_general_single_language = 'False'
    else:
        settings_general_single_language = 'True'
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
    settings_general_embedded = request.forms.get('settings_general_embedded')
    if settings_general_embedded is None:
        settings_general_embedded = 'False'
    else:
        settings_general_embedded = 'True'
    settings_subfolder = request.forms.get('settings_subfolder')
    settings_subfolder_custom = request.forms.get('settings_subfolder_custom')
    settings_upgrade_subs = request.forms.get('settings_upgrade_subs')
    if settings_upgrade_subs is None:
        settings_upgrade_subs = 'False'
    else:
        settings_upgrade_subs = 'True'
    settings_days_to_upgrade_subs = request.forms.get('settings_days_to_upgrade_subs')
    settings_upgrade_manual = request.forms.get('settings_upgrade_manual')
    if settings_upgrade_manual is None:
        settings_upgrade_manual = 'False'
    else:
        settings_upgrade_manual = 'True'
    
    settings.general.ip = text_type(settings_general_ip)
    settings.general.port = text_type(settings_general_port)
    settings.general.base_url = text_type(settings_general_baseurl)
    settings.general.path_mappings = text_type(settings_general_pathmapping)
    settings.general.single_language = text_type(settings_general_single_language)
    settings.general.use_sonarr = text_type(settings_general_use_sonarr)
    settings.general.use_radarr = text_type(settings_general_use_radarr)
    settings.general.path_mappings_movie = text_type(settings_general_pathmapping_movie)
    settings.general.subfolder = text_type(settings_subfolder)
    settings.general.subfolder_custom = text_type(settings_subfolder_custom)
    settings.general.use_embedded_subs = text_type(settings_general_embedded)
    settings.general.upgrade_subs = text_type(settings_upgrade_subs)
    settings.general.days_to_upgrade_subs = text_type(settings_days_to_upgrade_subs)
    settings.general.upgrade_manual = text_type(settings_upgrade_manual)
    
    settings_sonarr_ip = request.forms.get('settings_sonarr_ip')
    settings_sonarr_port = request.forms.get('settings_sonarr_port')
    settings_sonarr_baseurl = request.forms.get('settings_sonarr_baseurl')
    settings_sonarr_ssl = request.forms.get('settings_sonarr_ssl')
    if settings_sonarr_ssl is None:
        settings_sonarr_ssl = 'False'
    else:
        settings_sonarr_ssl = 'True'
    settings_sonarr_apikey = request.forms.get('settings_sonarr_apikey')
    settings_sonarr_only_monitored = request.forms.get('settings_sonarr_only_monitored')
    if settings_sonarr_only_monitored is None:
        settings_sonarr_only_monitored = 'False'
    else:
        settings_sonarr_only_monitored = 'True'
    
    settings.sonarr.ip = text_type(settings_sonarr_ip)
    settings.sonarr.port = text_type(settings_sonarr_port)
    settings.sonarr.base_url = text_type(settings_sonarr_baseurl)
    settings.sonarr.ssl = text_type(settings_sonarr_ssl)
    settings.sonarr.apikey = text_type(settings_sonarr_apikey)
    settings.sonarr.only_monitored = text_type(settings_sonarr_only_monitored)
    
    settings_radarr_ip = request.forms.get('settings_radarr_ip')
    settings_radarr_port = request.forms.get('settings_radarr_port')
    settings_radarr_baseurl = request.forms.get('settings_radarr_baseurl')
    settings_radarr_ssl = request.forms.get('settings_radarr_ssl')
    if settings_radarr_ssl is None:
        settings_radarr_ssl = 'False'
    else:
        settings_radarr_ssl = 'True'
    settings_radarr_apikey = request.forms.get('settings_radarr_apikey')
    settings_radarr_only_monitored = request.forms.get('settings_radarr_only_monitored')
    if settings_radarr_only_monitored is None:
        settings_radarr_only_monitored = 'False'
    else:
        settings_radarr_only_monitored = 'True'
    
    settings.radarr.ip = text_type(settings_radarr_ip)
    settings.radarr.port = text_type(settings_radarr_port)
    settings.radarr.base_url = text_type(settings_radarr_baseurl)
    settings.radarr.ssl = text_type(settings_radarr_ssl)
    settings.radarr.apikey = text_type(settings_radarr_apikey)
    settings.radarr.only_monitored = text_type(settings_radarr_only_monitored)
    
    settings_subliminal_providers = request.forms.getall('settings_subliminal_providers')
    settings.general.enabled_providers = u'' if not settings_subliminal_providers else ','.join(
        settings_subliminal_providers)
    
    settings_addic7ed_random_agents = request.forms.get('settings_addic7ed_random_agents')
    if settings_addic7ed_random_agents is None:
        settings_addic7ed_random_agents = 'False'
    else:
        settings_addic7ed_random_agents = 'True'
    
    settings_opensubtitles_vip = request.forms.get('settings_opensubtitles_vip')
    if settings_opensubtitles_vip is None:
        settings_opensubtitles_vip = 'False'
    else:
        settings_opensubtitles_vip = 'True'
    
    settings_opensubtitles_ssl = request.forms.get('settings_opensubtitles_ssl')
    if settings_opensubtitles_ssl is None:
        settings_opensubtitles_ssl = 'False'
    else:
        settings_opensubtitles_ssl = 'True'
    
    settings_opensubtitles_skip_wrong_fps = request.forms.get('settings_opensubtitles_skip_wrong_fps')
    if settings_opensubtitles_skip_wrong_fps is None:
        settings_opensubtitles_skip_wrong_fps = 'False'
    else:
        settings_opensubtitles_skip_wrong_fps = 'True'
    
    settings.addic7ed.username = request.forms.get('settings_addic7ed_username')
    settings.addic7ed.password = request.forms.get('settings_addic7ed_password')
    settings.addic7ed.random_agents = text_type(settings_addic7ed_random_agents)
    settings.assrt.token = request.forms.get('settings_assrt_token')
    settings.legendastv.username = request.forms.get('settings_legendastv_username')
    settings.legendastv.password = request.forms.get('settings_legendastv_password')
    settings.opensubtitles.username = request.forms.get('settings_opensubtitles_username')
    settings.opensubtitles.password = request.forms.get('settings_opensubtitles_password')
    settings.opensubtitles.vip = text_type(settings_opensubtitles_vip)
    settings.opensubtitles.ssl = text_type(settings_opensubtitles_ssl)
    settings.opensubtitles.skip_wrong_fps = text_type(settings_opensubtitles_skip_wrong_fps)
    settings.xsubs.username = request.forms.get('settings_xsubs_username')
    settings.xsubs.password = request.forms.get('settings_xsubs_password')
    settings.napisy24.username = request.forms.get('settings_napisy24_username')
    settings.napisy24.password = request.forms.get('settings_napisy24_password')
    settings.subscene.username = request.forms.get('settings_subscene_username')
    settings.subscene.password = request.forms.get('settings_subscene_password')
    settings.betaseries.token = request.forms.get('settings_betaseries_token')
    
    settings_subliminal_languages = request.forms.getall('settings_subliminal_languages')
    c.execute("UPDATE table_settings_languages SET enabled = 0")
    for item in settings_subliminal_languages:
        c.execute("UPDATE table_settings_languages SET enabled = '1' WHERE code2 = ?", (item,))
    
    settings_serie_default_enabled = request.forms.get('settings_serie_default_enabled')
    if settings_serie_default_enabled is None:
        settings_serie_default_enabled = 'False'
    else:
        settings_serie_default_enabled = 'True'
    settings.general.serie_default_enabled = text_type(settings_serie_default_enabled)
    
    settings_serie_default_languages = str(request.forms.getall('settings_serie_default_languages'))
    if settings_serie_default_languages == "['None']":
        settings_serie_default_languages = 'None'
    settings.general.serie_default_language = text_type(settings_serie_default_languages)
    
    settings_serie_default_hi = request.forms.get('settings_serie_default_hi')
    if settings_serie_default_hi is None:
        settings_serie_default_hi = 'False'
    else:
        settings_serie_default_hi = 'True'
    settings.general.serie_default_hi = text_type(settings_serie_default_hi)
    
    settings_movie_default_enabled = request.forms.get('settings_movie_default_enabled')
    if settings_movie_default_enabled is None:
        settings_movie_default_enabled = 'False'
    else:
        settings_movie_default_enabled = 'True'
    settings.general.movie_default_enabled = text_type(settings_movie_default_enabled)
    
    settings_movie_default_languages = str(request.forms.getall('settings_movie_default_languages'))
    if settings_movie_default_languages == "['None']":
        settings_movie_default_languages = 'None'
    settings.general.movie_default_language = text_type(settings_movie_default_languages)
    
    settings_movie_default_hi = request.forms.get('settings_movie_default_hi')
    if settings_movie_default_hi is None:
        settings_movie_default_hi = 'False'
    else:
        settings_movie_default_hi = 'True'
    settings.general.movie_default_hi = text_type(settings_movie_default_hi)
    
    settings_movie_default_forced = str(request.forms.getall('settings_movie_default_forced'))
    settings.general.movie_default_forced = text_type(settings_movie_default_forced)
    
    with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
        settings.write(handle)
    
    conn.commit()
    c.close()
    
    configured()
    redirect(base_url)


@route(base_url + 'static/:path#.+#', name='static')
@custom_auth_basic(check_credentials)
def static(path):
    return static_file(path, root=os.path.join(os.path.dirname(__file__), '../static'))


@route(base_url + 'emptylog')
@custom_auth_basic(check_credentials)
def emptylog():
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    empty_log()
    logging.info('BAZARR Log file emptied')
    
    redirect(ref)


@route(base_url + 'bazarr.log')
@custom_auth_basic(check_credentials)
def download_log():
    authorize()
    return static_file('bazarr.log', root=os.path.join(args.config_dir, 'log/'), download='bazarr.log')


@route(base_url + 'image_proxy/<url:path>', method='GET')
@custom_auth_basic(check_credentials)
def image_proxy(url):
    authorize()
    apikey = settings.sonarr.apikey
    url_image = url_sonarr_short + '/' + url + '?apikey=' + apikey
    try:
        image_buffer = BytesIO(
            requests.get(url_sonarr + '/api' + url_image.split(url_sonarr)[1], timeout=15, verify=False).content)
    except:
        return None
    else:
        image_buffer.seek(0)
        bytes = image_buffer.read()
        response.set_header('Content-type', 'image/jpeg')
        return bytes


@route(base_url + 'image_proxy_movies/<url:path>', method='GET')
@custom_auth_basic(check_credentials)
def image_proxy_movies(url):
    authorize()
    apikey = settings.radarr.apikey
    try:
        url_image = (url_radarr_short + '/' + url + '?apikey=' + apikey).replace('/fanart.jpg', '/banner.jpg')
        image_buffer = BytesIO(
            requests.get(url_radarr + '/api' + url_image.split(url_radarr)[1], timeout=15, verify=False).content)
    except:
        url_image = url_radarr_short + '/' + url + '?apikey=' + apikey
        image_buffer = BytesIO(
            requests.get(url_radarr + '/api' + url_image.split(url_radarr)[1], timeout=15, verify=False).content)
    else:
        image_buffer.seek(0)
        bytes = image_buffer.read()
        response.set_header('Content-type', 'image/jpeg')
        return bytes


@route(base_url)
@route(base_url.rstrip('/'))
@custom_auth_basic(check_credentials)
def redirect_root():
    authorize()
    if settings.general.getboolean('use_sonarr'):
        redirect(base_url + 'series')
    elif settings.general.getboolean('use_radarr'):
        redirect(base_url + 'movies')
    elif not settings.general.enabled_providers:
        redirect(base_url + 'wizard')
    else:
        redirect(base_url + 'settings')


@route(base_url + 'series')
@custom_auth_basic(check_credentials)
def series():
    authorize()
    single_language = settings.general.getboolean('single_language')
    
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()
    
    c.execute("SELECT COUNT(*) FROM table_shows")
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    page_size = int(settings.general.page_size)
    offset = (int(page) - 1) * page_size
    max_page = int(math.ceil(missing_count / (page_size + 0.0)))
    
    if settings.sonarr.getboolean('only_monitored'):
        monitored_only_query_string = ' AND monitored = "True"'
    else:
        monitored_only_query_string = ""
    
    c.execute(
        "SELECT tvdbId, title, path_substitution(path), languages, hearing_impaired, sonarrSeriesId, poster, audio_language, forced FROM table_shows ORDER BY sortTitle ASC LIMIT ? OFFSET ?",
        (page_size, offset,))
    data = c.fetchall()
    c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1")
    languages = c.fetchall()
    c.execute(
        "SELECT table_shows.sonarrSeriesId, COUNT(table_episodes.missing_subtitles) FROM table_shows LEFT JOIN table_episodes ON table_shows.sonarrSeriesId=table_episodes.sonarrSeriesId WHERE table_shows.languages IS NOT 'None' AND table_episodes.missing_subtitles IS NOT '[]'" + monitored_only_query_string + " GROUP BY table_shows.sonarrSeriesId")
    missing_subtitles_list = c.fetchall()
    c.execute(
        "SELECT table_shows.sonarrSeriesId, COUNT(table_episodes.missing_subtitles) FROM table_shows LEFT JOIN table_episodes ON table_shows.sonarrSeriesId=table_episodes.sonarrSeriesId WHERE table_shows.languages IS NOT 'None'" + monitored_only_query_string + " GROUP BY table_shows.sonarrSeriesId")
    total_subtitles_list = c.fetchall()
    c.close()
    output = template('series', bazarr_version=bazarr_version, rows=data,
                      missing_subtitles_list=missing_subtitles_list, total_subtitles_list=total_subtitles_list,
                      languages=languages, missing_count=missing_count, page=page, max_page=max_page, base_url=base_url,
                      single_language=single_language, page_size=page_size, current_port=settings.general.port)
    return output


@route(base_url + 'serieseditor')
@custom_auth_basic(check_credentials)
def serieseditor():
    authorize()
    single_language = settings.general.getboolean('single_language')
    
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()
    
    c.execute("SELECT COUNT(*) FROM table_shows")
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    
    c.execute(
        "SELECT tvdbId, title, path_substitution(path), languages, hearing_impaired, sonarrSeriesId, poster, audio_language, forced FROM table_shows ORDER BY title ASC")
    data = c.fetchall()
    c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1")
    languages = c.fetchall()
    c.close()
    output = template('serieseditor', bazarr_version=bazarr_version, rows=data, languages=languages,
                      missing_count=missing_count, base_url=base_url, single_language=single_language,
                      current_port=settings.general.port)
    return output


@route(base_url + 'search_json/<query>', method='GET')
@custom_auth_basic(check_credentials)
def search_json(query):
    authorize()
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    
    search_list = []
    if settings.general.getboolean('use_sonarr'):
        c.execute("SELECT title, sonarrSeriesId, year FROM table_shows WHERE title LIKE ? ORDER BY title",
                  ('%' + query + '%',))
        series = c.fetchall()
        for serie in series:
            search_list.append(dict([('name', re.sub(r'\ \(\d{4}\)', '', serie[0]) + ' (' + serie[2] + ')'),
                                     ('url', base_url + 'episodes/' + str(serie[1]))]))
    
    if settings.general.getboolean('use_radarr'):
        c.execute("SELECT title, radarrId, year FROM table_movies WHERE title LIKE ? ORDER BY title",
                  ('%' + query + '%',))
        movies = c.fetchall()
        for movie in movies:
            search_list.append(dict([('name', re.sub(r'\ \(\d{4}\)', '', movie[0]) + ' (' + movie[2] + ')'),
                                     ('url', base_url + 'movie/' + str(movie[1]))]))
    c.close()
    
    response.content_type = 'application/json'
    return dict(items=search_list)


@route(base_url + 'edit_series/<no:int>', method='POST')
@custom_auth_basic(check_credentials)
def edit_series(no):
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    lang = request.forms.getall('languages')
    if len(lang) > 0:
        pass
    else:
        lang = 'None'
    
    single_language = settings.general.getboolean('single_language')
    if single_language:
        if str(lang) == "['None']":
            lang = 'None'
        else:
            lang = str(lang)
    else:
        if str(lang) == "['']":
            lang = '[]'
    
    hi = request.forms.get('hearing_impaired')
    forced = request.forms.get('forced')
    
    if hi == "on":
        hi = "True"
    else:
        hi = "False"
    
    conn = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = conn.cursor()
    c.execute("UPDATE table_shows SET languages = ?, hearing_impaired = ?, forced = ? WHERE sonarrSeriesId LIKE ?",
              (str(lang), hi, forced, no))
    conn.commit()
    c.close()
    
    list_missing_subtitles(no)
    
    redirect(ref)


@route(base_url + 'edit_serieseditor', method='POST')
@custom_auth_basic(check_credentials)
def edit_serieseditor():
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    series = request.forms.get('series')
    series = ast.literal_eval(str('[' + series + ']'))
    lang = request.forms.getall('languages')
    hi = request.forms.get('hearing_impaired')
    forced = request.forms.get('forced')
    
    conn = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
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
        if forced != '':
            c.execute("UPDATE table_shows SET forced = ? WHERE sonarrSeriesId LIKE ?", (forced, serie))
    
    conn.commit()
    c.close()
    
    for serie in series:
        list_missing_subtitles(serie)
    
    redirect(ref)


@route(base_url + 'episodes/<no:int>', method='GET')
@custom_auth_basic(check_credentials)
def episodes(no):
    authorize()
    # single_language = settings.general.getboolean('single_language')
    
    conn = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    conn.create_function("path_substitution", 1, path_replace)
    c = conn.cursor()
    
    series_details = []
    series_details = c.execute(
        "SELECT title, overview, poster, fanart, hearing_impaired, tvdbid, audio_language, languages, path_substitution(path), forced FROM table_shows WHERE sonarrSeriesId LIKE ?",
        (str(no),)).fetchone()
    tvdbid = series_details[5]
    
    episodes = c.execute(
        "SELECT title, path_substitution(path), season, episode, subtitles, sonarrSeriesId, missing_subtitles, sonarrEpisodeId, scene_name, monitored, failedAttempts FROM table_episodes WHERE sonarrSeriesId LIKE ? ORDER BY episode ASC",
        (str(no),)).fetchall()
    number = len(episodes)
    languages = c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1").fetchall()
    c.close()
    episodes = reversed(sorted(episodes, key=operator.itemgetter(2)))
    seasons_list = []
    for key, season in itertools.groupby(episodes, operator.itemgetter(2)):
        seasons_list.append(list(season))
    
    return template('episodes', bazarr_version=bazarr_version, no=no, details=series_details,
                    languages=languages, seasons=seasons_list, url_sonarr_short=url_sonarr_short, base_url=base_url,
                    tvdbid=tvdbid, number=number, current_port=settings.general.port)


@route(base_url + 'movies')
@custom_auth_basic(check_credentials)
def movies():
    authorize()
    single_language = settings.general.getboolean('single_language')
    
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace_movie)
    c = db.cursor()
    
    c.execute("SELECT COUNT(*) FROM table_movies")
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    page_size = int(settings.general.page_size)
    offset = (int(page) - 1) * page_size
    max_page = int(math.ceil(missing_count / (page_size + 0.0)))
    
    c.execute(
        "SELECT tmdbId, title, path_substitution(path), languages, hearing_impaired, radarrId, poster, audio_language, monitored, sceneName, forced FROM table_movies ORDER BY sortTitle ASC LIMIT ? OFFSET ?",
        (page_size, offset,))
    data = c.fetchall()
    c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1")
    languages = c.fetchall()
    c.close()
    output = template('movies', bazarr_version=bazarr_version, rows=data, languages=languages,
                      missing_count=missing_count, page=page, max_page=max_page, base_url=base_url,
                      single_language=single_language, page_size=page_size, current_port=settings.general.port)
    return output


@route(base_url + 'movieseditor')
@custom_auth_basic(check_credentials)
def movieseditor():
    authorize()
    single_language = settings.general.getboolean('single_language')
    
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace_movie)
    c = db.cursor()
    
    c.execute("SELECT COUNT(*) FROM table_movies")
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    
    c.execute(
        "SELECT tmdbId, title, path_substitution(path), languages, hearing_impaired, radarrId, poster, audio_language, forced FROM table_movies ORDER BY title ASC")
    data = c.fetchall()
    c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1")
    languages = c.fetchall()
    c.close()
    output = template('movieseditor', bazarr_version=bazarr_version, rows=data, languages=languages,
                      missing_count=missing_count, base_url=base_url, single_language=single_language,
                      current_port=settings.general.port)
    return output


@route(base_url + 'edit_movieseditor', method='POST')
@custom_auth_basic(check_credentials)
def edit_movieseditor():
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    movies = request.forms.get('movies')
    movies = ast.literal_eval(str('[' + movies + ']'))
    lang = request.forms.getall('languages')
    hi = request.forms.get('hearing_impaired')
    forced = request.forms.get('forced')
    
    conn = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
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
        if forced != '':
            c.execute("UPDATE table_movies SET forced = ? WHERE radarrId LIKE ?", (forced, movie))
    
    conn.commit()
    c.close()
    
    for movie in movies:
        list_missing_subtitles_movies(movie)
    
    redirect(ref)


@route(base_url + 'edit_movie/<no:int>', method='POST')
@custom_auth_basic(check_credentials)
def edit_movie(no):
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    lang = request.forms.getall('languages')
    if len(lang) > 0:
        pass
    else:
        lang = 'None'
    
    single_language = settings.general.getboolean('single_language')
    if single_language:
        if str(lang) == "['None']":
            lang = 'None'
        else:
            lang = str(lang)
    else:
        if str(lang) == "['']":
            lang = '[]'
    
    hi = request.forms.get('hearing_impaired')
    forced = request.forms.get('forced')
    
    if hi == "on":
        hi = "True"
    else:
        hi = "False"
    
    conn = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = conn.cursor()
    c.execute("UPDATE table_movies SET languages = ?, hearing_impaired = ?, forced = ? WHERE radarrId LIKE ?",
              (str(lang), hi, forced, no))
    conn.commit()
    c.close()
    
    list_missing_subtitles_movies(no)
    
    redirect(ref)


@route(base_url + 'movie/<no:int>', method='GET')
@custom_auth_basic(check_credentials)
def movie(no):
    authorize()
    
    conn = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    conn.create_function("path_substitution", 1, path_replace_movie)
    c = conn.cursor()
    
    movies_details = []
    movies_details = c.execute(
        "SELECT title, overview, poster, fanart, hearing_impaired, tmdbid, audio_language, languages, path_substitution(path), subtitles, radarrId, missing_subtitles, sceneName, monitored, failedAttempts, forced FROM table_movies WHERE radarrId LIKE ?",
        (str(no),)).fetchone()
    tmdbid = movies_details[5]
    
    languages = c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1").fetchall()
    c.close()
    
    return template('movie', bazarr_version=bazarr_version, no=no, details=movies_details,
                    languages=languages, url_radarr_short=url_radarr_short, base_url=base_url, tmdbid=tmdbid,
                    current_port=settings.general.port)


@route(base_url + 'scan_disk/<no:int>', method='GET')
@custom_auth_basic(check_credentials)
def scan_disk(no):
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    series_scan_subtitles(no)
    
    redirect(ref)


@route(base_url + 'scan_disk_movie/<no:int>', method='GET')
@custom_auth_basic(check_credentials)
def scan_disk_movie(no):
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    movies_scan_subtitles(no)
    
    redirect(ref)


@route(base_url + 'search_missing_subtitles/<no:int>', method='GET')
@custom_auth_basic(check_credentials)
def search_missing_subtitles(no):
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    add_job(series_download_subtitles, args=[no], name=('search_missing_subtitles_' + str(no)))
    
    redirect(ref)


@route(base_url + 'search_missing_subtitles_movie/<no:int>', method='GET')
@custom_auth_basic(check_credentials)
def search_missing_subtitles_movie(no):
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    add_job(movies_download_subtitles, args=[no], name=('movies_download_subtitles_' + str(no)))
    
    redirect(ref)


@route(base_url + 'history')
@custom_auth_basic(check_credentials)
def history():
    authorize()
    return template('history', bazarr_version=bazarr_version, base_url=base_url, current_port=settings.general.port)


@route(base_url + 'historyseries')
@custom_auth_basic(check_credentials)
def historyseries():
    authorize()
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    
    c.execute("SELECT COUNT(*) FROM table_history")
    row_count = c.fetchone()
    row_count = row_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    page_size = int(settings.general.page_size)
    offset = (int(page) - 1) * page_size
    max_page = int(math.ceil(row_count / (page_size + 0.0)))
    
    now = datetime.now()
    today = []
    thisweek = []
    thisyear = []
    stats = c.execute("SELECT timestamp FROM table_history WHERE action > 0").fetchall()
    total = len(stats)
    for stat in stats:
        if now - timedelta(hours=24) <= datetime.fromtimestamp(stat[0]) <= now:
            today.append(datetime.fromtimestamp(stat[0]).date())
        if now - timedelta(weeks=1) <= datetime.fromtimestamp(stat[0]) <= now:
            thisweek.append(datetime.fromtimestamp(stat[0]).date())
        if now - timedelta(weeks=52) <= datetime.fromtimestamp(stat[0]) <= now:
            thisyear.append(datetime.fromtimestamp(stat[0]).date())
    stats = [len(today), len(thisweek), len(thisyear), total]
    
    c.execute(
        "SELECT table_history.action, table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, table_history.timestamp, table_history.description, table_history.sonarrSeriesId, table_episodes.path, table_shows.languages, table_history.language, table_history.score, table_shows.forced FROM table_history LEFT JOIN table_shows on table_shows.sonarrSeriesId = table_history.sonarrSeriesId LEFT JOIN table_episodes on table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId ORDER BY id DESC LIMIT ? OFFSET ?",
        (page_size, offset,))
    data = c.fetchall()
    
    upgradable_episodes = []
    upgradable_episodes_not_perfect = []
    if settings.general.getboolean('upgrade_subs'):
        days_to_upgrade_subs = settings.general.days_to_upgrade_subs
        minimum_timestamp = ((datetime.now() - timedelta(days=int(days_to_upgrade_subs))) -
                             datetime(1970, 1, 1)).total_seconds()
        
        if settings.general.getboolean('upgrade_manual'):
            query_actions = [1, 2, 3]
        else:
            query_actions = [1, 3]
        
        upgradable_episodes = c.execute("""SELECT video_path, MAX(timestamp), score
                                             FROM table_history
                                            WHERE action IN (""" + ','.join(map(str, query_actions)) + """) AND 
                                                  timestamp > ? AND score is not null
                                         GROUP BY table_history.video_path, table_history.language""",
                                        (minimum_timestamp,)).fetchall()
        for upgradable_episode in upgradable_episodes:
            try:
                int(upgradable_episode[2])
            except ValueError:
                pass
            else:
                if int(upgradable_episode[2]) < 360:
                    upgradable_episodes_not_perfect.append(upgradable_episode)
    
    c.close()
    
    data = reversed(sorted(data, key=operator.itemgetter(4)))
    
    return template('historyseries', bazarr_version=bazarr_version, rows=data, row_count=row_count,
                    page=page, max_page=max_page, stats=stats, base_url=base_url, page_size=page_size,
                    current_port=settings.general.port, upgradable_episodes=upgradable_episodes_not_perfect)


@route(base_url + 'historymovies')
@custom_auth_basic(check_credentials)
def historymovies():
    authorize()
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    
    c.execute("SELECT COUNT(*) FROM table_history_movie")
    row_count = c.fetchone()
    row_count = row_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    page_size = int(settings.general.page_size)
    offset = (int(page) - 1) * page_size
    max_page = int(math.ceil(row_count / (page_size + 0.0)))
    
    now = datetime.now()
    today = []
    thisweek = []
    thisyear = []
    stats = c.execute("SELECT timestamp FROM table_history_movie WHERE action > 0").fetchall()
    total = len(stats)
    for stat in stats:
        if now - timedelta(hours=24) <= datetime.fromtimestamp(stat[0]) <= now:
            today.append(datetime.fromtimestamp(stat[0]).date())
        if now - timedelta(weeks=1) <= datetime.fromtimestamp(stat[0]) <= now:
            thisweek.append(datetime.fromtimestamp(stat[0]).date())
        if now - timedelta(weeks=52) <= datetime.fromtimestamp(stat[0]) <= now:
            thisyear.append(datetime.fromtimestamp(stat[0]).date())
    stats = [len(today), len(thisweek), len(thisyear), total]
    
    c.execute(
        "SELECT table_history_movie.action, table_movies.title, table_history_movie.timestamp, table_history_movie.description, table_history_movie.radarrId, table_history_movie.video_path, table_movies.languages, table_history_movie.language, table_history_movie.score, table_movies.forced FROM table_history_movie LEFT JOIN table_movies on table_movies.radarrId = table_history_movie.radarrId ORDER BY id DESC LIMIT ? OFFSET ?",
        (page_size, offset,))
    data = c.fetchall()
    
    upgradable_movies = []
    upgradable_movies_not_perfect = []
    if settings.general.getboolean('upgrade_subs'):
        days_to_upgrade_subs = settings.general.days_to_upgrade_subs
        minimum_timestamp = ((datetime.now() - timedelta(days=int(days_to_upgrade_subs))) -
                             datetime(1970, 1, 1)).total_seconds()
        
        if settings.general.getboolean('upgrade_manual'):
            query_actions = [1, 2, 3]
        else:
            query_actions = [1, 3]
        
        upgradable_movies = c.execute("""SELECT video_path, MAX(timestamp), score
                                           FROM table_history_movie
                                          WHERE action IN (""" + ','.join(map(str, query_actions)) + """) AND 
                                                timestamp > ? AND score is not null
                                       GROUP BY video_path, language""",
                                      (minimum_timestamp,)).fetchall()
        for upgradable_movie in upgradable_movies:
            try:
                int(upgradable_movie[2])
            except ValueError:
                pass
            else:
                if int(upgradable_movie[2]) < 120:
                    upgradable_movies_not_perfect.append(upgradable_movie)
    
    c.close()
    data = reversed(sorted(data, key=operator.itemgetter(2)))
    return template('historymovies', bazarr_version=bazarr_version, rows=data, row_count=row_count,
                    page=page, max_page=max_page, stats=stats, base_url=base_url, page_size=page_size,
                    current_port=settings.general.port, upgradable_movies=upgradable_movies_not_perfect)


@route(base_url + 'wanted')
@custom_auth_basic(check_credentials)
def wanted():
    authorize()
    return template('wanted', bazarr_version=bazarr_version, base_url=base_url, current_port=settings.general.port)


@route(base_url + 'wantedseries')
@custom_auth_basic(check_credentials)
def wantedseries():
    authorize()
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()
    
    if settings.sonarr.getboolean('only_monitored'):
        monitored_only_query_string = ' AND monitored = "True"'
    else:
        monitored_only_query_string = ""
    
    c.execute("SELECT COUNT(*) FROM table_episodes WHERE missing_subtitles != '[]'" + monitored_only_query_string)
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    page_size = int(settings.general.page_size)
    offset = (int(page) - 1) * page_size
    max_page = int(math.ceil(missing_count / (page_size + 0.0)))
    
    c.execute(
        "SELECT table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, table_episodes.missing_subtitles, table_episodes.sonarrSeriesId, path_substitution(table_episodes.path), table_shows.hearing_impaired, table_episodes.sonarrEpisodeId, table_episodes.scene_name, table_episodes.failedAttempts FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE table_episodes.missing_subtitles != '[]'" + monitored_only_query_string + " ORDER BY table_episodes._rowid_ DESC LIMIT ? OFFSET ?",
        (page_size, offset,))
    data = c.fetchall()
    c.close()
    return template('wantedseries', bazarr_version=bazarr_version, rows=data,
                    missing_count=missing_count, page=page, max_page=max_page, base_url=base_url, page_size=page_size,
                    current_port=settings.general.port)


@route(base_url + 'wantedmovies')
@custom_auth_basic(check_credentials)
def wantedmovies():
    authorize()
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace_movie)
    c = db.cursor()
    
    if settings.radarr.getboolean('only_monitored'):
        monitored_only_query_string = ' AND monitored = "True"'
    else:
        monitored_only_query_string = ""
    
    c.execute("SELECT COUNT(*) FROM table_movies WHERE missing_subtitles != '[]'" + monitored_only_query_string)
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    page_size = int(settings.general.page_size)
    offset = (int(page) - 1) * page_size
    max_page = int(math.ceil(missing_count / (page_size + 0.0)))
    
    c.execute(
        "SELECT title, missing_subtitles, radarrId, path_substitution(path), hearing_impaired, sceneName, failedAttempts FROM table_movies WHERE missing_subtitles != '[]'" + monitored_only_query_string + " ORDER BY _rowid_ DESC LIMIT ? OFFSET ?",
        (page_size, offset,))
    data = c.fetchall()
    c.close()
    return template('wantedmovies', bazarr_version=bazarr_version, rows=data,
                    missing_count=missing_count, page=page, max_page=max_page, base_url=base_url, page_size=page_size,
                    current_port=settings.general.port)


@route(base_url + 'wanted_search_missing_subtitles')
@custom_auth_basic(check_credentials)
def wanted_search_missing_subtitles_list():
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    add_job(wanted_search_missing_subtitles, name='manual_wanted_search_missing_subtitles')
    
    redirect(ref)


@route(base_url + 'settings')
@custom_auth_basic(check_credentials)
def _settings():
    authorize()
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    c.execute("SELECT * FROM table_settings_languages ORDER BY name")
    settings_languages = c.fetchall()
    settings_providers = sorted(provider_manager.names())
    c.execute("SELECT * FROM table_settings_notifier ORDER BY name")
    settings_notifier = c.fetchall()
    c.close()
    
    return template('settings', bazarr_version=bazarr_version, settings=settings, settings_languages=settings_languages,
                    settings_providers=settings_providers, settings_notifier=settings_notifier, base_url=base_url,
                    current_port=settings.general.port)


@route(base_url + 'save_settings', method='POST')
@custom_auth_basic(check_credentials)
def save_settings():
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    conn = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = conn.cursor()
    
    settings_general_ip = request.forms.get('settings_general_ip')
    settings_general_port = request.forms.get('settings_general_port')
    settings_general_baseurl = request.forms.get('settings_general_baseurl')
    if not settings_general_baseurl.endswith('/'):
        settings_general_baseurl += '/'
    settings_general_debug = request.forms.get('settings_general_debug')
    if settings_general_debug is None:
        settings_general_debug = 'False'
    else:
        settings_general_debug = 'True'
    settings_general_chmod_enabled = request.forms.get('settings_general_chmod_enabled')
    if settings_general_chmod_enabled is None:
        settings_general_chmod_enabled = 'False'
    else:
        settings_general_chmod_enabled = 'True'
    settings_general_chmod = request.forms.get('settings_general_chmod')
    settings_general_sourcepath = request.forms.getall('settings_general_sourcepath')
    settings_general_destpath = request.forms.getall('settings_general_destpath')
    settings_general_pathmapping = []
    settings_general_pathmapping.extend([list(a) for a in zip(settings_general_sourcepath, settings_general_destpath)])
    settings_general_sourcepath_movie = request.forms.getall('settings_general_sourcepath_movie')
    settings_general_destpath_movie = request.forms.getall('settings_general_destpath_movie')
    settings_general_pathmapping_movie = []
    settings_general_pathmapping_movie.extend(
        [list(a) for a in zip(settings_general_sourcepath_movie, settings_general_destpath_movie)])
    settings_general_branch = request.forms.get('settings_general_branch')
    settings_general_automatic = request.forms.get('settings_general_automatic')
    if settings_general_automatic is None:
        settings_general_automatic = 'False'
    else:
        settings_general_automatic = 'True'
    settings_general_update_restart = request.forms.get('settings_general_update_restart')
    if settings_general_update_restart is None:
        settings_general_update_restart = 'False'
    else:
        settings_general_update_restart = 'True'
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
    settings_general_mediainfo = request.forms.get('settings_general_mediainfo')
    if settings_general_mediainfo is None:
        settings_general_mediainfo = 'False'
    else:
        settings_general_mediainfo = 'True'
    settings_general_embedded = request.forms.get('settings_general_embedded')
    if settings_general_embedded is None:
        settings_general_embedded = 'False'
    else:
        settings_general_embedded = 'True'
    settings_general_utf8_encode = request.forms.get('settings_general_utf8_encode')
    if settings_general_utf8_encode is None:
        settings_general_utf8_encode = 'False'
    else:
        settings_general_utf8_encode = 'True'
    settings_general_ignore_pgs = request.forms.get('settings_general_ignore_pgs')
    if settings_general_ignore_pgs is None:
        settings_general_ignore_pgs = 'False'
    else:
        settings_general_ignore_pgs = 'True'
    settings_general_adaptive_searching = request.forms.get('settings_general_adaptive_searching')
    if settings_general_adaptive_searching is None:
        settings_general_adaptive_searching = 'False'
    else:
        settings_general_adaptive_searching = 'True'
    settings_general_multithreading = request.forms.get('settings_general_multithreading')
    if settings_general_multithreading is None:
        settings_general_multithreading = 'False'
    else:
        settings_general_multithreading = 'True'
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
    settings_subfolder = request.forms.get('settings_subfolder')
    settings_subfolder_custom = request.forms.get('settings_subfolder_custom')
    settings_upgrade_subs = request.forms.get('settings_upgrade_subs')
    if settings_upgrade_subs is None:
        settings_upgrade_subs = 'False'
    else:
        settings_upgrade_subs = 'True'
    settings_days_to_upgrade_subs = request.forms.get('settings_days_to_upgrade_subs')
    settings_upgrade_manual = request.forms.get('settings_upgrade_manual')
    if settings_upgrade_manual is None:
        settings_upgrade_manual = 'False'
    else:
        settings_upgrade_manual = 'True'
    settings_anti_captcha_provider = request.forms.get('settings_anti_captcha_provider')
    settings_anti_captcha_key = request.forms.get('settings_anti_captcha_key')
    settings_death_by_captcha_username = request.forms.get('settings_death_by_captcha_username')
    settings_death_by_captcha_password = request.forms.get('settings_death_by_captcha_password')
    
    before = (unicode(settings.general.ip), int(settings.general.port), unicode(settings.general.base_url),
              unicode(settings.general.path_mappings), unicode(settings.general.getboolean('use_sonarr')),
              unicode(settings.general.getboolean('use_radarr')), unicode(settings.general.path_mappings_movie))
    after = (unicode(settings_general_ip), int(settings_general_port), unicode(settings_general_baseurl),
             unicode(settings_general_pathmapping), unicode(settings_general_use_sonarr),
             unicode(settings_general_use_radarr), unicode(settings_general_pathmapping_movie))
    
    settings.general.ip = text_type(settings_general_ip)
    settings.general.port = text_type(settings_general_port)
    settings.general.base_url = text_type(settings_general_baseurl)
    settings.general.path_mappings = text_type(settings_general_pathmapping)
    settings.general.debug = text_type(settings_general_debug)
    settings.general.chmod_enabled = text_type(settings_general_chmod_enabled)
    settings.general.chmod = text_type(settings_general_chmod)
    settings.general.branch = text_type(settings_general_branch)
    settings.general.auto_update = text_type(settings_general_automatic)
    settings.general.update_restart = text_type(settings_general_update_restart)
    settings.general.single_language = text_type(settings_general_single_language)
    settings.general.minimum_score = text_type(settings_general_minimum_score)
    settings.general.use_scenename = text_type(settings_general_scenename)
    settings.general.use_mediainfo = text_type(settings_general_mediainfo)
    settings.general.use_postprocessing = text_type(settings_general_use_postprocessing)
    settings.general.postprocessing_cmd = text_type(settings_general_postprocessing_cmd)
    settings.general.use_sonarr = text_type(settings_general_use_sonarr)
    settings.general.use_radarr = text_type(settings_general_use_radarr)
    settings.general.path_mappings_movie = text_type(settings_general_pathmapping_movie)
    settings.general.page_size = text_type(settings_page_size)
    settings.general.subfolder = text_type(settings_subfolder)
    if settings.general.subfolder == 'current':
        settings.general.subfolder_custom = ''
    else:
        settings.general.subfolder_custom = text_type(settings_subfolder_custom)
    settings.general.upgrade_subs = text_type(settings_upgrade_subs)
    settings.general.days_to_upgrade_subs = text_type(settings_days_to_upgrade_subs)
    settings.general.upgrade_manual = text_type(settings_upgrade_manual)
    settings.general.anti_captcha_provider = text_type(settings_anti_captcha_provider)
    settings.anticaptcha.anti_captcha_key = text_type(settings_anti_captcha_key)
    settings.deathbycaptcha.username = text_type(settings_death_by_captcha_username)
    settings.deathbycaptcha.password = text_type(settings_death_by_captcha_password)
    
    # set anti-captcha provider and key
    if settings.general.anti_captcha_provider == 'anti-captcha':
        os.environ["ANTICAPTCHA_CLASS"] = 'AntiCaptchaProxyLess'
        os.environ["ANTICAPTCHA_ACCOUNT_KEY"] = settings.anticaptcha.anti_captcha_key
    elif settings.general.anti_captcha_provider == 'death-by-captcha':
        os.environ["ANTICAPTCHA_CLASS"] = 'DeathByCaptchaProxyLess'
        os.environ["ANTICAPTCHA_ACCOUNT_KEY"] = ':'.join(
            {settings.deathbycaptcha.username, settings.deathbycaptcha.password})
    else:
        os.environ["ANTICAPTCHA_CLASS"] = ''
    
    settings.general.minimum_score_movie = text_type(settings_general_minimum_score_movies)
    settings.general.use_embedded_subs = text_type(settings_general_embedded)
    settings.general.utf8_encode = text_type(settings_general_utf8_encode)
    settings.general.ignore_pgs_subs = text_type(settings_general_ignore_pgs)
    settings.general.adaptive_searching = text_type(settings_general_adaptive_searching)
    settings.general.multithreading = text_type(settings_general_multithreading)
    
    if after != before:
        configured()
    
    settings_proxy_type = request.forms.get('settings_proxy_type')
    settings_proxy_url = request.forms.get('settings_proxy_url')
    settings_proxy_port = request.forms.get('settings_proxy_port')
    settings_proxy_username = request.forms.get('settings_proxy_username')
    settings_proxy_password = request.forms.get('settings_proxy_password')
    settings_proxy_exclude = request.forms.get('settings_proxy_exclude')
    
    before_proxy_password = (unicode(settings.proxy.type), unicode(settings.proxy.exclude))
    if before_proxy_password[0] != settings_proxy_type:
        configured()
    if before_proxy_password[1] == settings_proxy_password:
        settings.proxy.type = text_type(settings_proxy_type)
        settings.proxy.url = text_type(settings_proxy_url)
        settings.proxy.port = text_type(settings_proxy_port)
        settings.proxy.username = text_type(settings_proxy_username)
        settings.proxy.exclude = text_type(settings_proxy_exclude)
    else:
        settings.proxy.type = text_type(settings_proxy_type)
        settings.proxy.url = text_type(settings_proxy_url)
        settings.proxy.port = text_type(settings_proxy_port)
        settings.proxy.username = text_type(settings_proxy_username)
        settings.proxy.password = text_type(settings_proxy_password)
        settings.proxy.exclude = text_type(settings_proxy_exclude)
    
    settings_auth_type = request.forms.get('settings_auth_type')
    settings_auth_username = request.forms.get('settings_auth_username')
    settings_auth_password = request.forms.get('settings_auth_password')
    
    if settings.auth.type != settings_auth_type:
        configured()
    if settings.auth.password == settings_auth_password:
        settings.auth.type = text_type(settings_auth_type)
        settings.auth.username = text_type(settings_auth_username)
    else:
        settings.auth.type = text_type(settings_auth_type)
        settings.auth.username = text_type(settings_auth_username)
        settings.auth.password = hashlib.md5(settings_auth_password).hexdigest()
    if settings_auth_username not in aaa._store.users:
        cork = Cork(os.path.normpath(os.path.join(args.config_dir, 'config')), initialize=True)
        cork._store.roles[''] = 100
        cork._store.save_roles()
        cork._store.users[settings_auth_username] = {
            'role': '',
            'hash': cork._hash(settings_auth_username, settings_auth_password),
            'email_addr': '',
            'desc': '',
            'creation_date': time.time()
        }
        cork._store.save_users()
        if settings_auth_type == 'basic' or settings_auth_type == 'None':
            pass
        else:
            aaa._beaker_session.delete()
    else:
        if settings.auth.password != settings_auth_password:
            aaa.user(settings_auth_username).update(role='', pwd=settings_auth_password)
            if settings_auth_type == 'basic' or settings_auth_type == 'None':
                pass
            else:
                aaa._beaker_session.delete()
    
    settings_sonarr_ip = request.forms.get('settings_sonarr_ip')
    settings_sonarr_port = request.forms.get('settings_sonarr_port')
    settings_sonarr_baseurl = request.forms.get('settings_sonarr_baseurl')
    settings_sonarr_ssl = request.forms.get('settings_sonarr_ssl')
    if settings_sonarr_ssl is None:
        settings_sonarr_ssl = 'False'
    else:
        settings_sonarr_ssl = 'True'
    settings_sonarr_apikey = request.forms.get('settings_sonarr_apikey')
    settings_sonarr_only_monitored = request.forms.get('settings_sonarr_only_monitored')
    if settings_sonarr_only_monitored is None:
        settings_sonarr_only_monitored = 'False'
    else:
        settings_sonarr_only_monitored = 'True'
    settings_sonarr_sync = request.forms.get('settings_sonarr_sync')
    
    settings.sonarr.ip = text_type(settings_sonarr_ip)
    settings.sonarr.port = text_type(settings_sonarr_port)
    settings.sonarr.base_url = text_type(settings_sonarr_baseurl)
    settings.sonarr.ssl = text_type(settings_sonarr_ssl)
    settings.sonarr.apikey = text_type(settings_sonarr_apikey)
    settings.sonarr.only_monitored = text_type(settings_sonarr_only_monitored)
    settings.sonarr.full_update = text_type(settings_sonarr_sync)
    
    settings_radarr_ip = request.forms.get('settings_radarr_ip')
    settings_radarr_port = request.forms.get('settings_radarr_port')
    settings_radarr_baseurl = request.forms.get('settings_radarr_baseurl')
    settings_radarr_ssl = request.forms.get('settings_radarr_ssl')
    if settings_radarr_ssl is None:
        settings_radarr_ssl = 'False'
    else:
        settings_radarr_ssl = 'True'
    settings_radarr_apikey = request.forms.get('settings_radarr_apikey')
    settings_radarr_only_monitored = request.forms.get('settings_radarr_only_monitored')
    if settings_radarr_only_monitored is None:
        settings_radarr_only_monitored = 'False'
    else:
        settings_radarr_only_monitored = 'True'
    settings_radarr_sync = request.forms.get('settings_radarr_sync')
    
    settings.radarr.ip = text_type(settings_radarr_ip)
    settings.radarr.port = text_type(settings_radarr_port)
    settings.radarr.base_url = text_type(settings_radarr_baseurl)
    settings.radarr.ssl = text_type(settings_radarr_ssl)
    settings.radarr.apikey = text_type(settings_radarr_apikey)
    settings.radarr.only_monitored = text_type(settings_radarr_only_monitored)
    settings.radarr.full_update = text_type(settings_radarr_sync)
    
    settings_subliminal_providers = request.forms.getall('settings_subliminal_providers')
    settings.general.enabled_providers = u'' if not settings_subliminal_providers else ','.join(
        settings_subliminal_providers)
    
    settings_addic7ed_random_agents = request.forms.get('settings_addic7ed_random_agents')
    if settings_addic7ed_random_agents is None:
        settings_addic7ed_random_agents = 'False'
    else:
        settings_addic7ed_random_agents = 'True'
    
    settings_opensubtitles_vip = request.forms.get('settings_opensubtitles_vip')
    if settings_opensubtitles_vip is None:
        settings_opensubtitles_vip = 'False'
    else:
        settings_opensubtitles_vip = 'True'
    
    settings_opensubtitles_ssl = request.forms.get('settings_opensubtitles_ssl')
    if settings_opensubtitles_ssl is None:
        settings_opensubtitles_ssl = 'False'
    else:
        settings_opensubtitles_ssl = 'True'
    
    settings_opensubtitles_skip_wrong_fps = request.forms.get('settings_opensubtitles_skip_wrong_fps')
    if settings_opensubtitles_skip_wrong_fps is None:
        settings_opensubtitles_skip_wrong_fps = 'False'
    else:
        settings_opensubtitles_skip_wrong_fps = 'True'
    
    settings.addic7ed.username = request.forms.get('settings_addic7ed_username')
    settings.addic7ed.password = request.forms.get('settings_addic7ed_password')
    settings.addic7ed.random_agents = text_type(settings_addic7ed_random_agents)
    settings.assrt.token = request.forms.get('settings_assrt_token')
    settings.legendastv.username = request.forms.get('settings_legendastv_username')
    settings.legendastv.password = request.forms.get('settings_legendastv_password')
    settings.opensubtitles.username = request.forms.get('settings_opensubtitles_username')
    settings.opensubtitles.password = request.forms.get('settings_opensubtitles_password')
    settings.opensubtitles.vip = text_type(settings_opensubtitles_vip)
    settings.opensubtitles.ssl = text_type(settings_opensubtitles_ssl)
    settings.opensubtitles.skip_wrong_fps = text_type(settings_opensubtitles_skip_wrong_fps)
    settings.xsubs.username = request.forms.get('settings_xsubs_username')
    settings.xsubs.password = request.forms.get('settings_xsubs_password')
    settings.napisy24.username = request.forms.get('settings_napisy24_username')
    settings.napisy24.password = request.forms.get('settings_napisy24_password')
    settings.subscene.username = request.forms.get('settings_subscene_username')
    settings.subscene.password = request.forms.get('settings_subscene_password')
    settings.betaseries.token = request.forms.get('settings_betaseries_token')

    settings_subliminal_languages = request.forms.getall('settings_subliminal_languages')
    c.execute("UPDATE table_settings_languages SET enabled = 0")
    for item in settings_subliminal_languages:
        c.execute("UPDATE table_settings_languages SET enabled = '1' WHERE code2 = ?", (item,))
    
    settings_serie_default_enabled = request.forms.get('settings_serie_default_enabled')
    if settings_serie_default_enabled is None:
        settings_serie_default_enabled = 'False'
    else:
        settings_serie_default_enabled = 'True'
    settings.general.serie_default_enabled = text_type(settings_serie_default_enabled)
    
    settings_serie_default_languages = str(request.forms.getall('settings_serie_default_languages'))
    if settings_serie_default_languages == "['None']":
        settings_serie_default_languages = 'None'
    settings.general.serie_default_language = text_type(settings_serie_default_languages)
    
    settings_serie_default_hi = request.forms.get('settings_serie_default_hi')
    if settings_serie_default_hi is None:
        settings_serie_default_hi = 'False'
    else:
        settings_serie_default_hi = 'True'
    settings.general.serie_default_hi = text_type(settings_serie_default_hi)
    
    settings_serie_default_forced = str(request.forms.get('settings_serie_default_forced'))
    settings.general.serie_default_forced = text_type(settings_serie_default_forced)
    
    settings_movie_default_enabled = request.forms.get('settings_movie_default_enabled')
    if settings_movie_default_enabled is None:
        settings_movie_default_enabled = 'False'
    else:
        settings_movie_default_enabled = 'True'
    settings.general.movie_default_enabled = text_type(settings_movie_default_enabled)
    
    settings_movie_default_languages = str(request.forms.getall('settings_movie_default_languages'))
    if settings_movie_default_languages == "['None']":
        settings_movie_default_languages = 'None'
    settings.general.movie_default_language = text_type(settings_movie_default_languages)
    
    settings_movie_default_hi = request.forms.get('settings_movie_default_hi')
    if settings_movie_default_hi is None:
        settings_movie_default_hi = 'False'
    else:
        settings_movie_default_hi = 'True'
    settings.general.movie_default_hi = text_type(settings_movie_default_hi)
    
    settings_movie_default_forced = str(request.forms.get('settings_movie_default_forced'))
    settings.general.movie_default_forced = text_type(settings_movie_default_forced)
    
    with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
        settings.write(handle)
    
    configure_logging(settings.general.getboolean('debug') or args.debug)
    
    notifiers = c.execute("SELECT * FROM table_settings_notifier ORDER BY name").fetchall()
    for notifier in notifiers:
        enabled = request.forms.get('settings_notifier_' + notifier[0] + '_enabled')
        if enabled == 'on':
            enabled = 1
        else:
            enabled = 0
        notifier_url = request.forms.get('settings_notifier_' + notifier[0] + '_url')
        c.execute("UPDATE table_settings_notifier SET enabled = ?, url = ? WHERE name = ?",
                  (enabled, notifier_url, notifier[0]))
    
    conn.commit()
    c.close()
    
    schedule_update_job()
    sonarr_full_update()
    radarr_full_update()
    
    logging.info('BAZARR Settings saved succesfully.')
    
    if ref.find('saved=true') > 0:
        redirect(ref)
    else:
        redirect(ref + "?saved=true")


@route(base_url + 'check_update')
@custom_auth_basic(check_credentials)
def check_update():
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    if not args.no_update:
        check_and_apply_update()
    
    redirect(ref)


@route(base_url + 'system')
@custom_auth_basic(check_credentials)
def system():
    authorize()
    
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
        text = ""
        sun = str(cron[4])
        hour = str(cron[5])
        minute = str(cron[6])
        second = str(cron[7])
        
        if sun != "*":
            text = "Sunday at "
        
        if hour != "0" and hour != "*":
            text = text + hour
            if hour == "0" or hour == "1":
                text = text + " hour"
            elif sun != "*" or hour == "4" or hour == "5":
                text = text + "am"
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
        if text != "" and sun == "*":
            text = "everyday at " + text
        elif text == "":
            text = "Never"
        
        return text
    
    task_list = []
    for job in scheduler.get_jobs():
        if isinstance(job.trigger, CronTrigger):
            if str(job.trigger.__getstate__()['fields'][0]) == "2100":
                next_run = 'Never'
            else:
                next_run = pretty.date(job.next_run_time.replace(tzinfo=None))
        else:
            next_run = pretty.date(job.next_run_time.replace(tzinfo=None))
        
        if isinstance(job.trigger, IntervalTrigger):
            interval = "every " + get_time_from_interval(job.trigger.__getstate__()['interval'])
            task_list.append([job.name, interval, next_run, job.id])
        elif isinstance(job.trigger, CronTrigger):
            task_list.append([job.name, get_time_from_cron(job.trigger.fields), next_run, job.id])
    
    throttled_providers = list_throttled_providers()
    
    try:
        with open(os.path.join(args.config_dir, 'config', 'releases.txt'), 'r') as f:
            releases = ast.literal_eval(f.read())
    except Exception as e:
        releases = []
        logging.exception(
            'BAZARR cannot parse releases caching file: ' + os.path.join(args.config_dir, 'config', 'releases.txt'))
    
    use_sonarr = settings.general.getboolean('use_sonarr')
    apikey_sonarr = settings.sonarr.apikey
    sv = url_sonarr + "/api/system/status?apikey=" + apikey_sonarr
    sonarr_version = ''
    if use_sonarr:
        try:
            sonarr_version = requests.get(sv, timeout=15, verify=False).json()['version']
        except:
            pass
    
    use_radarr = settings.general.getboolean('use_radarr')
    apikey_radarr = settings.radarr.apikey
    rv = url_radarr + "/api/system/status?apikey=" + apikey_radarr
    radarr_version = ''
    if use_radarr:
        try:
            radarr_version = requests.get(rv, timeout=15, verify=False).json()['version']
        except:
            pass
    
    page_size = int(settings.general.page_size)
    
    return template('system', bazarr_version=bazarr_version,
                    sonarr_version=sonarr_version, radarr_version=radarr_version,
                    operating_system=platform.platform(), python_version=platform.python_version(),
                    config_dir=args.config_dir, bazarr_dir=os.path.normcase(os.path.dirname(os.path.dirname(__file__))),
                    base_url=base_url, task_list=task_list, page_size=page_size, releases=releases,
                    current_port=settings.general.port, throttled_providers=throttled_providers)


@route(base_url + 'logs')
@custom_auth_basic(check_credentials)
def get_logs():
    authorize()
    logs = []
    for line in reversed(open(os.path.join(args.config_dir, 'log', 'bazarr.log')).readlines()):
        lin = []
        lin = line.split('|')
        logs.append(lin)
    
    return dict(data=logs)


@route(base_url + 'execute/<taskid>')
@custom_auth_basic(check_credentials)
def execute_task(taskid):
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    execute_now(taskid)
    
    redirect(ref)


@route(base_url + 'remove_subtitles', method='POST')
@custom_auth_basic(check_credentials)
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
    except OSError as e:
        logging.exception('BAZARR cannot delete subtitles file: ' + subtitlesPath)
    store_subtitles(unicode(episodePath))
    list_missing_subtitles(sonarrSeriesId)


@route(base_url + 'remove_subtitles_movie', method='POST')
@custom_auth_basic(check_credentials)
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
    except OSError as e:
        logging.exception('BAZARR cannot delete subtitles file: ' + subtitlesPath)
    store_subtitles_movie(unicode(moviePath))
    list_missing_subtitles_movies(radarrId)


@route(base_url + 'get_subtitle', method='POST')
@custom_auth_basic(check_credentials)
def get_subtitle():
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    episodePath = request.forms.get('episodePath')
    sceneName = request.forms.get('sceneName')
    language = request.forms.get('language')
    hi = request.forms.get('hi')
    forced = request.forms.get('forced')
    sonarrSeriesId = request.forms.get('sonarrSeriesId')
    sonarrEpisodeId = request.forms.get('sonarrEpisodeId')
    title = request.forms.get('title')
    
    providers_list = get_providers()
    providers_auth = get_providers_auth()
    
    try:
        result = download_subtitle(episodePath, language, hi, forced, providers_list, providers_auth, sceneName, title,
                                   'series')
        if result is not None:
            message = result[0]
            path = result[1]
            forced = result[5]
            language_code = result[2] + ":forced" if forced else result[2]
            provider = result[3]
            score = result[4]
            history_log(1, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score)
            send_notifications(sonarrSeriesId, sonarrEpisodeId, message)
            store_subtitles(unicode(episodePath))
            list_missing_subtitles(sonarrSeriesId)
        redirect(ref)
    except OSError:
        pass


@route(base_url + 'manual_search', method='POST')
@custom_auth_basic(check_credentials)
def manual_search_json():
    authorize()
    
    episodePath = request.forms.get('episodePath')
    sceneName = request.forms.get('sceneName')
    language = request.forms.get('language')
    hi = request.forms.get('hi')
    forced = request.forms.get('forced')
    title = request.forms.get('title')
    
    providers_list = get_providers()
    providers_auth = get_providers_auth()
    
    data = manual_search(episodePath, language, hi, forced, providers_list, providers_auth, sceneName, title, 'series')
    return dict(data=data)


@route(base_url + 'manual_get_subtitle', method='POST')
@custom_auth_basic(check_credentials)
def manual_get_subtitle():
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    episodePath = request.forms.get('episodePath')
    sceneName = request.forms.get('sceneName')
    language = request.forms.get('language')
    hi = request.forms.get('hi')
    forced = request.forms.get('forced')
    selected_provider = request.forms.get('provider')
    subtitle = request.forms.get('subtitle')
    sonarrSeriesId = request.forms.get('sonarrSeriesId')
    sonarrEpisodeId = request.forms.get('sonarrEpisodeId')
    title = request.forms.get('title')
    
    providers_auth = get_providers_auth()
    
    try:
        result = manual_download_subtitle(episodePath, language, hi, forced, subtitle, selected_provider,
                                          providers_auth,
                                          sceneName, title, 'series')
        if result is not None:
            message = result[0]
            path = result[1]
            forced = result[5]
            language_code = result[2] + ":forced" if forced else result[2]
            provider = result[3]
            score = result[4]
            history_log(2, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score)
            send_notifications(sonarrSeriesId, sonarrEpisodeId, message)
            store_subtitles(unicode(episodePath))
            list_missing_subtitles(sonarrSeriesId)
        redirect(ref)
    except OSError:
        pass


@route(base_url + 'manual_upload_subtitle', method='POST')
@custom_auth_basic(check_credentials)
def perform_manual_upload_subtitle():
    authorize()
    ref = request.environ['HTTP_REFERER']

    episodePath = request.forms.get('episodePath')
    sceneName = request.forms.get('sceneName')
    language = request.forms.get('language')
    forced = True if request.forms.get('forced') == '1' else False
    upload = request.files.get('upload')
    sonarrSeriesId = request.forms.get('sonarrSeriesId')
    sonarrEpisodeId = request.forms.get('sonarrEpisodeId')
    title = request.forms.get('title')

    _, ext = os.path.splitext(upload.filename)

    if ext not in SUBTITLE_EXTENSIONS:
        raise ValueError('A subtitle of an invalid format was uploaded.')
    
    try:
        result = manual_upload_subtitle(path=episodePath, 
                                        language=language,
                                        forced=forced,
                                        title=title, 
                                        scene_name=sceneName, 
                                        media_type='series',
                                        subtitle=upload)
        
        if result is not None:
            message = result[0]
            path = result[1]
            language_code = language + ":forced" if forced else language
            provider = "manual"
            score = 360
            history_log(4, sonarrSeriesId, sonarrEpisodeId, message, path, language_code, provider, score)
            send_notifications(sonarrSeriesId, sonarrEpisodeId, message)
            store_subtitles(unicode(episodePath))
            list_missing_subtitles(sonarrSeriesId)
        
        redirect(ref)
    except OSError:
        pass


@route(base_url + 'get_subtitle_movie', method='POST')
@custom_auth_basic(check_credentials)
def get_subtitle_movie():
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    moviePath = request.forms.get('moviePath')
    sceneName = request.forms.get('sceneName')
    language = request.forms.get('language')
    hi = request.forms.get('hi')
    forced = request.forms.get('forced')
    radarrId = request.forms.get('radarrId')
    title = request.forms.get('title')
    
    providers_list = get_providers()
    providers_auth = get_providers_auth()
    
    try:
        result = download_subtitle(moviePath, language, hi, forced, providers_list, providers_auth, sceneName, title,
                                   'movie')
        if result is not None:
            message = result[0]
            path = result[1]
            forced = result[5]
            language_code = result[2] + ":forced" if forced else result[2]
            provider = result[3]
            score = result[4]
            history_log_movie(1, radarrId, message, path, language_code, provider, score)
            send_notifications_movie(radarrId, message)
            store_subtitles_movie(unicode(moviePath))
            list_missing_subtitles_movies(radarrId)
        redirect(ref)
    except OSError:
        pass


@route(base_url + 'manual_search_movie', method='POST')
@custom_auth_basic(check_credentials)
def manual_search_movie_json():
    authorize()
    
    moviePath = request.forms.get('moviePath')
    sceneName = request.forms.get('sceneName')
    language = request.forms.get('language')
    hi = request.forms.get('hi')
    forced = request.forms.get('forced')
    title = request.forms.get('title')
    
    providers_list = get_providers()
    providers_auth = get_providers_auth()
    
    data = manual_search(moviePath, language, hi, forced, providers_list, providers_auth, sceneName, title, 'movie')
    return dict(data=data)


@route(base_url + 'manual_get_subtitle_movie', method='POST')
@custom_auth_basic(check_credentials)
def manual_get_subtitle_movie():
    authorize()
    ref = request.environ['HTTP_REFERER']
    
    moviePath = request.forms.get('moviePath')
    sceneName = request.forms.get('sceneName')
    language = request.forms.get('language')
    hi = request.forms.get('hi')
    forced = request.forms.get('forced')
    selected_provider = request.forms.get('provider')
    subtitle = request.forms.get('subtitle')
    radarrId = request.forms.get('radarrId')
    title = request.forms.get('title')
    
    providers_auth = get_providers_auth()
    
    try:
        result = manual_download_subtitle(moviePath, language, hi, forced, subtitle, selected_provider, providers_auth,
                                          sceneName, title, 'movie')
        if result is not None:
            message = result[0]
            path = result[1]
            forced = result[5]
            language_code = result[2] + ":forced" if forced else result[2]
            provider = result[3]
            score = result[4]
            history_log_movie(2, radarrId, message, path, language_code, provider, score)
            send_notifications_movie(radarrId, message)
            store_subtitles_movie(unicode(moviePath))
            list_missing_subtitles_movies(radarrId)
        redirect(ref)
    except OSError:
        pass


@route(base_url + 'manual_upload_subtitle_movie', method='POST')
@custom_auth_basic(check_credentials)
def perform_manual_upload_subtitle_movie():
    authorize()
    ref = request.environ['HTTP_REFERER']

    moviePath = request.forms.get('moviePath')
    sceneName = request.forms.get('sceneName')
    language = request.forms.get('language')
    forced = True if request.forms.get('forced') == '1' else False
    upload = request.files.get('upload')
    radarrId = request.forms.get('radarrId')
    title = request.forms.get('title')

    _, ext = os.path.splitext(upload.filename)

    if ext not in SUBTITLE_EXTENSIONS:
        raise ValueError('A subtitle of an invalid format was uploaded.')
    
    try:
        result = manual_upload_subtitle(path=moviePath, 
                                        language=language,
                                        forced=forced,
                                        title=title, 
                                        scene_name=sceneName, 
                                        media_type='series',
                                        subtitle=upload)
        
        if result is not None:
            message = result[0]
            path = result[1]
            language_code = language + ":forced" if forced else language
            provider = "manual"
            score = 120
            history_log_movie(4, radarrId, message, path, language_code, provider, score)
            send_notifications_movie(radarrId, message)
            store_subtitles_movie(unicode(moviePath))
            list_missing_subtitles_movies(radarrId)
        
        redirect(ref)
    except OSError:
        pass


def configured():
    conn = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = conn.cursor()
    c.execute("UPDATE system SET configured = 1")
    conn.commit()
    c.close()


@route(base_url + 'api/series/wanted')
def api_wanted():
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    data = c.execute(
        "SELECT table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, table_episodes.missing_subtitles FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE table_episodes.missing_subtitles != '[]' ORDER BY table_episodes._rowid_ DESC LIMIT 10").fetchall()
    c.close()
    return dict(subtitles=data)


@route(base_url + 'api/series/history')
def api_history():
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    data = c.execute(
        "SELECT table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, strftime('%Y-%m-%d', datetime(table_history.timestamp, 'unixepoch')), table_history.description FROM table_history INNER JOIN table_shows on table_shows.sonarrSeriesId = table_history.sonarrSeriesId INNER JOIN table_episodes on table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId WHERE table_history.action != '0' ORDER BY id DESC LIMIT 10").fetchall()
    c.close()
    return dict(subtitles=data)


@route(base_url + 'api/movies/wanted')
def api_wanted():
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    data = c.execute(
        "SELECT table_movies.title, table_movies.missing_subtitles FROM table_movies WHERE table_movies.missing_subtitles != '[]' ORDER BY table_movies._rowid_ DESC LIMIT 10").fetchall()
    c.close()
    return dict(subtitles=data)


@route(base_url + 'api/movies/history')
def api_history():
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    data = c.execute(
        "SELECT table_movies.title, strftime('%Y-%m-%d', datetime(table_history_movie.timestamp, 'unixepoch')), table_history_movie.description FROM table_history_movie INNER JOIN table_movies on table_movies.radarrId = table_history_movie.radarrId WHERE table_history_movie.action != '0' ORDER BY id DESC LIMIT 10").fetchall()
    c.close()
    return dict(subtitles=data)


@route(base_url + 'test_url/<protocol>/<url:path>', method='GET')
@custom_auth_basic(check_credentials)
def test_url(protocol, url):
    url = urllib.unquote(url)
    try:
        result = requests.get(protocol + "://" + url, allow_redirects=False, verify=False).json()['version']
    except:
        return dict(status=False)
    else:
        return dict(status=True, version=result)


@route(base_url + 'test_notification/<protocol>/<provider:path>', method='GET')
@custom_auth_basic(check_credentials)
def test_notification(protocol, provider):
    provider = urllib.unquote(provider)
    apobj = apprise.Apprise()
    apobj.add(protocol + "://" + provider)
    
    apobj.notify(
        title='Bazarr test notification',
        body=('Test notification')
    )


@route(base_url + 'notifications')
@custom_auth_basic(check_credentials)
def notifications():
    if queueconfig.notifications:
        return queueconfig.notifications.read()
    else:
        return None


@route(base_url + 'running_tasks')
@custom_auth_basic(check_credentials)
def running_tasks_list():
    return dict(tasks=running_tasks)


# Mute DeprecationWarning
warnings.simplefilter("ignore", DeprecationWarning)
server = WSGIServer((str(settings.general.ip), (int(args.port) if args.port else int(settings.general.port))), app,
                    handler_class=WebSocketHandler)
try:
    logging.info('BAZARR is started and waiting for request on http://' + str(settings.general.ip) + ':' + (str(
        args.port) if args.port else str(settings.general.port)) + str(base_url))
    server.serve_forever()
except KeyboardInterrupt:
    shutdown()

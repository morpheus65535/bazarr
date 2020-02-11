# coding=utf-8

bazarr_version = '0.9'

import os
os.environ["SZ_USER_AGENT"] = "Bazarr/1"
os.environ["BAZARR_VERSION"] = bazarr_version

import gc
import sys
import libs
import io

import six
from six.moves import zip
from functools import reduce

import itertools
import operator
import pretty
import math
import ast
import hashlib
import six.moves.urllib.request, six.moves.urllib.parse, six.moves.urllib.error
import warnings
import queueconfig
import platform
import apprise
import operator


from get_args import args
from logger import empty_log
from config import settings, url_sonarr, url_radarr, url_radarr_short, url_sonarr_short, base_url

from init import *
import logging
from database import database, dict_mapper

from notifier import update_notifier

from cherrypy.wsgiserver import CherryPyWSGIServer

from io import BytesIO
from six import text_type
from datetime import timedelta, datetime
from get_languages import load_language_in_db, language_from_alpha3, language_from_alpha2, alpha2_from_alpha3
from flask import make_response, request, redirect, abort, render_template, Response, session, flash, url_for, \
    send_file, stream_with_context

from get_providers import get_providers, get_providers_auth, list_throttled_providers
from get_series import *
from get_episodes import *
from get_movies import *

from list_subtitles import store_subtitles, store_subtitles_movie, series_scan_subtitles, movies_scan_subtitles, \
    list_missing_subtitles, list_missing_subtitles_movies
from get_subtitle import download_subtitle, series_download_subtitles, movies_download_subtitles, \
    manual_search, manual_download_subtitle, manual_upload_subtitle
from utils import history_log, history_log_movie, get_sonarr_version, get_radarr_version
from helper import path_replace, path_replace_movie, path_replace_reverse, path_replace_reverse_movie
from scheduler import Scheduler
from notifier import send_notifications, send_notifications_movie
from subliminal_patch.extensions import provider_registry as provider_manager
from subliminal_patch.core import SUBTITLE_EXTENSIONS
from functools import wraps

from app import create_app, socketio
app = create_app()

from api import api_bp
app.register_blueprint(api_bp)

scheduler = Scheduler()

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

# Reset restart required warning on start
database.execute("UPDATE system SET configured='0', updated='0'")

# Load languages in database
load_language_in_db()

login_auth = settings.auth.type

update_notifier()


def check_credentials(user, pw):
    username = settings.auth.username
    password = settings.auth.password
    if hashlib.md5(pw.encode('utf-8')).hexdigest() == password and user == username:
        return True
    return False

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        test = request
        if settings.auth.type == 'basic':
            auth = request.authorization
            if not (auth and check_credentials(request.authorization.username, request.authorization.password)):
                return ('Unauthorized', 401, {
                    'WWW-Authenticate': 'Basic realm="Login Required"'
                })

            return f(*args, **kwargs)
        elif settings.auth.type == 'form':
            if 'logged_in' in session:
                return f(*args, **kwargs)
            else:
                flash("You need to login first")
                return redirect(url_for('login_page'))
        else:
            return f(*args, **kwargs)
    return wrap


@app.route('/login/', methods=["GET", "POST"])
def login_page():
    error = ''
    try:
        if request.method == "POST":
            if check_credentials(request.form['username'], request.form['password']):
                session['logged_in'] = True
                session['username'] = request.form['username']

                flash("You are now logged in")
                return redirect(url_for("redirect_root"))
            else:
                error = "Invalid credentials, try again."
        gc.collect()

        return render_template("login.html", error=error)

    except Exception as e:
        # flash(e)
        error = "Invalid credentials, try again."
        return render_template("login.html", error=error)


@app.context_processor
def restart_processor():
    def restart_required():
        restart_required = database.execute("SELECT configured, updated FROM system", only_one=True)
        return restart_required
    return dict(restart_required=restart_required()['configured'], update_required=restart_required()['updated'], ast=ast, settings=settings, locals=locals(), args=args, os=os)


def api_authorize():
    if 'apikey' in request.GET.dict:
        if request.GET.dict['apikey'][0] == settings.auth.apikey:
            return
        else:
            abort(401, 'Unauthorized')
    else:
        abort(401, 'Unauthorized')


def post_get(name, default=''):
    return request.POST.get(name, default).strip()


@app.route("/logout/")
@login_required
def logout():
    if settings.auth.type == 'basic':
        return abort(401)
    elif settings.auth.type == 'form':
        session.clear()
        flash("You have been logged out!")
        gc.collect()
        return redirect(url_for('redirect_root'))


@app.route('/shutdown/')
@login_required
def shutdown():
    doShutdown()

def doShutdown():
    try:
        server.stop()
    except:
        logging.error('BAZARR Cannot stop CherryPy.')
    else:
        database.close()
        try:
            stop_file = io.open(os.path.join(args.config_dir, "bazarr.stop"), "w", encoding='UTF-8')
        except Exception as e:
            logging.error('BAZARR Cannot create bazarr.stop file.')
        else:
            stop_file.write(six.text_type(''))
            stop_file.close()
            sys.exit(0)
    return ''


@app.route('/restart/')
@login_required
def restart():
    try:
        server.stop()
    except:
        logging.error('BAZARR Cannot stop CherryPy.')
    else:
        database.close()
        try:
            restart_file = io.open(os.path.join(args.config_dir, "bazarr.restart"), "w", encoding='UTF-8')
        except Exception as e:
            logging.error('BAZARR Cannot create bazarr.restart file.')
        else:
            logging.info('Bazarr is being restarted...')
            restart_file.write(six.text_type(''))
            restart_file.close()
            sys.exit(0)
    return ''


@app.route('/wizard/')
@login_required
def wizard():
    # Get languages list
    settings_languages = database.execute("SELECT * FROM table_settings_languages ORDER BY name")
    # Get providers list
    settings_providers = sorted(provider_manager.names())

    return render_template('wizard.html', bazarr_version=bazarr_version, settings=settings,
                    settings_languages=settings_languages, settings_providers=settings_providers,
                    base_url=base_url, ast=ast)


@app.route('/save_wizard', methods=['POST'])
@login_required
def save_wizard():
    settings_general_ip = request.form.get('settings_general_ip')
    settings_general_port = request.form.get('settings_general_port')
    settings_general_baseurl = request.form.get('settings_general_baseurl')
    if not settings_general_baseurl.endswith('/'):
        settings_general_baseurl += '/'
    settings_general_sourcepath = request.form.getlist('settings_general_sourcepath[]')
    settings_general_destpath = request.form.getlist('settings_general_destpath[]')
    settings_general_pathmapping = []
    settings_general_pathmapping.extend([list(a) for a in zip(settings_general_sourcepath, settings_general_destpath)])
    settings_general_sourcepath_movie = request.form.getlist('settings_general_sourcepath_movie[]')
    settings_general_destpath_movie = request.form.getlist('settings_general_destpath_movie[]')
    settings_general_pathmapping_movie = []
    settings_general_pathmapping_movie.extend(
        [list(a) for a in zip(settings_general_sourcepath_movie, settings_general_destpath_movie)])
    settings_general_single_language = request.form.get('settings_general_single_language')
    if settings_general_single_language is None:
        settings_general_single_language = 'False'
    else:
        settings_general_single_language = 'True'
    settings_general_use_sonarr = request.form.get('settings_general_use_sonarr')
    if settings_general_use_sonarr is None:
        settings_general_use_sonarr = 'False'
    else:
        settings_general_use_sonarr = 'True'
    settings_general_use_radarr = request.form.get('settings_general_use_radarr')
    if settings_general_use_radarr is None:
        settings_general_use_radarr = 'False'
    else:
        settings_general_use_radarr = 'True'
    settings_general_embedded = request.form.get('settings_general_embedded')
    if settings_general_embedded is None:
        settings_general_embedded = 'False'
    else:
        settings_general_embedded = 'True'
    settings_subfolder = request.form.get('settings_subfolder')
    settings_subfolder_custom = request.form.get('settings_subfolder_custom')
    settings_upgrade_subs = request.form.get('settings_upgrade_subs')
    if settings_upgrade_subs is None:
        settings_upgrade_subs = 'False'
    else:
        settings_upgrade_subs = 'True'
    settings_days_to_upgrade_subs = request.form.get('settings_days_to_upgrade_subs')
    settings_upgrade_manual = request.form.get('settings_upgrade_manual')
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

    settings_sonarr_ip = request.form.get('settings_sonarr_ip')
    settings_sonarr_port = request.form.get('settings_sonarr_port')
    settings_sonarr_baseurl = request.form.get('settings_sonarr_baseurl')
    settings_sonarr_ssl = request.form.get('settings_sonarr_ssl')
    if settings_sonarr_ssl is None:
        settings_sonarr_ssl = 'False'
    else:
        settings_sonarr_ssl = 'True'
    settings_sonarr_apikey = request.form.get('settings_sonarr_apikey')
    settings_sonarr_only_monitored = request.form.get('settings_sonarr_only_monitored')
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

    settings_radarr_ip = request.form.get('settings_radarr_ip')
    settings_radarr_port = request.form.get('settings_radarr_port')
    settings_radarr_baseurl = request.form.get('settings_radarr_baseurl')
    settings_radarr_ssl = request.form.get('settings_radarr_ssl')
    if settings_radarr_ssl is None:
        settings_radarr_ssl = 'False'
    else:
        settings_radarr_ssl = 'True'
    settings_radarr_apikey = request.form.get('settings_radarr_apikey')
    settings_radarr_only_monitored = request.form.get('settings_radarr_only_monitored')
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

    settings_subliminal_providers = request.form.getlist('settings_subliminal_providers')
    settings.general.enabled_providers = u'' if not settings_subliminal_providers else ','.join(
        settings_subliminal_providers)

    settings_addic7ed_random_agents = request.form.get('settings_addic7ed_random_agents')
    if settings_addic7ed_random_agents is None:
        settings_addic7ed_random_agents = 'False'
    else:
        settings_addic7ed_random_agents = 'True'

    settings_opensubtitles_vip = request.form.get('settings_opensubtitles_vip')
    if settings_opensubtitles_vip is None:
        settings_opensubtitles_vip = 'False'
    else:
        settings_opensubtitles_vip = 'True'

    settings_opensubtitles_ssl = request.form.get('settings_opensubtitles_ssl')
    if settings_opensubtitles_ssl is None:
        settings_opensubtitles_ssl = 'False'
    else:
        settings_opensubtitles_ssl = 'True'

    settings_opensubtitles_skip_wrong_fps = request.form.get('settings_opensubtitles_skip_wrong_fps')
    if settings_opensubtitles_skip_wrong_fps is None:
        settings_opensubtitles_skip_wrong_fps = 'False'
    else:
        settings_opensubtitles_skip_wrong_fps = 'True'

    settings.addic7ed.username = request.form.get('settings_addic7ed_username') or ''
    settings.addic7ed.password = request.form.get('settings_addic7ed_password') or ''
    settings.addic7ed.random_agents = text_type(settings_addic7ed_random_agents) or ''
    settings.assrt.token = request.form.get('settings_assrt_token') or ''
    settings.legendasdivx.username = request.form.get('settings_legendasdivx_username') or ''
    settings.legendasdivx.password = request.form.get('settings_legendasdivx_password') or ''
    settings.legendastv.username = request.form.get('settings_legendastv_username') or ''
    settings.legendastv.password = request.form.get('settings_legendastv_password') or ''
    settings.opensubtitles.username = request.form.get('settings_opensubtitles_username') or ''
    settings.opensubtitles.password = request.form.get('settings_opensubtitles_password') or ''
    settings.opensubtitles.vip = text_type(settings_opensubtitles_vip)
    settings.opensubtitles.ssl = text_type(settings_opensubtitles_ssl)
    settings.opensubtitles.skip_wrong_fps = text_type(settings_opensubtitles_skip_wrong_fps)
    settings.xsubs.username = request.form.get('settings_xsubs_username') or ''
    settings.xsubs.password = request.form.get('settings_xsubs_password') or ''
    settings.napisy24.username = request.form.get('settings_napisy24_username') or ''
    settings.napisy24.password = request.form.get('settings_napisy24_password') or ''
    settings.subscene.username = request.form.get('settings_subscene_username') or ''
    settings.subscene.password = request.form.get('settings_subscene_password') or ''
    settings.titlovi.username = request.form.get('settings_titlovi_username') or ''
    settings.titlovi.password = request.form.get('settings_titlovi_password') or ''
    settings.betaseries.token = request.form.get('settings_betaseries_token') or ''

    settings_subliminal_languages = request.form.getlist('settings_subliminal_languages')
    # Disable all languages in DB
    database.execute("UPDATE table_settings_languages SET enabled=0")
    for item in settings_subliminal_languages:
        # Enable each desired language in DB
        database.execute("UPDATE table_settings_languages SET enabled=1 WHERE code2=?", (item,))

    settings_serie_default_enabled = request.form.get('settings_serie_default_enabled')
    if settings_serie_default_enabled is None:
        settings_serie_default_enabled = 'False'
    else:
        settings_serie_default_enabled = 'True'
    settings.general.serie_default_enabled = text_type(settings_serie_default_enabled)

    settings_serie_default_languages = str(request.form.getlist('settings_serie_default_languages'))
    if settings_serie_default_languages == "['None']":
        settings_serie_default_languages = 'None'
    settings.general.serie_default_language = text_type(settings_serie_default_languages)

    settings_serie_default_hi = request.form.get('settings_serie_default_hi')
    if settings_serie_default_hi is None:
        settings_serie_default_hi = 'False'
    else:
        settings_serie_default_hi = 'True'
    settings.general.serie_default_hi = text_type(settings_serie_default_hi)

    settings_movie_default_enabled = request.form.get('settings_movie_default_enabled')
    if settings_movie_default_enabled is None:
        settings_movie_default_enabled = 'False'
    else:
        settings_movie_default_enabled = 'True'
    settings.general.movie_default_enabled = text_type(settings_movie_default_enabled)

    settings_movie_default_languages = str(request.form.getlist('settings_movie_default_languages'))
    if settings_movie_default_languages == "['None']":
        settings_movie_default_languages = 'None'
    settings.general.movie_default_language = text_type(settings_movie_default_languages)

    settings_movie_default_hi = request.form.get('settings_movie_default_hi')
    if settings_movie_default_hi is None:
        settings_movie_default_hi = 'False'
    else:
        settings_movie_default_hi = 'True'
    settings.general.movie_default_hi = text_type(settings_movie_default_hi)

    settings_movie_default_forced = str(request.form.get('settings_movie_default_forced'))
    settings.general.movie_default_forced = text_type(settings_movie_default_forced)

    with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
        settings.write(handle)

    configured()
    return redirect(base_url)


@app.route('/emptylog')
@login_required
def emptylog():
    ref = request.environ['HTTP_REFERER']

    empty_log()
    logging.info('BAZARR Log file emptied')

    redirect(ref)


@app.route('/bazarr.log')
@login_required
def download_log():
    return send_file(os.path.join(args.config_dir, 'log/'),
                     attachment_filename='bazarr.log')


@app.route('/image_proxy/<path:url>', methods=['GET'])
@login_required
def image_proxy(url):
    apikey = settings.sonarr.apikey
    url_image = (url_sonarr() + '/' + url + '?apikey=' + apikey).replace('poster-250', 'poster-500')
    try:
        req = requests.get(url_image, stream=True, timeout=15, verify=False)
    except:
        return None
    else:
        return Response(stream_with_context(req.iter_content(2048)), content_type=req.headers['content-type'])


@app.route('/image_proxy_movies/<path:url>', methods=['GET'])
@login_required
def image_proxy_movies(url):
    apikey = settings.radarr.apikey
    url_image = url_radarr() + '/' + url + '?apikey=' + apikey
    try:
        req = requests.get(url_image, stream=True, timeout=15, verify=False)
    except:
        return None
    else:
        return Response(stream_with_context(req.iter_content(2048)), content_type=req.headers['content-type'])


@app.route("/")
@login_required
def redirect_root():
    if settings.general.getboolean('use_sonarr'):
        return redirect(url_for('series'))
    elif settings.general.getboolean('use_radarr'):
        return redirect(url_for('movies'))
    elif not settings.general.enabled_providers:
        return redirect('/wizard')
    else:
        return redirect('/settings')


@app.route('/series/')
@login_required
def series():
    return render_template('series.html')


@app.route('/serieseditor/')
@login_required
def serieseditor():
    return render_template('serieseditor.html')


@app.route('/search_json/<query>', methods=['GET'])
@login_required
def search_json(query):


    query = '%' + query + '%'
    search_list = []

    if settings.general.getboolean('use_sonarr'):
        # Get matching series
        series = database.execute("SELECT title, sonarrSeriesId, year FROM table_shows WHERE title LIKE ? ORDER BY "
                                  "title ASC", (query,))
        for serie in series:
            search_list.append(dict([('name', re.sub(r'\ \(\d{4}\)', '', serie['title']) + ' (' + serie['year'] + ')'),
                                     ('url', '/episodes/' + str(serie['sonarrSeriesId']))]))

    if settings.general.getboolean('use_radarr'):
        # Get matching movies
        movies = database.execute("SELECT title, radarrId, year FROM table_movies WHERE title LIKE ? ORDER BY "
                                  "title ASC", (query,))
        for movie in movies:
            search_list.append(dict([('name', re.sub(r'\ \(\d{4}\)', '', movie['title']) + ' (' + movie['year'] + ')'),
                                     ('url', '/movie/' + str(movie['radarrId']))]))

    request.content_type = 'application/json'
    return dict(items=search_list)


@app.route('/episodes/<no>')
@login_required
def episodes(no):
    return render_template('episodes.html', id=str(no))


@app.route('/movies')
@login_required
def movies():
    return render_template('movies.html')


@app.route('/movieseditor')
@login_required
def movieseditor():
    return render_template('movieseditor.html')


@app.route('/movie/<no>')
@login_required
def movie(no):
    return render_template('movie.html', id=str(no))


@app.route('/scan_disk_movie/<int:no>', methods=['GET'])
@login_required
def scan_disk_movie(no):
    movies_scan_subtitles(no)
    return '', 200


@app.route('/search_missing_subtitles_movie/<int:no>', methods=['GET'])
@login_required
def search_missing_subtitles_movie(no):

    ref = request.environ['HTTP_REFERER']

    scheduler.add_job(movies_download_subtitles, args=[no], name=('movies_download_subtitles_' + str(no)))
    redirect(ref)


@app.route('/historyseries/')
@login_required
def historyseries():
    return render_template('historyseries.html')


@app.route('/historymovies/')
@login_required
def historymovies():
    return render_template('historymovies.html')


@app.route('/wanted')
@login_required
def wanted():

    return render_template('wanted.html', bazarr_version=bazarr_version, base_url=base_url, current_port=settings.general.port)


@app.route('/wantedseries')
@login_required
def wantedseries():


    if settings.sonarr.getboolean('only_monitored'):
        monitored_only_query_string = " AND monitored='True'"
    else:
        monitored_only_query_string = ''

    missing_count = database.execute("SELECT COUNT(*) as count FROM table_episodes WHERE missing_subtitles != '[]'" +
                                     monitored_only_query_string, only_one=True)['count']
    page = request.data
    if page == "":
        page = "1"
    page_size = int(settings.general.page_size)
    offset = (int(page) - 1) * page_size
    max_page = int(math.ceil(missing_count / (page_size + 0.0)))

    data = database.execute("SELECT table_shows.title as seriesTitle, "
                            "table_episodes.season || 'x' || table_episodes.episode as episode_number, "
                            "table_episodes.title as episodeTitle, table_episodes.missing_subtitles, table_episodes.sonarrSeriesId, "
                            "table_episodes.path, table_shows.hearing_impaired, table_episodes.sonarrEpisodeId, "
                            "table_episodes.scene_name, table_episodes.failedAttempts FROM table_episodes "
                            "INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId "
                            "WHERE table_episodes.missing_subtitles != '[]'" + monitored_only_query_string +
                            " ORDER BY table_episodes._rowid_ DESC LIMIT ? OFFSET ?", (page_size, offset))
    # path_replace
    dict_mapper.path_replace(data)

    return render_template('wantedseries.html', bazarr_version=bazarr_version, rows=data, missing_count=missing_count, page=page,
                    max_page=max_page, base_url=base_url, page_size=page_size, current_port=settings.general.port)


@app.route('/wantedmovies')
@login_required
def wantedmovies():


    if settings.radarr.getboolean('only_monitored'):
        monitored_only_query_string = " AND monitored='True'"
    else:
        monitored_only_query_string = ''

    missing_count = database.execute("SELECT COUNT(*) as count FROM table_movies WHERE missing_subtitles != '[]'" +
                                     monitored_only_query_string, only_one=True)['count']
    page = request.args.page
    if page == "":
        page = "1"
    page_size = int(settings.general.page_size)
    offset = (int(page) - 1) * page_size
    max_page = int(math.ceil(missing_count / (page_size + 0.0)))

    data = database.execute("SELECT title, missing_subtitles, radarrId, path, hearing_impaired, sceneName, "
                            "failedAttempts FROM table_movies WHERE missing_subtitles != '[]'" +
                            monitored_only_query_string + " ORDER BY _rowid_ DESC LIMIT ? OFFSET ?",
                            (page_size, offset))
    # path_replace
    dict_mapper.path_replace_movie(data)

    return render_template('wantedmovies.html', bazarr_version=bazarr_version, rows=data,
                    missing_count=missing_count, page=page, max_page=max_page, base_url=base_url, page_size=page_size,
                    current_port=settings.general.port)


@app.route('/wanted_search_missing_subtitles')
@login_required
def wanted_search_missing_subtitles_list():

    ref = request.environ['HTTP_REFERER']

    scheduler.add_job(wanted_search_missing_subtitles, name='manual_wanted_search_missing_subtitles')
    redirect(ref)


@app.route('/settings/')
@login_required
def _settings():


    settings_languages = database.execute("SELECT * FROM table_settings_languages ORDER BY name")
    settings_providers = sorted(provider_manager.names())
    settings_notifier = database.execute("SELECT * FROM table_settings_notifier ORDER BY name")

    return render_template('settings.html', bazarr_version=bazarr_version, settings=settings, settings_languages=settings_languages,
                    settings_providers=settings_providers, settings_notifier=settings_notifier, base_url=base_url,
                    current_port=settings.general.port, ast=ast, args=args, sys=sys)


@app.route('/save_settings', methods=['POST'])
@login_required
def save_settings():

    ref = request.environ['HTTP_REFERER']

    settings_general_ip = request.form.get('settings_general_ip')
    settings_general_port = request.form.get('settings_general_port')
    settings_general_baseurl = request.form.get('settings_general_baseurl')
    if not settings_general_baseurl.endswith('/'):
        settings_general_baseurl += '/'
    settings_general_debug = request.form.get('settings_general_debug')
    if settings_general_debug is None:
        settings_general_debug = 'False'
    else:
        settings_general_debug = 'True'
    settings_general_chmod_enabled = request.form.get('settings_general_chmod_enabled')
    if settings_general_chmod_enabled is None:
        settings_general_chmod_enabled = 'False'
    else:
        settings_general_chmod_enabled = 'True'
    settings_general_chmod = request.form.get('settings_general_chmod')
    settings_general_sourcepath = request.form.getlist('settings_general_sourcepath')
    settings_general_destpath = request.form.getlist('settings_general_destpath')
    settings_general_pathmapping = []
    settings_general_pathmapping.extend([list(a) for a in zip(settings_general_sourcepath, settings_general_destpath)])
    settings_general_sourcepath_movie = request.form.getlist('settings_general_sourcepath_movie')
    settings_general_destpath_movie = request.form.getlist('settings_general_destpath_movie')
    settings_general_pathmapping_movie = []
    settings_general_pathmapping_movie.extend(
        [list(a) for a in zip(settings_general_sourcepath_movie, settings_general_destpath_movie)])
    settings_general_branch = request.form.get('settings_general_branch')
    settings_general_automatic = request.form.get('settings_general_automatic')
    if settings_general_automatic is None:
        settings_general_automatic = 'False'
    else:
        settings_general_automatic = 'True'
    settings_general_update_restart = request.form.get('settings_general_update_restart')
    if settings_general_update_restart is None:
        settings_general_update_restart = 'False'
    else:
        settings_general_update_restart = 'True'
    settings_analytics_enabled = request.form.get('settings_analytics_enabled')
    if settings_analytics_enabled is None:
        settings_analytics_enabled = 'False'
    else:
        settings_analytics_enabled = 'True'
    settings_general_single_language = request.form.get('settings_general_single_language')
    if settings_general_single_language is None:
        settings_general_single_language = 'False'
    else:
        settings_general_single_language = 'True'
    settings_general_wanted_search_frequency = request.form.get('settings_general_wanted_search_frequency')
    settings_general_scenename = request.form.get('settings_general_scenename')
    if settings_general_scenename is None:
        settings_general_scenename = 'False'
    else:
        settings_general_scenename = 'True'
    settings_general_embedded = request.form.get('settings_general_embedded')
    if settings_general_embedded is None:
        settings_general_embedded = 'False'
    else:
        settings_general_embedded = 'True'
    settings_general_utf8_encode = request.form.get('settings_general_utf8_encode')
    if settings_general_utf8_encode is None:
        settings_general_utf8_encode = 'False'
    else:
        settings_general_utf8_encode = 'True'
    settings_general_ignore_pgs = request.form.get('settings_general_ignore_pgs')
    if settings_general_ignore_pgs is None:
        settings_general_ignore_pgs = 'False'
    else:
        settings_general_ignore_pgs = 'True'
    settings_general_adaptive_searching = request.form.get('settings_general_adaptive_searching')
    if settings_general_adaptive_searching is None:
        settings_general_adaptive_searching = 'False'
    else:
        settings_general_adaptive_searching = 'True'
    settings_general_multithreading = request.form.get('settings_general_multithreading')
    if settings_general_multithreading is None:
        settings_general_multithreading = 'False'
    else:
        settings_general_multithreading = 'True'
    settings_general_minimum_score = request.form.get('settings_general_minimum_score')
    settings_general_minimum_score_movies = request.form.get('settings_general_minimum_score_movies')
    settings_general_use_postprocessing = request.form.get('settings_general_use_postprocessing')
    if settings_general_use_postprocessing is None:
        settings_general_use_postprocessing = 'False'
    else:
        settings_general_use_postprocessing = 'True'
    settings_general_postprocessing_cmd = request.form.get('settings_general_postprocessing_cmd')
    settings_general_use_sonarr = request.form.get('settings_general_use_sonarr')
    if settings_general_use_sonarr is None:
        settings_general_use_sonarr = 'False'
    else:
        settings_general_use_sonarr = 'True'
    settings_general_use_radarr = request.form.get('settings_general_use_radarr')
    if settings_general_use_radarr is None:
        settings_general_use_radarr = 'False'
    else:
        settings_general_use_radarr = 'True'
    settings_page_size = request.form.get('settings_page_size')
    settings_subfolder = request.form.get('settings_subfolder')
    settings_subfolder_custom = request.form.get('settings_subfolder_custom')
    settings_upgrade_subs = request.form.get('settings_upgrade_subs')
    if settings_upgrade_subs is None:
        settings_upgrade_subs = 'False'
    else:
        settings_upgrade_subs = 'True'
    settings_upgrade_subs_frequency = request.form.get('settings_upgrade_subs_frequency')
    settings_days_to_upgrade_subs = request.form.get('settings_days_to_upgrade_subs')
    settings_upgrade_manual = request.form.get('settings_upgrade_manual')
    if settings_upgrade_manual is None:
        settings_upgrade_manual = 'False'
    else:
        settings_upgrade_manual = 'True'
    settings_anti_captcha_provider = request.form.get('settings_anti_captcha_provider')
    settings_anti_captcha_key = request.form.get('settings_anti_captcha_key')
    settings_death_by_captcha_username = request.form.get('settings_death_by_captcha_username')
    settings_death_by_captcha_password = request.form.get('settings_death_by_captcha_password')

    before = (six.text_type(settings.general.ip), int(settings.general.port), six.text_type(settings.general.base_url),
              six.text_type(settings.general.path_mappings), six.text_type(settings.general.getboolean('use_sonarr')),
              six.text_type(settings.general.getboolean('use_radarr')), six.text_type(settings.general.path_mappings_movie))
    after = (six.text_type(settings_general_ip), int(settings_general_port), six.text_type(settings_general_baseurl),
             six.text_type(settings_general_pathmapping), six.text_type(settings_general_use_sonarr),
             six.text_type(settings_general_use_radarr), six.text_type(settings_general_pathmapping_movie))

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
    settings.analytics.enabled = text_type(settings_analytics_enabled)
    settings.general.single_language = text_type(settings_general_single_language)
    settings.general.minimum_score = text_type(settings_general_minimum_score)
    settings.general.wanted_search_frequency = text_type(settings_general_wanted_search_frequency)
    settings.general.use_scenename = text_type(settings_general_scenename)
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
    settings.general.upgrade_frequency = text_type(settings_upgrade_subs_frequency)
    settings.general.days_to_upgrade_subs = text_type(settings_days_to_upgrade_subs)
    settings.general.upgrade_manual = text_type(settings_upgrade_manual)
    settings.general.anti_captcha_provider = text_type(settings_anti_captcha_provider)
    settings.anticaptcha.anti_captcha_key = text_type(settings_anti_captcha_key)
    settings.deathbycaptcha.username = text_type(settings_death_by_captcha_username)
    settings.deathbycaptcha.password = text_type(settings_death_by_captcha_password)

    # set anti-captcha provider and key
    if settings.general.anti_captcha_provider == 'anti-captcha':
        os.environ["ANTICAPTCHA_CLASS"] = 'AntiCaptchaProxyLess'
        os.environ["ANTICAPTCHA_ACCOUNT_KEY"] = str(settings.anticaptcha.anti_captcha_key)
    elif settings.general.anti_captcha_provider == 'death-by-captcha':
        os.environ["ANTICAPTCHA_CLASS"] = 'DeathByCaptchaProxyLess'
        os.environ["ANTICAPTCHA_ACCOUNT_KEY"] = str(':'.join(
            {settings.deathbycaptcha.username, settings.deathbycaptcha.password}))
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

    settings_proxy_type = request.form.get('settings_proxy_type')
    settings_proxy_url = request.form.get('settings_proxy_url')
    settings_proxy_port = request.form.get('settings_proxy_port')
    settings_proxy_username = request.form.get('settings_proxy_username')
    settings_proxy_password = request.form.get('settings_proxy_password')
    settings_proxy_exclude = request.form.get('settings_proxy_exclude')

    before_proxy_password = (six.text_type(settings.proxy.type), six.text_type(settings.proxy.exclude))
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

    settings_auth_type = request.form.get('settings_auth_type')
    settings_auth_username = request.form.get('settings_auth_username')
    settings_auth_password = request.form.get('settings_auth_password')

    if settings.auth.type != settings_auth_type:
        configured()
    if settings.auth.password == settings_auth_password:
        settings.auth.type = text_type(settings_auth_type)
        settings.auth.username = text_type(settings_auth_username)
    else:
        settings.auth.type = text_type(settings_auth_type)
        settings.auth.username = text_type(settings_auth_username)
        settings.auth.password = hashlib.md5(settings_auth_password.encode('utf-8')).hexdigest()
    settings.auth.apikey = request.form.get('settings_auth_apikey')

    settings_sonarr_ip = request.form.get('settings_sonarr_ip')
    settings_sonarr_port = request.form.get('settings_sonarr_port')
    settings_sonarr_baseurl = request.form.get('settings_sonarr_baseurl')
    settings_sonarr_ssl = request.form.get('settings_sonarr_ssl')
    if settings_sonarr_ssl is None:
        settings_sonarr_ssl = 'False'
    else:
        settings_sonarr_ssl = 'True'
    settings_sonarr_apikey = request.form.get('settings_sonarr_apikey')
    settings_sonarr_only_monitored = request.form.get('settings_sonarr_only_monitored')
    if settings_sonarr_only_monitored is None:
        settings_sonarr_only_monitored = 'False'
    else:
        settings_sonarr_only_monitored = 'True'
    settings_sonarr_sync = request.form.get('settings_sonarr_sync')
    settings_sonarr_sync_day = request.form.get('settings_sonarr_sync_day')
    settings_sonarr_sync_hour = request.form.get('settings_sonarr_sync_hour')

    settings.sonarr.ip = text_type(settings_sonarr_ip)
    settings.sonarr.port = text_type(settings_sonarr_port)
    settings.sonarr.base_url = text_type(settings_sonarr_baseurl)
    settings.sonarr.ssl = text_type(settings_sonarr_ssl)
    settings.sonarr.apikey = text_type(settings_sonarr_apikey)
    settings.sonarr.only_monitored = text_type(settings_sonarr_only_monitored)
    settings.sonarr.full_update = text_type(settings_sonarr_sync)
    settings.sonarr.full_update_day = text_type(settings_sonarr_sync_day)
    settings.sonarr.full_update_hour = text_type(settings_sonarr_sync_hour)

    settings_radarr_ip = request.form.get('settings_radarr_ip')
    settings_radarr_port = request.form.get('settings_radarr_port')
    settings_radarr_baseurl = request.form.get('settings_radarr_baseurl')
    settings_radarr_ssl = request.form.get('settings_radarr_ssl')
    if settings_radarr_ssl is None:
        settings_radarr_ssl = 'False'
    else:
        settings_radarr_ssl = 'True'
    settings_radarr_apikey = request.form.get('settings_radarr_apikey')
    settings_radarr_only_monitored = request.form.get('settings_radarr_only_monitored')
    if settings_radarr_only_monitored is None:
        settings_radarr_only_monitored = 'False'
    else:
        settings_radarr_only_monitored = 'True'
    settings_radarr_sync = request.form.get('settings_radarr_sync')
    settings_radarr_sync_day = request.form.get('settings_radarr_sync_day')
    settings_radarr_sync_hour = request.form.get('settings_radarr_sync_hour')

    settings.radarr.ip = text_type(settings_radarr_ip)
    settings.radarr.port = text_type(settings_radarr_port)
    settings.radarr.base_url = text_type(settings_radarr_baseurl)
    settings.radarr.ssl = text_type(settings_radarr_ssl)
    settings.radarr.apikey = text_type(settings_radarr_apikey)
    settings.radarr.only_monitored = text_type(settings_radarr_only_monitored)
    settings.radarr.full_update = text_type(settings_radarr_sync)
    settings.radarr.full_update_day = text_type(settings_radarr_sync_day)
    settings.radarr.full_update_hour = text_type(settings_radarr_sync_hour)

    settings_subliminal_providers = request.form.getlist('settings_subliminal_providers')
    settings.general.enabled_providers = u'' if not settings_subliminal_providers else ','.join(
        settings_subliminal_providers)

    settings_addic7ed_random_agents = request.form.get('settings_addic7ed_random_agents')
    if settings_addic7ed_random_agents is None:
        settings_addic7ed_random_agents = 'False'
    else:
        settings_addic7ed_random_agents = 'True'

    settings_opensubtitles_vip = request.form.get('settings_opensubtitles_vip')
    if settings_opensubtitles_vip is None:
        settings_opensubtitles_vip = 'False'
    else:
        settings_opensubtitles_vip = 'True'

    settings_opensubtitles_ssl = request.form.get('settings_opensubtitles_ssl')
    if settings_opensubtitles_ssl is None:
        settings_opensubtitles_ssl = 'False'
    else:
        settings_opensubtitles_ssl = 'True'

    settings_opensubtitles_skip_wrong_fps = request.form.get('settings_opensubtitles_skip_wrong_fps')
    if settings_opensubtitles_skip_wrong_fps is None:
        settings_opensubtitles_skip_wrong_fps = 'False'
    else:
        settings_opensubtitles_skip_wrong_fps = 'True'

    settings.addic7ed.username = request.form.get('settings_addic7ed_username')
    settings.addic7ed.password = request.form.get('settings_addic7ed_password')
    settings.addic7ed.random_agents = text_type(settings_addic7ed_random_agents)
    settings.assrt.token = request.form.get('settings_assrt_token')
    settings.legendasdivx.username = request.form.get('settings_legendasdivx_username')
    settings.legendasdivx.password = request.form.get('settings_legendasdivx_password')
    settings.legendastv.username = request.form.get('settings_legendastv_username')
    settings.legendastv.password = request.form.get('settings_legendastv_password')
    settings.opensubtitles.username = request.form.get('settings_opensubtitles_username')
    settings.opensubtitles.password = request.form.get('settings_opensubtitles_password')
    settings.opensubtitles.vip = text_type(settings_opensubtitles_vip)
    settings.opensubtitles.ssl = text_type(settings_opensubtitles_ssl)
    settings.opensubtitles.skip_wrong_fps = text_type(settings_opensubtitles_skip_wrong_fps)
    settings.xsubs.username = request.form.get('settings_xsubs_username')
    settings.xsubs.password = request.form.get('settings_xsubs_password')
    settings.napisy24.username = request.form.get('settings_napisy24_username')
    settings.napisy24.password = request.form.get('settings_napisy24_password')
    settings.subscene.username = request.form.get('settings_subscene_username')
    settings.subscene.password = request.form.get('settings_subscene_password')
    settings.titlovi.username = request.form.get('settings_titlovi_username')
    settings.titlovi.password = request.form.get('settings_titlovi_password')
    settings.betaseries.token = request.form.get('settings_betaseries_token')

    settings_subliminal_languages = request.form.getlist('settings_subliminal_languages')
    database.execute("UPDATE table_settings_languages SET enabled=0")
    for item in settings_subliminal_languages:
        database.execute("UPDATE table_settings_languages SET enabled=1 WHERE code2=?", (item,))

    settings_serie_default_enabled = request.form.get('settings_serie_default_enabled')
    if settings_serie_default_enabled is None:
        settings_serie_default_enabled = 'False'
    else:
        settings_serie_default_enabled = 'True'
    settings.general.serie_default_enabled = text_type(settings_serie_default_enabled)

    settings_serie_default_languages = str(request.form.getlist('settings_serie_default_languages'))
    if settings_serie_default_languages == "['None']":
        settings_serie_default_languages = 'None'
    settings.general.serie_default_language = text_type(settings_serie_default_languages)

    settings_serie_default_hi = request.form.get('settings_serie_default_hi')
    if settings_serie_default_hi is None:
        settings_serie_default_hi = 'False'
    else:
        settings_serie_default_hi = 'True'
    settings.general.serie_default_hi = text_type(settings_serie_default_hi)

    settings_serie_default_forced = str(request.form.get('settings_serie_default_forced'))
    settings.general.serie_default_forced = text_type(settings_serie_default_forced)

    settings_movie_default_enabled = request.form.get('settings_movie_default_enabled')
    if settings_movie_default_enabled is None:
        settings_movie_default_enabled = 'False'
    else:
        settings_movie_default_enabled = 'True'
    settings.general.movie_default_enabled = text_type(settings_movie_default_enabled)

    settings_movie_default_languages = str(request.form.getlist('settings_movie_default_languages'))
    if settings_movie_default_languages == "['None']":
        settings_movie_default_languages = 'None'
    settings.general.movie_default_language = text_type(settings_movie_default_languages)

    settings_movie_default_hi = request.form.get('settings_movie_default_hi')
    if settings_movie_default_hi is None:
        settings_movie_default_hi = 'False'
    else:
        settings_movie_default_hi = 'True'
    settings.general.movie_default_hi = text_type(settings_movie_default_hi)

    settings_movie_default_forced = str(request.form.get('settings_movie_default_forced'))
    settings.general.movie_default_forced = text_type(settings_movie_default_forced)

    with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
        settings.write(handle)

    configure_logging(settings.general.getboolean('debug') or args.debug)

    notifiers = database.execute("SELECT * FROM table_settings_notifier ORDER BY name")
    for notifier in notifiers:
        enabled = request.form.get('settings_notifier_' + notifier['name'] + '_enabled')
        if enabled == 'on':
            enabled = 1
        else:
            enabled = 0
        notifier_url = request.form.get('settings_notifier_' + notifier['name'] + '_url')
        database.execute("UPDATE table_settings_notifier SET enabled=?, url=? WHERE name=?",
                         (enabled,notifier_url,notifier['name']))

    scheduler.update_configurable_tasks()
    logging.info('BAZARR Settings saved succesfully.')

    if ref.find('saved=true') > 0:
        return redirect(ref)
    else:
        return redirect(ref + "?saved=true")


@app.route('/check_update')
@login_required
def check_update():

    ref = request.environ['HTTP_REFERER']

    if not args.no_update:
        check_and_apply_update()

    redirect(ref)


@app.route('/system')
@login_required
def system():


    task_list = scheduler.get_task_list()

    throttled_providers = list_throttled_providers()

    try:
        with io.open(os.path.join(args.config_dir, 'config', 'releases.txt'), 'r', encoding='UTF-8') as f:
            releases = ast.literal_eval(f.read())
    except Exception as e:
        releases = []
        logging.exception(
            'BAZARR cannot parse releases caching file: ' + os.path.join(args.config_dir, 'config', 'releases.txt'))

    sonarr_version = get_sonarr_version()

    radarr_version = get_radarr_version()

    page_size = int(settings.general.page_size)

    return render_template('system.html', bazarr_version=bazarr_version,
                    sonarr_version=sonarr_version, radarr_version=radarr_version,
                    operating_system=platform.platform(), python_version=platform.python_version(),
                    config_dir=args.config_dir, bazarr_dir=os.path.normcase(os.path.dirname(os.path.dirname(__file__))),
                    base_url=base_url, task_list=task_list, page_size=page_size, releases=releases,
                    current_port=settings.general.port, throttled_providers=throttled_providers)


@app.route('/logs')
@login_required
def get_logs():

    logs = []
    with io.open(os.path.join(args.config_dir, 'log', 'bazarr.log'), encoding='UTF-8') as file:
        for line in file.readlines():
            lin = []
            lin = line.split('|')
            logs.append(lin)
        logs.reverse()

    return dict(data=logs)


@app.route('/execute/<taskid>')
@login_required
def execute_task(taskid):
    scheduler.execute_now(taskid)
    return '', 200


@app.route('/remove_subtitles_movie', methods=['POST'])
@login_required
def remove_subtitles_movie():
    moviePath = request.form.get('moviePath')
    language = request.form.get('language')
    subtitlesPath = request.form.get('subtitlesPath')
    radarrId = request.form.get('radarrId')

    try:
        os.remove(subtitlesPath)
        result = language_from_alpha3(language) + " subtitles deleted from disk."
        history_log_movie(0, radarrId, result, language=alpha2_from_alpha3(language))
    except OSError as e:
        logging.exception('BAZARR cannot delete subtitles file: ' + subtitlesPath)
    store_subtitles_movie(path_replace_reverse_movie(moviePath), moviePath)


@app.route('/get_subtitle_movie', methods=['POST'])
@login_required
def get_subtitle_movie():

    ref = request.environ['HTTP_REFERER']

    moviePath = request.form.get('moviePath')
    sceneName = request.form.get('sceneName')
    if sceneName == "null":
        sceneName = "None"
    language = request.form.get('language')
    hi = request.form.get('hi').capitalize()
    forced = request.form.get('forced').capitalize()
    radarrId = request.form.get('radarrId')
    title = request.form.get('title')
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
            store_subtitles_movie(path, moviePath)
        redirect(ref)
    except OSError:
        pass


@app.route('/manual_search_movie', methods=['POST'])
@login_required
def manual_search_movie_json():


    moviePath = request.form.get('moviePath')
    sceneName = request.form.get('sceneName')
    if sceneName == "null":
        sceneName = "None"
    language = request.form.get('language')
    hi = request.form.get('hi').capitalize()
    forced = request.form.get('forced').capitalize()
    title = request.form.get('title')
    providers_list = get_providers()
    providers_auth = get_providers_auth()

    data = manual_search(moviePath, language, hi, forced, providers_list, providers_auth, sceneName, title, 'movie')
    return dict(data=data)


@app.route('/manual_get_subtitle_movie', methods=['POST'])
@login_required
def manual_get_subtitle_movie():

    ref = request.environ['HTTP_REFERER']

    moviePath = request.form.get('moviePath')
    sceneName = request.form.get('sceneName')
    if sceneName == "null":
        sceneName = "None"
    language = request.form.get('language')
    hi = request.form.get('hi').capitalize()
    forced = request.form.get('forced').capitalize()
    selected_provider = request.form.get('provider')
    subtitle = request.form.get('subtitle')
    radarrId = request.form.get('radarrId')
    title = request.form.get('title')
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
            store_subtitles_movie(path, moviePath)
        redirect(ref)
    except OSError:
        pass


@app.route('/manual_upload_subtitle_movie', methods=['POST'])
@login_required
def perform_manual_upload_subtitle_movie():

    ref = request.environ['HTTP_REFERER']

    moviePath = request.form.get('moviePath')
    sceneName = request.form.get('sceneName')
    if sceneName == "null":
        sceneName = "None"
    language = request.form.get('language')
    forced = True if request.form.get('forced') == '1' else False
    upload = request.files.get('upload')
    radarrId = request.form.get('radarrId')
    title = request.form.get('title')

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
            store_subtitles_movie(path, moviePath)

        redirect(ref)
    except OSError:
        pass


def configured():
    database.execute("UPDATE system SET configured = 1")


@app.route('/api/series/wanted')
def api_wanted():
    data = database.execute("SELECT table_shows.title as seriesTitle, table_episodes.season || 'x' || table_episodes.episode as episode_number, "
                            "table_episodes.title as episodeTitle, table_episodes.missing_subtitles FROM table_episodes "
                            "INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId "
                            "WHERE table_episodes.missing_subtitles != '[]' ORDER BY table_episodes._rowid_ DESC "
                            "LIMIT 10")

    wanted_subs = []
    for item in data:
        wanted_subs.append([item['seriesTitle'], item['episode_number'], item['episodeTitle'], item['missing_subtitles']])

    return dict(subtitles=wanted_subs)


@app.route('/api/series/history')
def api_history():
    data = database.execute("SELECT table_shows.title as seriesTitle, "
                            "table_episodes.season || 'x' || table_episodes.episode as episode_number, "
                            "table_episodes.title as episodeTitle, "
                            "strftime('%Y-%m-%d', datetime(table_history.timestamp, 'unixepoch')) as date, "
                            "table_history.description FROM table_history "
                            "INNER JOIN table_shows on table_shows.sonarrSeriesId = table_history.sonarrSeriesId "
                            "INNER JOIN table_episodes on table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId "
                            "WHERE table_history.action != '0' ORDER BY id DESC LIMIT 10")

    history_subs = []
    for item in data:
        history_subs.append([item['seriesTitle'], item['episode_number'], item['episodeTitle'], item['date'], item['description']])

    return dict(subtitles=history_subs)


@app.route('/api/movies/wanted/')
def api_movies_wanted():
    data = database.execute("SELECT table_movies.title, table_movies.missing_subtitles FROM table_movies "
                            "WHERE table_movies.missing_subtitles != '[]' ORDER BY table_movies._rowid_ DESC LIMIT 10")

    wanted_subs = []
    for item in data:
        wanted_subs.append([item['title'], item['missing_subtitles']])

    return dict(subtitles=wanted_subs)


@app.route('/api/movies/history/')
def api_movies_history():
    data = database.execute("SELECT table_movies.title, strftime('%Y-%m-%d', "
                            "datetime(table_history_movie.timestamp, 'unixepoch')) as date, "
                            "table_history_movie.description FROM table_history_movie "
                            "INNER JOIN table_movies on table_movies.radarrId = table_history_movie.radarrId "
                            "WHERE table_history_movie.action != '0' ORDER BY id DESC LIMIT 10")

    history_subs = []
    for item in data:
        history_subs.append([item['title'], item['date'], item['description']])

    return dict(subtitles=history_subs)


@app.route('/test_url/<protocol>/<path:url>', methods=['GET'])
@login_required
def test_url(protocol, url):

    url = six.moves.urllib.parse.unquote(url)
    try:
        result = requests.get(protocol + "://" + url, allow_redirects=False, verify=False).json()['version']
    except:
        return dict(status=False)
    else:
        return dict(status=True, version=result)


@app.route('/test_notification/<protocol>/<path:provider>', methods=['GET'])
@login_required
def test_notification(protocol, provider):

    provider = six.moves.urllib.parse.unquote(provider)
    apobj = apprise.Apprise()
    apobj.add(protocol + "://" + provider)

    apobj.notify(
        title='Bazarr test notification',
        body=('Test notification')
    )


@app.route('/notifications')
@login_required
def notifications():
    if queueconfig.notifications:
        test = queueconfig.notifications
        return queueconfig.notifications.read() or ''
    else:
        return abort(400)


@app.route('/running_tasks')
@login_required
def running_tasks_list():

    return dict(tasks=scheduler.get_running_tasks())


@app.route('/episode_history/<int:no>')
@login_required
def episode_history(no):

    episode_history = database.execute("SELECT action, timestamp, language, provider, score FROM table_history "
                                       "WHERE sonarrEpisodeId=? ORDER BY timestamp DESC", (no,))
    for item in episode_history:
        item['timestamp'] = "<div data-tooltip='" + \
                            time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(item['timestamp'])) + "'>" + \
                            pretty.date(datetime.fromtimestamp(item['timestamp'])) + "</div>"
        if item['language']:
            item['language'] = language_from_alpha2(item['language'])
        else:
            item['language'] = "<i>undefined</i>"
        if item['score']:
            item['score'] = str(round((int(item['score']) * 100 / 360), 2)) + "%"

    return dict(data=episode_history)


@app.route('/movie_history/<int:no>')
@login_required
def movie_history(no):

    movie_history = database.execute("SELECT action, timestamp, language, provider, score FROM table_history_movie "
                                     "WHERE radarrId=? ORDER BY timestamp DESC", (no,))
    for item in movie_history:
        if item['action'] == 0:
            item['action'] = "<div class ='ui inverted basic compact icon' data-tooltip='Subtitle file has been " \
                             "erased.' data-inverted='' data-position='top left'><i class='ui trash icon'></i></div>"
        elif item['action'] == 1:
            item['action'] = "<div class ='ui inverted basic compact icon' data-tooltip='Subtitle file has been " \
                             "downloaded.' data-inverted='' data-position='top left'><i class='ui download " \
                             "icon'></i></div>"
        elif item['action'] == 2:
            item['action'] = "<div class ='ui inverted basic compact icon' data-tooltip='Subtitle file has been " \
                             "manually downloaded.' data-inverted='' data-position='top left'><i class='ui user " \
                             "icon'></i></div>"
        elif item['action'] == 3:
            item['action'] = "<div class ='ui inverted basic compact icon' data-tooltip='Subtitle file has been " \
                             "upgraded.' data-inverted='' data-position='top left'><i class='ui recycle " \
                             "icon'></i></div>"
        elif item['action'] == 4:
            item['action'] = "<div class ='ui inverted basic compact icon' data-tooltip='Subtitle file has been " \
                             "manually uploaded.' data-inverted='' data-position='top left'><i class='ui cloud " \
                             "upload icon'></i></div>"

        item['timestamp'] = "<div data-tooltip='" + \
                            time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(item['timestamp'])) + "'>" + \
                            pretty.date(datetime.fromtimestamp(item['timestamp'])) + "</div>"
        if item['language']:
            item['language'] = language_from_alpha2(item['language'])
        else:
            item['language'] = "<i>undefined</i>"
        if item['score']:
            item['score'] = str(round((int(item['score']) * 100 / 120), 2)) + '%'

    return dict(data=movie_history)


# Mute DeprecationWarning
warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", BrokenPipeError)
if args.dev:
    server = app.run(
        host=str(settings.general.ip), port=(int(args.port) if args.port else int(settings.general.port)))
else:
    server = CherryPyWSGIServer((str(settings.general.ip), (int(args.port) if args.port else int(settings.general.port))), app)
try:
    logging.info('BAZARR is started and waiting for request on http://' + str(settings.general.ip) + ':' + (str(
        args.port) if args.port else str(settings.general.port)) + str(base_url))
    if not args.dev:
        server.start()
except KeyboardInterrupt:
    doShutdown()

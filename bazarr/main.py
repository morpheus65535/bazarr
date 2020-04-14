# coding=utf-8

bazarr_version = '0.9'

import os
os.environ["SZ_USER_AGENT"] = "Bazarr/1"
os.environ["BAZARR_VERSION"] = bazarr_version

import gc
import sys
import libs
import io

import pretty
import ast
import hashlib
import warnings
import queueconfig
import apprise
import requests


from get_args import args
from logger import empty_log
from config import settings, url_sonarr, url_radarr, url_radarr_short, url_sonarr_short, base_url

from init import *
import logging
from database import database, dict_mapper

from notifier import update_notifier

from cherrypy.wsgiserver import CherryPyWSGIServer

from urllib.parse import unquote
from datetime import datetime
from get_languages import load_language_in_db, language_from_alpha3, language_from_alpha2, alpha2_from_alpha3
from flask import make_response, request, redirect, abort, render_template, Response, session, flash, url_for, \
    send_file, stream_with_context

from get_series import *
from get_episodes import *
from get_movies import *

from scheduler import Scheduler
from check_update import check_and_apply_update
from subliminal_patch.extensions import provider_registry as provider_manager
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
    test = settings.auth.type
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
            stop_file.write(str(''))
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
            restart_file.write(str(''))
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

    settings.general.ip = str(settings_general_ip)
    settings.general.port = str(settings_general_port)
    settings.general.base_url = str(settings_general_baseurl)
    settings.general.path_mappings = str(settings_general_pathmapping)
    settings.general.single_language = str(settings_general_single_language)
    settings.general.use_sonarr = str(settings_general_use_sonarr)
    settings.general.use_radarr = str(settings_general_use_radarr)
    settings.general.path_mappings_movie = str(settings_general_pathmapping_movie)
    settings.general.subfolder = str(settings_subfolder)
    settings.general.subfolder_custom = str(settings_subfolder_custom)
    settings.general.use_embedded_subs = str(settings_general_embedded)
    settings.general.upgrade_subs = str(settings_upgrade_subs)
    settings.general.days_to_upgrade_subs = str(settings_days_to_upgrade_subs)
    settings.general.upgrade_manual = str(settings_upgrade_manual)

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

    settings.sonarr.ip = str(settings_sonarr_ip)
    settings.sonarr.port = str(settings_sonarr_port)
    settings.sonarr.base_url = str(settings_sonarr_baseurl)
    settings.sonarr.ssl = str(settings_sonarr_ssl)
    settings.sonarr.apikey = str(settings_sonarr_apikey)
    settings.sonarr.only_monitored = str(settings_sonarr_only_monitored)

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

    settings.radarr.ip = str(settings_radarr_ip)
    settings.radarr.port = str(settings_radarr_port)
    settings.radarr.base_url = str(settings_radarr_baseurl)
    settings.radarr.ssl = str(settings_radarr_ssl)
    settings.radarr.apikey = str(settings_radarr_apikey)
    settings.radarr.only_monitored = str(settings_radarr_only_monitored)

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
    settings.addic7ed.random_agents = str(settings_addic7ed_random_agents) or ''
    settings.assrt.token = request.form.get('settings_assrt_token') or ''
    settings.legendasdivx.username = request.form.get('settings_legendasdivx_username') or ''
    settings.legendasdivx.password = request.form.get('settings_legendasdivx_password') or ''
    settings.legendastv.username = request.form.get('settings_legendastv_username') or ''
    settings.legendastv.password = request.form.get('settings_legendastv_password') or ''
    settings.opensubtitles.username = request.form.get('settings_opensubtitles_username') or ''
    settings.opensubtitles.password = request.form.get('settings_opensubtitles_password') or ''
    settings.opensubtitles.vip = str(settings_opensubtitles_vip)
    settings.opensubtitles.ssl = str(settings_opensubtitles_ssl)
    settings.opensubtitles.skip_wrong_fps = str(settings_opensubtitles_skip_wrong_fps)
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
    settings.general.serie_default_enabled = str(settings_serie_default_enabled)

    settings_serie_default_languages = str(request.form.getlist('settings_serie_default_languages'))
    if settings_serie_default_languages == "['None']":
        settings_serie_default_languages = 'None'
    settings.general.serie_default_language = str(settings_serie_default_languages)

    settings_serie_default_hi = request.form.get('settings_serie_default_hi')
    if settings_serie_default_hi is None:
        settings_serie_default_hi = 'False'
    else:
        settings_serie_default_hi = 'True'
    settings.general.serie_default_hi = str(settings_serie_default_hi)

    settings_movie_default_enabled = request.form.get('settings_movie_default_enabled')
    if settings_movie_default_enabled is None:
        settings_movie_default_enabled = 'False'
    else:
        settings_movie_default_enabled = 'True'
    settings.general.movie_default_enabled = str(settings_movie_default_enabled)

    settings_movie_default_languages = str(request.form.getlist('settings_movie_default_languages'))
    if settings_movie_default_languages == "['None']":
        settings_movie_default_languages = 'None'
    settings.general.movie_default_language = str(settings_movie_default_languages)

    settings_movie_default_hi = request.form.get('settings_movie_default_hi')
    if settings_movie_default_hi is None:
        settings_movie_default_hi = 'False'
    else:
        settings_movie_default_hi = 'True'
    settings.general.movie_default_hi = str(settings_movie_default_hi)

    settings_movie_default_forced = str(request.form.get('settings_movie_default_forced'))
    settings.general.movie_default_forced = str(settings_movie_default_forced)

    with open(os.path.join(args.config_dir, 'config', 'config.ini'), 'w+') as handle:
        settings.write(handle)

    configured()
    return redirect(base_url)


@app.route('/emptylog')
@login_required
def emptylog():
    empty_log()
    return '', 200


@app.route('/bazarr.log')
@login_required
def download_log():
    r = Response()
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return send_file(os.path.join(args.config_dir, 'log', 'bazarr.log'), cache_timeout=0)


@app.route('/image_proxy/<path:url>', methods=['GET'])
@login_required
def image_proxy(url):
    apikey = settings.sonarr.apikey
    url_image = (url_sonarr() + '/api/' + url + '?apikey=' + apikey).replace('poster-250', 'poster-500')
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
    url_image = url_radarr() + '/api/' + url + '?apikey=' + apikey
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


@app.route('/history/series/')
@login_required
def historyseries():
    return render_template('historyseries.html')


@app.route('/history/movies/')
@login_required
def historymovies():
    return render_template('historymovies.html')


@app.route('/wanted/series/')
@login_required
def wantedseries():
    return render_template('wantedseries.html')


@app.route('/wanted/movies/')
@login_required
def wantedmovies():
    return render_template('wantedmovies.html')


@app.route('/settings/general/')
@login_required
def settingsgeneral():
    return render_template('settingsgeneral.html')


@app.route('/settings/sonarr/')
@login_required
def settingssonarr():
    return render_template('settingssonarr.html')


@app.route('/settings/radarr/')
@login_required
def settingsradarr():
    return render_template('settingsradarr.html')


@app.route('/check_update')
@login_required
def check_update():
    if not args.no_update:
        check_and_apply_update()

    return '', 200


@app.route('/system/tasks')
@login_required
def systemtasks():
    return render_template('systemtasks.html')


@app.route('/system/logs')
@login_required
def systemlogs():
    return render_template('systemlogs.html')


@app.route('/system/providers')
@login_required
def systemproviders():
    return render_template('systemproviders.html')


@app.route('/system/status')
@login_required
def systemstatus():
    return render_template('systemstatus.html')


@app.route('/system/releases')
@login_required
def systemreleases():
    return render_template('systemreleases.html')


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


@app.route('/test_url', methods=['GET'])
@app.route('/test_url/<protocol>/<path:url>', methods=['GET'])
@login_required
def test_url(protocol, url):
    url = unquote(url)
    try:
        result = requests.get(url, allow_redirects=False, verify=False).json()['version']
    except Exception as e:
        logging.exception('BAZARR cannot successfully contact this URL: ' + url)
        return dict(status=False)
    else:
        return dict(status=True, version=result)


@app.route('/test_notification/<protocol>/<path:provider>', methods=['GET'])
@login_required
def test_notification(protocol, provider):

    provider = unquote(provider)
    apobj = apprise.Apprise()
    apobj.add(protocol + "://" + provider)

    apobj.notify(
        title='Bazarr test notification',
        body='Test notification'
    )


# Mute DeprecationWarning
warnings.simplefilter("ignore", DeprecationWarning)
# Mute Insecure HTTPS requests made to Sonarr and Radarr
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
# Mute Python3 BrokenPipeError
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
